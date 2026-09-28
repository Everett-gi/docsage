# Imagem da aplicação DocSage (Python 3.12 / FastAPI).
FROM python:3.12-slim
WORKDIR /app

# Não gera .pyc e não faz buffer de logs (melhor em container)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1) Dependências primeiro (aproveita o cache de build do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Código da aplicação
COPY . .

# 3) Usuário sem privilégios + pasta de cache do modelo com permissão correta.
#    (Criar a pasta com dono "app" ANTES do volume evita erro de permissão.)
RUN useradd --create-home app \
    && mkdir -p /home/app/.cache \
    && chown -R app:app /app /home/app/.cache
USER app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
