"""Conexão com o PostgreSQL via SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# pool_pre_ping evita erros de "conexão morta" após ociosidade.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Fábrica de sessões (uma sessão = uma "conversa" com o banco).
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Classe base que todas as tabelas (models) herdam.
Base = declarative_base()


def get_db():
    """Dependência do FastAPI: abre uma sessão por requisição e fecha no fim."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
