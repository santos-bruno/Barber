"""Schemas Pydantic para validação de entrada/saída da API."""
from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- Services ----------
class ServiceBase(BaseModel):
    name: str
    description: str = ""
    price: float
    duration_minutes: int = 30
    active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceOut(ServiceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Clients ----------
class ClientBase(BaseModel):
    name: str
    phone: str = ""
    notes: str = ""


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Appointments ----------
class AppointmentBase(BaseModel):
    customer_name: str
    phone: str = ""
    service_id: Optional[int] = None
    service_name: str
    date: date_type
    time: time_type
    notes: str = ""


class AppointmentCreate(AppointmentBase):
    source: str = "admin"


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[date_type] = None
    time: Optional[time_type] = None


class AppointmentOut(AppointmentBase):
    id: int
    client_id: Optional[int] = None
    price: float
    duration_minutes: int
    status: str
    source: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Cash flow ----------
class TransactionBase(BaseModel):
    type: str  # entrada | saida
    amount: float
    description: str = ""
    category: str = ""
    date: date_type


class TransactionCreate(TransactionBase):
    appointment_id: Optional[int] = None


class TransactionOut(TransactionBase):
    id: int
    appointment_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CashSummary(BaseModel):
    entradas: float
    saidas: float
    saldo: float
    total_lancamentos: int


# ---------- Business hours ----------
class BusinessHourBase(BaseModel):
    weekday: int  # 0=segunda ... 6=domingo
    is_open: bool = True
    open_time: Optional[time_type] = None
    close_time: Optional[time_type] = None
    slot_minutes: int = 30


class BusinessHourOut(BusinessHourBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Availability ----------
class AvailabilityOut(BaseModel):
    date: date_type
    slots: list[str]  # ["09:00", "09:30", ...]
