"""Endpoints de fluxo de caixa."""
from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


@router.get("", response_model=List[schemas.TransactionOut])
def list_transactions(
    start: Optional[date_type] = None,
    end: Optional[date_type] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)
    if start:
        query = query.filter(models.Transaction.date >= start)
    if end:
        query = query.filter(models.Transaction.date <= end)
    return query.order_by(models.Transaction.date.desc(), models.Transaction.id.desc()).all()


@router.get("/summary", response_model=schemas.CashSummary)
def summary(
    start: Optional[date_type] = None,
    end: Optional[date_type] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)
    if start:
        query = query.filter(models.Transaction.date >= start)
    if end:
        query = query.filter(models.Transaction.date <= end)

    entradas = (
        query.filter(models.Transaction.type == "entrada")
        .with_entities(func.coalesce(func.sum(models.Transaction.amount), 0.0))
        .scalar()
    )
    saidas = (
        query.filter(models.Transaction.type == "saida")
        .with_entities(func.coalesce(func.sum(models.Transaction.amount), 0.0))
        .scalar()
    )
    total = query.count()
    return schemas.CashSummary(
        entradas=float(entradas),
        saidas=float(saidas),
        saldo=float(entradas) - float(saidas),
        total_lancamentos=total,
    )


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    if payload.type not in {"entrada", "saida"}:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'entrada' ou 'saida'.")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero.")
    tx = models.Transaction(**payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    tx = db.get(models.Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado.")
    db.delete(tx)
    db.commit()
