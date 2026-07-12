# Barbearia e Belezaria Sr. Perison 💈

Sistema completo de gestão e agendamento da **Barbearia e Belezaria Sr. Perison**.

- **Endereço:** Av. Bartolomeu de Gusmão, 857 - Casa E - Aparecida, Santarém - PA, 68030-350
- **WhatsApp:** (93) 99207-8226 — [wa.me/5593992078226](https://wa.me/5593992078226)
- **Desenvolvedor:** Bruno

## Como funciona (dois lados)

```
        CLIENTE                              VOCÊ (ADMIN)
   ┌───────────────┐                    ┌────────────────────┐
   │  Site de       │   agendamento     │  App (APK Android) │
   │  agendamento   │ ───────────────►  │  Agenda · Clientes │
   │ (link/anúncio) │                   │  Caixa · Horários  │
   └──────┬─────────┘                   └─────────┬──────────┘
          │                                       │
          └──────────►  BACKEND (nuvem)  ◄────────┘
                    FastAPI + PostgreSQL (Render)
```

- **Clientes** abrem o **link** (você põe no anúncio / manda no WhatsApp),
  escolhem serviço, dia e horário livre e agendam sozinhos.
- O agendamento cai **automaticamente** na sua **Agenda** no app.
- Você gerencia tudo: agenda, fluxo de clientes, contatos, fluxo de caixa e
  horários de funcionamento.

## Estrutura

```
.
├── frontend/                 # App admin — React Native + Expo (gera o APK)
├── backend/                  # API + site de agendamento — FastAPI
│   └── web/index.html         # Site público de agendamento
├── .github/workflows/
│   └── android-apk.yml        # CI/CD: build automático do APK
├── render.yaml                # Deploy do backend (Render + Postgres grátis)
└── init_repo.sh
```

## Passo a passo para colocar no ar

### 1. Backend na nuvem (grátis)
1. Crie conta em https://render.com
2. **New + → Blueprint** e conecte este repositório.
3. O Render lê o `render.yaml`, cria o **Postgres grátis** e sobe a API.
4. Copie a URL final (ex.: `https://barbearia-perison.onrender.com`).
   - Essa URL **é o link de agendamento** dos clientes.

### 2. App admin
- Baixe o APK (Release `apk-latest`) e instale no Android.
- Abra **Configurações** e cole a URL do backend.

### 3. Divulgue
- Compartilhe a URL no anúncio / WhatsApp / Instagram. Pronto.

## Tecnologias

| Camada    | Stack |
|-----------|-------|
| App admin | React Native, Expo, React Navigation |
| Site      | HTML/JS servido pelo FastAPI |
| Back-end  | FastAPI, SQLAlchemy, PostgreSQL / SQLite |
| Deploy    | Render (Blueprint) · Docker |
| CI/CD     | GitHub Actions → APK (Expo prebuild + Gradle) |

## APK
Build automático a cada push. Download direto:
**[Release `apk-latest`](https://github.com/santos-bruno/Barber/releases/tag/apk-latest)**.
