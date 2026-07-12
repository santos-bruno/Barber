"""Cria dados padrão (serviços + horários) para uma nova barbearia."""
from datetime import time

from sqlalchemy.orm import Session

import models

SERVICOS_PADRAO = [
    {"name": "Corte de Cabelo", "description": "Corte masculino tradicional ou moderno",
     "price": 35.0, "duration_minutes": 30},
    {"name": "Barba", "description": "Aparo e modelagem de barba com toalha quente",
     "price": 25.0, "duration_minutes": 30},
    {"name": "Corte + Barba", "description": "Combo completo corte e barba",
     "price": 55.0, "duration_minutes": 60},
    {"name": "Sobrancelha", "description": "Design e limpeza de sobrancelha",
     "price": 15.0, "duration_minutes": 15},
]


def seed_tenant_defaults(db: Session, tenant_id: int) -> None:
    for s in SERVICOS_PADRAO:
        db.add(models.Service(tenant_id=tenant_id, **s))
    for weekday in range(7):
        is_open = weekday != 6  # fecha domingo
        db.add(
            models.BusinessHour(
                tenant_id=tenant_id,
                weekday=weekday,
                is_open=is_open,
                open_time=time(9, 0) if is_open else None,
                close_time=time(19, 0) if is_open else None,
                slot_minutes=30,
            )
        )
