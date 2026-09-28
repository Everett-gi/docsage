"""Geração da resposta com a API da Anthropic, usando apenas o contexto recuperado."""
from anthropic import Anthropic

from app.config import settings
from app.models import Chunk

# Cliente criado uma vez (não faz chamada de rede na criação).
_client = Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = (
    "Você é o DocSage, um assistente que responde perguntas SOMENTE com base "
    "nos trechos de documentos fornecidos. Se a resposta não estiver nos trechos, "
    "diga claramente que não encontrou a informação nos documentos. Cite as fontes "
    "usando os números [1], [2] etc. que aparecem antes de cada trecho. "
    "Responda em português, de forma objetiva."
)


def build_context(chunks: list[Chunk]) -> str:
    """Monta o bloco de contexto numerado que vai no prompt.

    A numeração [1], [2]... segue a ORDEM da lista de trechos, então o número
    citado na resposta corresponde à mesma posição na lista de `citations`.
    """
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (arquivo: {c.document.filename})\n{c.content}")
    return "\n\n".join(blocks)


def answer_question(question: str, chunks: list[Chunk]) -> str:
    """Pergunta ao modelo usando o contexto e retorna o texto da resposta."""
    context = build_context(chunks)
    user_message = f"Trechos disponíveis:\n\n{context}\n\nPergunta: {question}"

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # A resposta vem como uma lista de blocos; juntamos apenas o texto.
    return "".join(block.text for block in response.content if block.type == "text")
