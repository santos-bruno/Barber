"""Painel do dono do SaaS: assinantes e faturamento (protegido por chave)."""
import os

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
                "plan": t.plan,
                "status": t.subscription_status,
                "created_at": t.created_at,
                "current_period_end": t.current_period_end,
            }
        )
    ativos = sum(1 for t in tenants if t.subscription_status == "active")
    return {
        "total_barbearias": len(tenants),
        "assinantes_ativos": ativos,
        "mrr_estimado": round(mrr, 2),
        "barbearias": result,
    }
