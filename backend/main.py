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
from routers import (
    appointments,
    auth,
    billing,
    cashflow,
    clients,
    hours,
    public,
    services,
    superadmin,
)

Base.metadata.create_all(bind=engine)

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
app.include_router(public.router)
app.include_router(services.router)
app.include_router(clients.router)
app.include_router(appointments.router)
app.include_router(cashflow.router)
app.include_router(hours.router)
app.include_router(superadmin.router)


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
