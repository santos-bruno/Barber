"""Painel do dono do SaaS: assinantes, faturamento e controle de acesso.

Protegido por chave (header X-Admin-Key == SUPERADMIN_KEY).
"""
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from plans import PLANS

router = APIRouter(prefix="/admin", tags=["superadmin"])

SUPERADMIN_KEY = os.getenv("SUPERADMIN_KEY", "")


def _auth(x_admin_key: str = Header(None)):
    if not SUPERADMIN_KEY or x_admin_key != SUPERADMIN_KEY:
        raise HTTPException(status_code=401, detail="Acesso negado.")


def _owner_email(db: Session, tenant_id: int) -> str:
    u = (
        db.query(models.User)
        .filter(models.User.tenant_id == tenant_id)
        .order_by(models.User.id)
        .first()
    )
    return u.email if u else ""


@router.get("/tenants", dependencies=[Depends(_auth)])
def list_tenants(db: Session = Depends(get_db)):
    tenants = db.query(models.Tenant).order_by(models.Tenant.created_at.desc()).all()
    mrr = 0.0
    result = []
    for t in tenants:
        if t.subscription_status == "active" and t.plan in PLANS:
            price = PLANS[t.plan]["price"]
            mrr += price / 12 if t.plan == "anual" else price
        result.append(
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "owner_email": _owner_email(db, t.id),
                "whatsapp": t.whatsapp,
                "plan": t.plan,
                "status": t.subscription_status,
                "created_at": t.created_at,
                "trial_ends_at": t.trial_ends_at,
                "current_period_end": t.current_period_end,
            }
        )
    ativos = sum(1 for t in tenants if t.subscription_status == "active")
    trials = sum(1 for t in tenants if t.subscription_status == "trial")
    return {
        "total_barbearias": len(tenants),
        "assinantes_ativos": ativos,
        "em_teste": trials,
        "mrr_estimado": round(mrr, 2),
        "barbearias": result,
    }


def _get_tenant(db: Session, tenant_id: int) -> models.Tenant:
    t = db.get(models.Tenant, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada.")
    return t


@router.post("/tenants/{tenant_id}/activate", dependencies=[Depends(_auth)])
def activate(tenant_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Libera acesso manualmente (ex.: cortesia) por N dias."""
    t = _get_tenant(db, tenant_id)
    t.subscription_status = "active"
    t.current_period_end = datetime.utcnow() + timedelta(days=days)
    db.commit()
    return {"ok": True, "status": t.subscription_status}


@router.post("/tenants/{tenant_id}/block", dependencies=[Depends(_auth)])
def block(tenant_id: int, db: Session = Depends(get_db)):
    """Bloqueia o acesso da barbearia."""
    t = _get_tenant(db, tenant_id)
    t.subscription_status = "canceled"
    db.commit()
    return {"ok": True, "status": t.subscription_status}


@router.post("/tenants/{tenant_id}/trial", dependencies=[Depends(_auth)])
def extend_trial(tenant_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Estende (ou reabre) o período de teste por N dias."""
    t = _get_tenant(db, tenant_id)
    t.subscription_status = "trial"
    t.trial_ends_at = datetime.utcnow() + timedelta(days=days)
    db.commit()
    return {"ok": True, "status": t.subscription_status}
