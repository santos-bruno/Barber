"""Endpoints de horário de funcionamento (escopados por barbearia)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_active_subscription

router = APIRouter(prefix="/hours", tags=["hours"])


@router.get("", response_model=List[schemas.BusinessHourOut])
def list_hours(
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.BusinessHour)
        .filter(models.BusinessHour.tenant_id == tenant.id)
        .order_by(models.BusinessHour.weekday)
        .all()
    )


@router.put("/{weekday}", response_model=schemas.BusinessHourOut)
def upsert_hour(
    weekday: int,
    payload: schemas.BusinessHourBase,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if weekday < 0 or weekday > 6:
        raise HTTPException(status_code=400, detail="weekday deve ser 0..6.")
    bh = (
        db.query(models.BusinessHour)
        .filter(
            models.BusinessHour.tenant_id == tenant.id,
            models.BusinessHour.weekday == weekday,
        )
        .first()
    )
    if not bh:
        bh = models.BusinessHour(tenant_id=tenant.id, weekday=weekday)
        db.add(bh)
    bh.is_open = payload.is_open
    bh.open_time = payload.open_time
    bh.close_time = payload.close_time
    bh.slot_minutes = payload.slot_minutes
    db.commit()
    db.refresh(bh)
    return bh
