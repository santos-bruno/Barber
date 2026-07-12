"""Endpoints de agendamentos e de disponibilidade de horários."""
from datetime import date as date_type
from datetime import datetime, time, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.clients import get_or_create_client

router = APIRouter(prefix="/appointments", tags=["appointments"])

STATUS_VALIDOS = {"pendente", "confirmado", "concluido", "cancelado"}


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _minutes_to_hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


@router.get("/availability", response_model=schemas.AvailabilityOut)
def availability(
    date: date_type = Query(...),
    service_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Retorna os horários livres para uma data (considera horário de
    funcionamento, duração do serviço e agendamentos já existentes)."""
    weekday = date.weekday()  # 0=segunda ... 6=domingo
    bh = (
        db.query(models.BusinessHour)
        .filter(models.BusinessHour.weekday == weekday)
        .first()
    )
    if not bh or not bh.is_open or not bh.open_time or not bh.close_time:
        return schemas.AvailabilityOut(date=date, slots=[])

    # Duração do serviço solicitado (padrão = passo da agenda).
    duration = bh.slot_minutes
    if service_id:
        service = db.get(models.Service, service_id)
        if service:
            duration = service.duration_minutes

    open_m = _to_minutes(bh.open_time)
    close_m = _to_minutes(bh.close_time)
    step = bh.slot_minutes or 30

    # Intervalos já ocupados (ignora cancelados).
    booked = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.date == date,
            models.Appointment.status != "cancelado",
        )
        .all()
    )
    busy = [
        (_to_minutes(a.time), _to_minutes(a.time) + (a.duration_minutes or step))
        for a in booked
    ]

    # Se a data for hoje, não oferecer horários que já passaram.
    now_min = -1
    if date == datetime.now().date():
        now_min = datetime.now().hour * 60 + datetime.now().minute

    slots: List[str] = []
    start = open_m
    while start + duration <= close_m:
        end = start + duration
        overlaps = any(start < b_end and b_start < end for b_start, b_end in busy)
        if not overlaps and start > now_min:
            slots.append(_minutes_to_hhmm(start))
        start += step

    return schemas.AvailabilityOut(date=date, slots=slots)


@router.get("", response_model=List[schemas.AppointmentOut])
def list_appointments(
    date: Optional[date_type] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Appointment)
    if date:
        query = query.filter(models.Appointment.date == date)
    if status:
        query = query.filter(models.Appointment.status == status)
    return query.order_by(
        models.Appointment.date.asc(), models.Appointment.time.asc()
    ).all()


@router.post("", response_model=schemas.AppointmentOut, status_code=201)
def create_appointment(
    payload: schemas.AppointmentCreate, db: Session = Depends(get_db)
):
    if not payload.customer_name.strip():
        raise HTTPException(status_code=400, detail="Nome do cliente é obrigatório.")

    # Resolve serviço (preço/duração) quando informado.
    price = 0.0
    duration = 30
    service_name = payload.service_name
    if payload.service_id:
        service = db.get(models.Service, payload.service_id)
        if service:
            price = service.price
            duration = service.duration_minutes
            service_name = service.name

    # Evita conflito de horário (mesma data/hora já ocupada).
    conflict = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.date == payload.date,
            models.Appointment.time == payload.time,
            models.Appointment.status != "cancelado",
        )
        .first()
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Horário já ocupado.")

    client = get_or_create_client(db, payload.customer_name.strip(), payload.phone)

    appointment = models.Appointment(
        client_id=client.id,
        customer_name=payload.customer_name.strip(),
        phone=payload.phone,
        service_id=payload.service_id,
        service_name=service_name,
        price=price,
        date=payload.date,
        time=payload.time,
        duration_minutes=duration,
        status="pendente",
        source=payload.source,
        notes=payload.notes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}", response_model=schemas.AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
):
    appt = db.get(models.Appointment, appointment_id)
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
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.get(models.Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    db.delete(appt)
    db.commit()
