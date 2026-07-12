"""Autenticação (JWT), hashing de senha e dependências de tenant/assinatura."""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user: models.User) -> str:
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user.id),
        "tenant_id": user.tenant_id,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _unauthorized(detail: str = "Não autenticado."):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized()
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise _unauthorized("Sessão inválida ou expirada.")

    user = db.get(models.User, user_id)
    if not user:
        raise _unauthorized("Usuário não encontrado.")
    return user


def get_current_tenant(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> models.Tenant:
    tenant = db.get(models.Tenant, user.tenant_id)
    if not tenant:
        raise _unauthorized("Barbearia não encontrada.")
    return tenant


def subscription_active(tenant: models.Tenant) -> bool:
    """True se o tenant pode usar o sistema (trial válido ou assinatura ativa)."""
    now = datetime.utcnow()
    if tenant.subscription_status == "active":
        if tenant.current_period_end and tenant.current_period_end < now:
            return False
        return True
    if tenant.subscription_status == "trial":
        return not tenant.trial_ends_at or tenant.trial_ends_at >= now
    return False


def require_active_subscription(
    tenant: models.Tenant = Depends(get_current_tenant),
) -> models.Tenant:
    if not subscription_active(tenant):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Assinatura inativa. Renove para continuar usando o sistema.",
        )
    return tenant
