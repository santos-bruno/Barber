# Segurança — Agenda Barber

Resumo das proteções ativas na API e como operá-las com segurança.

## Autenticação e acesso
- **JWT** assinado com `SECRET_KEY` (HS256), enviado no header `Authorization: Bearer`.
  A `SECRET_KEY` é **obrigatória em produção** — o sistema não sobe sem ela (evita
  chave previsível). O Render gera automaticamente (`generateValue`).
- Senhas com **bcrypt** (nunca armazenadas em texto). Mínimo de 6 caracteres.
- **Multi-tenant**: cada requisição resolve o tenant pelo token; dados são sempre
  filtrados por `tenant_id`. Áreas financeiras/gestão exigem papel `owner`.
- **Painel admin** (`/admin/*`, `/painel`) protegido por `SUPERADMIN_KEY`
  (header `X-Admin-Key`), comparada com `secrets.compare_digest` (anti-timing).

## Proteções de borda
- **CORS** restrito às origens em `CORS_ORIGINS` (ou `APP_BASE_URL` + localhost).
  Sem cookies (`allow_credentials=False`) — a auth é por header.
- **Cabeçalhos de segurança** em toda resposta: `Content-Security-Policy`,
  `Strict-Transport-Security` (HTTPS), `X-Frame-Options: SAMEORIGIN`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`.
- **Limite de corpo** (`MAX_BODY_BYTES`, padrão 1 MB) e **limites de tamanho**
  de campos (nome, telefone, notas, etc.) via Pydantic.
- **Rate limiting** por IP (em memória):
  - Login: 12/min · Cadastro: 6/h
  - Agendamento/compra pública: 20/h · Painel admin: 30/min

## Pagamentos (Appmax)
- Dados de cartão são tokenizados e **não são gravados** no banco nem em logs.
- Webhook valida um token opcional em querystring (`APPMAX_WEBHOOK_TOKEN`,
  comparado com `compare_digest`). Recomendado defini-lo em produção.
- Logs do webhook registram apenas `evento`, `order_id` e `customer_id` (sem PII).

## Segredos
- Nenhum segredo fica no repositório: `.env`, `*.db` e chaves estão no `.gitignore`.
- Configure tudo pelo painel do Render (Environment). Veja `.env.example`.

## Se escalar
O rate limiter e os states de conexão são **em memória** (processo único, plano
free). Para múltiplas instâncias/workers, migre esses estados para Redis.
