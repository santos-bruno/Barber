"""Gestão de barbeiros (logins de equipe) — somente o dono."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import hash_password, require_active_subscription, require_owner

router = APIRouter(prefix="/staff", tags=["staff"], dependencies=[Depends(require_owner)])


@router.get("", response_model=List[schemas.StaffOut])
def list_staff(
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.User)
        .filter(
            models.User.tenant_id == tenant.id,
            models.User.role == "barber",
            models.User.active.is_(True),
        )
        .order_by(models.User.name)
        .all()
    )


@router.post("", response_model=schemas.StaffOut, status_code=201)
def create_staff(
    payload: schemas.StaffCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter ao menos 6 caracteres.")
    exists = db.query(models.User).filter(models.User.email == payload.email.lower()).first()
    if exists:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    barber = models.User(
        tenant_id=tenant.id,
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="barber",
        active=True,
    )
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber


@router.delete("/{staff_id}", status_code=204)
def deactivate_staff(
    staff_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    barber = (
        db.query(models.User)
        .filter(
            models.User.id == staff_id,
            models.User.tenant_id == tenant.id,
            models.User.role == "barber",
        )
        .first()
    )
    if not barber:
        raise HTTPException(status_code=404, detail="Barbeiro não encontrado.")
    barber.active = False
    db.commit()


def _barber_of_tenant(db, tenant_id, barber_id):
    b = (
        db.query(models.User)
        .filter(
            models.User.id == barber_id,
            models.User.tenant_id == tenant_id,
            models.User.role == "barber",
        )
        .first()
    )
    if not b:
        raise HTTPException(status_code=404, detail="Barbeiro não encontrado.")
    return b


@router.get("/{barber_id}/hours", response_model=List[schemas.BarberHourOut])
def barber_hours(
    barber_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    _barber_of_tenant(db, tenant.id, barber_id)
    return (
        db.query(models.BarberHour)
        .filter(models.BarberHour.tenant_id == tenant.id, models.BarberHour.barber_id == barber_id)
        .order_by(models.BarberHour.weekday)
        .all()
    )


@router.put("/{barber_id}/hours/{weekday}", response_model=schemas.BarberHourOut)
def set_barber_hour(
    barber_id: int,
    weekday: int,
    payload: schemas.BarberHourBase,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if weekday < 0 or weekday > 6:
        raise HTTPException(status_code=400, detail="weekday deve ser 0..6.")
    _barber_of_tenant(db, tenant.id, barber_id)
    bh = (
        db.query(models.BarberHour)
        .filter(
            models.BarberHour.tenant_id == tenant.id,
            models.BarberHour.barber_id == barber_id,
            models.BarberHour.weekday == weekday,
        )
        .first()
    )
    if not bh:
        bh = models.BarberHour(tenant_id=tenant.id, barber_id=barber_id, weekday=weekday)
        db.add(bh)
    bh.is_open = payload.is_open
    bh.open_time = payload.open_time
    bh.close_time = payload.close_time
    db.commit()
    db.refresh(bh)
    return bh
