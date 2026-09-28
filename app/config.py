"""Configurações da aplicação, lidas das variáveis de ambiente (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lê de variáveis de ambiente; usa .env como fallback no desenvolvimento local.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco de dados
    database_url: str

    # Embeddings (modelo local)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # LLM (geração das respostas)
    anthropic_api_key: str
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Parâmetros do RAG / limites
    max_upload_mb: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 5


# Instância única usada em todo o projeto.
settings = Settings()
