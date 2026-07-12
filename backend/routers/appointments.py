"""Endpoints de agendamentos (admin, escopados por barbearia)."""
from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from booking import compute_availability, create_appointment_core
from database import get_db
from security import require_active_subscription

router = APIRouter(prefix="/appointments", tags=["appointments"])

STATUS_VALIDOS = {"pendente", "confirmado", "concluido", "cancelado"}


@router.get("/availability", response_model=schemas.AvailabilityOut)
def availability(
    date: date_type = Query(...),
    service_id: Optional[int] = Query(None),
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    slots = compute_availability(db, tenant.id, date, service_id)
    return schemas.AvailabilityOut(date=date, slots=slots)


@router.get("", response_model=List[schemas.AppointmentOut])
def list_appointments(
    date: Optional[date_type] = None,
    status: Optional[str] = None,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    query = db.query(models.Appointment).filter(models.Appointment.tenant_id == tenant.id)
    if date:
        query = query.filter(models.Appointment.date == date)
    if status:
        query = query.filter(models.Appointment.status == status)
    return query.order_by(
        models.Appointment.date.asc(), models.Appointment.time.asc()
    ).all()


@router.post("", response_model=schemas.AppointmentOut, status_code=201)
def create_appointment(
    payload: schemas.AppointmentCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return create_appointment_core(
        db,
        tenant.id,
        payload.customer_name,
        payload.phone,
        payload.service_id,
        payload.service_name,
        payload.date,
        payload.time,
        source="admin",
        notes=payload.notes,
        payment_type=payload.payment_type,
    )


@router.patch("/{appointment_id}", response_model=schemas.AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: schemas.AppointmentUpdate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    appt = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.tenant_id == tenant.id,
        )
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    if payload.status is not None:
        if payload.status not in STATUS_VALIDOS:
            raise HTTPException(status_code=400, detail="Status inválido.")
        appt.status = payload.status
    if payload.notes is not None:
        appt.notes = payload.notes
    if payload.date is not None:
        appt.date = payload.date
    if payload.time is not None:
        appt.time = payload.time
    db.commit()
    db.refresh(appt)

    # Ao concluir, lança entrada automática no caixa (uma única vez).
    if appt.status == "concluido" and appt.price and appt.price > 0:
        ja_lancado = (
            db.query(models.Transaction)
            .filter(models.Transaction.appointment_id == appt.id)
            .first()
        )
        if not ja_lancado:
            db.add(
                models.Transaction(
                    tenant_id=tenant.id,
                    type="entrada",
                    amount=appt.price,
                    description=f"{appt.service_name} - {appt.customer_name}",
                    category="Serviço",
                    date=appt.date,
                    appointment_id=appt.id,
                )
            )
            db.commit()
            db.refresh(appt)

    return appt


@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(
    appointment_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    appt = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.tenant_id == tenant.id,
        )
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    db.delete(appt)
    db.commit()
