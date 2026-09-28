# Começando do zero — DocSage

Do download do projeto até rodar na sua máquina e publicar no GitHub.
Depois disso, siga o [DEPLOY.md](./DEPLOY.md) para colocar no ar.

---

## Etapa 0 — Instalar o necessário (uma vez só)

| Ferramenta | Para quê | Onde baixar |
|---|---|---|
| **Docker Desktop** | roda a aplicação e o banco | https://www.docker.com/products/docker-desktop |
| **Git** | versionamento | https://git-scm.com/download/win |
| **Claude Code** | desenvolver com IA | `npm install -g @anthropic-ai/claude-code` |
| **VS Code** (opcional) | editor | https://code.visualstudio.com |

> O Claude Code precisa do **Node.js 18+**: https://nodejs.org

Confirme no PowerShell (se algum comando falhar, a ferramenta não foi instalada):

```powershell
docker --version
git --version
node --version
```

> **Docker Desktop:** deixe-o aberto antes de rodar o projeto. Se der erro de "daemon",
> quase sempre é porque ele não está em execução.

---

## Etapa 1 — Extrair o projeto

Extraia o `docsage.zip` na sua pasta de usuário. A estrutura final deve ser:

```
C:\Users\SEU_USUARIO\projetos\docsage\
├── CLAUDE.md
├── README.md
├── SECURITY.md
├── Caddyfile
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── .dockerignore
├── app\          (o código Python)
├── db\           (init.sql)
├── tests\        (testes)
├── docs\         (este guia e o DEPLOY.md)
└── .github\      (CI)
```

> **Confira que as pastas `app\`, `db\` e `tests\` vieram junto.** Se o conteúdo do `app\`
> ficar solto na raiz, os imports quebram.

**Windows esconde arquivos que começam com ponto.** Para ver o `.env`, `.gitignore` etc.,
ative no Explorador: **Exibir → Mostrar → Itens ocultos**.

---

## Etapa 2 — Pegar a chave da API da Anthropic

1. Acesse **https://console.anthropic.com**
2. **Settings → API Keys → Create Key**
3. Copie a chave (começa com `sk-ant-`). **Ela só aparece uma vez.**
4. Adicione créditos em **Plans & Billing** (US$ 5 duram bastante com o modelo Haiku).

> A conta do Claude.ai e a do Console são cobranças separadas. Assinar o Claude Pro não
> dá créditos de API.

**Regra de ouro:** essa chave é uma senha. Ela vai **só** no `.env` — nunca no código,
nunca num print, nunca num commit.

---

## Etapa 3 — Configurar o `.env`

No PowerShell, dentro da pasta do projeto:

```powershell
cd C:\Users\SEU_USUARIO\projetos\docsage
copy .env.example .env
notepad .env
```

Altere **três** coisas:

1. `POSTGRES_PASSWORD` → uma senha forte
2. Dentro de `DATABASE_URL` → **a mesma** senha (é o erro nº 1 de quem começa)
3. `ANTHROPIC_API_KEY` → sua chave real

Exemplo (as duas senhas em destaque precisam ser idênticas):

```bash
POSTGRES_PASSWORD=Xk9mP2vL8qR4nT6w
DATABASE_URL=postgresql+psycopg://docsage:Xk9mP2vL8qR4nT6w@db:5432/docsage
ANTHROPIC_API_KEY=sk-ant-api03-abc123...
```

Deixe `DOMAIN` e `ACME_EMAIL` como estão — só valem em produção.

---

## Etapa 4 — Rodar

```powershell
docker compose up -d --build
```

**A primeira vez demora de 5 a 15 minutos** (baixa o PyTorch, que é grande). Depois, segundos.

Acompanhe:

```powershell
docker compose logs -f app
```

Espere aparecer `Application startup complete`. `Ctrl+C` sai do log **sem** derrubar a app.

Abra: **http://localhost:8080/docs**

Você verá o Swagger — dá para testar tudo por ali, sem escrever código.

---

## Etapa 5 — Testar o fluxo completo

No Swagger:

1. **`POST /documents`** → *Try it out* → escolha um PDF de teste → *Execute*
   Resposta esperada: `201` com `num_chunks` maior que zero.
2. **`GET /documents`** → confirme que ele aparece na lista.
3. **`POST /ask`** → *Try it out* → cole e execute:
   ```json
   { "question": "Do que trata este documento?" }
   ```
   Resposta esperada: `200` com `answer` e a lista `citations`.

**Funcionou? A aplicação está completa e operante.** 🎉

Comandos úteis:

```powershell
docker compose down       # para tudo (mantém os dados)
docker compose down -v    # para e APAGA o banco (recomeçar do zero)
docker compose ps         # o que está rodando
```

---

## Etapa 6 — Enviar para o GitHub com segurança

### 6.1 Crie o repositório

No GitHub: **New repository** → nome `docsage` → **NÃO** marque "Add a README" nem
"Add .gitignore" (o repositório precisa nascer vazio para não conflitar).

### 6.2 Configure o Git (se for a primeira vez)

```powershell
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

### 6.3 Envie

```powershell
git init
git add .
git status
```

⚠️ **PARE E OLHE A LISTA DO `git status`.**
Se **`.env`** aparecer ali, **não commite** — significa que o `.gitignore` não está
sendo aplicado. Confira se o arquivo `.gitignore` está na raiz do projeto.
Só devem aparecer `.env.example`, o código, e os arquivos de configuração.

Estando certo:

```powershell
git commit -m "feat: DocSage v1 - RAG sobre documentos com FastAPI e pgvector"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/docsage.git
git push -u origin main
```

> Na autenticação, a **senha do GitHub não funciona**. Use um *Personal Access Token*
> (GitHub → Settings → Developer settings → Personal access tokens) como se fosse a senha,
> ou configure SSH.

### 6.4 Ative as proteções (recomendado)

No repositório: **Settings → Code security and analysis** → habilite:

- **Secret scanning** — detecta chaves vazadas
- **Push protection** — **bloqueia** o push se detectar uma chave
- **Dependabot alerts** — avisa de dependências vulneráveis

### Se você vazar um segredo sem querer

A ordem correta importa:

1. **Primeiro, revogue a chave** no console da Anthropic e gere outra. Assim que um
   segredo vai para o GitHub, considere-o comprometido — bots varrem commits públicos
   em minutos.
2. Só depois limpe o histórico (`git filter-repo` ou BFG).

Apagar do histórico sem revogar **não resolve nada**.

---

## Etapa 7 — Desenvolver com o Claude Code

```powershell
cd C:\Users\SEU_USUARIO\projetos\docsage
claude
```

Na primeira execução ele pede login. O `CLAUDE.md` na raiz é lido automaticamente —
ele já vai conhecer a arquitetura, as convenções e as regras de segurança do projeto.

Bons primeiros pedidos:

```
Leia o CLAUDE.md e me explique o fluxo do endpoint /ask, arquivo por arquivo.
```

```
Vamos implementar o item 1 da v2 do roadmap: autenticação JWT.
Antes de escrever código, me mostre o plano e os arquivos que serão alterados.
```

```
Rode os testes e o lint, e corrija o que estiver quebrado.
```

**Dicas de uso:**
- Peça o **plano antes do código** em mudanças grandes — é mais fácil corrigir um plano.
- Trabalhe em **uma tarefa por vez**; commite entre elas.
- Use `/clear` ao trocar de assunto, para limpar o contexto.
- Revise o que ele escreve. Você é o responsável pelo código — ele é o par, não o piloto.

---

## Ordem completa dos comandos (resumo)

```powershell
# --- No seu PC (uma vez) ---
cd C:\Users\SEU_USUARIO\projetos\docsage
copy .env.example .env
notepad .env                       # senha do banco (2 lugares) + chave da Anthropic

# --- Rodar ---
docker compose up -d --build
docker compose logs -f app
# testar em http://localhost:8080/docs

# --- GitHub ---
git init
git add .
git status                         # ⚠️ confirme que .env NÃO aparece
git commit -m "feat: DocSage v1"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/docsage.git
git push -u origin main

# --- Desenvolver ---
claude

# --- Deploy (veja docs/DEPLOY.md) ---
ssh docsage
git clone https://github.com/SEU_USUARIO/docsage.git && cd docsage
nano .env                          # .env de PRODUÇÃO, criado aqui (não vem do Git)
chmod 600 .env
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `docker: command not found` | Docker Desktop não instalado ou não está aberto |
| `error during connect` / daemon | Abra o Docker Desktop e espere ficar verde |
| `password authentication failed` | Senha diferente em `POSTGRES_PASSWORD` e `DATABASE_URL` |
| `type "vector" does not exist` | `docker compose down -v` e suba de novo |
| Erro 401 na `/ask` | Chave da Anthropic inválida ou sem créditos |
| `ModuleNotFoundError: app` | A pasta `app\` não foi extraída na raiz do projeto |
| Porta 8080 em uso | Mude `APP_PORT` no `.env` (ex.: `8081`) |
| Build muito lento | Normal na 1ª vez (PyTorch). Só acontece uma vez |
| `.env` aparece no `git status` | O `.gitignore` não está na raiz — não commite até resolver |
