"""Cliente da API v3 da Appmax (admin.appmax.com.br/api/v3).

Autenticação: o token vai no CORPO de cada requisição, no campo "access-token".
Endpoint base: https://admin.appmax.com.br/api/v3

Fluxo:
  POST /customer          -> data.id (customer_id)
  POST /order             -> data.id (order_id)   (total em REAIS; digital_product:1)
  POST /payment/credit-card -> processa o pagamento do pedido

Configuração por variáveis de ambiente:
  APPMAX_ACCESS_TOKEN  -> token fornecido pelo suporte da Appmax
  APPMAX_BASE_URL      -> padrão https://admin.appmax.com.br/api/v3
"""
import os

import httpx

ACCESS_TOKEN = os.getenv("APPMAX_ACCESS_TOKEN", "")
BASE_URL = os.getenv("APPMAX_BASE_URL", "https://admin.appmax.com.br/api/v3").rstrip("/")


def is_configured() -> bool:
    return bool(ACCESS_TOKEN)


def _only_digits(s: str) -> str:
    return "".join(filter(str.isdigit, s or ""))


def _post(path: str, payload: dict) -> dict:
    """POST autenticado (access-token no corpo). Retorna o objeto `data`."""
    if not is_configured():
        raise RuntimeError("APPMAX_ACCESS_TOKEN não configurado no servidor.")
    body = {"access-token": ACCESS_TOKEN, **payload}
    r = httpx.post(f"{BASE_URL}{path}", json=body, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"Appmax {path} {r.status_code}: {r.text}")
    data = r.json()
    if isinstance(data, dict) and data.get("success") is False:
        raise RuntimeError(f"Appmax {path}: {data}")
    return data.get("data", data) if isinstance(data, dict) else data


def create_customer(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    ip: str = "",
    document_number: str = "",
) -> int:
    """Cria um cliente. Retorna o customer_id."""
    body = {
        "firstname": first_name or ".",
        "lastname": last_name or ".",
        "email": email,
        "telephone": _only_digits(phone),
    }
    doc = _only_digits(document_number)
    if doc:
        body["cpf" if len(doc) <= 11 else "cnpj"] = doc
    if ip:
        body["ip"] = ip
    data = _post("/customer", body)
    return data["id"]


def create_order(customer_id: int, value_reais: float, product_name: str, sku: str) -> int:
    """Cria um pedido (infoproduto/digital). Retorna o order_id. Total em REAIS."""
    body = {
        "total": round(float(value_reais), 2),
        "products": [{"sku": sku, "name": product_name, "qty": 1}],
        "customer_id": customer_id,
        "digital_product": 1,
    }
    data = _post("/order", body)
    return data["id"]


def pay_credit_card(
    order_id: int,
    customer_id: int,
    card_token: str,
    holder_name: str,
    holder_document_number: str,
    installments: int = 1,
    soft_descriptor: str = "AGENDABARBER",
    recurrence: bool = False,
) -> dict:
    """Paga um pedido no cartão usando o token do cartão (tokenizado no navegador).

    `recurrence`: quando True, marca a cobrança como recorrente (assinatura).
    O parâmetro exato de recorrência da v3 é confirmado com o suporte Appmax.
    """
    credit_card = {
        "token": card_token,
        "name": holder_name,
        "document_number": _only_digits(holder_document_number),
        "installments": installments,
        "soft_descriptor": soft_descriptor[:22],
    }
    body = {
        "cart": {"order_id": order_id},
        "customer": {"customer_id": customer_id},
        "payment": {"CreditCard": credit_card},
    }
    if recurrence:
        # A Appmax v3 ativa a recorrência via o app "Appmax Assinaturas".
        # Sinalizamos aqui; ajustar o campo conforme orientação do suporte.
        body["payment"]["CreditCard"]["recurrence"] = True
    return _post("/payment/credit-card", body)
