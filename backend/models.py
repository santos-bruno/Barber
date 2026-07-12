"""Modelos ORM (SQLAlchemy) da aplicação."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from database import Base


class Service(Base):
    """Serviço oferecido pela barbearia (corte, barba, etc.)."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, default=30)


class Appointment(Base):
    """Agendamento feito por um cliente."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    date = Column(String, nullable=False)  # AAAA-MM-DD
    time = Column(String, nullable=False)  # HH:MM
    phone = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
