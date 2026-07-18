"""Modelos ORM (SQLAlchemy) — SaaS multi-barbearia."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship

from database import Base


class Tenant(Base):
    """Uma barbearia assinante do serviço (tenant)."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)  # p/ link público
    address = Column(String, default="")
    whatsapp = Column(String, default="")
    logo_url = Column(Text, default="")  # logo/foto da barbearia (data URL redimensionada)
    # Antecedência mínima (horas) para o cliente cancelar sozinho pelo link.
    min_cancel_hours = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Assinatura
    plan = Column(String, default="")          # mensal | anual | ""
    # trial | active | overdue | canceled
    subscription_status = Column(String, default="trial")
    trial_ends_at = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    asaas_customer_id = Column(String, default="")
    asaas_subscription_id = Column(String, default="")
    # Appmax (gateway alternativo)
    appmax_customer_id = Column(String, default="")
    appmax_order_id = Column(String, default="")

    users = relationship("User", back_populates="tenant")


class User(Base):
    """Usuário dono/operador de uma barbearia."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="owner")  # owner | barber
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, default=30)
    active = Column(Boolean, default=True)


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="", index=True)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="client")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    phone = Column(String, default="")
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service_name = Column(String, nullable=False)
    price = Column(Float, default=0.0)
    barber_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    barber_name = Column(String, default="")
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String, default="pendente", index=True)
    source = Column(String, default="admin")  # web | admin
    # avista = pago no ato | assinatura = usa plano de corte do cliente
    payment_type = Column(String, default="avista")
    client_subscription_id = Column(Integer, ForeignKey("client_subscriptions.id"), nullable=True)
    notes = Column(String, default="")
    # Token aleatório para o cliente cancelar pelo link público (sem login).
    cancel_token = Column(String, default="", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="appointments")


class PushToken(Base):
    """Token de dispositivo (FCM) para notificação push."""

    __tablename__ = "push_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    is_admin = Column(Boolean, default=False)  # token do dono do SaaS (recebe avisos de venda)
    platform = Column(String, default="android")
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # entrada | saida
    amount = Column(Float, nullable=False)
    description = Column(String, default="")
    category = Column(String, default="")
    date = Column(Date, nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SubscriptionPlan(Base):
    """Plano de assinatura de corte que a barbearia oferece aos clientes dela."""

    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)  # valor mensal do plano
    cuts_per_month = Column(Integer, default=0)  # 0 = ilimitado
    allowed_weekdays = Column(String, default="")  # ex: "0,1,2" (0=segunda)
    allowed_time_start = Column(Time, nullable=True)
    allowed_time_end = Column(Time, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClientSubscription(Base):
    """Assinatura de corte contratada por um cliente da barbearia."""

    __tablename__ = "client_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    plan_name = Column(String, default="")
    status = Column(String, default="ativa")  # ativa | cancelada
    period_start = Column(Date, nullable=True)  # início do ciclo mensal atual
    cuts_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    """Produto/material da loja e do estoque."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    price = Column(Float, default=0.0)  # preço de venda
    cost = Column(Float, default=0.0)  # custo de compra
    stock = Column(Integer, default=0)
    sellable_online = Column(Boolean, default=True)  # aparece na loja virtual
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockMovement(Base):
    """Movimentação de estoque (entrada/saída de material)."""

    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String, nullable=False)  # entrada | saida
    qty = Column(Integer, nullable=False)
    note = Column(String, default="")
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    """Pedido feito na loja virtual."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    customer_name = Column(String, nullable=False)
    phone = Column(String, default="")
    total = Column(Float, default=0.0)
    status = Column(String, default="novo")  # novo | entregue | cancelado
    source = Column(String, default="web")
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String, default="")
    qty = Column(Integer, default=1)
    price = Column(Float, default=0.0)


class BusinessHour(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)  # 0..6
    is_open = Column(Boolean, default=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    slot_minutes = Column(Integer, default=30)


class BarberHour(Base):
    """Horário de trabalho individual de um barbeiro (sobrepõe o da barbearia)."""

    __tablename__ = "barber_hours"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    barber_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)  # 0..6
    is_open = Column(Boolean, default=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
