"""Endpoints de clientes (escopados por barbearia)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_active_subscription

router = APIRouter(prefix="/clients", tags=["clients"])


def get_or_create_client(
    db: Session, tenant_id: int, name: str, phone: str
) -> models.Client:
    """Localiza um cliente pelo telefone (no tenant) ou cria um novo."""
    client = None
    if phone:
        client = (
            db.query(models.Client)
            .filter(models.Client.tenant_id == tenant_id, models.Client.phone == phone)
            .first()
        )
    if not client:
        client = models.Client(tenant_id=tenant_id, name=name, phone=phone)
        db.add(client)
        db.flush()
    return client


@router.get("", response_model=List[schemas.ClientOut])
def list_clients(
    search: str = "",
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    query = db.query(models.Client).filter(models.Client.tenant_id == tenant.id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Client.name.ilike(like)) | (models.Client.phone.ilike(like))
        )
    return query.order_by(models.Client.name).all()


@router.post("", response_model=schemas.ClientOut, status_code=201)
def create_client(
    payload: schemas.ClientCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Nome é obrigatório.")
    client = models.Client(tenant_id=tenant.id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    client = (
        db.query(models.Client)
        .filter(models.Client.id == client_id, models.Client.tenant_id == tenant.id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return client


@router.get("/{client_id}/appointments", response_model=List[schemas.AppointmentOut])
def client_appointments(
    client_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.client_id == client_id,
            models.Appointment.tenant_id == tenant.id,
        )
        .order_by(models.Appointment.date.desc(), models.Appointment.time.desc())
        .all()
    )


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    payload: schemas.ClientCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    client = (
        db.query(models.Client)
        .filter(models.Client.id == client_id, models.Client.tenant_id == tenant.id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    for key, value in payload.model_dump().items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client
