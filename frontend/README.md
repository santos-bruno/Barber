# App Admin — Barbearia e Belezaria Sr. Perison

App de **gestão** (React Native + Expo) para o dono da barbearia. Os clientes
agendam pelo **site** (servido pelo backend); este app é o painel do Sr. Perison.

## Telas
- **Dashboard** — resumo do dia (agenda + caixa) e atalho para compartilhar o
  link de agendamento.
- **Agenda** — agendamentos por data; confirmar / concluir / cancelar e chamar
  o cliente no WhatsApp. Concluir lança a entrada no caixa automaticamente.
- **Novo agendamento** — o admin marca manualmente (mostra só horários livres).
- **Clientes** — fluxo de clientes / contatos, com busca e WhatsApp.
- **Fluxo de caixa** — saldo, entradas/saídas e lançamentos.
- **Horários** — configura o funcionamento por dia da semana.
- **Configurações** — endereço do backend (nuvem) + teste de conexão.

## Configurando o servidor
Após o deploy do backend (veja `../backend/README.md`), abra o app em
**Configurações** e cole a URL do Render (ex.:
`https://barbearia-perison.onrender.com`). Fica salvo no aparelho — não precisa
recompilar o APK. Para builds, também dá para fixar via `EXPO_PUBLIC_API_URL`.

## Rodando localmente
```bash
cd frontend
npm install
npx expo start
```

## Build do APK
Automático pela pipeline `.github/workflows/android-apk.yml` a cada push.
O APK sai como Artifact e como Release (`apk-latest`).
