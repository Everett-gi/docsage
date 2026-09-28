"""Funções puras de manipulação de texto.

Este módulo NÃO importa banco de dados nem o modelo de embeddings de propósito:
assim ele pode ser testado de forma rápida e isolada (testes unitários puros).
"""
import io

from pypdf import PdfReader


def extract_text(content: bytes, content_type: str, filename: str) -> str:
    """Extrai texto puro de um PDF ou de um arquivo de texto simples."""
    is_pdf = content_type == "application/pdf" or filename.lower().endswith(".pdf")
    if is_pdf:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return content.decode("utf-8", errors="ignore")


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Divide o texto em pedaços de `size` caracteres com `overlap` de sobreposição.

    A sobreposição existe para não "cortar" uma ideia no meio: o fim de um pedaço
    se repete no início do seguinte, preservando o contexto nas bordas.
    """
    if size <= 0:
        raise ValueError("size deve ser maior que zero.")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap deve ser >= 0 e menor que size.")

    text = " ".join(text.split())  # normaliza espaços, tabs e quebras de linha
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    step = size - overlap
    while start < len(text):
        chunks.append(text[start:start + size])
        start += step
    return chunks
