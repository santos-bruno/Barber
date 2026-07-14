"""
Migração leve de schema (idempotente).

O `Base.metadata.create_all` cria tabelas novas, mas NÃO adiciona colunas em
tabelas que já existem. Como o banco de produção é persistente e o modelo
evoluiu (papéis de barbeiro, etc.), esta função adiciona as colunas que
faltam via ALTER TABLE — sem apagar dados.
"""
from sqlalchemy import inspect, text

from database import engine


def _bool_default() -> str:
    return "true" if engine.dialect.name == "postgresql" else "1"


# Colunas que podem faltar em bancos criados por versões anteriores.
EXPECTED = {
    "appointments": {
        "barber_id": "INTEGER",
        "barber_name": "VARCHAR DEFAULT ''",
        "payment_type": "VARCHAR DEFAULT 'avista'",
        "client_subscription_id": "INTEGER",
    },
    "users": {
        "active": "__bool__",
    },
    "services": {
        "active": "__bool__",
    },
    "products": {
        "sellable_online": "__bool__",
    },
}


def run_migrations() -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    stmts = []
    for table, cols in EXPECTED.items():
        if table not in tables:
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        for col, ddl in cols.items():
            if col in existing:
                continue
            if ddl == "__bool__":
                ddl = f"BOOLEAN DEFAULT {_bool_default()}"
            stmts.append(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")

    if not stmts:
        return

    with engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
            except Exception as e:  # noqa: BLE001
                print(f"[migrate] ignorado: {s} -> {e}")
