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
