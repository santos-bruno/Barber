# Alternativa de deploy via container (Fly.io, Railway, Cloud Run, etc.).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# A plataforma injeta $PORT; usa 8000 como padrão local.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
