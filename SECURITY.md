# Política de Segurança — DocSage

## Reportar uma vulnerabilidade

Envie um e-mail para **[seu-email@exemplo.com]** com a descrição e os passos para
reproduzir. Por favor, não abra *issues* públicas para falhas de segurança.

## Gestão de segredos

- Nenhum segredo é versionado: `.env` está no `.gitignore` e no `.dockerignore`.
- O repositório contém apenas `.env.example`, com valores fictícios.
- Segredos entram na aplicação por **variáveis de ambiente**, em tempo de execução —
  nunca são embutidos na imagem Docker nem no código.
- Segredos de CI ficam em *GitHub Actions Secrets*.
- O *Secret Scanning* e o *Push Protection* do GitHub estão habilitados no repositório.

## Medidas implementadas (v1)

| Risco (OWASP) | Mitigação |
|---|---|
| **A03 — Injection** | Acesso ao banco exclusivamente via ORM (SQLAlchemy) com parâmetros ligados. Nenhum SQL concatenado. |
| **A04 — Insecure Design** | Upload restrito a `application/pdf` e `text/plain`; limite de tamanho (`MAX_UPLOAD_MB`) verificado antes do processamento. |
| **A05 — Security Misconfiguration** | Container roda com usuário **não-root**; porta do PostgreSQL não é exposta publicamente; imagem sem segredos. |
| **A02 — Cryptographic Failures** | TLS obrigatório em produção (Caddy + Let's Encrypt), com HSTS. |
| **A09 — Logging Failures** | Conteúdo dos documentos e chaves de API nunca são registrados em log. |
| **Prompt Injection** | O *system prompt* restringe as respostas aos trechos fornecidos; o modelo é instruído a admitir quando a informação não consta nos documentos. |

## Privacidade

Os **embeddings são gerados localmente**, no próprio servidor. O conteúdo integral dos
documentos não é enviado a terceiros — apenas os trechos relevantes a cada pergunta
seguem para a API do modelo de linguagem.

## Limitações conhecidas (v1)

Esta versão é *single-user* e **não possui autenticação**: qualquer pessoa com acesso à
API enxerga todos os documentos. Ela é adequada para uso local ou em ambiente restrito.
Autenticação JWT, isolamento por usuário e *rate limiting* estão previstos na v2 —
veja o roadmap em `CLAUDE.md`.

## Dependências

Verificação automática no CI a cada push, com `pip-audit` (vulnerabilidades conhecidas)
e `bandit` (análise estática de código), além do Dependabot.
