# Barbearia e Belezaria Sr. Perison 💈

Aplicativo de agendamentos da **Barbearia e Belezaria Sr. Perison**.

- **Endereço:** Av. Bartolomeu de Gusmão, 857 - Casa E - Aparecida, Santarém - PA, 68030-350
- **WhatsApp:** (93) 99207-8226 — [wa.me/5593992078226](https://wa.me/5593992078226)
- **Desenvolvedor:** Bruno

## Estrutura

```
.
├── frontend/                 # App mobile — React Native + Expo
├── backend/                  # API — FastAPI + PostgreSQL/SQLite
├── .github/workflows/
│   └── android-apk.yml        # CI/CD: build automático do APK
├── init_repo.sh               # Script de inicialização do Git
└── .gitignore
```

## Tecnologias

| Camada       | Stack                                             |
|--------------|---------------------------------------------------|
| Front-end    | React Native, Expo, React Navigation              |
| Back-end     | FastAPI (Python), SQLAlchemy, PostgreSQL / SQLite |
| CI/CD        | GitHub Actions → APK via Expo prebuild + Gradle   |

## Como rodar

### Back-end
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Front-end
```bash
cd frontend
npm install
npx expo start
```

## Build automático do APK

A cada `push` na branch `main`, o workflow
[`.github/workflows/android-apk.yml`](.github/workflows/android-apk.yml):

1. Faz o checkout do código.
2. Instala Node.js e dependências.
3. Roda `npx expo prebuild --platform android`.
4. Configura Java 17.
5. Compila com `./gradlew assembleRelease`.
6. Publica o `.apk` como **Artifact** para download.

Baixe o APK em: **Actions → (último workflow) → Artifacts → `barbearia-sr-perison-apk`**.

## Funcionalidade principal

Na tela de **Agendamento**, o cliente escolhe serviço, data e hora; o app monta
automaticamente a mensagem e abre o WhatsApp do estabelecimento:

> *"Olá Sr. Perison, gostaria de agendar Corte + Barba para 12/07/2026 às 14:30. (Cliente: João)"*
