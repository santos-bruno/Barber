"""Endpoints de cobrança/assinatura (Asaas)."""
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import asaas
import models
import schemas
from database import get_db
from plans import PLANS, TRIAL_DAYS, get_plan
from security import get_current_tenant, require_owner

router = APIRouter(prefix="/billing", tags=["billing"])

# Token opcional para validar o webhook do Asaas (configure o mesmo no painel Asaas).
ASAAS_WEBHOOK_TOKEN = os.getenv("ASAAS_WEBHOOK_TOKEN", "")


@router.get("/plans")
def list_plans():
    """Lista pública dos planos (para a página de vendas)."""
    return {
        "trial_days": TRIAL_DAYS,
        "asaas_configured": asaas.is_configured(),
        "plans": list(PLANS.values()),
    }


@router.get("/status", response_model=schemas.TenantOut)
def billing_status(
    tenant: models.Tenant = Depends(get_current_tenant),
    _owner: models.User = Depends(require_owner),
):
    return tenant


@router.post("/subscribe", response_model=schemas.CheckoutOut)
def subscribe(
    payload: schemas.SubscribeInput,
    tenant: models.Tenant = Depends(get_current_tenant),
    _owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db),
):
    plan = get_plan(payload.plan)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido.")
    if not asaas.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Pagamento ainda não configurado (defina ASAAS_API_KEY no servidor).",
        )

    owner = tenant.users[0] if tenant.users else None
    email = owner.email if owner else f"{tenant.slug}@exemplo.com"
    name = owner.name if owner else tenant.name

    try:
        # Reutiliza o customer do Asaas, se já existir.
        customer_id = tenant.asaas_customer_id or asaas.create_customer(
            name=name, email=email, cpf_cnpj=payload.cpf_cnpj, phone=tenant.whatsapp
        )
        sub = asaas.create_subscription(
            customer_id=customer_id,
            billing_type=payload.billing_type,
            value=plan["price"],
            cycle=plan["cycle"],
            description=plan["description"],
            next_due_date=datetime.utcnow().strftime("%Y-%m-%d"),
        )
        checkout_url = asaas.first_payment_checkout_url(sub["id"])
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro no Asaas: {e}")

    tenant.asaas_customer_id = customer_id
    tenant.asaas_subscription_id = sub["id"]
    tenant.plan = plan["id"]
    db.commit()

    return schemas.CheckoutOut(
        checkout_url=checkout_url, subscription_id=sub["id"], status=sub.get("status", "")
    )


@router.post("/webhook")
async def asaas_webhook(request: Request, db: Session = Depends(get_db)):
    """Recebe eventos do Asaas e atualiza o status da assinatura."""
    # Fail-closed: se a cobrança está ativa, o webhook DEVE ter token configurado.
    if asaas.is_configured() and not ASAAS_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Webhook sem token de segurança. Defina ASAAS_WEBHOOK_TOKEN.",
        )
    if ASAAS_WEBHOOK_TOKEN:
        token = request.headers.get("asaas-access-token", "")
        if token != ASAAS_WEBHOOK_TOKEN:
            raise HTTPException(status_code=401, detail="Token de webhook inválido.")

    body = await request.json()
    event = body.get("event", "")
    payment = body.get("payment") or {}
    subscription_id = payment.get("subscription")
    if not subscription_id:
        return {"ok": True}

    tenant = (
        db.query(models.Tenant)
        .filter(models.Tenant.asaas_subscription_id == subscription_id)
        .first()
    )
    if not tenant:
        return {"ok": True}

    if event in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
        days = 366 if tenant.plan == "anual" else 31
        tenant.subscription_status = "active"
        tenant.current_period_end = datetime.utcnow() + timedelta(days=days)
    elif event in ("PAYMENT_OVERDUE",):
        tenant.subscription_status = "overdue"
    elif event in ("SUBSCRIPTION_DELETED", "PAYMENT_DELETED", "PAYMENT_REFUNDED"):
        tenant.subscription_status = "canceled"

    db.commit()
    return {"ok": True}
