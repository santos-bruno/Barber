"""Endpoints de serviços (escopados por barbearia)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_active_subscription

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=List[schemas.ServiceOut])
def list_services(
    only_active: bool = True,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    query = db.query(models.Service).filter(models.Service.tenant_id == tenant.id)
    if only_active:
        query = query.filter(models.Service.active.is_(True))
    return query.order_by(models.Service.name).all()


@router.post("", response_model=schemas.ServiceOut, status_code=201)
def create_service(
    payload: schemas.ServiceCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    service = models.Service(tenant_id=tenant.id, **payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/{service_id}", response_model=schemas.ServiceOut)
def update_service(
    service_id: int,
    payload: schemas.ServiceCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    service = (
        db.query(models.Service)
        .filter(models.Service.id == service_id, models.Service.tenant_id == tenant.id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")
    for key, value in payload.model_dump().items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    service = (
        db.query(models.Service)
        .filter(models.Service.id == service_id, models.Service.tenant_id == tenant.id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")
    service.active = False
    db.commit()
