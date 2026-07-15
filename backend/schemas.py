"""Schemas Pydantic para validação de entrada/saída da API."""
from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------- Auth / Tenant ----------
class RegisterInput(BaseModel):
    barbershop_name: str
    owner_name: str
    email: EmailStr
    password: str
    whatsapp: str = ""
    address: str = ""


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordInput(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordInput(BaseModel):
    new_password: Optional[str] = None


class TenantOut(BaseModel):
    id: int
    name: str
    slug: str
    address: str
    whatsapp: str
    plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


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
    card_token: str  # token gerado no navegador pelo Appmax JS
    holder_name: str
    cpf_cnpj: str


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
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Staff (barbeiros) ----------
class StaffCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


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
    customer_name: str
    phone: str = ""
    items: list[OrderItemIn]


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
