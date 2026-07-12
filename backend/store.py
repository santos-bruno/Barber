"""Lógica compartilhada de criação de pedidos da loja virtual."""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models


def create_order_core(db: Session, tenant_id: int, customer_name: str, phone: str, items):
    if not customer_name.strip():
        raise HTTPException(status_code=400, detail="Nome é obrigatório.")
    if not items:
        raise HTTPException(status_code=400, detail="Pedido sem itens.")

    order = models.Order(
        tenant_id=tenant_id, customer_name=customer_name.strip(), phone=phone,
        total=0.0, status="novo", source="web",
    )
    db.add(order)
    db.flush()

    total = 0.0
    for it in items:
        product = (
            db.query(models.Product)
            .filter(models.Product.id == it.product_id, models.Product.tenant_id == tenant_id)
            .first()
        )
        if not product or not product.active:
            raise HTTPException(status_code=404, detail="Produto indisponível.")
        qty = max(1, it.qty)
        if product.stock < qty:
            raise HTTPException(status_code=409, detail=f"Sem estoque de {product.name}.")
        product.stock -= qty
        total += product.price * qty
        db.add(models.OrderItem(
            order_id=order.id, product_id=product.id, product_name=product.name,
            qty=qty, price=product.price,
        ))
        db.add(models.StockMovement(
            tenant_id=tenant_id, product_id=product.id, type="saida", qty=qty,
            note="Venda loja virtual", date=date.today(),
        ))

    order.total = total
    # Venda entra no caixa.
    db.add(models.Transaction(
        tenant_id=tenant_id, type="entrada", amount=total,
        description=f"Pedido loja - {customer_name.strip()}", category="Produtos", date=date.today(),
    ))
    db.commit()
    db.refresh(order)
    return order
