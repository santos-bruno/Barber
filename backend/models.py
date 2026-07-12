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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Assinatura
    plan = Column(String, default="")          # mensal | anual | ""
    # trial | active | overdue | canceled
    subscription_status = Column(String, default="trial")
    trial_ends_at = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    asaas_customer_id = Column(String, default="")
    asaas_subscription_id = Column(String, default="")

    users = relationship("User", back_populates="tenant")


class User(Base):
    """Usuário dono/operador de uma barbearia."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="owner")  # owner | superadmin
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
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String, default="pendente", index=True)
    source = Column(String, default="admin")  # web | admin
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="appointments")


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


class BusinessHour(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)  # 0..6
    is_open = Column(Boolean, default=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    slot_minutes = Column(Integer, default=30)
