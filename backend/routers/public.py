"""Endpoints públicos do site de agendamento (por slug da barbearia)."""
from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from booking import compute_availability, create_appointment_core
from database import get_db
from security import subscription_active

router = APIRouter(prefix="/public", tags=["public"])


def _get_tenant(db: Session, slug: str) -> models.Tenant:
    tenant = db.query(models.Tenant).filter(models.Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada.")
    if not subscription_active(tenant):
        raise HTTPException(
            status_code=403,
            detail="Esta barbearia está temporariamente indisponível para agendamento online.",
        )
    return tenant


@router.get("/{slug}/info")
def public_info(slug: str, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    return {
        "nome": tenant.name,
        "endereco": tenant.address,
        "whatsapp": tenant.whatsapp,
        "whatsapp_number": "".join(filter(str.isdigit, tenant.whatsapp or "")),
        "slug": tenant.slug,
    }


@router.get("/{slug}/services", response_model=List[schemas.ServiceOut])
def public_services(slug: str, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    return (
        db.query(models.Service)
        .filter(models.Service.tenant_id == tenant.id, models.Service.active.is_(True))
        .order_by(models.Service.name)
        .all()
    )


@router.get("/{slug}/availability", response_model=schemas.AvailabilityOut)
def public_availability(
    slug: str,
    date: date_type = Query(...),
    service_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    tenant = _get_tenant(db, slug)
    slots = compute_availability(db, tenant.id, date, service_id)
    return schemas.AvailabilityOut(date=date, slots=slots)


@router.post("/{slug}/appointments", response_model=schemas.AppointmentOut, status_code=201)
def public_create_appointment(
    slug: str, payload: schemas.AppointmentCreate, db: Session = Depends(get_db)
):
    tenant = _get_tenant(db, slug)
    return create_appointment_core(
        db,
        tenant.id,
        payload.customer_name,
        payload.phone,
        payload.service_id,
        payload.service_name,
        payload.date,
        payload.time,
        source="web",
        notes=payload.notes,
    )
