"""
SaaS de agendamento para barbearias — API + páginas web.

- API multi-tenant com autenticação (JWT) e assinaturas (Asaas)
- Página de vendas em "/"
- Site de agendamento por barbearia em "/agendar/{slug}"
- Docs da API em /docs
"""
import html as _html
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import models
from database import Base, SessionLocal, engine
from demo import seed_demo
from hardening import SecurityHeadersMiddleware
from migrate import run_migrations
from routers import (
    appmax_billing,
    appointments,
    auth,
    billing,
    cashflow,
    clients,
    hours,
    notifications,
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


def _cors_origins() -> list[str]:
    """Origens permitidas para chamadas de navegador (CORS).

    Defina CORS_ORIGINS no ambiente (lista separada por vírgula) para adicionar
    domínios próprios. O app mobile nativo não envia Origin, então não é afetado.
    """
    raw = os.getenv("CORS_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    app_url = os.getenv("APP_BASE_URL", "https://agenda-barber-o0to.onrender.com").rstrip("/")
    # Produção + origens comuns de desenvolvimento (Expo / web local).
    return [
        app_url,
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
    ]


# Barra corpos grandes e injeta cabeçalhos de segurança (HSTS, CSP, etc.).
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,  # auth via header Bearer (JWT), não cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key"],
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
app.include_router(notifications.router)


@app.on_event("startup")
def on_startup() -> None:
    seed_demo()


@app.get("/favicon.ico")
def favicon():
    path = os.path.join(WEB_DIR, "favicon.png")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({}, status_code=404)


@app.get("/favicon.png")
def favicon_png():
    return _serve("favicon.png")


@app.get("/og-image.png")
def og_image():
    """Imagem de prévia ao compartilhar o link (Open Graph)."""
    return _serve("og-image.png")


@app.get("/health")
def health():
    return {"status": "ok"}


APP_BASE_URL = os.getenv("APP_BASE_URL", "https://agenda-barber-o0to.onrender.com").rstrip("/")


def _serve(filename: str):
    path = os.path.join(WEB_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"status": "ok"})


def _og_meta(title: str, desc: str, url: str, image: str) -> str:
    """Bloco de meta tags (Open Graph + Twitter) para prévia ao compartilhar."""
    e = _html.escape
    t, d, u, i = e(title), e(desc), e(url), e(image)
    return (
        f'<meta property="og:type" content="website">'
        f'<meta property="og:site_name" content="Agenda Barber">'
        f'<meta property="og:title" content="{t}">'
        f'<meta property="og:description" content="{d}">'
        f'<meta property="og:url" content="{u}">'
        f'<meta property="og:image" content="{i}">'
        f'<meta property="og:locale" content="pt_BR">'
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{t}">'
        f'<meta name="twitter:description" content="{d}">'
        f'<meta name="twitter:image" content="{i}">'
    )


def _serve_public(slug: str, filename: str, kind: str):
    """Serve a página pública (agendamento/loja) já com SEO por barbearia:
    título, descrição e imagem (logo) para a prévia do link ao compartilhar."""
    path = os.path.join(WEB_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse({"status": "ok"})
    try:
        page = open(path, encoding="utf-8").read()
    except OSError:
        return _serve(filename)

    db = SessionLocal()
    try:
        tenant = db.query(models.Tenant).filter(models.Tenant.slug == slug).first()
    finally:
        db.close()

    if tenant:
        name = tenant.name
        if kind == "loja":
            title = f"Loja da {name}"
            desc = "Peça seus produtos online. " + (tenant.address or "")
            url = f"{APP_BASE_URL}/loja/{slug}"
        else:
            title = f"Agende seu horário na {name}"
            desc = (
                "Escolha o serviço e o horário e agende online, sem precisar ligar. "
                + (tenant.address or "")
            ).strip()
            url = f"{APP_BASE_URL}/agendar/{slug}"
        image = (
            f"{APP_BASE_URL}/public/{slug}/logo.png"
            if tenant.logo_url
            else f"{APP_BASE_URL}/og-image.png"
        )
        favicon = f"{APP_BASE_URL}/public/{slug}/logo.png" if tenant.logo_url else "/favicon.png"
        inject = (
            _og_meta(title, desc, url, image)
            + f'<link rel="apple-touch-icon" href="{_html.escape(favicon)}">'
        )
        page = page.replace("<head>", "<head>\n" + inject, 1)
    return HTMLResponse(page)


@app.get("/")
def landing():
    """Página de vendas do SaaS."""
    return _serve("landing.html")


@app.get("/agendar/{slug}")
def booking(slug: str):
    """Site de agendamento de uma barbearia (o JS lê o slug da URL)."""
    return _serve_public(slug, "index.html", "agendar")


@app.get("/loja/{slug}")
def store(slug: str):
    """Loja virtual de uma barbearia (o JS lê o slug da URL)."""
    return _serve_public(slug, "store.html", "loja")


@app.get("/cancelar/{slug}")
def cancel_page(slug: str):
    """Página pública para o cliente cancelar o agendamento (lê o token da URL)."""
    return _serve("cancel.html")


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
