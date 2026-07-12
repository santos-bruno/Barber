"""
API + site de agendamento da Barbearia e Belezaria Sr. Perison.

- API REST: /services, /clients, /appointments, /cashflow, /hours
- Site público de agendamento servido em "/" (o link para anúncios/clientes)
- Docs interativas em /docs
"""
import os
from datetime import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

import models
from database import Base, SessionLocal, engine
from routers import appointments, cashflow, clients, hours, services

Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

ESTABELECIMENTO = {
    "nome": "Barbearia e Belezaria Sr. Perison",
    "endereco": "Av. Bartolomeu de Gusmão, 857 - Casa E - Aparecida, "
    "Santarém - PA, 68030-350",
    "whatsapp": "(93) 99207-8226",
    "whatsapp_link": "https://wa.me/5593992078226",
    "whatsapp_number": "5593992078226",
    "desenvolvedor": "Bruno",
}

SERVICOS_PADRAO = [
    {"name": "Corte de Cabelo", "description": "Corte masculino tradicional ou moderno",
     "price": 35.0, "duration_minutes": 30},
    {"name": "Barba", "description": "Aparo e modelagem de barba com toalha quente",
     "price": 25.0, "duration_minutes": 30},
    {"name": "Corte + Barba", "description": "Combo completo corte e barba",
     "price": 55.0, "duration_minutes": 60},
    {"name": "Sobrancelha", "description": "Design e limpeza de sobrancelha",
     "price": 15.0, "duration_minutes": 15},
    {"name": "Pézinho / Acabamento", "description": "Acabamento e contorno",
     "price": 15.0, "duration_minutes": 15},
]


def seed() -> None:
    """Popula serviços e horários padrão no primeiro boot."""
    db = SessionLocal()
    try:
        if db.query(models.Service).count() == 0:
            for s in SERVICOS_PADRAO:
                db.add(models.Service(**s))

        if db.query(models.BusinessHour).count() == 0:
            for weekday in range(7):
                is_open = weekday != 6  # fecha aos domingos
                db.add(
                    models.BusinessHour(
                        weekday=weekday,
                        is_open=is_open,
                        open_time=time(9, 0) if is_open else None,
                        close_time=time(19, 0) if is_open else None,
                        slot_minutes=30,
                    )
                )
        db.commit()
    finally:
        db.close()


app = FastAPI(
    title="Barbearia e Belezaria Sr. Perison",
    description="API e site de agendamentos.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services.router)
app.include_router(clients.router)
app.include_router(appointments.router)
app.include_router(cashflow.router)
app.include_router(hours.router)


@app.on_event("startup")
def on_startup() -> None:
    seed()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"estabelecimento": ESTABELECIMENTO}


@app.get("/")
def booking_site():
    """Serve o site de agendamento (link público)."""
    index = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return JSONResponse({"status": "ok", "estabelecimento": ESTABELECIMENTO})
