"""Endpoints públicos do site de agendamento (por slug da barbearia)."""
import base64
from datetime import date as date_type
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

import email_send
import models
import schemas
from booking import compute_availability, create_appointment_core
from database import get_db
from hardening import rate_limit
from security import subscription_active
from store import create_order_core


def _owner_email(db: Session, tenant_id: int) -> str:
    u = (
        db.query(models.User)
        .filter(models.User.tenant_id == tenant_id, models.User.role == "owner")
        .order_by(models.User.id)
        .first()
    )
    return u.email if u else ""


def _fmt_date(d) -> str:
    try:
        return d.strftime("%d/%m/%Y")
    except Exception:  # noqa: BLE001
        return str(d)


def _fmt_time(t) -> str:
    try:
        return t.strftime("%H:%M")
    except Exception:  # noqa: BLE001
        return str(t)[:5]

router = APIRouter(prefix="/public", tags=["public"])


def _get_tenant(db: Session, slug: str) -> models.Tenant:
    tenant = db.query(models.Tenant).filter(models.Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada.")
    if not subscription_active(tenant):
        raise HTTPException(
            status_code=403,
            detail="Esta barbearia está temporariamente indisponível para agendamento online.",
        )
    return tenant


@router.get("/{slug}/info")
def public_info(slug: str, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    return {
        "nome": tenant.name,
        "endereco": tenant.address,
        "whatsapp": tenant.whatsapp,
        "whatsapp_number": "".join(filter(str.isdigit, tenant.whatsapp or "")),
        "slug": tenant.slug,
        "logo_url": tenant.logo_url or "",
    }


@router.get("/{slug}/logo.png")
def public_logo(slug: str, db: Session = Depends(get_db)):
    """Serve a logo da barbearia como imagem real (URL http), para prévia de
    link (og:image) e favicon do site de agendamento. Sem logo -> imagem padrão."""
    tenant = db.query(models.Tenant).filter(models.Tenant.slug == slug).first()
    logo = (tenant.logo_url if tenant else "") or ""
    if logo.startswith("data:image/"):
        try:
            header, b64 = logo.split(",", 1)
            mime = header.split(";")[0].split(":", 1)[1] or "image/png"
            data = base64.b64decode(b64)
            return Response(
                content=data,
                media_type=mime,
                headers={"Cache-Control": "public, max-age=3600"},
            )
        except Exception:  # noqa: BLE001
            pass
    return RedirectResponse("/og-image.png")


@router.get("/{slug}/services", response_model=List[schemas.ServiceOut])
def public_services(slug: str, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    return (
        db.query(models.Service)
        .filter(models.Service.tenant_id == tenant.id, models.Service.active.is_(True))
        .order_by(models.Service.name)
        .all()
    )


@router.get("/{slug}/barbers")
def public_barbers(slug: str, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    barbers = (
        db.query(models.User)
        .filter(
            models.User.tenant_id == tenant.id,
            models.User.role == "barber",
            models.User.active.is_(True),
        )
        .order_by(models.User.name)
        .all()
    )
    return [{"id": b.id, "name": b.name} for b in barbers]


@router.get("/{slug}/availability", response_model=schemas.AvailabilityOut)
def public_availability(
    slug: str,
    date: date_type = Query(...),
    service_id: Optional[int] = Query(None),
    barber_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    tenant = _get_tenant(db, slug)
    slots = compute_availability(db, tenant.id, date, service_id, barber_id)
    return schemas.AvailabilityOut(date=date, slots=slots)


@router.post(
    "/{slug}/appointments",
    response_model=schemas.AppointmentOut,
    status_code=201,
    dependencies=[Depends(rate_limit("public_book", 20, 3600))],  # anti-spam de bots
)
def public_create_appointment(
    slug: str,
    payload: schemas.AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    tenant = _get_tenant(db, slug)
    # Agendamento pelo site é sempre à vista (assinatura é validada no balcão).
    appt = create_appointment_core(
        db,
        tenant.id,
        payload.customer_name,
        payload.phone,
        payload.service_id,
        payload.service_name,
        payload.date,
        payload.time,
        source="web",
        notes=payload.notes,
        payment_type="avista",
        barber_id=payload.barber_id,
    )
    # Avisa o dono da barbearia por e-mail (em segundo plano).
    owner = _owner_email(db, tenant.id)
    if owner:
        background_tasks.add_task(
            email_send.send_shop_new_booking,
            owner, tenant.name, appt.customer_name, appt.service_name,
            _fmt_date(appt.date), _fmt_time(appt.time), appt.barber_name or "",
        )
    return appt


def _appt_by_token(db: Session, slug: str, token: str):
    """Localiza (tenant, agendamento) pelo token público de cancelamento."""
    tenant = db.query(models.Tenant).filter(models.Tenant.slug == slug).first()
    if not tenant or not token:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    appt = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.tenant_id == tenant.id,
            models.Appointment.cancel_token == token,
        )
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return tenant, appt


def _cancel_deadline(tenant, appt):
    """Momento-limite para o cliente poder cancelar sozinho."""
    appt_dt = datetime.combine(appt.date, appt.time)
    hours = tenant.min_cancel_hours if tenant.min_cancel_hours is not None else 3
    return appt_dt - timedelta(hours=hours)


@router.get("/{slug}/appointment/{token}")
def public_get_appointment(slug: str, token: str, db: Session = Depends(get_db)):
    """Detalhes do agendamento para a página de cancelamento (via token)."""
    tenant, appt = _appt_by_token(db, slug, token)
    now = datetime.now()
    open_status = appt.status in ("pendente", "confirmado")
    can_cancel = open_status and now < _cancel_deadline(tenant, appt)
    return {
        "shop": tenant.name,
        "whatsapp_number": "".join(filter(str.isdigit, tenant.whatsapp or "")),
        "customer_name": appt.customer_name,
        "service_name": appt.service_name,
        "barber_name": appt.barber_name or "",
        "date": _fmt_date(appt.date),
        "time": _fmt_time(appt.time),
        "status": appt.status,
        "can_cancel": can_cancel,
        "min_cancel_hours": tenant.min_cancel_hours,
        "already_canceled": appt.status == "cancelado",
    }


@router.post(
    "/{slug}/appointment/{token}/cancel",
    dependencies=[Depends(rate_limit("public_cancel", 30, 3600))],
)
def public_cancel_appointment(
    slug: str, token: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """Cliente cancela o próprio agendamento (respeitando a antecedência mínima)."""
    tenant, appt = _appt_by_token(db, slug, token)
    if appt.status == "cancelado":
        return {"ok": True, "status": "cancelado"}
    if appt.status not in ("pendente", "confirmado"):
        raise HTTPException(status_code=400, detail="Este agendamento não pode ser cancelado.")
    if datetime.now() >= _cancel_deadline(tenant, appt):
        raise HTTPException(
            status_code=400,
            detail=(
                f"O cancelamento pelo link só é permitido até {tenant.min_cancel_hours}h antes. "
                "Fale com a barbearia no WhatsApp."
            ),
        )
    appt.status = "cancelado"
    db.commit()
    owner = _owner_email(db, tenant.id)
    if owner:
        background_tasks.add_task(
            email_send.send_shop_cancellation,
            owner, tenant.name, appt.customer_name, appt.service_name,
            _fmt_date(appt.date), _fmt_time(appt.time),
        )
    return {"ok": True, "status": "cancelado"}


@router.get("/{slug}/products", response_model=List[schemas.ProductOut])
def public_products(slug: str, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    return (
        db.query(models.Product)
        .filter(
            models.Product.tenant_id == tenant.id,
            models.Product.active.is_(True),
            models.Product.sellable_online.is_(True),
        )
        .order_by(models.Product.name)
        .all()
    )


@router.post(
    "/{slug}/orders",
    response_model=schemas.OrderOut,
    status_code=201,
    dependencies=[Depends(rate_limit("public_order", 20, 3600))],
)
def public_create_order(slug: str, payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    tenant = _get_tenant(db, slug)
    order = create_order_core(db, tenant.id, payload.customer_name, payload.phone, payload.items)
    items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all()
    data = schemas.OrderOut.model_validate(order)
    data.items = [schemas.OrderItemOut.model_validate(i) for i in items]
    return data
