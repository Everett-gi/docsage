-- Executado automaticamente pelo PostgreSQL na PRIMEIRA vez que o banco é criado
-- (montado em /docker-entrypoint-initdb.d pelo docker-compose).
-- Habilita a extensão pgvector, que adiciona o tipo "vector" e a busca por similaridade.
CREATE EXTENSION IF NOT EXISTS vector;
