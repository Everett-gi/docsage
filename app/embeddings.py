"""Geração de embeddings com um modelo LOCAL (gratuito, roda no próprio servidor)."""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    """Carrega o modelo uma única vez (baixado no 1º uso e reaproveitado)."""
    return SentenceTransformer(settings.embedding_model)


def warmup() -> None:
    """Carrega o modelo antecipadamente (chamado na inicialização da app)."""
    _model()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Converte uma lista de textos em vetores normalizados."""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    """Converte uma única pergunta em vetor."""
    return embed_texts([text])[0]
