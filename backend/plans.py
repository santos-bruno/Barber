"""Configuração dos planos de assinatura (ajustável por variáveis de ambiente)."""
import os

TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "7"))

# Valores em reais. Anual com desconto (equivale a ~2 meses grátis).
PLANS = {
    "mensal": {
        "id": "mensal",
        "label": "Mensal",
        "price": float(os.getenv("PLAN_MENSAL_PRICE", "49.90")),
        "cycle": "MONTHLY",
        "description": "Assinatura mensal - Sistema Barbearia",
    },
    "anual": {
        "id": "anual",
        "label": "Anual",
        "price": float(os.getenv("PLAN_ANUAL_PRICE", "499.00")),
        "cycle": "YEARLY",
        "description": "Assinatura anual - Sistema Barbearia",
    },
}


def get_plan(plan_id: str):
    return PLANS.get(plan_id)
