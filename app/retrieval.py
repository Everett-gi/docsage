"""Busca semântica: encontra os pedaços mais parecidos com a pergunta."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings import embed_query
from app.models import Chunk


def search_chunks(db: Session, question: str, top_k: int) -> list[Chunk]:
    """Retorna os `top_k` pedaços mais próximos da pergunta (distância de cosseno).

    `cosine_distance` é fornecido pelo pgvector: quanto menor a distância,
    mais parecido o significado do pedaço com o da pergunta.
    """
    query_vector = embed_query(question)
    stmt = (
        select(Chunk)
        .order_by(Chunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    return list(db.scalars(stmt))
