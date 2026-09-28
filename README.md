# DocSage

Faça perguntas em linguagem natural sobre os seus próprios documentos (PDF/TXT).
As respostas são geradas **apenas** com base no conteúdo enviado, sempre com citação
das fontes — arquitetura **RAG** (*Retrieval-Augmented Generation*).

## Stack

- **Python 3.12 + FastAPI**
- **PostgreSQL 16 + pgvector** — busca por similaridade vetorial
- **Embeddings locais** (sentence-transformers) — rodam no servidor, sem custo
- **Claude** (API da Anthropic) — geração da resposta final
- **Docker + Docker Compose** · **Caddy** (HTTPS automático em produção)

## Como funciona

**Ingestão** — o documento é dividido em pedaços com sobreposição; cada pedaço vira um
vetor (*embedding*) que representa o seu significado e é guardado no PostgreSQL.

**Pergunta** — a pergunta também vira um vetor; o banco encontra os pedaços de significado
mais próximo (busca semântica); esses trechos, e só eles, vão para o Claude, que responde
citando as fontes usadas.

```
Ingestão:  arquivo -> texto -> pedaços -> vetores -> PostgreSQL/pgvector
Pergunta:  pergunta -> vetor -> busca top-k -> Claude -> resposta + citações
```

## Documentação

| Guia | Para quê |
|---|---|
| **[docs/PASSO-A-PASSO.md](docs/PASSO-A-PASSO.md)** | **Comece aqui.** Do zero até rodar e publicar no GitHub |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Colocar no ar na Oracle Cloud (grátis), com HTTPS |
| [CLAUDE.md](CLAUDE.md) | Arquitetura, convenções e roadmap (contexto do Claude Code) |
| [SECURITY.md](SECURITY.md) | Política de segurança |

## Rodando localmente

Pré-requisitos: Docker e Docker Compose.

```bash
cp .env.example .env     # depois edite: senha do banco + chave da Anthropic
docker compose up -d --build
docker compose logs -f app
```

Swagger (teste manual dos endpoints): **http://localhost:8080/docs**
Parar: `docker compose down`

> A primeira subida demora alguns minutos: baixa o modelo de embeddings e as dependências.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Verificação de disponibilidade |
| `POST` | `/documents` | Envia e indexa um PDF/TXT |
| `GET` | `/documents` | Lista os documentos indexados |
| `POST` | `/ask` | Pergunta sobre os documentos |

Exemplos:

```bash
# Enviar um documento
curl -F "file=@contrato.pdf" http://localhost:8080/documents

# Perguntar
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual o prazo de entrega descrito no contrato?"}'
```

A resposta traz o texto e a lista `citations`. Os números `[1]`, `[2]` citados na resposta
correspondem à posição na lista de citações.

## Testes e qualidade

```bash
pytest -q        # testes das funções puras (rápidos, sem banco)
ruff check .     # lint + regras de segurança
```

O CI (GitHub Actions) roda lint, testes, `pip-audit` e `bandit` a cada push.

## Segurança

- Segredos apenas em variáveis de ambiente — fora do Git e fora da imagem Docker
- Container roda com usuário **não-root**; PostgreSQL não exposto publicamente
- Upload restrito por tipo e tamanho; acesso ao banco só via ORM
- HTTPS obrigatório em produção, com cabeçalhos de segurança (HSTS, CSP, nosniff)
- Os embeddings são gerados localmente: o conteúdo integral dos documentos não sai do servidor

Detalhes e limitações em [SECURITY.md](SECURITY.md).

> **v1 é single-user e sem autenticação** — intencional, para desenvolver rápido.
> Auth JWT e isolamento por usuário são o primeiro item da v2 (veja o roadmap em `CLAUDE.md`).

## Licença

MIT
