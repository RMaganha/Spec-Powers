---
description: Gera o boilerplate de conexão a banco no padrão MSIG (SQL Server via pyodbc, ou Postgres)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar o **módulo de conexão** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` para hosts e convenções. Mostre o código e **confirme antes de gravar**.

1. Pergunte: **SQL Server ou Postgres?**
2. **Postgres**: gere um `get_connection` usando `psycopg` (v3 — padrão pra projeto novo; `psycopg2` só se o projeto já o usa), lendo `PG_CONN_STR` do ambiente; host conforme `docs/AMBIENTE.md` (`postgres-db` na rede Docker; `mitiai-poc.msig.com.br` fora; `localhost`/`host.docker.internal` em dev). Acrescente `PG_CONN_STR=postgresql://<usuario>:<senha>@<host>:5432/miti_ai_<projeto>` no `.env.example`.
3. **SQL Server**: pergunte **modo simples ou Fernet?**
   - Simples: `get_connection_<banco>()` com `pyodbc`, lendo `SQL_CONNECTION_STRING_<BANCO>` do ambiente; se for Streamlit e reutilizar conexão, `@st.cache_resource`. `.env.example` recebe a connection string com `Driver={ODBC Driver 17 for SQL Server};Server=MSSQLD0;Database=<banco>;UID=;PWD=;TrustServerCertificate=yes;`.
   - Fernet: `get_connection()` que descriptografa `ENCRYPTED_CONN` com `ENCRYPTION_KEY` (lib `cryptography`) e conecta via `pyodbc` (`autocommit=True`). `.env.example` recebe `ENCRYPTION_KEY=` e `ENCRYPTED_CONN=`.
4. Se container precisar resolver `MSSQLD0`, lembre de adicionar `extra_hosts: ["MSSQLD0:10.170.210.36"]` no `docker-compose.yml`.
5. Nunca gere `.env` real nem valores de credencial — só `.env.example` com placeholders.
