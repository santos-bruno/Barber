"""
Conta de demonstração (opcional).

Ativada quando a variável de ambiente SEED_DEMO=true. Cria uma barbearia
"Barbearia Demo" já com serviços, clientes, agendamentos e caixa, para
login de teste imediato:

    e-mail: demo@agendabarber.com
    senha:  demo123

É idempotente: só cria se ainda não existir.
"""
import os
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

import models
from database import SessionLocal
from security import hash_password
from seeds import seed_tenant_defaults

DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@agendabarber.com")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")


def _refresh_demo(db: Session, tenant_id: int) -> None:
    """Mantém a demo 'viva': re-data os agendamentos e o caixa para HOJE.

    Sem isso, a agenda da demonstração fica presa na data do deploy e aparece
    vazia quando um cliente em potencial abre o link — demo vazia não vende.
    """
    hoje = date.today()
    appts = (
        db.query(models.Appointment)
        .filter(models.Appointment.tenant_id == tenant_id)
        .all()
    )
    if appts and all(a.date < hoje for a in appts):
        for a in appts:
            a.date = hoje
        for t in (
            db.query(models.Transaction)
            .filter(models.Transaction.tenant_id == tenant_id)
            .all()
        ):
            t.date = hoje
        db.commit()


def seed_demo() -> None:
    if os.getenv("SEED_DEMO", "").lower() not in ("1", "true", "yes"):
        return

    db: Session = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
        if existing:
            _refresh_demo(db, existing.tenant_id)
            return  # já existe (só re-data)

        tenant = models.Tenant(
            name="Barbearia Demo",
            slug="demo",
            address="Rua Exemplo, 123 - Centro, Santarém - PA",
            whatsapp="93999990000",
            subscription_status="active",
            current_period_end=datetime.utcnow() + timedelta(days=3650),
            plan="anual",
        )
        db.add(tenant)
        db.flush()

        db.add(
            models.User(
                tenant_id=tenant.id,
                name="Dono Demo",
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                role="owner",
            )
        )
        # Barbeiro de exemplo (login: barbeiro@agendabarber.com / demo123)
        barber = models.User(
            tenant_id=tenant.id,
            name="Barbeiro Carlos",
            email="barbeiro@agendabarber.com",
            password_hash=hash_password(DEMO_PASSWORD),
            role="barber",
        )
        db.add(barber)
        seed_tenant_defaults(db, tenant.id)
        db.flush()

        # Clientes
        clientes = [
            ("João Silva", "5593999990001"),
            ("Pedro Alves", "5593988880002"),
            ("Carlos Mendes", "5593977770003"),
        ]
        client_objs = []
        for nome, tel in clientes:
            c = models.Client(tenant_id=tenant.id, name=nome, phone=tel)
            db.add(c)
            db.flush()
            client_objs.append(c)

        servicos = (
            db.query(models.Service).filter(models.Service.tenant_id == tenant.id).all()
        )
        serv = {s.name: s for s in servicos}
        hoje = date.today()

        def add_appt(cli, s, hh, mm, status, barber_obj=None):
            db.add(
                models.Appointment(
                    tenant_id=tenant.id,
                    client_id=cli.id,
                    customer_name=cli.name,
                    phone=cli.phone,
                    service_id=s.id,
                    service_name=s.name,
                    price=s.price,
                    barber_id=barber_obj.id if barber_obj else None,
                    barber_name=barber_obj.name if barber_obj else "",
                    date=hoje,
                    time=time(hh, mm),
                    duration_minutes=s.duration_minutes,
                    status=status,
                    source="web" if status == "confirmado" else "admin",
                )
            )

        corte = serv.get("Corte de Cabelo") or servicos[0]
        combo = serv.get("Corte + Barba") or servicos[0]
        barba = serv.get("Barba") or servicos[0]
        add_appt(client_objs[0], combo, 9, 0, "concluido", barber)
        add_appt(client_objs[1], corte, 10, 30, "confirmado", barber)
        add_appt(client_objs[2], barba, 14, 0, "pendente")

        # Produtos da loja
        for nome, desc, preco, custo, estoque in [
            ("Pomada Modeladora", "Fixação forte, efeito matte", 30.0, 12.0, 15),
            ("Óleo para Barba", "Hidrata e amacia", 25.0, 10.0, 10),
            ("Shampoo Barba & Cabelo", "Limpeza 2 em 1", 20.0, 8.0, 8),
        ]:
            db.add(models.Product(tenant_id=tenant.id, name=nome, description=desc,
                                  price=preco, cost=custo, stock=estoque, sellable_online=True))

        # Plano de assinatura de corte demo
        db.add(models.SubscriptionPlan(
            tenant_id=tenant.id, name="Corte Mensal", price=80.0, cuts_per_month=4,
            allowed_weekdays="0,1,2,3,4", allowed_time_start=time(9, 0), allowed_time_end=time(18, 0),
        ))

        # Caixa (entradas do dia + uma saída)
        db.add(models.Transaction(tenant_id=tenant.id, type="entrada", amount=combo.price,
                                  description=f"{combo.name} - João Silva", category="Serviço", date=hoje))
        db.add(models.Transaction(tenant_id=tenant.id, type="entrada", amount=corte.price,
                                  description=f"{corte.name} - Ana", category="Serviço", date=hoje))
        db.add(models.Transaction(tenant_id=tenant.id, type="saida", amount=25.0,
                                  description="Lâminas", category="Insumos", date=hoje))

        db.commit()
    finally:
        db.close()
