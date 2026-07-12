"""Endpoints de fluxo de caixa (escopados por barbearia)."""
from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_active_subscription

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


def _scoped(db: Session, tenant_id: int, start, end):
    query = db.query(models.Transaction).filter(models.Transaction.tenant_id == tenant_id)
    if start:
        query = query.filter(models.Transaction.date >= start)
    if end:
        query = query.filter(models.Transaction.date <= end)
    return query


@router.get("", response_model=List[schemas.TransactionOut])
def list_transactions(
    start: Optional[date_type] = None,
    end: Optional[date_type] = None,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return (
        _scoped(db, tenant.id, start, end)
        .order_by(models.Transaction.date.desc(), models.Transaction.id.desc())
        .all()
    )


@router.get("/summary", response_model=schemas.CashSummary)
def summary(
    start: Optional[date_type] = None,
    end: Optional[date_type] = None,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    base = _scoped(db, tenant.id, start, end)
    entradas = (
        base.filter(models.Transaction.type == "entrada")
        .with_entities(func.coalesce(func.sum(models.Transaction.amount), 0.0))
        .scalar()
    )
    saidas = (
        _scoped(db, tenant.id, start, end)
        .filter(models.Transaction.type == "saida")
        .with_entities(func.coalesce(func.sum(models.Transaction.amount), 0.0))
        .scalar()
    )
    total = _scoped(db, tenant.id, start, end).count()
    return schemas.CashSummary(
        entradas=float(entradas),
        saidas=float(saidas),
        saldo=float(entradas) - float(saidas),
        total_lancamentos=total,
    )


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(
    payload: schemas.TransactionCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if payload.type not in {"entrada", "saida"}:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'entrada' ou 'saida'.")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero.")
    tx = models.Transaction(tenant_id=tenant.id, **payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == tx_id, models.Transaction.tenant_id == tenant.id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado.")
    db.delete(tx)
    db.commit()
