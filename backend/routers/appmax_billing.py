"""Cobrança/assinatura via Appmax (gateway completo por API).

Endpoints:
  POST /billing/appmax/validate  -> health-check da instalação do app (retorna external_id UUID)
  POST /billing/appmax/webhook   -> eventos da Appmax (libera/bloqueia a barbearia)
  POST /billing/appmax/checkout  -> cria cliente+pedido+pagamento recorrente (token do Appmax JS)
"""
import os
import secrets
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


def _admin_ok(key: str) -> bool:
    """Confere a chave de admin de forma resistente a timing attack."""
    return bool(SUPERADMIN_KEY) and bool(key) and secrets.compare_digest(key, SUPERADMIN_KEY)


@router.get("/debug")
def debug(key: str = ""):
    """Diagnóstico da configuração do app (sem expor segredos)."""
    if not _admin_ok(key):
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


@router.get("/try")
def try_authorize(key: str = "", app_id: str = "", external_key: str = "agendabarber"):
    """Diagnóstico: testa /app/authorize com um app_id específico e mostra a
    resposta CRUA da Appmax — sem redirecionar. Serve para descobrir qual
    formato de app_id a Appmax aceita (UUID x ID numérico x client_id) sem
    precisar redeployar. Ex.:
        /billing/appmax/try?key=SUA_CHAVE&app_id=8765588b-...   (UUID)
        /billing/appmax/try?key=SUA_CHAVE&app_id=123            (numérico)
    """
    if not _admin_ok(key):
        raise HTTPException(status_code=401, detail="Acesso negado.")
    if not appmax.app_configured():
        raise HTTPException(status_code=503, detail="Credenciais do app não configuradas.")
    used = app_id or appmax.APP_ID
    url_callback = f"{APP_BASE_URL}/billing/appmax/callback?state=teste"
    try:
        status_code, body = appmax._app_authorize_raw(used, external_key, url_callback)
    except Exception as e:  # noqa: BLE001
        return {"app_id_testado": used, "erro_oauth": str(e)}
    return {
        "app_id_testado": used,
        "status": status_code,
        "aceito": status_code < 300,
        "resposta": body,
        "dica": "Se 'aceito' for true, defina esse valor em APPMAX_APP_ID no Render.",
    }


@router.get("/v3-test")
def v3_test(key: str = "", token: str = ""):
    """Diagnóstico da API v3 clássica: cria um cliente de teste com o token do
    lojista e mostra a resposta crua. Se funcionar, esse é o caminho para
    receber pagamentos (sem o fluxo de instalação/appstore).

    Passe ?token= para testar sem gravar env, ou defina APPMAX_V3_TOKEN.
        /billing/appmax/v3-test?key=SUA_CHAVE&token=SEU-TOKEN-DE-LOJISTA
    """
    if not _admin_ok(key):
        raise HTTPException(status_code=401, detail="Acesso negado.")
    tok = token or appmax.V3_TOKEN
    if not tok:
        raise HTTPException(status_code=400, detail="Informe ?token= ou defina APPMAX_V3_TOKEN.")
    try:
        data = appmax._v3_post(
            "/customer",
            {
                "firstname": "Teste",
                "lastname": "Agenda Barber",
                "email": "teste-agendabarber@example.com",
                "telephone": "51999999999",
            },
            tok,
        )
        cid = (data.get("data") or {}).get("id")
        return {"funciona": True, "customer_id": cid, "resposta": data}
    except Exception as e:  # noqa: BLE001
        return {"funciona": False, "erro": str(e)}


@router.get("/v3-order-test")
def v3_order_test(key: str = "", token: str = ""):
    """Diagnóstico da v3: cria cliente + PEDIDO de teste (SEM cobrar cartão) e
    mostra as respostas. Valida o schema de pedido antes de qualquer cobrança
    real. Não gera pagamento — é seguro."""
    if not _admin_ok(key):
        raise HTTPException(status_code=401, detail="Acesso negado.")
    tok = token or appmax.V3_TOKEN
    if not tok:
        raise HTTPException(status_code=400, detail="Informe ?token= ou defina APPMAX_V3_TOKEN.")
    try:
        cid = appmax.v3_create_customer(
            "Teste", "Agenda Barber", "teste-agendabarber@example.com",
            "51999999999", token=tok,
        )
        oid = appmax.v3_create_order(
            customer_id=cid, value_reais=49.90,
            product_name="Agenda Barber (teste)", sku="plano-teste", token=tok,
        )
        return {"funciona": True, "customer_id": cid, "order_id": oid}
    except Exception as e:  # noqa: BLE001
        return {"funciona": False, "erro": str(e)}


@router.get("/connect")
def connect(key: str = "", app_id: str = ""):
    """Inicia a instalação do app: autoriza e redireciona o dono para a Appmax.

    `app_id` opcional na querystring sobrescreve o APPMAX_APP_ID (para testar o
    ID numérico direto pela URL).
    """
    if not _admin_ok(key):
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
        hash_token = appmax.app_authorize("agendabarber", url_callback, app_id=app_id)
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

def _norm_event(ev: str) -> str:
    """Normaliza o nome do evento (a v3 manda PascalCase 'OrderApproved',
    a v1 manda 'order_approved') para comparar sem depender de formato."""
    return "".join(ch for ch in (ev or "").lower() if ch.isalnum())


# Eventos que aprovam/reprovam a assinatura (v1 e v3, já normalizados).
_APPROVE = {
    "orderapproved",
    "orderpaid",
    "orderpaidbypix",
    "orderintegrated",
    "subscriptionchargesuccess",
}
_CANCEL = {
    "subscriptioncancelation",
    "orderrefund",
    "ordercancel",
    "ordercanceled",
    "ordercancelled",
}
_OVERDUE = {
    "subscriptiondelayed",
    "subscriptionchargefailed",
    "paymentnotauthorized",
    "orderbilletoverdue",
    "orderrefusedbyrisk",
    "orderrefused",
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
    """Localiza a barbearia pelo pedido/cliente do webhook.

    Aceita os dois formatos: v1 (campos planos order_id/customer_id) e v3
    (data.id = pedido, data.customer.id = cliente).
    """
    order_id = str(data.get("order_id") or data.get("id") or "")
    cust = data.get("customer") or {}
    customer_id = str(
        data.get("customer_id") or (cust.get("id") if isinstance(cust, dict) else "") or ""
    )
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
    if APPMAX_WEBHOOK_TOKEN:
        got = request.query_params.get("token") or ""
        if not secrets.compare_digest(got, APPMAX_WEBHOOK_TOKEN):
            return {"ok": True}  # ignora silenciosamente (não dispara retry)

    try:
        body = await request.json()
        event = _norm_event(body.get("event"))
        data = body.get("data") or {}
        # Log só o essencial (sem PII do cliente): evento + ids do pedido/cliente.
        print(
            f"[appmax webhook] evento={body.get('event')} "
            f"order={data.get('order_id') or data.get('id')}"
        )
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


def _payment_configured() -> bool:
    """Pagamento disponível se a v3 (token de lojista) OU a v1 estiverem prontas."""
    return appmax.v3_configured() or appmax.is_configured()


def _v3_looks_approved(result: dict) -> bool:
    """Heurística de aprovação na resposta do pagamento v3 (a liberação
    definitiva ainda vem pelo webhook; isto é só um bônus imediato)."""
    if not isinstance(result, dict) or not result.get("success", True):
        return False
    data = result.get("data") or {}
    status_txt = str(data.get("status") or data.get("pay_status") or "").lower()
    if not status_txt:
        return False
    return any(
        s in status_txt
        for s in ("aprovad", "autoriz", "integrad", "approv", "author", "paid", "pago")
    )


@router.get("/status")
def status(_owner: models.User = Depends(require_owner)):
    """Diz se a Appmax está configurada no servidor (para o painel decidir o botão)."""
    return {"configured": _payment_configured()}


@router.post("/checkout", response_model=schemas.TenantOut)
def checkout(
    payload: schemas.AppmaxCheckoutInput,
    request: Request,
    tenant: models.Tenant = Depends(get_current_tenant),
    _owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db),
):
    """Cria a assinatura na Appmax com os dados do cartão.

    Usa a API v3 clássica (token de lojista) se disponível; senão, a v1.
    """
    plan = get_plan(payload.plan)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido.")
    if not _payment_configured():
        raise HTTPException(
            status_code=503,
            detail="Pagamento Appmax não configurado no servidor.",
        )

    owner = tenant.users[0] if tenant.users else None
    email = owner.email if owner else f"{tenant.slug}@exemplo.com"
    full = (owner.name if owner else tenant.name).strip()
    first, _, last = full.partition(" ")
    ip = request.client.host if request.client else "0.0.0.0"

    approved = False
    try:
        if appmax.v3_configured():
            customer_id = appmax.v3_create_customer(
                first_name=first, last_name=last, email=email,
                phone=tenant.whatsapp, document_number=payload.cpf_cnpj,
            )
            order_id = appmax.v3_create_order(
                customer_id=customer_id,
                value_reais=plan["price"],
                product_name=plan["description"],
                sku=f"plano-{plan['id']}",
            )
            result = appmax.v3_pay_credit_card(
                order_id=order_id,
                customer_id=customer_id,
                card_number=payload.card_number,
                card_cvv=payload.card_cvv,
                card_month=payload.card_exp_month,
                card_year=payload.card_exp_year,
                holder_name=payload.holder_name,
                holder_document=payload.cpf_cnpj,
            )
            approved = _v3_looks_approved(result)
        else:
            # Fallback: fluxo v1 (Bearer/merchant OAuth).
            value_cents = int(round(plan["price"] * 100))
            interval = "year" if plan["id"] == "anual" else "month"
            customer_id = appmax.create_customer(
                first_name=first, last_name=last, email=email,
                phone=tenant.whatsapp, ip=ip, document_number=payload.cpf_cnpj,
            )
            order_id = appmax.create_order(
                customer_id=customer_id, value_cents=value_cents,
                product_name=plan["description"], sku=f"plano-{plan['id']}",
            )
            card_token = appmax.tokenize_card(
                number=payload.card_number, cvv=payload.card_cvv,
                expiration_month=payload.card_exp_month,
                expiration_year=payload.card_exp_year,
                holder_name=payload.holder_name,
            )
            appmax.pay_credit_card(
                order_id=order_id, customer_id=customer_id, card_token=card_token,
                holder_name=payload.holder_name,
                holder_document_number=payload.cpf_cnpj, interval=interval,
            )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro na Appmax: {e}")

    tenant.appmax_customer_id = str(customer_id)
    tenant.appmax_order_id = str(order_id)
    tenant.plan = plan["id"]
    # A liberação definitiva vem pelo webhook (order_approved). Se o pagamento já
    # voltou aprovado, liberamos na hora como bônus (o webhook confirma depois).
    if approved:
        tenant.subscription_status = "active"
        tenant.current_period_end = datetime.utcnow() + timedelta(
            days=_period_days(plan["id"])
        )
    db.commit()
    db.refresh(tenant)
    return tenant
