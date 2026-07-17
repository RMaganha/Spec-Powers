---
description: Gera o boilerplate de conexão a banco no padrão MSIG (SQL Server multi-ambiente via get_connection.py, ou Postgres)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar o **módulo de conexão** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` para hosts e convenções. Mostre o código e **confirme antes de gravar**.

1. Pergunte: **SQL Server ou Postgres?**
2. **SQL Server — escolha como guardar a credencial** (recomendo **variável de ambiente** pra projeto novo, que quase sempre é web app Azure):
   - **(a) Variável de ambiente [RECOMENDADO]** — a conn string vive numa variável: `.env` em dev (gitignored) → **Azure App Settings** em prod; o `get_connection.py` lê via `os.getenv` (ex.: `SQL_CONN_STR`). Segredo **nunca** no código nem no commit. `.env.example` traz só a chave vazia (`SQL_CONN_STR=`). É o mais seguro e o padrão de web app Azure — **não** precisa de Fernet nem de `cryptography`.
   - **(b) Fernet no código [continuidade]** — par Fernet KEY/CIPHERTEXT por base/ambiente embutido no `get_connection.py` (padrão do Transportes V2; copie `${CLAUDE_PLUGIN_ROOT}/templates/get_connection.py` → `utils/get_connection.py`). **É só ofuscação** (a chave viaja no repo) — use pra **continuidade** com projetos que já usam, não como segurança nova. `.env` só com seletores, **comentário em linha própria** (inline o Docker Compose quebra): `CONEXAO_SQL=D0` (D0|HML|PRD) + `CONEXAO_SQL_PORTA=` (opcional). Base MSIG conhecida (SSC, MS10=`tkgs_corp`, TRP, OnBase) → aponte as constantes no Transportes V2 pro owner colar (copiar credencial entre projetos é decisão DELE); base nova → gere o par localmente por script, sem ecoar segredo. Requer `cryptography`.
   - `requirements.txt`: garanta `pyodbc`, `python-dotenv` (+ `cryptography` só no modo Fernet).
   - **`Server=` real** (vale nos dois modos): confirme host/porta pelo projeto de referência — fatos verificados (2026-07-08): SSC dev = `10.170.210.36,1435`; `tkgs_corp` (MS10) e `MSS_TRP` dev = `10.170.210.36` sem porta explícita; SSC prod = `10.170.210.48`. Não assuma `MSSQLD0:1433`; porta errada = erro 53/timeout. Fora da rede corporativa nada responde — erro de rede não é credencial.
3. **Postgres**: gere um `get_connection` usando `psycopg` (v3 — padrão pra projeto novo; `psycopg2` só se o projeto já o usa), lendo `PG_CONN_STR` do ambiente; host conforme `docs/AMBIENTE.md` (`postgres-db` na rede Docker; `mitiai-poc.msig.com.br` fora; `localhost`/`host.docker.internal` em dev). Acrescente `PG_CONN_STR=postgresql://<usuario>:<senha>@<host>:5432/miti_ai_<projeto>` no `.env.example`.
4. Se container precisar resolver `MSSQLD0`, lembre de adicionar `extra_hosts: ["MSSQLD0:10.170.210.36"]` no `docker-compose.yml`.
5. Nunca gere `.env` real com credencial, nunca ecoe conn string decriptada no chat (use `mask_password`), e nunca deixe credencial em texto plano em lugar nenhum do repo.
6. **Log (protocolo de geração de arquivos):** o módulo de conexão é justamente uma camada que se beneficia de log (banco). Antes de gravar, aplique o protocolo do `/mss-spec:log`: se o projeto já tem o padrão de log montado (`config/logging.py`), **pergunte se quer instrumentar** o `get_connection.py` com `logger = logging.getLogger(__name__)` (o template já loga a conn string mascarada via `mask_password`). Se o padrão ainda não existe, ofereça rodar o `/mss-spec:log` primeiro. Não instrumente sem o OK.
