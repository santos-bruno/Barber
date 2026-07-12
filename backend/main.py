"""
API da Barbearia e Belezaria Sr. Perison.

Endpoints:
    GET  /               -> healthcheck + dados do estabelecimento
    GET  /services       -> lista de serviços
    POST /services       -> cria um serviço
    GET  /appointments   -> lista de agendamentos
    POST /appointments   -> cria um agendamento
"""
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine, get_db

# Cria as tabelas no primeiro boot.
Base.metadata.create_all(bind=engine)

# Dados do estabelecimento (hardcoded, conforme especificação).
ESTABELECIMENTO = {
    "nome": "Barbearia e Belezaria Sr. Perison",
    "endereco": "Av. Bartolomeu de Gusmão, 857 - Casa E - Aparecida, "
    "Santarém - PA, 68030-350",
    "whatsapp": "(93) 99207-8226",
    "whatsapp_link": "https://wa.me/5593992078226",
    "desenvolvedor": "Bruno",
}

# Serviços padrão inseridos no primeiro boot, caso a tabela esteja vazia.
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


def seed_services() -> None:
    """Popula os serviços padrão se ainda não houver nenhum cadastrado."""
    db = SessionLocal()
    try:
        if db.query(models.Service).count() == 0:
            for s in SERVICOS_PADRAO:
                db.add(models.Service(**s))
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="API - Barbearia e Belezaria Sr. Perison",
    description="Back-end de agendamentos da barbearia.",
    version="1.0.0",
)

# CORS liberado para o app mobile (Expo) consumir a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    seed_services()


@app.get("/")
def root():
    """Healthcheck + dados do estabelecimento."""
    return {"status": "ok", "estabelecimento": ESTABELECIMENTO}


# ---------- Services ----------
@app.get("/services", response_model=List[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return db.query(models.Service).all()


@app.post("/services", response_model=schemas.ServiceOut, status_code=201)
def create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db)):
    service = models.Service(**payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


# ---------- Appointments ----------
@app.get("/appointments", response_model=List[schemas.AppointmentOut])
def list_appointments(db: Session = Depends(get_db)):
    return db.query(models.Appointment).order_by(models.Appointment.created_at.desc()).all()


@app.post("/appointments", response_model=schemas.AppointmentOut, status_code=201)
def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    if not payload.customer_name.strip():
        raise HTTPException(status_code=400, detail="Nome do cliente é obrigatório.")
    appointment = models.Appointment(**payload.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
