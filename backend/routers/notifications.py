"""Registro de tokens de dispositivo (push) e utilidades de envio."""
import os
import secrets as _secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import get_db
from security import get_current_tenant, get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

SUPERADMIN_KEY = os.getenv("SUPERADMIN_KEY", "")


class TokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=400)
    platform: str = Field(default="android", max_length=20)


def _upsert(db: Session, token: str, platform: str, *, user_id=None, tenant_id=None, is_admin=False):
    row = db.query(models.PushToken).filter(models.PushToken.token == token).first()
    if row:
        row.user_id = user_id
        row.tenant_id = tenant_id
        row.is_admin = is_admin
        row.platform = platform
    else:
        db.add(models.PushToken(
            token=token, platform=platform, user_id=user_id,
            tenant_id=tenant_id, is_admin=is_admin,
        ))
    db.commit()


@router.post("/register")
def register(
    payload: TokenIn,
    user: models.User = Depends(get_current_user),
    tenant: models.Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """O app registra o token do aparelho para receber avisos de agendamento."""
    _upsert(db, payload.token, payload.platform, user_id=user.id, tenant_id=tenant.id)
    return {"ok": True}


@router.delete("/register")
def unregister(payload: TokenIn, _user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(models.PushToken).filter(models.PushToken.token == payload.token).delete()
    db.commit()
    return {"ok": True}


@router.post("/register-admin")
def register_admin(payload: TokenIn, x_admin_key: str = Header(None), db: Session = Depends(get_db)):
    """Registra o aparelho do dono do SaaS (recebe avisos de novo assinante)."""
    if not SUPERADMIN_KEY or not x_admin_key or not _secrets.compare_digest(x_admin_key, SUPERADMIN_KEY):
        raise HTTPException(status_code=401, detail="Acesso negado.")
    _upsert(db, payload.token, payload.platform, is_admin=True)
    return {"ok": True}


# ---- Helpers usados por outros routers para descobrir os destinos ----
def tokens_for_users(db: Session, user_ids: list) -> list:
    ids = [i for i in user_ids if i]
    if not ids:
        return []
    rows = db.query(models.PushToken).filter(models.PushToken.user_id.in_(ids)).all()
    return [r.token for r in rows]


def admin_tokens(db: Session) -> list:
    rows = db.query(models.PushToken).filter(models.PushToken.is_admin.is_(True)).all()
    return [r.token for r in rows]
