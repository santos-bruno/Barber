# Back-end — Barbearia e Belezaria Sr. Perison

API em **FastAPI** para serviços e agendamentos.

## Rodando localmente

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Docs interativas: http://localhost:8000/docs
- Por padrão usa **SQLite** (`barbearia.db`). Para usar **PostgreSQL**, defina
  `DATABASE_URL` no `.env` (veja `.env.example`).

## Endpoints

| Método | Rota            | Descrição                        |
|--------|-----------------|----------------------------------|
| GET    | `/`             | Healthcheck + dados da barbearia |
| GET    | `/services`     | Lista de serviços                |
| POST   | `/services`     | Cria um serviço                  |
| GET    | `/appointments` | Lista de agendamentos            |
| POST   | `/appointments` | Cria um agendamento              |

No primeiro boot, uma lista de serviços padrão é inserida automaticamente.
