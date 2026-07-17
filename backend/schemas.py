"""Schemas Pydantic para validação de entrada/saída da API."""
from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth / Tenant ----------
class RegisterInput(BaseModel):
    barbershop_name: str = Field(min_length=1, max_length=120)
    owner_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    whatsapp: str = Field(default="", max_length=30)
    address: str = Field(default="", max_length=200)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordInput(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ResetPasswordInput(BaseModel):
    new_password: Optional[str] = None


class TenantOut(BaseModel):
    id: int
    name: str
    slug: str
    address: str
    whatsapp: str
    logo_url: str = ""
    min_cancel_hours: int = 3
    plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=200)
    # data URL da logo (imagem redimensionada no navegador); ~até 600 KB
    logo_url: Optional[str] = Field(default=None, max_length=600000)
    min_cancel_hours: Optional[int] = Field(default=None, ge=0, le=168)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class AuthOut(BaseModel):
    token: str
    user: UserOut
    tenant: TenantOut


# ---------- Billing ----------
class SubscribeInput(BaseModel):
    plan: str  # mensal | anual
    cpf_cnpj: str
    billing_type: str = "CREDIT_CARD"  # CREDIT_CARD | PIX | BOLETO | UNDEFINED


class CheckoutOut(BaseModel):
    checkout_url: str
    subscription_id: str
    status: str


class AppmaxCheckoutInput(BaseModel):
    plan: str  # mensal | anual
    holder_name: str
    cpf_cnpj: str
    card_number: str
    card_cvv: str
    card_exp_month: str
    card_exp_year: str


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
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=30)
    notes: str = Field(default="", max_length=1000)


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Appointments ----------
class AppointmentBase(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=30)
    service_id: Optional[int] = None
    service_name: str = Field(min_length=1, max_length=120)
    date: date_type
    time: time_type
    notes: str = Field(default="", max_length=500)
    payment_type: str = "avista"  # avista | assinatura
    barber_id: Optional[int] = None


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
    barber_name: str = ""
    cancel_token: str = ""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Staff (barbeiros) ----------
class StaffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class StaffOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    active: bool
    model_config = ConfigDict(from_attributes=True)


# ---------- Subscription plans (planos de corte da barbearia) ----------
class SubscriptionPlanBase(BaseModel):
    name: str
    price: float
    cuts_per_month: int = 0  # 0 = ilimitado
    allowed_weekdays: str = ""  # ex: "0,1,2"
    allowed_time_start: Optional[time_type] = None
    allowed_time_end: Optional[time_type] = None
    active: bool = True


class SubscriptionPlanOut(SubscriptionPlanBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ClientSubscriptionCreate(BaseModel):
    client_id: int
    plan_id: int


class ClientSubscriptionOut(BaseModel):
    id: int
    client_id: int
    plan_id: int
    plan_name: str
    status: str
    period_start: Optional[date_type] = None
    cuts_used: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Products / stock ----------
class ProductBase(BaseModel):
    name: str
    description: str = ""
    price: float = 0.0
    cost: float = 0.0
    stock: int = 0
    sellable_online: bool = True
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StockMovementCreate(BaseModel):
    type: str  # entrada | saida
    qty: int
    note: str = ""
    affects_cash: bool = True  # gera lançamento no caixa


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    type: str
    qty: int
    note: str
    date: date_type
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Orders (loja virtual) ----------
class OrderItemIn(BaseModel):
    product_id: int
    qty: int = 1


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=30)
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)


class OrderItemOut(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    qty: int
    price: float
    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    customer_name: str
    phone: str
    total: float
    status: str
    source: str
    created_at: datetime
    items: list[OrderItemOut] = []
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


class BarberHourBase(BaseModel):
    weekday: int
    is_open: bool = True
    open_time: Optional[time_type] = None
    close_time: Optional[time_type] = None


class BarberHourOut(BarberHourBase):
    id: int
    barber_id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Availability ----------
class AvailabilityOut(BaseModel):
    date: date_type
    slots: list[str]  # ["09:00", "09:30", ...]
