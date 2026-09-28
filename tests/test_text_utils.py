"""Testes das funções puras de texto (rápidos: não precisam de banco nem de modelo)."""
import pytest

from app.text_utils import chunk_text, extract_text


def test_chunk_text_divide_com_sobreposicao():
    texto = "a" * 250
    chunks = chunk_text(texto, size=100, overlap=20)
    # passo = 100 - 20 = 80  ->  inícios em 0, 80, 160, 240
    assert len(chunks) == 4
    assert len(chunks[0]) == 100
    assert chunks[-1] == "a" * 10  # último pedaço é o resto


def test_chunk_text_preserva_contexto_na_borda():
    texto = "PRIMEIRA_PARTE " + ("x" * 80) + " SEGUNDA_PARTE"
    chunks = chunk_text(texto, size=50, overlap=25)
    # a sobreposição faz o fim de um pedaço reaparecer no início do próximo
    assert chunks[0][-25:] == chunks[1][:25]


def test_chunk_text_normaliza_espacos():
    chunks = chunk_text("olá\n\n   mundo\t\tteste", size=100, overlap=0)
    assert chunks == ["olá mundo teste"]


def test_chunk_text_texto_vazio_retorna_lista_vazia():
    assert chunk_text("", size=100, overlap=10) == []
    assert chunk_text("   \n\t  ", size=100, overlap=10) == []


def test_chunk_text_rejeita_parametros_invalidos():
    with pytest.raises(ValueError):
        chunk_text("abc", size=0, overlap=0)
    with pytest.raises(ValueError):
        chunk_text("abc", size=10, overlap=10)  # overlap não pode ser >= size


def test_extract_text_de_arquivo_txt():
    conteudo = "Contrato de teste".encode("utf-8")
    assert extract_text(conteudo, "text/plain", "doc.txt") == "Contrato de teste"
