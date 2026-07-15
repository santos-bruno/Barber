# Handoff — Integração Appmax (assinatura recorrente)

Contexto para continuar a integração de pagamento da Appmax no Agenda Barber.
**Nenhum segredo neste arquivo** — todas as credenciais ficam nas variáveis de
ambiente do Render.

## Objetivo
Cobrar a mensalidade/anuidade das barbearias (SaaS) via **Appmax API v1**, com
**cobrança recorrente** no cartão.

## O que já está pronto (no código, branch `claude/barbearia-perison-app-setup-kzvgv5`)
- `backend/appmax.py` — cliente da API v1:
  - Auth Bearer: usa `APPMAX_ACCESS_TOKEN` direto **ou** OAuth
    `client_credentials` com `APPMAX_MERCHANT_CLIENT_ID/SECRET`.
  - `create_customer` (`POST /v1/customers`), `create_order` (`POST /v1/orders`,
    valores em **centavos**), `tokenize_card` (`POST /v1/payments/tokenize`),
    `pay_credit_card` (`POST /v1/payments/credit-card` + objeto
    `subscription {interval, interval_count}` para recorrência).
  - Fluxo de instalação do app: `app_authorize` (`POST /app/authorize`),
    `app_generate_merchant` (`POST /app/client/generate`).
- `backend/routers/appmax_billing.py`:
  - `POST /billing/appmax/validate` — health-check da instalação (retorna
    `external_id` UUID novo a cada chamada). **Já funciona.**
  - `POST /billing/appmax/webhook` — eventos (schema oficial: `data.order_id`,
    `data.customer_id`), libera/bloqueia o tenant. Responde 200 rápido, sem
    exigir header (a Appmax não envia token no webhook).
  - `POST /billing/appmax/checkout` — cria cliente + pedido + tokeniza cartão no
    servidor + paga com recorrência.
  - `GET /billing/appmax/connect?key=SUPERADMIN_KEY` — inicia a instalação
    (authorize) e redireciona para a Appmax.
  - `GET /billing/appmax/callback` — recebe o retorno, gera as credenciais do
    merchant e mostra numa página para colar no Render.
  - `GET /billing/appmax/debug?key=SUPERADMIN_KEY` — diagnóstico (URLs, app_id,
    se o OAuth do app funciona).
- `backend/web/assinar.html` + rota `/assinar` — checkout logado (coleta cartão,
  backend tokeniza).
- Campos `appmax_customer_id`, `appmax_order_id` no `Tenant` (+ migração).

## Variáveis de ambiente (Render) — SANDBOX
```
APPMAX_APP_ID            = <UUID do app OU ID numérico — ver "problema atual">
APPMAX_APP_CLIENT_ID     = <Client ID sandbox do app>       (secreto)
APPMAX_APP_CLIENT_SECRET = <Client Secret sandbox do app>   (secreto)
APPMAX_BASE_URL          = https://api.sandboxappmax.com.br
APPMAX_AUTH_URL          = https://auth.sandboxappmax.com.br/oauth2/token
APPMAX_AUTHORIZE_URL     = https://breakingcode.sandboxappmax.com.br/appstore/integration/
# Geradas em /billing/appmax/connect:
APPMAX_MERCHANT_CLIENT_ID     = <gerado>
APPMAX_MERCHANT_CLIENT_SECRET = <gerado>
```
Produção: trocar `sandboxappmax`→`appmax` e o AUTHORIZE_URL para
`https://admin.appmax.com.br/appstore/integration/`.

## Fluxo para obter as credenciais do merchant
1. Portal do desenvolvedor (appstore.appmax.com.br): criar app, preencher URLs
   (Webhook=`/billing/appmax/webhook`, Validação=`/billing/appmax/validate`,
   Plataforma=`/gerente`), marcar permissões (order_approved, order_paid,
   payment_not_authorized, subscription_*), salvar.
2. Pôr as credenciais do **app** no Render (sandbox).
3. Abrir `/billing/appmax/connect?key=SUPERADMIN_KEY` → autorizar na Appmax →
   a página de callback mostra `client_id`/`client_secret` do **merchant**.
4. Colar as do merchant no Render → deploy → testar `/assinar`.

## ⚠️ PROBLEMA ATUAL (bloqueio)
`POST /app/authorize` retorna:
```
422 {"errors":{"message":{"app_id":["The selected app id is invalid."]}}}
```
Diagnóstico via `/billing/appmax/debug` confirma:
- `base_url`/`auth_url`/`authorize_url` = **sandbox** (corretos)
- `app_id` = UUID do app (`8765...`)
- `app_oauth` = **ok** (as credenciais do app são válidas e o token é obtido)

Ou seja: o OAuth do app funciona, mas a Appmax rejeita o `app_id` no
`/app/authorize`. A doc diz para usar o **UUID** (é o que está lá), então:

### Hipóteses a testar (em ordem)
1. Trocar `APPMAX_APP_ID` para o **ID numérico** do app (em vez do UUID) e
   repetir `/connect`. (A doc diz UUID, mas o UUID está sendo recusado.)
2. Verificar se há **mais de um app** em "Meus aplicativos" — o `client_id`/
   `secret` no Render podem ser de um app e o `app_id` de outro. Reconciliar:
   usar UUID/numérico, client_id e client_secret **todos do mesmo app**.
3. Confirmar com o suporte Appmax (chat) se, com o app **"Em análise"**, o
   `/app/authorize` self-install já é permitido no sandbox.

## Cartão de teste (sandbox)
`4000000000000010`, validade futura (ex.: 12/2030), CVV `123` → sucesso.
`4000000000000028` → recusado.

## Como rodar/local
```
cd backend && pip install -r requirements.txt
uvicorn main:app --reload
```
Deploy: Render (Blueprint `render.yaml`), branch acima é a default do repo.
