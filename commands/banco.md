---
description: Gera o boilerplate de conexão a banco no padrão MSIG (SQL Server multi-ambiente via get_connection.py, ou Postgres)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar o **módulo de conexão** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` para hosts e convenções. Mostre o código e **confirme antes de gravar**.

1. Pergunte: **SQL Server ou Postgres?**
2. **SQL Server — padrão canônico da casa: `get_connection.py` multi-ambiente** (referência real: `C:\Ronaldo\_Mitsui\Python\Transportes\V2\get_connection.py`):
   - Copie `${CLAUDE_PLUGIN_ROOT}/templates/get_connection.py` → `utils/get_connection.py` e troque os `<BASE>`/`<base>` pela(s) base(s) do projeto.
   - **Credencial NUNCA no `.env`** (regra do owner: "no `.env` no máximo o ambiente"). Cada base tem par Fernet KEY/CIPHERTEXT **por ambiente** (DEV/D0 · HML/HI · PROD) embutido no arquivo.
   - **Preencher os pares**: base que outro projeto MSIG já usa (SSC, MS10=`tkgs_corp`, TRP, OnBase) → os pares prontos estão no arquivo de referência do Transportes V2; **quem copia credencial entre projetos é o owner** — aponte o caminho e as constantes, não cole você mesmo. Base nova → gere o par **localmente por script** (snippet no docstring do template), sem ecoar segredo no chat.
   - `.env.example` recebe só: `CONEXAO_PRD=` (vazio = DEV; qualquer valor = PROD) e, se o projeto usa, `API_ENV=`.
   - `requirements.txt`: garanta `pyodbc`, `cryptography`, `python-dotenv`.
   - **`Server=` real**: confirme host/porta decriptando/lendo o projeto de referência — fatos verificados (2026-07-08): SSC dev = `10.170.210.36,1435`; `tkgs_corp` (MS10) e `MSS_TRP` dev = `10.170.210.36` sem porta explícita; SSC prod = `10.170.210.48`. Não assuma `MSSQLD0:1433`; porta errada = erro 53/timeout. Fora da rede corporativa nada responde — erro de rede não é credencial.
3. **Postgres**: gere um `get_connection` usando `psycopg` (v3 — padrão pra projeto novo; `psycopg2` só se o projeto já o usa), lendo `PG_CONN_STR` do ambiente; host conforme `docs/AMBIENTE.md` (`postgres-db` na rede Docker; `mitiai-poc.msig.com.br` fora; `localhost`/`host.docker.internal` em dev). Acrescente `PG_CONN_STR=postgresql://<usuario>:<senha>@<host>:5432/miti_ai_<projeto>` no `.env.example`.
4. Se container precisar resolver `MSSQLD0`, lembre de adicionar `extra_hosts: ["MSSQLD0:10.170.210.36"]` no `docker-compose.yml`.
5. Nunca gere `.env` real com credencial, nunca ecoe conn string decriptada no chat (use `mask_password`), e nunca deixe credencial em texto plano em lugar nenhum do repo.
