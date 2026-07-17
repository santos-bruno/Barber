"""Endpoints de autenticação e cadastro de barbearias."""
import re
import unicodedata
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import email_send
import models
import schemas
from database import get_db
from hardening import rate_limit
from plans import TRIAL_DAYS
from security import (
    create_token,
    get_current_tenant,
    get_current_user,
    hash_password,
    require_owner,
    verify_password,
)



from seeds import seed_tenant_defaults

router = APIRouter(prefix="/auth", tags=["auth"])


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "barbearia"


def unique_slug(db: Session, base: str) -> str:
    slug = slugify(base)
    candidate = slug
    i = 1
    while db.query(models.Tenant).filter(models.Tenant.slug == candidate).first():
        i += 1
        candidate = f"{slug}-{i}"
    return candidate


@router.post(
    "/register",
    response_model=schemas.AuthOut,
    status_code=201,
    dependencies=[Depends(rate_limit("register", 6, 3600))],  # 6 cadastros/h por IP
)
def register(
    payload: schemas.RegisterInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(models.User).filter(models.User.email == payload.email.lower()).first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter ao menos 6 caracteres.")

    tenant = models.Tenant(
        name=payload.barbershop_name.strip(),
        slug=unique_slug(db, payload.barbershop_name),
        address=payload.address.strip(),
        whatsapp=payload.whatsapp.strip(),
        subscription_status="trial",
        trial_ends_at=datetime.utcnow() + timedelta(days=TRIAL_DAYS),
    )
    db.add(tenant)
    db.flush()

    user = models.User(
        tenant_id=tenant.id,
        name=payload.owner_name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    seed_tenant_defaults(db, tenant.id)
    db.commit()
    db.refresh(tenant)
    db.refresh(user)

    # E-mail de boas-vindas para a barbearia (best-effort, em segundo plano).
    background_tasks.add_task(
        email_send.send_welcome,
        user.name,
        tenant.name,
        user.email,
        tenant.slug,
        TRIAL_DAYS,
    )
    # Aviso para o dono do SaaS: nova barbearia cadastrada.
    background_tasks.add_task(
        email_send.send_owner_new_signup,
        tenant.name,
        user.name,
        user.email,
        tenant.whatsapp,
    )

    return schemas.AuthOut(token=create_token(user), user=user, tenant=tenant)


@router.post(
    "/login",
    response_model=schemas.AuthOut,
    dependencies=[Depends(rate_limit("login", 12, 60))],  # 12 tentativas/min por IP
)
def login(payload: schemas.LoginInput, db: Session = Depends(get_db)):
    user = (
        db.query(models.User).filter(models.User.email == payload.email.lower()).first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    if not user.active:
        raise HTTPException(status_code=403, detail="Acesso desativado. Fale com o dono da barbearia.")
    tenant = db.get(models.Tenant, user.tenant_id)
    return schemas.AuthOut(token=create_token(user), user=user, tenant=tenant)


@router.get("/me", response_model=schemas.AuthOut)
def me(
    user: models.User = Depends(get_current_user),
    tenant: models.Tenant = Depends(get_current_tenant),
):
    # Reaproveita AuthOut sem gerar novo token (o cliente já tem o seu).
    return schemas.AuthOut(token="", user=user, tenant=tenant)


@router.patch("/tenant", response_model=schemas.TenantOut)
def update_tenant(
    payload: schemas.TenantUpdate,
    _owner: models.User = Depends(require_owner),
    tenant: models.Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Atualiza os dados da barbearia (nome, WhatsApp, endereço e logo/foto).
    Só o dono pode alterar."""
    if payload.name is not None:
        name = payload.name.strip()
        if name:
            tenant.name = name
    if payload.whatsapp is not None:
        tenant.whatsapp = payload.whatsapp.strip()
    if payload.address is not None:
        tenant.address = payload.address.strip()
    if payload.logo_url is not None:
        logo = payload.logo_url.strip()
        # Aceita só data URL de imagem ou vazio (para remover) — evita URLs externas.
        if logo and not logo.startswith("data:image/"):
            raise HTTPException(status_code=400, detail="Logo inválida.")
        tenant.logo_url = logo
    if payload.min_cancel_hours is not None:
        tenant.min_cancel_hours = payload.min_cancel_hours
    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/change-password")
def change_password(
    payload: schemas.ChangePasswordInput,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="A nova senha deve ter ao menos 6 caracteres.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}
