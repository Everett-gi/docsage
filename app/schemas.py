"""Schemas de entrada e saída da API (validação com Pydantic)."""
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    """Resposta ao listar/enviar um documento."""
    id: int
    filename: str
    num_chunks: int
    created_at: datetime

    model_config = {"from_attributes": True}   # permite construir a partir do objeto do banco


class AskRequest(BaseModel):
    """Corpo da pergunta enviada pelo usuário."""
    question: str
    conversation_id: int | None = None   # opcional: continua uma conversa existente


class Citation(BaseModel):
    """Uma fonte usada na resposta (para transparência/rastreabilidade)."""
    document_id: int
    filename: str
    chunk_index: int
    snippet: str


class AskResponse(BaseModel):
    """Resposta gerada + as fontes que a fundamentaram."""
    answer: str
    citations: list[Citation]
    conversation_id: int
