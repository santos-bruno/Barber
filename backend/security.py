"""Autenticação (JWT), hashing de senha e dependências de tenant/assinatura."""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import get_db

_WEAK_DEFAULT = "troque-esta-chave-em-producao"
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

# Em produção (banco Postgres) exigimos uma chave forte e definida. Sem ela, o
# sistema não sobe — evita rodar com uma chave previsível que permitiria forjar
# tokens de qualquer usuário. Em desenvolvimento (SQLite) geramos uma chave
# efêmera (os tokens expiram ao reiniciar, o que é aceitável localmente).
_is_production = os.getenv("DATABASE_URL", "").startswith(("postgres://", "postgresql"))
if not SECRET_KEY or SECRET_KEY == _WEAK_DEFAULT:
    if _is_production:
        raise RuntimeError(
            "SECRET_KEY não definida (ou usando o valor padrão) em produção. "
            "Defina uma chave forte na variável de ambiente SECRET_KEY."
        )
    SECRET_KEY = secrets.token_urlsafe(48)

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prep(password: str) -> str:
    """O bcrypt só considera os primeiros 72 bytes. Truncamos de forma segura
    (em UTF-8) para nunca estourar erro em versões novas da lib e manter o
    hashing consistente."""
    return password.encode("utf-8")[:72].decode("utf-8", "ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_prep(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_prep(plain), hashed)


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
    if not user.active:
        raise _unauthorized("Acesso desativado.")
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


def require_owner(user: models.User = Depends(get_current_user)) -> models.User:
    """Somente o dono/gerente (não barbeiros) acessa áreas financeiras/gestão."""
    if user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao dono da barbearia.",
        )
    return user
