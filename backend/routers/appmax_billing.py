"""Cobrança/assinatura via Appmax (gateway completo por API).

Endpoints:
  POST /billing/appmax/validate  -> health-check da instalação do app (retorna external_id UUID)
  POST /billing/appmax/webhook   -> eventos da Appmax (libera/bloqueia a barbearia)
  POST /billing/appmax/checkout  -> cria cliente+pedido+pagamento recorrente (token do Appmax JS)
"""
import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import appmax
import models
import schemas
from database import get_db
from plans import get_plan
from security import get_current_tenant, require_owner

router = APIRouter(prefix="/billing/appmax", tags=["appmax"])

# Token opcional para validar o webhook (configure o mesmo no app da Appmax).
APPMAX_WEBHOOK_TOKEN = os.getenv("APPMAX_WEBHOOK_TOKEN", "")

# Eventos da Appmax que aprovam/reprovam a assinatura.
_APPROVE = {"order_approved", "order_paid", "order_paid_by_pix", "order_integrated"}
_CANCEL = {"subscription_cancelation", "order_refund"}
_OVERDUE = {"subscription_delayed", "payment_not_authorized", "order_billet_overdue"}


@router.post("/validate")
async def validate_install(request: Request):
    """Health-check chamado pela Appmax durante a instalação do aplicativo.

    Deve responder 200 + um external_id (UUID v4) novo a cada chamada. Nunca
    rejeita por campo opcional ausente (só app_id é relevante, e mesmo assim
    não bloqueamos).
    """
    try:
        await request.json()
    except Exception:  # noqa: BLE001
        pass  # corpo pode vir vazio — não pode falhar
    return {"external_id": str(uuid.uuid4())}


def _period_days(plan: str) -> int:
    return 366 if plan == "anual" else 31


def _find_tenant_by_payload(db: Session, body: dict):
    """Localiza a barbearia a partir do order_id/customer_id que vier no webhook."""
    data = body.get("data") or body
    order = data.get("order") if isinstance(data.get("order"), dict) else data
    order_id = str(order.get("id") or data.get("order_id") or body.get("order_id") or "")
    customer = data.get("customer") if isinstance(data.get("customer"), dict) else {}
    customer_id = str(customer.get("id") or data.get("customer_id") or "")

    q = db.query(models.Tenant)
    if order_id:
        t = q.filter(models.Tenant.appmax_order_id == order_id).first()
        if t:
            return t
    if customer_id:
        t = q.filter(models.Tenant.appmax_customer_id == customer_id).first()
        if t:
            return t
    return None


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Recebe eventos da Appmax e atualiza o status da assinatura."""
    if APPMAX_WEBHOOK_TOKEN:
        token = (
            request.headers.get("x-appmax-token")
            or request.query_params.get("token")
            or ""
        )
        if token != APPMAX_WEBHOOK_TOKEN:
            raise HTTPException(status_code=401, detail="Token de webhook inválido.")

    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return {"ok": True}

    event = (body.get("event") or "").lower()
    tenant = _find_tenant_by_payload(db, body)
    if not tenant:
        # Loga para depuração e responde 200 (não reprocessar).
        print(f"[appmax webhook] tenant não encontrado para evento={event}: {body}")
        return {"ok": True}

    if event in _APPROVE:
        tenant.subscription_status = "active"
        tenant.current_period_end = datetime.utcnow() + timedelta(
            days=_period_days(tenant.plan)
        )
    elif event in _OVERDUE:
        tenant.subscription_status = "overdue"
    elif event in _CANCEL:
        tenant.subscription_status = "canceled"

    db.commit()
    return {"ok": True}


@router.get("/status")
def status(_owner: models.User = Depends(require_owner)):
    """Diz se a Appmax está configurada no servidor (para o painel decidir o botão)."""
    return {"configured": appmax.is_configured()}


@router.post("/subscribe")
def subscribe_link(
    payload: schemas.SubscribeInput,
    tenant: models.Tenant = Depends(get_current_tenant),
    _owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db),
):
    """Gera um link de pagamento hospedado da Appmax e devolve o checkout_url.

    Caminho mais simples (a Appmax cuida do cartão/pix/boleto). A liberação da
    barbearia vem pelo webhook (order_approved).
    """
    plan = get_plan(payload.plan)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido.")
    if not appmax.is_configured():
        raise HTTPException(status_code=503, detail="Pagamento Appmax não configurado.")
    value_cents = int(round(plan["price"] * 100))
    try:
        link = appmax.create_payment_link(
            name=f"{plan['label']} — {tenant.name}",
            value_cents=value_cents,
            description=plan["description"],
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro na Appmax: {e}")

    tenant.plan = plan["id"]
    if link.get("id"):
        tenant.appmax_order_id = str(link["id"])  # p/ correlacionar no webhook
    db.commit()
    return {"checkout_url": link.get("checkout_url", ""), "id": link.get("id")}


@router.post("/checkout", response_model=schemas.TenantOut)
def checkout(
    payload: schemas.AppmaxCheckoutInput,
    request: Request,
    tenant: models.Tenant = Depends(get_current_tenant),
    _owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db),
):
    """Cria a assinatura recorrente na Appmax com o token de cartão (Appmax JS)."""
    plan = get_plan(payload.plan)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido.")
    if not appmax.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Pagamento Appmax não configurado no servidor.",
        )

    owner = tenant.users[0] if tenant.users else None
    email = owner.email if owner else f"{tenant.slug}@exemplo.com"
    full = (owner.name if owner else tenant.name).strip()
    first, _, last = full.partition(" ")
    value_cents = int(round(plan["price"] * 100))
    interval = "year" if plan["id"] == "anual" else "month"
    ip = request.client.host if request.client else "0.0.0.0"

    try:
        customer_id = appmax.create_customer(
            first_name=first,
            last_name=last,
            email=email,
            phone=tenant.whatsapp,
            ip=ip,
            document_number=payload.cpf_cnpj,
        )
        order_id = appmax.create_order(
            customer_id=customer_id,
            value_cents=value_cents,
            product_name=plan["description"],
            sku=f"plano-{plan['id']}",
        )
        appmax.pay_credit_card_recurring(
            order_id=order_id,
            customer_id=customer_id,
            card_token=payload.card_token,
            holder_name=payload.holder_name,
            holder_document_number=payload.cpf_cnpj,
            interval=interval,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro na Appmax: {e}")

    tenant.appmax_customer_id = str(customer_id)
    tenant.appmax_order_id = str(order_id)
    tenant.plan = plan["id"]
    # Liberação definitiva vem pelo webhook (order_approved). Aqui só registramos.
    db.commit()
    db.refresh(tenant)
    return tenant
