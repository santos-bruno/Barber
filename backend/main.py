"""
SaaS de agendamento para barbearias — API + páginas web.

- API multi-tenant com autenticação (JWT) e assinaturas (Asaas)
- Página de vendas em "/"
- Site de agendamento por barbearia em "/agendar/{slug}"
- Docs da API em /docs
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from database import Base, engine
from demo import seed_demo
from migrate import run_migrations
from routers import (
    appmax_billing,
    appointments,
    auth,
    billing,
    cashflow,
    clients,
    hours,
    products,
    public,
    services,
    staff,
    subscriptions,
    superadmin,
)

Base.metadata.create_all(bind=engine)
run_migrations()  # adiciona colunas novas em bancos já existentes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

app = FastAPI(
    title="SaaS Agendamento - Barbearias",
    description="Sistema de gestão e agendamento para barbearias (multi-tenant).",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(appmax_billing.router)
app.include_router(public.router)
app.include_router(services.router)
app.include_router(clients.router)
app.include_router(appointments.router)
app.include_router(cashflow.router)
app.include_router(hours.router)
app.include_router(subscriptions.router)
app.include_router(products.router)
app.include_router(staff.router)
app.include_router(superadmin.router)


@app.on_event("startup")
def on_startup() -> None:
    seed_demo()


@app.get("/favicon.ico")
def favicon():
    path = os.path.join(WEB_DIR, "favicon.png")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({}, status_code=404)


@app.get("/health")
def health():
    return {"status": "ok"}


def _serve(filename: str):
    path = os.path.join(WEB_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"status": "ok"})


@app.get("/")
def landing():
    """Página de vendas do SaaS."""
    return _serve("landing.html")


@app.get("/agendar/{slug}")
def booking(slug: str):
    """Site de agendamento de uma barbearia (o JS lê o slug da URL)."""
    return _serve("index.html")


@app.get("/loja/{slug}")
def store(slug: str):
    """Loja virtual de uma barbearia (o JS lê o slug da URL)."""
    return _serve("store.html")


@app.get("/painel")
def owner_panel():
    """Painel do dono do SaaS (protegido pela chave de administrador)."""
    return _serve("painel.html")


@app.get("/gerente")
def manager_web():
    """Versão web para a barbearia gerenciar (agenda, caixa, barbeiros...)."""
    return _serve("gerente.html")


@app.get("/assinar")
def subscribe_page():
    """Checkout de assinatura via Appmax (cartão recorrente ou link de pagamento)."""
    return _serve("assinar.html")


@app.get("/guia")
def guide_page():
    """Guia de primeiros passos (versão web)."""
    return _serve("guia.html")


@app.get("/guia.pdf")
def guide_pdf():
    """Guia de primeiros passos em PDF (download)."""
    path = os.path.join(WEB_DIR, "guia-agenda-barber.pdf")
    if os.path.exists(path):
        return FileResponse(
            path,
            media_type="application/pdf",
            filename="Guia-Agenda-Barber.pdf",
        )
    return JSONResponse({"detail": "Guia não encontrado."}, status_code=404)
