"""Cliente mínimo da API do Asaas (assinaturas recorrentes).

Configuração por variáveis de ambiente:
  ASAAS_API_KEY   -> chave da API (sandbox começa com $aact_hmlg_, prod $aact_prod_)
  ASAAS_BASE_URL  -> padrão sandbox: https://api-sandbox.asaas.com/v3
                     produção:       https://api.asaas.com/v3
"""
import os

import httpx

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")
ASAAS_BASE_URL = os.getenv("ASAAS_BASE_URL", "https://api-sandbox.asaas.com/v3").rstrip("/")


def is_configured() -> bool:
    return bool(ASAAS_API_KEY)


def _headers():
    return {"access_token": ASAAS_API_KEY, "Content-Type": "application/json"}


def _client():
    if not is_configured():
        raise RuntimeError(
            "ASAAS_API_KEY não configurada. Defina a chave do Asaas no ambiente."
        )
    return httpx.Client(base_url=ASAAS_BASE_URL, headers=_headers(), timeout=30)


def create_customer(name: str, email: str, cpf_cnpj: str, phone: str = "") -> str:
    with _client() as c:
        r = c.post(
            "/customers",
            json={
                "name": name,
                "email": email,
                "cpfCnpj": cpf_cnpj,
                "mobilePhone": "".join(filter(str.isdigit, phone or "")) or None,
            },
        )
        r.raise_for_status()
        return r.json()["id"]


def create_subscription(
    customer_id: str,
    billing_type: str,
    value: float,
    cycle: str,
    description: str,
    next_due_date: str,
) -> dict:
    with _client() as c:
        r = c.post(
            "/subscriptions",
            json={
                "customer": customer_id,
                "billingType": billing_type,  # CREDIT_CARD | PIX | BOLETO | UNDEFINED
                "value": value,
                "cycle": cycle,  # MONTHLY | YEARLY
                "description": description,
                "nextDueDate": next_due_date,
            },
        )
        r.raise_for_status()
        return r.json()


def first_payment_checkout_url(subscription_id: str) -> str:
    """Retorna a URL de checkout (invoiceUrl) da primeira cobrança da assinatura."""
    with _client() as c:
        r = c.get(f"/subscriptions/{subscription_id}/payments")
        r.raise_for_status()
        data = r.json().get("data", [])
        if data:
            return data[0].get("invoiceUrl", "")
    return ""
