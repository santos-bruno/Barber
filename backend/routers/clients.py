"""Endpoints de clientes (fluxo de clientes / contatos)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/clients", tags=["clients"])


def get_or_create_client(db: Session, name: str, phone: str) -> models.Client:
    """Localiza um cliente pelo telefone ou cria um novo."""
    client = None
    if phone:
        client = (
            db.query(models.Client).filter(models.Client.phone == phone).first()
        )
    if not client:
        client = models.Client(name=name, phone=phone)
        db.add(client)
        db.flush()  # garante o id sem commit final
    return client


@router.get("", response_model=List[schemas.ClientOut])
def list_clients(search: str = "", db: Session = Depends(get_db)):
    query = db.query(models.Client)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Client.name.ilike(like)) | (models.Client.phone.ilike(like))
        )
    return query.order_by(models.Client.name).all()


@router.post("", response_model=schemas.ClientOut, status_code=201)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Nome é obrigatório.")
    client = models.Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return client


@router.get("/{client_id}/appointments", response_model=List[schemas.AppointmentOut])
def client_appointments(client_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.client_id == client_id)
        .order_by(models.Appointment.date.desc(), models.Appointment.time.desc())
        .all()
    )


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int, payload: schemas.ClientCreate, db: Session = Depends(get_db)
):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    for key, value in payload.model_dump().items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client
