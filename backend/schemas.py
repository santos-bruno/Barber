"""Schemas Pydantic para validação de entrada/saída da API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Services ----------
class ServiceBase(BaseModel):
    name: str
    description: str = ""
    price: float
    duration_minutes: int = 30


class ServiceCreate(ServiceBase):
    pass


class ServiceOut(ServiceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Appointments ----------
class AppointmentBase(BaseModel):
    customer_name: str
    service_name: str
    date: str  # AAAA-MM-DD
    time: str  # HH:MM
    phone: str = ""


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentOut(AppointmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
