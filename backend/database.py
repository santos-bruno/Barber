"""
Configuração da conexão com o banco de dados.

Usa PostgreSQL quando a variável de ambiente DATABASE_URL estiver definida
(ambiente de produção); caso contrário, cai para SQLite local (ambiente de
desenvolvimento inicial), conforme solicitado.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Ex.: postgresql+psycopg2://user:senha@localhost:5432/barbearia
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./barbearia.db")

# check_same_thread só é necessário/válido para o SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependência do FastAPI que fornece uma sessão de banco por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
