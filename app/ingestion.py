"""Pipeline de ingestão: extrai texto, divide em pedaços, gera embeddings e salva."""
from sqlalchemy.orm import Session

from app.config import settings
from app.embeddings import embed_texts
from app.models import Chunk, Document
from app.text_utils import chunk_text, extract_text


def ingest_document(
    db: Session, *, filename: str, content_type: str, content: bytes
) -> Document:
    """Orquestra a ingestão e persiste o documento + seus pedaços vetorizados.

    Passos: extrair texto -> dividir em chunks -> gerar embeddings -> salvar tudo
    numa única transação (ou grava tudo, ou nada).
    """
    text = extract_text(content, content_type, filename)
    pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not pieces:
        raise ValueError(
            "Não foi possível extrair texto do arquivo. "
            "PDFs escaneados (imagem) não são suportados nesta versão."
        )

    vectors = embed_texts(pieces)

    document = Document(
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
        num_chunks=len(pieces),
    )
    db.add(document)
    db.flush()  # gera o document.id sem encerrar a transação

    # strict=True: garante que a quantidade de pedaços e de vetores seja a mesma
    for i, (piece, vector) in enumerate(zip(pieces, vectors, strict=True)):
        db.add(
            Chunk(
                document_id=document.id,
                chunk_index=i,
                content=piece,
                embedding=vector,
            )
        )

    db.commit()
    db.refresh(document)
    return document
