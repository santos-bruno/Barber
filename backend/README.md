# Back-end + Site — Agenda Barber

API em **FastAPI** com o **site público de agendamento** e banco
**PostgreSQL** (produção) / **SQLite** (local).

## Rodando localmente

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Site de agendamento: http://localhost:8000/
- Docs da API: http://localhost:8000/docs

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/services` | Lista de serviços |
| POST/PUT/DELETE | `/services` | Gerenciar serviços |
| GET/POST/PUT | `/clients` | Clientes (fluxo de clientes / contatos) |
| GET | `/clients/{id}/appointments` | Histórico do cliente |
| GET | `/appointments` | Agenda (filtra por `date`, `status`) |
| GET | `/appointments/availability` | Horários livres (`date`, `service_id`) |
| POST | `/appointments` | Cria agendamento (site ou admin) |
| PATCH | `/appointments/{id}` | Muda status/horário (concluir gera caixa) |
| GET | `/cashflow` · `/cashflow/summary` | Fluxo de caixa e resumo |
| POST/DELETE | `/cashflow` | Lançar / remover no caixa |
| GET | `/hours` · PUT `/hours/{weekday}` | Horários de funcionamento |

## Deploy grátis na nuvem (Render)

1. Crie conta em https://render.com (grátis).
2. **New + → Blueprint**, conecte este repositório.
3. O Render lê o `render.yaml` da raiz, cria o **PostgreSQL grátis** e o
   **web service** automaticamente.
4. No fim você recebe uma URL pública, ex.:
   `https://agenda-barber-o0to.onrender.com`
   - Essa URL é o **link de agendamento** para colocar no anúncio.
   - Aponte o app admin para ela via `EXPO_PUBLIC_API_URL`.

> Observação: o plano free do Render "dorme" após inatividade; a primeira
> visita pode levar ~30s para acordar. Para uso intenso, suba de plano.

Alternativa: use o `Dockerfile` para Fly.io / Railway / Cloud Run.
