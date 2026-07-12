# App — Agenda Barber (SaaS)

App de gestão (React Native + Expo) para as barbearias **assinantes**. Cada
barbearia faz **login/cadastro**, cai no seu painel isolado e ganha um link de
agendamento próprio.

## Fluxo
- **Login / Cadastro** — cria a barbearia (com teste grátis) ou entra.
- **Dashboard** — resumo do dia, banner de assinatura e link de agendamento.
- **Agenda / Novo Agendamento / Clientes / Caixa / Horários** — gestão.
- **Assinatura** — status do plano e checkout (Asaas) no cartão.
- **Configurações** — endereço do servidor do SaaS (avançado).

## Servidor
O app aponta para o backend do SaaS. Fixe no build com
`EXPO_PUBLIC_API_URL=https://SEU-BACKEND` ou informe em **Login → servidor
(avançado)** / **Configurações**.

## Rodar / Buildar
```bash
cd frontend && npm install && npx expo start
```
APK: build automático pela pipeline (Release `apk-latest`).
