"""Cliente da API da Appmax (assinaturas recorrentes no cartão).

Fluxo (doc oficial appmax.readme.io):
  1. Autenticação OAuth2 (client_credentials) com as credenciais do MERCHANT
     -> POST {AUTH_URL}  (form-urlencoded)  -> access_token (Bearer, ~1h).
  2. Com o Bearer, chama os endpoints /v1:
       POST /v1/customers             -> data.customer.id
       POST /v1/orders                -> data.order.id   (valores em CENTAVOS)
       POST /v1/payments/credit-card  -> pagamento (+ objeto subscription p/ recorrência)
     E, opcionalmente, o link de pagamento hospedado:
       POST /v1/payment-link          -> data.checkout_url

Configuração por variáveis de ambiente:
  APPMAX_MERCHANT_CLIENT_ID      -> client_id do merchant (gerado na instalação do app)
  APPMAX_MERCHANT_CLIENT_SECRET  -> client_secret do merchant
  APPMAX_AUTH_URL   -> produção: https://auth.appmax.com.br/oauth2/token
                       sandbox:  https://auth.sandboxappmax.com.br/oauth2/token
  APPMAX_BASE_URL   -> produção: https://api.appmax.com.br
                       sandbox:  https://api.sandboxappmax.com.br
"""
import os
import time

import httpx

MERCHANT_CLIENT_ID = os.getenv("APPMAX_MERCHANT_CLIENT_ID", "")
MERCHANT_CLIENT_SECRET = os.getenv("APPMAX_MERCHANT_CLIENT_SECRET", "")
AUTH_URL = os.getenv("APPMAX_AUTH_URL", "https://auth.appmax.com.br/oauth2/token")
BASE_URL = os.getenv("APPMAX_BASE_URL", "https://api.appmax.com.br").rstrip("/")

# Cache do token de acesso (client_credentials expira em ~1h).
_token_cache = {"value": "", "exp": 0.0}


def is_configured() -> bool:
    return bool(MERCHANT_CLIENT_ID and MERCHANT_CLIENT_SECRET)


def _get_token() -> str:
    """Obtém (e reaproveita) o Bearer token do merchant via client_credentials."""
    now = time.time()
    if _token_cache["value"] and _token_cache["exp"] - 60 > now:
        return _token_cache["value"]
    if not is_configured():
        raise RuntimeError(
            "Appmax não configurada. Defina APPMAX_MERCHANT_CLIENT_ID e "
            "APPMAX_MERCHANT_CLIENT_SECRET no ambiente."
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


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "accept": "application/json",
            "content-type": "application/json",
        },
        timeout=30,
    )


def _only_digits(s: str) -> str:
    return "".join(filter(str.isdigit, s or ""))


def create_customer(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    ip: str,
    document_number: str = "",
) -> int:
    """Cria/atualiza um cliente. Retorna o customer_id."""
    body = {
        "first_name": first_name,
        "last_name": last_name or ".",
        "email": email,
        "phone": _only_digits(phone)[-11:] or "00000000000",
        "ip": ip or "0.0.0.0",
    }
    doc = _only_digits(document_number)
    if doc:
        body["document_number"] = doc
    with _client() as c:
        r = c.post("/v1/customers", json=body)
        if r.status_code >= 300:
            raise RuntimeError(f"Appmax /customers {r.status_code}: {r.text}")
        return r.json()["data"]["customer"]["id"]


def create_order(customer_id: int, value_cents: int, product_name: str, sku: str) -> int:
    """Cria um pedido (produto digital) vinculado ao cliente. Retorna o order_id."""
    body = {
        "customer_id": customer_id,
        "products_value": int(value_cents),
        "discount_value": 0,
        "shipping_value": 0,
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
    with _client() as c:
        r = c.post("/v1/orders", json=body)
        if r.status_code >= 300:
            raise RuntimeError(f"Appmax /orders {r.status_code}: {r.text}")
        return r.json()["data"]["order"]["id"]


def pay_credit_card_recurring(
    order_id: int,
    customer_id: int,
    card_token: str,
    holder_name: str,
    holder_document_number: str,
    interval: str,
    soft_descriptor: str = "AGENDABARBER",
) -> dict:
    """Paga um pedido no cartão com recorrência (assinatura).

    `card_token` é o token gerado no navegador pelo Appmax JS.
    `interval`: "month" (mensal) ou "year" (anual).
    """
    body = {
        "order_id": order_id,
        "customer_id": customer_id,
        "payment_data": {
            "credit_card": {
                "token": card_token,
                "holder_name": holder_name,
                "holder_document_number": _only_digits(holder_document_number),
                "installments": 1,
                "soft_descriptor": soft_descriptor[:22],
            }
        },
        "subscription": {"interval": interval, "interval_count": 1},
    }
    with _client() as c:
        r = c.post("/v1/payments/credit-card", json=body)
        if r.status_code >= 300:
            raise RuntimeError(f"Appmax /payments/credit-card {r.status_code}: {r.text}")
        return r.json()


def create_payment_link(name: str, value_cents: int, description: str) -> dict:
    """Cria um link de pagamento hospedado. Retorna {id, checkout_url}.

    Observação: o link cobre pagamento avulso (cartão/pix/boleto). A recorrência
    de assinatura é feita pelo fluxo de cartão (pay_credit_card_recurring).
    """
    body = {
        "name": name[:255],
        "value": max(int(value_cents), 500),
        "description": description[:1000],
        "product_type": "digital",
        "payments": ["creditcard", "pix", "boleto"],
        "max_installments": 1,
        "fee_transfer_from_installment": 0,
    }
    with _client() as c:
        r = c.post("/v1/payment-link", json=body)
        if r.status_code >= 300:
            raise RuntimeError(f"Appmax /payment-link {r.status_code}: {r.text}")
        return r.json()["data"]
