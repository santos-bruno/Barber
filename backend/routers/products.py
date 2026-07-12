"""Produtos, estoque e pedidos da loja (escopados por barbearia)."""
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_active_subscription

router = APIRouter(tags=["loja"])


# ---------- Produtos ----------
@router.get("/products", response_model=List[schemas.ProductOut])
def list_products(
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Product)
        .filter(models.Product.tenant_id == tenant.id, models.Product.active.is_(True))
        .order_by(models.Product.name)
        .all()
    )


@router.post("/products", response_model=schemas.ProductOut, status_code=201)
def create_product(
    payload: schemas.ProductCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    product = models.Product(tenant_id=tenant.id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    payload: schemas.ProductCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    product = _get_product(db, tenant.id, product_id)
    for k, v in payload.model_dump().items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    product = _get_product(db, tenant.id, product_id)
    product.active = False
    db.commit()


def _get_product(db, tenant_id, product_id):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id, models.Product.tenant_id == tenant_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return product


# ---------- Estoque ----------
@router.post("/products/{product_id}/stock", response_model=schemas.ProductOut)
def move_stock(
    product_id: int,
    payload: schemas.StockMovementCreate,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if payload.type not in {"entrada", "saida"}:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'entrada' ou 'saida'.")
    if payload.qty <= 0:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero.")

    product = _get_product(db, tenant.id, product_id)
    today = date.today()

    if payload.type == "entrada":
        product.stock += payload.qty
        cash = ("saida", product.cost * payload.qty, f"Compra: {product.name} x{payload.qty}")
    else:
        product.stock -= payload.qty
        cash = ("entrada", product.price * payload.qty, f"Venda: {product.name} x{payload.qty}")

    db.add(models.StockMovement(
        tenant_id=tenant.id, product_id=product.id, type=payload.type,
        qty=payload.qty, note=payload.note, date=today,
    ))

    if payload.affects_cash and cash[1] > 0:
        db.add(models.Transaction(
            tenant_id=tenant.id, type=cash[0], amount=cash[1],
            description=cash[2], category="Produtos", date=today,
        ))

    db.commit()
    db.refresh(product)
    return product


@router.get("/products/{product_id}/movements", response_model=List[schemas.StockMovementOut])
def list_movements(
    product_id: int,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    _get_product(db, tenant.id, product_id)
    return (
        db.query(models.StockMovement)
        .filter(models.StockMovement.tenant_id == tenant.id, models.StockMovement.product_id == product_id)
        .order_by(models.StockMovement.id.desc())
        .all()
    )


# ---------- Pedidos (loja virtual) ----------
@router.get("/orders", response_model=List[schemas.OrderOut])
def list_orders(
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(models.Order)
        .filter(models.Order.tenant_id == tenant.id)
        .order_by(models.Order.id.desc())
        .all()
    )
    result = []
    for o in orders:
        items = db.query(models.OrderItem).filter(models.OrderItem.order_id == o.id).all()
        data = schemas.OrderOut.model_validate(o)
        data.items = [schemas.OrderItemOut.model_validate(i) for i in items]
        result.append(data)
    return result


@router.patch("/orders/{order_id}", response_model=schemas.OrderOut)
def update_order(
    order_id: int,
    status: str,
    tenant: models.Tenant = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    if status not in {"novo", "entregue", "cancelado"}:
        raise HTTPException(status_code=400, detail="Status inválido.")
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.tenant_id == tenant.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    order.status = status
    db.commit()
    db.refresh(order)
    items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all()
    data = schemas.OrderOut.model_validate(order)
    data.items = [schemas.OrderItemOut.model_validate(i) for i in items]
    return data
