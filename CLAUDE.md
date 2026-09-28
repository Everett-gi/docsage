# DocSage — Contexto do Projeto

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o projeto.
> Ele define o que é o projeto, como trabalhar nele e o que NÃO fazer.

## O que é

API de perguntas e respostas sobre documentos do próprio usuário (PDF/TXT), usando
**RAG** (*Retrieval-Augmented Generation*). As respostas são geradas **apenas** a partir
do conteúdo enviado, sempre com citação das fontes.

Projeto de portfólio (fullstack + segurança). Prioridades, nesta ordem:
**1) segurança · 2) clareza do código · 3) funcionalidade.**

## Modo tutorial

O DocSage tem repositório próprio, mas faz parte da trilha de aprendizado do autor, cujo
índice fica no monorepo do portfólio
(https://github.com/Everett-gi/Projetos-e-ideias/blob/main/tutorial/README.md). Ele vem de
**C e C++** (domina lógica, ponteiros, memória, compilação) e está aprendendo Python.

- Explique cada passo e o **porquê**. Use analogias com C/C++ quando ajudarem.
- Não explique lógica de programação básica; foque no que é novo: idiomas da linguagem,
  bibliotecas, ferramentas, arquitetura e segurança.
- As lições deste projeto ficam em `docs/tutorial/` e terminam com exercícios. Deixe o
  autor rodar os comandos sempre que possível.
- Ambiente do autor: Windows 11 · PowerShell · VS Code · Python 3.12 (com o launcher `py`)
  · Git. Comandos em lições e respostas: sintaxe PowerShell.

## Stack

- Python 3.12 + FastAPI
- PostgreSQL 16 + **pgvector** (busca vetorial)
- Embeddings **locais** via `sentence-transformers` (gratuito, roda no servidor)
- Claude (API da Anthropic) apenas para gerar a resposta final
- Docker + Docker Compose
- pytest (testes) · ruff (lint) · GitHub Actions (CI)

## Como o RAG funciona aqui

**Ingestão** (`POST /documents`):
```
arquivo -> extract_text() -> chunk_text() -> embed_texts() -> salva Document + Chunks
```

**Pergunta** (`POST /ask`):
```
pergunta -> embed_query() -> busca vetorial (cosine distance, top_k)
         -> build_context() numera os trechos [1][2]...
         -> Claude responde citando os números -> salva Conversation/Messages
```

A numeração `[1] [2]` do prompt **segue a ordem da lista de chunks**, e essa mesma ordem
vai no campo `citations` da resposta. Se mexer na ordem em um lugar, mexa no outro.

## Mapa dos arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app/config.py` | Configurações via env (pydantic-settings). Fonte única de verdade. |
| `app/database.py` | Engine, `SessionLocal`, `Base`, dependência `get_db()`. |
| `app/models.py` | Tabelas: `Document`, `Chunk` (coluna `Vector`), `Conversation`, `Message`. |
| `app/schemas.py` | Entrada/saída da API (Pydantic). |
| `app/text_utils.py` | **Funções puras**: `extract_text`, `chunk_text`. Sem imports pesados. |
| `app/embeddings.py` | Modelo local de embeddings (cache via `lru_cache`). |
| `app/ingestion.py` | Orquestra a ingestão e persiste. |
| `app/retrieval.py` | Busca semântica (`cosine_distance` do pgvector). |
| `app/llm.py` | Prompt + chamada à API da Anthropic. |
| `app/main.py` | App FastAPI e endpoints. |
| `db/init.sql` | `CREATE EXTENSION vector` — roda 1x na criação do banco. |

**Regra de arquitetura:** `text_utils.py` não pode importar banco, config nem embeddings.
É o que mantém os testes rápidos. Ao adicionar lógica pura de texto, coloque lá.

## Comandos

```bash
# Subir tudo (app + banco)
docker compose up -d --build

# Logs da aplicação
docker compose logs -f app

# Testes (rápidos, sem banco)
pytest -q

# Lint
ruff check .

# Derrubar (mantém os dados)
docker compose down

# Derrubar APAGANDO o banco (recomeçar do zero)
docker compose down -v

# Acessar o banco
docker compose exec db psql -U docsage -d docsage
```

Swagger (teste manual dos endpoints): http://localhost:8080/docs

## Regras de segurança (inegociáveis)

- **NUNCA** commitar o `.env`, chaves, `.pem`, tokens ou senhas. Só `.env.example` com valores fictícios.
- **NUNCA** colocar segredo hardcoded no código — sempre via `app/config.py`.
- **NUNCA** montar SQL por concatenação de string. Só ORM / parâmetros ligados.
- Todo upload precisa validar **tipo** e **tamanho** antes de processar.
- Não logar conteúdo de documentos, chaves de API nem dados pessoais.
- A porta do PostgreSQL não é exposta publicamente (nem em dev nem em prod).
- Ao adicionar variável de ambiente: atualize `.env.example` **e** `app/config.py`.

## Convenções de código

- Comentários e docstrings em **português**; nomes de código em **inglês**.
- Docstring curta em toda função pública, explicando o "porquê", não o "o quê".
- Type hints sempre. SQLAlchemy 2.0 (`Mapped[...]` / `mapped_column`).
- Imports ordenados: stdlib → terceiros → `app.*`.
- Toda função pura nova em `text_utils.py` deve vir com teste em `tests/`.
- Mensagens de erro da API em português (é o usuário que lê).
- Commits no padrão *Conventional Commits*: `feat:`, `fix:`, `chore:`, `docs:`, `test:`.

## Estado atual — v1 (concluída)

- [x] Ingestão de PDF/TXT com chunking e sobreposição
- [x] Embeddings locais + armazenamento em pgvector
- [x] Busca semântica (top-k por distância de cosseno)
- [x] Resposta via Claude com citações
- [x] Histórico de conversas
- [x] Testes das funções puras + CI

**Limitação consciente da v1:** é *single-user*, sem autenticação. Todo mundo vê todos os
documentos. Isso é intencional para desenvolver rápido — e é o primeiro item da v2.

## Roadmap

**v2 — Segurança (próxima)**
1. Auth JWT (access + refresh) com hash Argon2/BCrypt
2. `user_id` em `Document` e `Conversation` + filtro obrigatório na busca (anti-IDOR)
3. Rate limiting (`slowapi`) em `/ask` e `/documents`
4. Cabeçalhos de segurança (CSP, HSTS, nosniff) + CORS restrito
5. Migrations com Alembic (substituir o `create_all`)

**v3 — Qualidade do RAG**
6. Índice HNSW no pgvector (performance da busca)
7. Chunking por parágrafo/sentença em vez de caractere fixo
8. Reranking dos resultados + limiar mínimo de similaridade
9. Suporte a DOCX e OCR para PDF escaneado

**v4 — Produto**
10. Interface web (React) + streaming da resposta
11. Filtro de busca por documento específico
12. Exclusão de documento/conta (LGPD)

## Armadilhas conhecidas

- **`EMBEDDING_DIM` deve bater com o modelo.** O modelo padrão gera 384 dimensões.
  Se trocar de modelo, ajuste a variável **e** recrie a tabela (`docker compose down -v`),
  senão o pgvector rejeita a inserção.
- **Primeira subida é lenta** (~1 min): baixa o modelo de embeddings. Fica em cache no
  volume `hfcache`.
- **`db/init.sql` só roda na criação do banco.** Se o volume `pgdata` já existir, ele é
  ignorado. Para forçar: `docker compose down -v`.
- **PDF escaneado (imagem) não extrai texto** — retorna erro 422. OCR está no roadmap.
- **`create_all` não migra schema.** Mudou `models.py`? Em dev, `docker compose down -v`.
  Em produção isso apaga dados — por isso Alembic está na v2.
