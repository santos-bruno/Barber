"""Cobrança/assinatura via Appmax (gateway completo por API).

Endpoints:
  POST /billing/appmax/validate  -> health-check da instalação do app (retorna external_id UUID)
  POST /billing/appmax/webhook   -> eventos da Appmax (libera/bloqueia a barbearia)
  POST /billing/appmax/checkout  -> cria cliente+pedido+pagamento recorrente (token do Appmax JS)
"""
import os
import time
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

import appmax
import email_send
import models
import schemas
from database import get_db
from plans import get_plan
from security import get_current_tenant, require_owner

router = APIRouter(prefix="/billing/appmax", tags=["appmax"])

# Token opcional para validar o webhook (configure o mesmo no app da Appmax).
APPMAX_WEBHOOK_TOKEN = os.getenv("APPMAX_WEBHOOK_TOKEN", "")
SUPERADMIN_KEY = os.getenv("SUPERADMIN_KEY", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://agenda-barber-o0to.onrender.com").rstrip("/")

# States efêmeros do fluxo de conexão (instalação do app).
_connect_states: dict = {}


@router.get("/debug")
def debug(key: str = ""):
    """Diagnóstico da configuração do app (sem expor segredos)."""
    if not SUPERADMIN_KEY or key != SUPERADMIN_KEY:
        raise HTTPException(status_code=401, detail="Acesso negado.")
    info = {
        "base_url": appmax.BASE_URL,
        "auth_url": appmax.AUTH_URL,
        "authorize_url": appmax.AUTHORIZE_URL,
        "app_id": appmax.APP_ID,  # não é secreto (UUID/ID numérico)
        "app_client_id_set": bool(appmax.APP_CLIENT_ID),
        "app_client_secret_set": bool(appmax.APP_CLIENT_SECRET),
        "merchant_configured": appmax.is_configured(),
    }
    try:
        tok = appmax._app_token()
        info["app_oauth"] = "ok" if tok else "sem access_token"
    except Exception as e:  # noqa: BLE001
        info["app_oauth"] = f"FALHOU: {e}"
    return info


@router.get("/connect")
def connect(key: str = ""):
    """Inicia a instalação do app: autoriza e redireciona o dono para a Appmax."""
    if not SUPERADMIN_KEY or key != SUPERADMIN_KEY:
        raise HTTPException(status_code=401, detail="Acesso negado.")
    if not appmax.app_configured():
        raise HTTPException(
            status_code=503,
            detail="Defina APPMAX_APP_ID, APPMAX_APP_CLIENT_ID e APPMAX_APP_CLIENT_SECRET.",
        )
    state = uuid.uuid4().hex
    _connect_states[state] = time.time()
    url_callback = f"{APP_BASE_URL}/billing/appmax/callback?state={state}"
    try:
        hash_token = appmax.app_authorize("agendabarber", url_callback)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro na Appmax: {e}")
    return RedirectResponse(appmax.AUTHORIZE_URL.rstrip("/") + "/" + hash_token)


@router.get("/callback", response_class=HTMLResponse)
def connect_callback(state: str = "", token: str = ""):
    """Recebe o retorno da autorização e gera as credenciais do merchant."""
    now = time.time()
    # limpa states velhos (>1h)
    for s in [s for s, t in _connect_states.items() if now - t > 3600]:
        _connect_states.pop(s, None)
    if not state or state not in _connect_states:
        return HTMLResponse("<h2>Sessão de conexão expirada. Recomece.</h2>", status_code=400)
    _connect_states.pop(state, None)
    if not token:
        return HTMLResponse("<h2>Autorização não concluída (sem token).</h2>", status_code=400)
    try:
        client = appmax.app_generate_merchant(token)
    except Exception as e:  # noqa: BLE001
        return HTMLResponse(f"<h2>Erro ao gerar credenciais</h2><pre>{e}</pre>", status_code=502)
    cid = client.get("client_id", "")
    csecret = client.get("client_secret", "")
    return HTMLResponse(
        f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Credenciais do merchant — Appmax</title>
        <style>body{{font-family:Arial,sans-serif;background:#0F1115;color:#F4F6FB;max-width:640px;margin:0 auto;padding:24px;line-height:1.5}}
        code{{background:#1E222B;border:1px solid #262B36;border-radius:8px;padding:10px;display:block;margin:6px 0;word-break:break-all;font-size:15px}}
        .g{{color:#F0C24B;font-weight:800}}</style></head><body>
        <h2>✅ App conectado!</h2>
        <p>Copie as <b>credenciais do merchant</b> abaixo e cole no Render (Environment):</p>
        <p class="g">APPMAX_MERCHANT_CLIENT_ID</p><code>{cid}</code>
        <p class="g">APPMAX_MERCHANT_CLIENT_SECRET</p><code>{csecret}</code>
        <p style="margin-top:18px">Depois, <b>apague</b> a variável <code style="display:inline">APPMAX_ACCESS_TOKEN</code>, salve e aguarde o deploy.
        Então teste o pagamento em <a href="/assinar" style="color:#F0C24B">/assinar</a>.</p>
        <p style="color:#9AA3B2;font-size:13px">Guarde essas credenciais com segurança — elas não serão exibidas de novo.</p>
        </body></html>"""
    )

# Eventos da Appmax que aprovam/reprovam a assinatura (schema oficial do webhook).
_APPROVE = {
    "order_approved",
    "order_paid",
    "order_paid_by_pix",
    "order_integrated",
    "subscription_charge_success",
}
_CANCEL = {"subscription_cancelation", "order_refund"}
_OVERDUE = {
    "subscription_delayed",
    "subscription_charge_failed",
    "payment_not_authorized",
    "order_billet_overdue",
    "order_refused_by_risk",
}


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


def _find_tenant_by_payload(db: Session, data: dict):
    """Localiza a barbearia pelo order_id/customer_id do webhook (campos planos)."""
    order_id = str(data.get("order_id") or "")
    customer_id = str(data.get("customer_id") or "")
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
async def webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Recebe eventos da Appmax e atualiza o status da assinatura.

    A Appmax NÃO envia token/HMAC nos webhooks e exige resposta 2xx rápida
    (timeout de 5s), senão faz retry. Por isso validamos só por token opcional
    na querystring (a URL que cadastramos) e sempre respondemos 200.
    """
    # Validação opcional por querystring (?token=...), nunca por header —
    # a Appmax não tem como enviar header, e 401/403 causaria retries.
    if APPMAX_WEBHOOK_TOKEN and request.query_params.get("token") != APPMAX_WEBHOOK_TOKEN:
        return {"ok": True}  # ignora silenciosamente (não dispara retry)

    try:
        body = await request.json()
        event = (body.get("event") or "").lower()
        data = body.get("data") or {}
        print(f"[appmax webhook] evento={event} data={data}")  # payload cru p/ debug
        tenant = _find_tenant_by_payload(db, data)
        if tenant:
            if event in _APPROVE:
                was_active = tenant.subscription_status == "active"
                tenant.subscription_status = "active"
                tenant.current_period_end = datetime.utcnow() + timedelta(
                    days=_period_days(tenant.plan)
                )
                if not was_active:  # avisa o dono só na 1ª ativação, não em cada renovação
                    owner = (
                        db.query(models.User)
                        .filter(models.User.tenant_id == tenant.id, models.User.role == "owner")
                        .order_by(models.User.id)
                        .first()
                    )
                    background_tasks.add_task(
                        email_send.send_owner_new_subscription,
                        tenant.name, tenant.plan, owner.email if owner else "",
                    )
            elif event in _OVERDUE:
                tenant.subscription_status = "overdue"
            elif event in _CANCEL:
                tenant.subscription_status = "canceled"
            db.commit()
    except Exception as e:  # noqa: BLE001
        print(f"[appmax webhook] erro ao processar: {e}")
    return {"ok": True}  # sempre 200 (evita retries desnecessários)


@router.get("/status")
def status(_owner: models.User = Depends(require_owner)):
    """Diz se a Appmax está configurada no servidor (para o painel decidir o botão)."""
    return {"configured": appmax.is_configured()}


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
    ip = request.client.host if request.client else "0.0.0.0"

    value_cents = int(round(plan["price"] * 100))
    interval = "year" if plan["id"] == "anual" else "month"
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
        card_token = appmax.tokenize_card(
            number=payload.card_number,
            cvv=payload.card_cvv,
            expiration_month=payload.card_exp_month,
            expiration_year=payload.card_exp_year,
            holder_name=payload.holder_name,
        )
        appmax.pay_credit_card(
            order_id=order_id,
            customer_id=customer_id,
            card_token=card_token,
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
