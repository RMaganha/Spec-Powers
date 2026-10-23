---
paths:
  - "**/*.sql"
  - "sql/**"
  - "persistencia/**"
---

# Banco e RAG de produção

<!-- Movido do CLAUDE.md em 2026-09-23 (teto de 10 KB; F-029/F-030 do kit): texto VERBATIM. A regra continua valendo — o CLAUDE.md mantém a frase-chave e aponta pra cá. -->

- **Banco:** PostgreSQL com **pgvector** + `pg_trgm` + FTS (base `miti_ai_chatbot`; roda no host, fora do compose). Conexão por `PG_CONN_STR`. **No caminho do turno** (busca, releitura da Q&A, chave, tabela de atividades, histórico, gravação do log) é **`with pg.conexao() as conn:`** de `persistencia/agent_bot_pg.py` — o pool de conexões, aberto na subida (desde 2026-10-06, V14.6/V14.7; abrir conexão custava às vezes ~3 s em produção) — **nunca** `psycopg2.connect` inline ali; leitura nova do turno entra no pool. Fora do turno (leituras próprias dos painéis, scripts de `sql/` e `_investigacao/`) segue `psycopg2.connect` inline. Spec: `docs/specs/pool-conexoes-postgres.md`. Sem `utils/get_connection.py` (regra de isolamento do projeto: o pool é módulo **do** projeto). DDL versionada em `sql/NN-*.sql`, rodada **FORA** do app; o esquema base (`rag_documents`, `historico_chat`, `rag_configuracoes`) vem do Sistema A. Credenciais só em `.env` (nunca commit/hardcode).

8. **Nunca tocar o que é do RAG em produção.** As chaves `v220_*` de `rag_configuracoes` são do `responder_backend_quadrant` (Sistema A) — o `agent_bot` tem chaves **próprias** `agent_v220_*`. Mexer nas `v220_*` afeta produção do RAG e está **proibido**. Na mesma linha: a tabela `rag_documents` é do Sistema A — este projeto lê o espelho `rag_documents_chat`, alimentado por trigger.
