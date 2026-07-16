"""Cliente da API v1 da Appmax (api.appmax.com.br/v1).

Fluxo de assinatura recorrente (documentação oficial):
  1. Autenticação -> Bearer token.
     - Se APPMAX_ACCESS_TOKEN estiver definido, ele é usado direto como Bearer.
     - Senão, OAuth2 client_credentials com APPMAX_MERCHANT_CLIENT_ID/SECRET.
  2. POST /v1/customers            -> data.customer.id
  3. POST /v1/orders              -> data.order.id   (valores em CENTAVOS)
  4. POST /v1/payments/tokenize   -> data.token      (tokeniza o cartão no servidor)
  5. POST /v1/payments/credit-card com payment_data.subscription {interval, interval_count}
     -> cobra e ativa a recorrência (mensal/anual).

Variáveis de ambiente:
  APPMAX_ACCESS_TOKEN            -> token Bearer (se o suporte forneceu um token pronto)
  APPMAX_MERCHANT_CLIENT_ID/SECRET -> alternativa via OAuth client_credentials
  APPMAX_AUTH_URL  -> prod: https://auth.appmax.com.br/oauth2/token
  APPMAX_BASE_URL  -> prod: https://api.appmax.com.br   (sandbox: https://api.sandboxappmax.com.br)
"""
import os
import time

import httpx

ACCESS_TOKEN = os.getenv("APPMAX_ACCESS_TOKEN", "")
MERCHANT_CLIENT_ID = os.getenv("APPMAX_MERCHANT_CLIENT_ID", "")
MERCHANT_CLIENT_SECRET = os.getenv("APPMAX_MERCHANT_CLIENT_SECRET", "")
AUTH_URL = os.getenv("APPMAX_AUTH_URL", "https://auth.appmax.com.br/oauth2/token")
BASE_URL = os.getenv("APPMAX_BASE_URL", "https://api.appmax.com.br").rstrip("/")

# Credenciais do APP (para o fluxo de instalação que gera as credenciais do merchant).
APP_ID = os.getenv("APPMAX_APP_ID", "")  # UUID do app
APP_CLIENT_ID = os.getenv("APPMAX_APP_CLIENT_ID", "")
APP_CLIENT_SECRET = os.getenv("APPMAX_APP_CLIENT_SECRET", "")
AUTHORIZE_URL = os.getenv(
    "APPMAX_AUTHORIZE_URL",
    "https://breakingcode.sandboxappmax.com.br/appstore/integration/",
)


def app_configured() -> bool:
    return bool(APP_ID and APP_CLIENT_ID and APP_CLIENT_SECRET)


def _app_token() -> str:
    """Token OAuth do APP (usado só no fluxo de instalação)."""
    r = httpx.post(
        AUTH_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": APP_CLIENT_ID,
            "client_secret": APP_CLIENT_SECRET,
        },
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Appmax app auth {r.status_code}: {r.text}")
    return r.json()["access_token"]


def _app_authorize_raw(app_id: str, external_key: str, url_callback: str):
    """Chama /app/authorize e devolve (status, corpo) SEM levantar exceção.

    Usado tanto pelo fluxo real quanto pelo diagnóstico /try (que testa qual
    formato de app_id a Appmax aceita — UUID x ID numérico x client_id).
    """
    token = _app_token()
    r = httpx.post(
        f"{BASE_URL}/app/authorize",
        headers={"Authorization": f"Bearer {token}", "content-type": "application/json"},
        json={"app_id": app_id, "external_key": external_key, "url_callback": url_callback},
        timeout=30,
    )
    try:
        body = r.json()
    except Exception:  # noqa: BLE001
        body = r.text
    return r.status_code, body


def app_authorize(external_key: str, url_callback: str, app_id: str = "") -> str:
    """Gera o hash de autorização. Retorna o hash p/ redirecionar o merchant.

    `app_id` opcional sobrescreve o APPMAX_APP_ID do ambiente (útil para testar
    o ID numérico sem redeploy).
    """
    status, body = _app_authorize_raw(app_id or APP_ID, external_key, url_callback)
    if status >= 300:
        raise RuntimeError(f"Appmax /app/authorize {status}: {body}")
    if isinstance(body, dict):
        return body["data"]["token"]
    raise RuntimeError(f"Appmax /app/authorize resposta inesperada: {body}")


def app_generate_merchant(hash_token: str) -> dict:
    """Troca o hash pelas credenciais do merchant (dispara o health-check)."""
    token = _app_token()
    r = httpx.post(
        f"{BASE_URL}/app/client/generate",
        headers={"Authorization": f"Bearer {token}", "content-type": "application/json"},
        json={"token": hash_token},
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Appmax /app/client/generate {r.status_code}: {r.text}")
    return r.json()["data"]["client"]  # {client_id, client_secret}

_token_cache = {"value": "", "exp": 0.0}


def is_configured() -> bool:
    return bool(ACCESS_TOKEN or (MERCHANT_CLIENT_ID and MERCHANT_CLIENT_SECRET))


def _only_digits(s: str) -> str:
    return "".join(filter(str.isdigit, s or ""))


def _bearer() -> str:
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    now = time.time()
    if _token_cache["value"] and _token_cache["exp"] - 60 > now:
        return _token_cache["value"]
    if not (MERCHANT_CLIENT_ID and MERCHANT_CLIENT_SECRET):
        raise RuntimeError(
            "Appmax não configurada. Defina APPMAX_ACCESS_TOKEN (ou "
            "APPMAX_MERCHANT_CLIENT_ID + APPMAX_MERCHANT_CLIENT_SECRET)."
        )
    r = httpx.post(
        AUTH_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": MERCHANT_CLIENT_ID,
            "client_secret": MERCHANT_CLIENT_SECRET,
        },
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Appmax auth {r.status_code}: {r.text}")
    data = r.json()
    token = data.get("access_token", "")
    if not token:
        raise RuntimeError(f"Appmax auth sem access_token: {data}")
    _token_cache["value"] = token
    _token_cache["exp"] = now + float(data.get("expires_in", 3600))
    return token


def _post(path: str, payload: dict) -> dict:
    if not is_configured():
        raise RuntimeError("APPMAX não configurado no servidor.")
    r = httpx.post(
        f"{BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {_bearer()}",
            "accept": "application/json",
            "content-type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Appmax {path} {r.status_code}: {r.text}")
    return r.json().get("data", {})


# =====================================================================
# API v3 clássica (admin.appmax.com.br/api/v3) — integração direta de um
# único lojista, autenticada por "access-token" no corpo de cada request.
# É o caminho para quem tem um token de lojista (suporte Appmax) e NÃO usa o
# fluxo de instalação/appstore.
# =====================================================================
V3_URL = os.getenv("APPMAX_V3_URL", "https://admin.appmax.com.br/api/v3").rstrip("/")
V3_TOKEN = os.getenv("APPMAX_V3_TOKEN", "")


def v3_configured() -> bool:
    return bool(V3_TOKEN)


def _v3_post(path: str, body: dict, token: str = "") -> dict:
    """POST na API v3. Devolve o JSON completo (com 'success'/'data'). Levanta
    RuntimeError com o corpo cru em caso de erro HTTP."""
    payload = {"access-token": token or V3_TOKEN, **body}
    r = httpx.post(
        f"{V3_URL}{path}",
        headers={"accept": "application/json", "content-type": "application/json"},
        json=payload,
        timeout=30,
    )
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        data = {"_raw": r.text}
    if r.status_code >= 300:
        raise RuntimeError(f"Appmax v3 {path} {r.status_code}: {data}")
    return data


def v3_create_customer(
    first_name: str, last_name: str, email: str, phone: str,
    document_number: str = "", token: str = "",
) -> int:
    body = {
        "firstname": first_name or ".",
        "lastname": last_name or ".",
        "email": email,
        "telephone": _only_digits(phone)[-11:] or "00000000000",
    }
    doc = _only_digits(document_number)
    if doc:
        body["cpf" if len(doc) <= 11 else "cnpj"] = doc
    data = _v3_post("/customer", body, token)
    return (data.get("data") or {}).get("id")


def v3_create_order(
    customer_id: int, value_reais: float, product_name: str, sku: str, token: str = ""
) -> int:
    body = {
        "total": round(float(value_reais), 2),
        "products": [
            {
                "sku": sku,
                "name": product_name,
                "qty": 1,
                "price": round(float(value_reais), 2),
                "digital_product": 1,
            }
        ],
        "customer_id": customer_id,
        "shipping": 0,
        "discount": 0,
    }
    data = _v3_post("/order", body, token)
    return (data.get("data") or {}).get("id")


def v3_pay_credit_card(
    order_id: int, customer_id: int, card_number: str, card_cvv: str,
    card_month: str, card_year: str, holder_name: str, holder_document: str,
    installments: int = 1, soft_descriptor: str = "AGENDABARBER", token: str = "",
) -> dict:
    body = {
        "cart": {"order_id": order_id},
        "customer": {"customer_id": customer_id},
        "payment": {
            "CreditCard": {
                "number": _only_digits(card_number),
                "cvv": _only_digits(card_cvv),
                "month": int(str(card_month).lstrip("0") or 0),
                "year": int(card_year),
                "name": holder_name,
                "document_number": _only_digits(holder_document),
                "installments": installments,
                "soft_descriptor": soft_descriptor[:22],
            }
        },
    }
    return _v3_post("/payment/credit-card", body, token)


def create_customer(
    first_name: str, last_name: str, email: str, phone: str, ip: str, document_number: str = ""
) -> int:
    """POST /v1/customers -> customer_id."""
    body = {
        "first_name": first_name or ".",
        "last_name": last_name or ".",
        "email": email,
        "phone": _only_digits(phone)[-11:] or "00000000000",
        "ip": ip or "127.0.0.1",
    }
    doc = _only_digits(document_number)
    if doc:
        body["document_number"] = doc
    return _post("/v1/customers", body)["customer"]["id"]


def create_order(customer_id: int, value_cents: int, product_name: str, sku: str) -> int:
    """POST /v1/orders -> order_id. Valores em CENTAVOS."""
    body = {
        "customer_id": customer_id,
        "shipping_value": 0,
        "discount_value": 0,
        "products": [
            {
                "sku": sku,
                "name": product_name,
                "quantity": 1,
                "unit_value": int(value_cents),
                "type": "digital",
            }
        ],
    }
    return _post("/v1/orders", body)["order"]["id"]


def tokenize_card(
    number: str, cvv: str, expiration_month: str, expiration_year: str, holder_name: str
) -> str:
    """POST /v1/payments/tokenize -> token (tokeniza o cartão no servidor)."""
    body = {
        "payment_data": {
            "credit_card": {
                "number": _only_digits(number),
                "cvv": _only_digits(cvv),
                "expiration_month": str(expiration_month),
                "expiration_year": str(expiration_year),
                "holder_name": holder_name,
            }
        }
    }
    return _post("/v1/payments/tokenize", body)["token"]


def pay_credit_card(
    order_id: int,
    customer_id: int,
    card_token: str,
    holder_name: str,
    holder_document_number: str,
    interval: str = "",
    soft_descriptor: str = "AGENDABARBER",
) -> dict:
    """POST /v1/payments/credit-card. Se `interval` ('month'/'year'), cobra com recorrência."""
    credit_card = {
        "token": card_token,
        "holder_name": holder_name,
        "holder_document_number": _only_digits(holder_document_number),
        "installments": 1,
        "soft_descriptor": soft_descriptor[:22],
    }
    payment_data = {"credit_card": credit_card}
    if interval:
        payment_data["subscription"] = {"interval": interval, "interval_count": 1}
    return _post(
        "/v1/payments/credit-card",
        {"order_id": order_id, "customer_id": customer_id, "payment_data": payment_data},
    )
