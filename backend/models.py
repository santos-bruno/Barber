"""Modelos ORM (SQLAlchemy) da aplicação."""
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


class Service(Base):
    """Serviço oferecido pela barbearia (corte, barba, etc.)."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, default=30)
    active = Column(Boolean, default=True)


class Client(Base):
    """Cliente cadastrado (fluxo de clientes / contatos)."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="", index=True)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="client")


class Appointment(Base):
    """Agendamento (feito pelo admin ou pelo site do cliente)."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    phone = Column(String, default="")
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service_name = Column(String, nullable=False)
    price = Column(Float, default=0.0)
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    # pendente | confirmado | concluido | cancelado
    status = Column(String, default="pendente", index=True)
    # web | admin
    source = Column(String, default="admin")
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="appointments")


class Transaction(Base):
    """Lançamento de fluxo de caixa (entrada ou saída)."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    # entrada | saida
    type = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, default="")
    category = Column(String, default="")
    date = Column(Date, nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BusinessHour(Base):
    """Horário de funcionamento por dia da semana (0=segunda ... 6=domingo)."""

    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    weekday = Column(Integer, nullable=False, unique=True)  # 0..6
    is_open = Column(Boolean, default=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    slot_minutes = Column(Integer, default=30)
