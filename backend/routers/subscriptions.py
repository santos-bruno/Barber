"""Planos de assinatura de corte e assinaturas dos clientes (escopados)."""
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_active_subscription

router = APIRouter(tags=["assinatura-corte"])


# ---------- Planos de corte ----------
@router.get("/subscription-plans", response_model=List[schemas.SubscriptionPlanOut])
def list_plans(
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.SubscriptionPlan)
        .filter(models.SubscriptionPlan.tenant_id == tenant.id, models.SubscriptionPlan.active.is_(True))
        .order_by(models.SubscriptionPlan.name)
        .all()
    )


@router.post("/subscription-plans", response_model=schemas.SubscriptionPlanOut, status_code=201)
def create_plan(
    payload: schemas.SubscriptionPlanBase,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    plan = models.SubscriptionPlan(tenant_id=tenant.id, **payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/subscription-plans/{plan_id}", response_model=schemas.SubscriptionPlanOut)
def update_plan(
    plan_id: int,
    payload: schemas.SubscriptionPlanBase,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    plan = (
        db.query(models.SubscriptionPlan)
        .filter(models.SubscriptionPlan.id == plan_id, models.SubscriptionPlan.tenant_id == tenant.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")
    for k, v in payload.model_dump().items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/subscription-plans/{plan_id}", status_code=204)
def delete_plan(
    plan_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    plan = (
        db.query(models.SubscriptionPlan)
        .filter(models.SubscriptionPlan.id == plan_id, models.SubscriptionPlan.tenant_id == tenant.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")
    plan.active = False
    db.commit()


# ---------- Assinaturas dos clientes ----------
@router.get("/client-subscriptions", response_model=List[schemas.ClientSubscriptionOut])
def list_client_subs(
    client_id: int = None,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    q = db.query(models.ClientSubscription).filter(
        models.ClientSubscription.tenant_id == tenant.id,
        models.ClientSubscription.status == "ativa",
    )
    if client_id:
        q = q.filter(models.ClientSubscription.client_id == client_id)
    return q.order_by(models.ClientSubscription.id.desc()).all()


@router.post("/client-subscriptions", response_model=schemas.ClientSubscriptionOut, status_code=201)
def create_client_sub(
    payload: schemas.ClientSubscriptionCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    client = (
        db.query(models.Client)
        .filter(models.Client.id == payload.client_id, models.Client.tenant_id == tenant.id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    plan = (
        db.query(models.SubscriptionPlan)
        .filter(models.SubscriptionPlan.id == payload.plan_id, models.SubscriptionPlan.tenant_id == tenant.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")

    # Cancela assinatura anterior ativa do mesmo cliente.
    db.query(models.ClientSubscription).filter(
        models.ClientSubscription.tenant_id == tenant.id,
        models.ClientSubscription.client_id == client.id,
        models.ClientSubscription.status == "ativa",
    ).update({"status": "cancelada"})

    sub = models.ClientSubscription(
        tenant_id=tenant.id,
        client_id=client.id,
        plan_id=plan.id,
        plan_name=plan.name,
        status="ativa",
        period_start=date.today().replace(day=1),
        cuts_used=0,
    )
    db.add(sub)

    # A mensalidade do plano entra no caixa.
    db.add(
        models.Transaction(
            tenant_id=tenant.id,
            type="entrada",
            amount=plan.price,
            description=f"Assinatura {plan.name} - {client.name}",
            category="Assinatura",
            date=date.today(),
        )
    )
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/client-subscriptions/{sub_id}", status_code=204)
def cancel_client_sub(
    sub_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(models.ClientSubscription)
        .filter(models.ClientSubscription.id == sub_id, models.ClientSubscription.tenant_id == tenant.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")
    sub.status = "cancelada"
    db.commit()
