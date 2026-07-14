"""Lógica compartilhada de disponibilidade e criação de agendamentos."""
from datetime import date as date_type
from datetime import datetime, time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models
from routers.clients import get_or_create_client


def _resolve_subscription(db, tenant_id, client, appt_date, appt_time):
    """Valida a assinatura de corte do cliente para a data/hora e devolve
    (client_subscription, plano). Lança HTTPException se não for permitido."""
    sub = (
        db.query(models.ClientSubscription)
        .filter(
            models.ClientSubscription.tenant_id == tenant_id,
            models.ClientSubscription.client_id == client.id,
            models.ClientSubscription.status == "ativa",
        )
        .order_by(models.ClientSubscription.id.desc())
        .first()
    )
    if not sub:
        raise HTTPException(status_code=400, detail="Cliente não tem assinatura de corte ativa.")

    plan = db.get(models.SubscriptionPlan, sub.plan_id)
    if not plan or not plan.active:
        raise HTTPException(status_code=400, detail="Plano de assinatura indisponível.")

    # Reset mensal dos cortes usados.
    if not sub.period_start or (sub.period_start.year, sub.period_start.month) != (appt_date.year, appt_date.month):
        sub.period_start = appt_date.replace(day=1)
        sub.cuts_used = 0

    # Regra de dias da semana.
    if plan.allowed_weekdays:
        allowed = {int(x) for x in plan.allowed_weekdays.split(",") if x.strip().isdigit()}
        if allowed and appt_date.weekday() not in allowed:
            raise HTTPException(status_code=400, detail="Dia não permitido para este plano de assinatura.")

    # Regra de janela de horário.
    if plan.allowed_time_start and appt_time < plan.allowed_time_start:
        raise HTTPException(status_code=400, detail="Horário fora da janela do plano.")
    if plan.allowed_time_end and appt_time > plan.allowed_time_end:
        raise HTTPException(status_code=400, detail="Horário fora da janela do plano.")

    # Cortes restantes (0 = ilimitado).
    if plan.cuts_per_month and sub.cuts_used >= plan.cuts_per_month:
        raise HTTPException(status_code=400, detail="Cortes do plano esgotados neste mês.")

    return sub, plan


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _minutes_to_hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def compute_availability(
    db: Session,
    tenant_id: int,
    date: date_type,
    service_id: Optional[int],
    barber_id: Optional[int] = None,
) -> List[str]:
    weekday = date.weekday()  # 0=segunda ... 6=domingo
    bh = (
        db.query(models.BusinessHour)
        .filter(
            models.BusinessHour.tenant_id == tenant_id,
            models.BusinessHour.weekday == weekday,
        )
        .first()
    )
    if not bh or not bh.is_open or not bh.open_time or not bh.close_time:
        return []

    step = bh.slot_minutes or 30
    duration = step
    if service_id:
        service = (
            db.query(models.Service)
            .filter(models.Service.id == service_id, models.Service.tenant_id == tenant_id)
            .first()
        )
        if service:
            duration = service.duration_minutes

    open_m = _to_minutes(bh.open_time)
    close_m = _to_minutes(bh.close_time)

    booked_q = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.tenant_id == tenant_id,
            models.Appointment.date == date,
            models.Appointment.status != "cancelado",
        )
    )
    if barber_id is not None:
        booked_q = booked_q.filter(models.Appointment.barber_id == barber_id)
    booked = booked_q.all()
    busy = [
        (_to_minutes(a.time), _to_minutes(a.time) + (a.duration_minutes or step))
        for a in booked
    ]

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
    return slots


def create_appointment_core(
    db: Session,
    tenant_id: int,
    customer_name: str,
    phone: str,
    service_id: Optional[int],
    service_name: str,
    date: date_type,
    time_value: time,
    source: str,
    notes: str = "",
    payment_type: str = "avista",
    barber_id: Optional[int] = None,
) -> models.Appointment:
    if not customer_name.strip():
        raise HTTPException(status_code=400, detail="Nome do cliente é obrigatório.")

    price = 0.0
    duration = 30
    resolved_name = service_name
    if service_id:
        service = (
            db.query(models.Service)
            .filter(models.Service.id == service_id, models.Service.tenant_id == tenant_id)
            .first()
        )
        if service:
            price = service.price
            duration = service.duration_minutes
            resolved_name = service.name

    # Resolve nome do barbeiro (se informado).
    barber_name = ""
    if barber_id is not None:
        barber = (
            db.query(models.User)
            .filter(models.User.id == barber_id, models.User.tenant_id == tenant_id)
            .first()
        )
        if not barber:
            raise HTTPException(status_code=404, detail="Barbeiro não encontrado.")
        barber_name = barber.name

    # Conflito de horário é por barbeiro (barbeiros diferentes podem atender ao mesmo tempo).
    conflict_q = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.tenant_id == tenant_id,
            models.Appointment.date == date,
            models.Appointment.time == time_value,
            models.Appointment.status != "cancelado",
            models.Appointment.barber_id == barber_id,
        )
    )
    if conflict_q.first():
        raise HTTPException(status_code=409, detail="Horário já ocupado.")

    client = get_or_create_client(db, tenant_id, customer_name.strip(), phone)

    subscription = None
    if payment_type == "assinatura":
        subscription, _plan = _resolve_subscription(db, tenant_id, client, date, time_value)
        subscription.cuts_used += 1
        price = 0.0  # já pago via mensalidade do plano

    appointment = models.Appointment(
        tenant_id=tenant_id,
        client_id=client.id,
        customer_name=customer_name.strip(),
        phone=phone,
        service_id=service_id,
        service_name=resolved_name,
        price=price,
        barber_id=barber_id,
        barber_name=barber_name,
        date=date,
        time=time_value,
        duration_minutes=duration,
        status="pendente",
        source=source,
        payment_type=payment_type,
        client_subscription_id=subscription.id if subscription else None,
        notes=notes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
