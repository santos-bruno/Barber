# Agenda Barber 💈 — SaaS de Agendamento para Barbearias

Plataforma **SaaS multi-barbearia**: você vende assinaturas e cada barbearia
ganha seu próprio painel, agenda, fluxo de caixa e link de agendamento online.

## Como funciona

```
   CLIENTE da barbearia            BARBEARIA (assinante)           VOCÊ (dono do SaaS)
  ┌────────────────────┐         ┌─────────────────────┐        ┌────────────────────┐
  │ /agendar/{slug}     │  agenda │ App (login) + link   │  paga  │ Painel superadmin  │
  │ site de agendamento │ ──────► │ Agenda/Clientes/Caixa│ ─────► │ assinantes + MRR   │
  └─────────┬───────────┘         └──────────┬──────────┘        └─────────┬──────────┘
            │                                 │                            │
            └──────────►  BACKEND SaaS (FastAPI + PostgreSQL)  ◄───────────┘
                         multi-tenant · JWT · assinaturas Asaas
```

- Cada **barbearia** se cadastra (teste grátis), assina um **plano mensal/anual**
  no cartão (via **Asaas**) e usa o app.
- Dados **isolados por barbearia** (multi-tenant).
- **Cliente final** agenda pelo link público `/agendar/{slug}`.
- **Você** acompanha assinantes e faturamento no painel superadmin.

## Estrutura

```
.
├── frontend/                  # App admin (Expo) → gera o APK
├── backend/                   # API + páginas web (FastAPI)
│   ├── routers/                # auth, billing, public, services, clients, ...
│   ├── web/landing.html        # página de vendas (/)
│   └── web/index.html          # site de agendamento (/agendar/{slug})
├── .github/workflows/          # CI: build do APK
└── render.yaml                 # deploy (Render + Postgres)
```

## Colocar no ar

### 1. Backend (Render)
1. Conta em https://render.com → **New + → Blueprint** → conecte este repo.
2. O `render.yaml` cria o Postgres, gera o `SECRET_KEY` e sobe a API.
3. No painel, preencha `ASAAS_API_KEY` (sua chave Asaas) e `SUPERADMIN_KEY`.
4. Para produção, troque `ASAAS_BASE_URL` para `https://api.asaas.com/v3`.
5. URL final ex.: `https://agenda-barber.onrender.com`.

### 2. Asaas
- Crie conta em https://www.asaas.com, gere a **API Key** (sandbox p/ testar).
- Configure o **webhook** apontando para `SEU-BACKEND/billing/webhook`.

### 3. App
- Baixe o APK (Release `apk-latest`), ou rebuilde com
  `EXPO_PUBLIC_API_URL=https://SEU-BACKEND`.

## Planos (ajustáveis por variáveis de ambiente)
- `PLAN_MENSAL_PRICE` (padrão R$ 49,90) · `PLAN_ANUAL_PRICE` (padrão R$ 499,00)
- `TRIAL_DAYS` (padrão 7)

## Tecnologias
FastAPI · SQLAlchemy · PostgreSQL · JWT · Asaas · React Native/Expo · GitHub Actions · Render

## APK
Build automático a cada push — **[Release `apk-latest`](https://github.com/santos-bruno/Barber/releases/tag/apk-latest)**.
