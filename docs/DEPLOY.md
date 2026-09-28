# Deploy do DocSage na Oracle Cloud (Always Free)

Guia completo, do zero ao HTTPS, para colocar a aplicação no ar sem custo.

> **Oracle Cloud ≠ AWS.** São empresas concorrentes. Usamos a **Oracle Cloud
> Infrastructure (OCI)** porque o *Always Free* dela é **permanente**, enquanto o Free
> Tier da AWS expira em 12 meses e passa a cobrar.

**Tempo estimado:** 1h a 2h na primeira vez.
**Custo:** R$ 0,00 (exceto centavos na API da Anthropic, por uso).

---

## Índice

1. [Como a arquitetura funciona](#1-como-a-arquitetura-funciona)
2. [Criar a conta na Oracle Cloud](#2-criar-a-conta-na-oracle-cloud)
3. [Gerar a chave SSH no Windows](#3-gerar-a-chave-ssh-no-windows)
4. [Criar a instância (a VM)](#4-criar-a-instância-a-vm)
5. [Abrir as portas na Security List](#5-abrir-as-portas-na-security-list)
6. [Primeira conexão SSH](#6-primeira-conexão-ssh)
7. [Liberar o firewall do sistema](#7-liberar-o-firewall-do-sistema-a-pegadinha-clássica) ⚠️
8. [Endurecer o servidor](#8-endurecer-o-servidor-hardening)
9. [Instalar o Docker](#9-instalar-o-docker)
10. [Criar o domínio no DuckDNS](#10-criar-o-domínio-grátis-no-duckdns)
11. [Publicar a aplicação](#11-publicar-a-aplicação)
12. [Verificar](#12-verificar-se-está-tudo-certo)
13. [Manutenção](#13-manutenção-do-dia-a-dia)
14. [Solução de problemas](#14-solução-de-problemas)

---

## 1. Como a arquitetura funciona

```
   Internet
      |
      v  (portas 80 e 443)
  +---------+
  |  Caddy  |  Recebe a requisição, cuida do HTTPS (certificado gratuito
  +---------+  do Let's Encrypt, renovado automaticamente)
      |
      v  (rede interna do Docker — invisível para a internet)
  +---------+
  |   app   |  FastAPI (DocSage), porta 8080
  +---------+
      |
      v  (rede interna do Docker)
  +---------+
  |   db    |  PostgreSQL + pgvector
  +---------+
```

**A ideia central:** só o Caddy fica exposto à internet. A aplicação e o banco vivem numa
rede interna do Docker — não há como acessá-los de fora, mesmo sabendo o IP. É por isso
que o `docker-compose.prod.yml` não declara `ports` nos serviços `app` e `db`.

---

## 2. Criar a conta na Oracle Cloud

1. Acesse **https://www.oracle.com/cloud/free/** e clique em *Start for free*.
2. Preencha os dados. Use um e-mail que você acesse (haverá verificação).
3. **Escolha a Home Region com cuidado — ela NÃO pode ser alterada depois.**
   Para o Brasil, prefira `Brazil East (São Paulo)` ou `Brazil Southeast (Vinhedo)`.
   Se você receber erro de capacidade mais tarde (comum), regiões dos EUA costumam ter
   mais disponibilidade de ARM. Escolher a região é o passo mais irreversível do processo.
4. **Cartão de crédito:** é exigido apenas para verificação de identidade. A Oracle faz
   uma pré-autorização de aproximadamente US$ 1,00, que é estornada. Enquanto a conta
   estiver como *Always Free*, não há cobrança.
5. Confirme o e-mail e aguarde o provisionamento (leva de alguns minutos a algumas horas).

> **Fique atento:** após 30 dias, o período de trial com créditos expira e a conta vira
> *Always Free* automaticamente. Recursos que estejam fora do Always Free são desligados,
> mas os que estão dentro (nossa VM) continuam funcionando para sempre.

---

## 3. Gerar a chave SSH no Windows

A chave SSH é o seu "crachá" para entrar no servidor: uma chave **privada** (fica no seu
PC, jamais compartilhe) e uma **pública** (fica no servidor). Isso é bem mais seguro que senha.

Abra o **PowerShell** e execute:

```powershell
# Cria a pasta padrão de chaves SSH (ignore o erro se ela já existir)
mkdir $env:USERPROFILE\.ssh -Force

# Gera o par de chaves (ed25519 é o algoritmo moderno recomendado)
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\oracle_docsage -C "docsage"
```

Ele vai pedir uma *passphrase*. **Use uma** — é uma senha extra que protege a chave caso
alguém copie o arquivo do seu PC.

Isso cria dois arquivos em `C:\Users\SEU_USUARIO\.ssh\`:

| Arquivo | O que é |
|---|---|
| `oracle_docsage` | chave **privada** — nunca envie a ninguém, nunca commite |
| `oracle_docsage.pub` | chave **pública** — esta você cola na Oracle |

Copie o conteúdo da chave pública para a área de transferência:

```powershell
Get-Content $env:USERPROFILE\.ssh\oracle_docsage.pub | Set-Clipboard
```

---

## 4. Criar a instância (a VM)

No console da Oracle: menu **☰ → Compute → Instances → Create instance**.

**Nome:** `docsage-server`

**Image and shape** → clique em *Edit*:

- **Image:** `Canonical Ubuntu 24.04`
- **Shape:** clique em *Change shape* → aba **Ampere** → `VM.Standard.A1.Flex`
  - **OCPUs:** `2`
  - **Memory (GB):** `12`

> Esses são os limites do Always Free desde a redução de junho/2026. A arquitetura é
> **ARM (aarch64)** — funciona perfeitamente com o nosso projeto, pois todas as imagens
> Docker que usamos têm versão ARM.

**Networking:** deixe o padrão (ele cria uma VCN nova). Garanta que
**Assign a public IPv4 address** esteja marcado — sem IP público, o servidor não é
acessível pela internet.

**Add SSH keys:** selecione *Paste public keys* e cole o conteúdo copiado no passo 3.

**Boot volume:** o padrão (~47 GB) já basta. O Always Free dá até 200 GB no total.

Clique em **Create**. Em 1 a 2 minutos o status fica **RUNNING**.
**Anote o `Public IP address`** que aparece na tela.

### Se der "Out of capacity"

É o erro mais comum do free tier ARM — significa que a região está sem estoque naquele
momento, não que você fez algo errado. Opções:

- Tente novamente em outro horário (madrugada costuma funcionar melhor).
- Tente outro *Availability Domain* (AD-1, AD-2, AD-3), se a sua região tiver mais de um.
- Como alternativa imediata, use a shape `VM.Standard.E2.1.Micro` (x86, 1 GB de RAM).
  **Atenção:** 1 GB de RAM é insuficiente para o modelo de embeddings deste projeto —
  serve para testar o acesso, mas insista no ARM para rodar o DocSage.

---

## 5. Abrir as portas na Security List

A Oracle tem um firewall próprio, na frente da VM. Por padrão, só a porta 22 (SSH) é
liberada. Precisamos abrir a 80 e a 443.

1. Na página da instância, clique no nome da **Subnet**.
2. Clique na **Security List** (geralmente `Default Security List for ...`).
3. Clique em **Add Ingress Rules** e crie **duas** regras:

| Campo | Regra HTTP | Regra HTTPS |
|---|---|---|
| Stateless | desmarcado | desmarcado |
| Source Type | CIDR | CIDR |
| Source CIDR | `0.0.0.0/0` | `0.0.0.0/0` |
| IP Protocol | TCP | TCP |
| Destination Port Range | `80` | `443` |

`0.0.0.0/0` significa "qualquer origem da internet" — correto para um site público.

---

## 6. Primeira conexão SSH

No PowerShell, troque `SEU_IP` pelo IP público anotado:

```powershell
ssh -i $env:USERPROFILE\.ssh\oracle_docsage ubuntu@SEU_IP
```

Na primeira vez ele pergunta sobre a autenticidade do host — digite `yes`.
O usuário é `ubuntu` (padrão das imagens Ubuntu da Oracle).

**Dica:** para não digitar isso toda vez, crie o arquivo `C:\Users\SEU_USUARIO\.ssh\config`:

```
Host docsage
    HostName SEU_IP
    User ubuntu
    IdentityFile ~/.ssh/oracle_docsage
```

Daí em diante, basta: `ssh docsage`

---

## 7. Liberar o firewall do sistema (a pegadinha clássica) ⚠️

**Este é o passo em que quase todo mundo trava.** As imagens Ubuntu da Oracle vêm com
regras `iptables` que bloqueiam tudo, menos SSH — **mesmo depois** de você abrir as portas
na Security List. São dois firewalls em série: o da nuvem (passo 5) e o do sistema (este).

Primeiro, veja as regras atuais com numeração:

```bash
sudo iptables -L INPUT --line-numbers -n
```

Você verá algo assim, com uma regra `REJECT` no fim:

```
num  target     prot opt source     destination
1    ACCEPT     udp  --  0.0.0.0/0  ...
2    ACCEPT     tcp  --  0.0.0.0/0  ... tcp dpt:22
...
6    REJECT     all  --  0.0.0.0/0  0.0.0.0/0  reject-with icmp-host-prohibited
```

**A ordem importa:** o iptables lê de cima para baixo e para na primeira regra que casar.
As novas regras precisam entrar **antes** do `REJECT`. Se o `REJECT` estiver na linha 6,
inserimos na posição 6 (empurrando-o para baixo):

```bash
# Ajuste o "6" para o número da linha do REJECT que VOCÊ viu acima
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# Confirme que as duas regras estão ANTES do REJECT
sudo iptables -L INPUT --line-numbers -n

# Torna as regras permanentes (senão elas somem no reboot)
sudo netfilter-persistent save
```

---

## 8. Endurecer o servidor (hardening)

```bash
# Atualiza o sistema
sudo apt update && sudo apt upgrade -y

# Instala o fail2ban: bane IPs que tentam adivinhar a senha do SSH
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
```

Desabilite o login por senha (só a sua chave SSH funcionará):

```bash
sudo nano /etc/ssh/sshd_config
```

Garanta que estas linhas estejam assim (remova o `#` do início, se houver):

```
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
```

Salve (`Ctrl+O`, `Enter`) e saia (`Ctrl+X`), depois recarregue o SSH:

```bash
sudo systemctl restart ssh
```

> **Não feche esta sessão ainda.** Abra um segundo PowerShell e teste o login. Se
> funcionar, está tudo certo. Se você errar algo aqui e fechar a única sessão, perde o
> acesso ao servidor.

**Swap (recomendado):** dá um respiro de memória durante o build do Docker, que é pesado.

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 9. Instalar o Docker

```bash
# Dependências e chave oficial do repositório Docker
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Adiciona o repositório (detecta ARM/x86 automaticamente)
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instala
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Permite usar docker sem sudo
sudo usermod -aG docker $USER
```

**Saia e entre de novo no SSH** (`exit`, depois `ssh docsage`) para o grupo valer. Teste:

```bash
docker run --rm hello-world
docker compose version
```

---

## 10. Criar o domínio grátis no DuckDNS

O Let's Encrypt não emite certificado para IP puro — precisamos de um domínio.

1. Acesse **https://www.duckdns.org** e faça login (Google/GitHub).
2. Em *domains*, digite um nome (ex.: `docsage-gil`) e clique em **add domain**.
3. No campo `current ip`, coloque o **IP público da sua VM** e clique em **update ip**.
4. Seu domínio será: `docsage-gil.duckdns.org`

Confirme que o DNS propagou (rode no servidor):

```bash
# Deve retornar o IP da sua VM
dig +short docsage-gil.duckdns.org
```

> Se não retornar nada, espere 2 a 5 minutos e tente de novo. **Não avance enquanto o DNS
> não estiver resolvendo** — o Let's Encrypt vai falhar e você pode bater no limite de
> tentativas (5 falhas por hora).

---

## 11. Publicar a aplicação

### 11.1 Clonar o repositório

```bash
cd ~
git clone https://github.com/Everett-gi/docsage.git
cd docsage
```

> Se o repositório for privado, gere uma chave SSH no servidor (`ssh-keygen -t ed25519`),
> adicione a chave pública em *GitHub → Settings → SSH and GPG keys*, e clone via SSH:
>
> ```bash
> git clone git@github.com:Everett-gi/docsage.git
> cd docsage
> ```

### 11.2 Criar o `.env` de produção

Este é o ponto-chave de segurança: **o `.env` não vem do Git**. Você o cria aqui, no
servidor, com valores diferentes dos que usa no seu PC.

```bash
# Gere uma senha forte para o banco e copie a saída
openssl rand -base64 24

nano .env
```

Cole o conteúdo abaixo, substituindo os valores marcados:

```bash
POSTGRES_DB=docsage
POSTGRES_USER=docsage
POSTGRES_PASSWORD=COLE_A_SENHA_GERADA_ACIMA
DATABASE_URL=postgresql+psycopg://docsage:COLE_A_MESMA_SENHA@db:5432/docsage

APP_ENV=production
APP_PORT=8080

EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIM=384

ANTHROPIC_API_KEY=sk-ant-SUA_CHAVE_REAL
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

MAX_UPLOAD_MB=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
TOP_K=5

DOMAIN=docsage-gil.duckdns.org
ACME_EMAIL=seu-email@exemplo.com
```

Proteja o arquivo (só o seu usuário pode ler):

```bash
chmod 600 .env
```

### 11.3 Subir tudo

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

> **A primeira vez demora bastante (10 a 25 min no ARM).** O build instala o PyTorch, que
> é uma dependência grande do modelo de embeddings. Isso é normal e acontece só uma vez —
> as próximas subidas aproveitam o cache.

Acompanhe:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

Aguarde até ver o Caddy obter o certificado e o Uvicorn indicar `Application startup complete`.
`Ctrl+C` sai do log sem derrubar nada.

---

## 12. Verificar se está tudo certo

```bash
# Todos os serviços devem estar "Up"
docker compose -f docker-compose.prod.yml ps

# Teste local, por dentro do servidor
curl -k https://localhost/health
```

Agora, **do seu navegador**:

- `https://docsage-gil.duckdns.org/health` → deve mostrar `{"status":"ok"}`
- `https://docsage-gil.duckdns.org/docs` → a interface Swagger

O cadeado deve aparecer no navegador, sem aviso de segurança. Se apareceu: **está no ar.** 🎉

Teste o fluxo completo pelo Swagger:
1. `POST /documents` → *Try it out* → escolha um PDF → *Execute*
2. `POST /ask` → *Try it out* → `{"question": "Do que trata o documento?"}` → *Execute*

---

## 13. Manutenção do dia a dia

### Atualizar a aplicação (após um push no GitHub)

```bash
ssh docsage
cd ~/docsage
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Comandos úteis

```bash
# Ver logs só da aplicação
docker compose -f docker-compose.prod.yml logs -f app

# Reiniciar
docker compose -f docker-compose.prod.yml restart

# Parar (mantém os dados)
docker compose -f docker-compose.prod.yml down

# Uso de recursos
docker stats

# Liberar espaço (imagens antigas)
docker system prune -af
```

### Backup do banco

```bash
# Gera um dump com a data no nome
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U docsage docsage | gzip > ~/backup-docsage-$(date +%F).sql.gz
```

Para automatizar (todo dia às 3h), rode `crontab -e` e adicione:

```
0 3 * * * cd ~/docsage && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U docsage docsage | gzip > ~/backups/docsage-$(date +\%F).sql.gz
```

Crie a pasta antes: `mkdir -p ~/backups`.
Backup no mesmo servidor protege contra erro humano, mas não contra perda da VM —
o ideal é enviar para um storage externo (como você já faz com o Cloudflare R2).

### Manter a VM ativa

A Oracle pode recuperar instâncias Always Free consideradas **ociosas** (baixo uso de CPU
por 7 dias seguidos). Uma aplicação real com tráfego costuma bastar. Se seu uso for
esporádico, um cron leve resolve.

---

## 14. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| SSH não conecta | Instância ainda subindo, ou IP errado | Aguarde 2 min; confira o IP público no console |
| `Permission denied (publickey)` | Chave ou usuário errado | Use `-i` apontando a chave privada e o usuário `ubuntu` |
| Site não abre, mas SSH funciona | **Firewall do sistema** | Refaça o [passo 7](#7-liberar-o-firewall-do-sistema-a-pegadinha-clássica) — é a causa mais comum |
| Site não abre e o passo 7 está ok | Security List | Confira as regras de ingress do [passo 5](#5-abrir-as-portas-na-security-list) |
| Caddy não obtém certificado | DNS não propagou, ou porta 80 fechada | `dig +short SEU_DOMINIO` deve retornar o IP da VM; a 80 precisa estar aberta |
| `too many failed authorizations` | Muitas tentativas do Let's Encrypt | Limite de 5 falhas/hora. Corrija o DNS e aguarde 1h |
| Build morre / "Killed" | Falta de memória | Adicione swap ([passo 8](#8-endurecer-o-servidor-hardening)) |
| App reinicia em loop | Erro de configuração | `docker compose -f docker-compose.prod.yml logs app` |
| `password authentication failed` | Senha divergente no `.env` | `POSTGRES_PASSWORD` e a senha dentro de `DATABASE_URL` devem ser idênticas |
| `type "vector" does not exist` | `init.sql` não rodou | O volume já existia. `docker compose -f docker-compose.prod.yml down -v` e suba de novo (⚠️ apaga os dados) |
| `Out of capacity` ao criar a VM | Região sem estoque ARM | Tente em outro horário ou outro AD ([passo 4](#4-criar-a-instância-a-vm)) |

### Checklist rápido quando o site não abre

```bash
# 1) Os containers estão de pé?
docker compose -f docker-compose.prod.yml ps

# 2) A aplicação responde por dentro?
docker compose -f docker-compose.prod.yml exec caddy wget -qO- http://app:8080/health

# 3) O sistema está escutando nas portas 80/443?
sudo ss -tlnp | grep -E ':80|:443'

# 4) O firewall do sistema está liberado?
sudo iptables -L INPUT --line-numbers -n

# 5) O DNS aponta para esta VM?
dig +short SEU_DOMINIO && curl -s ifconfig.me
```
