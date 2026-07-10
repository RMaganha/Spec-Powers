# Changelog do mss-spec

1 linha por mudança relevante; bump de versão no `plugin.json` a cada release.

## 0.5.0 — 2026-07-08 (deriva MSS-SSC → plugin)
- fix: `templates/docker/Dockerfile` ganha a receita do **ODBC Driver 17** (msodbcsql17, repo Microsoft debian/12) — furo real: projetos SQL nasciam sem driver e o `pyodbc` não conectava. Portado do canário MSS-SSC
- change: base `python:3.14-slim` → **`3.12-slim`** (padrão da casa: Transportes/jedai/MSS-SSC; casa com o repo ODBC debian/12)
- change: mecanismo de proxy alinhado ao MSS-SSC — `ARG HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` predefinidos (pip/apt usam sozinhos), no lugar do `PIP_PROXY` custom; base compose sem build.args, `office.yml` injeta o proxy do `.env` (sem IP hardcoded — fecha a contradição do review)
- docs: AMBIENTE §2, ambiente.md e COMO-FUNCIONA.html atualizados (3.12, novo fluxo de proxy)

## 0.4.0 — 2026-07-08
- feat: `templates/get_connection.py` — padrão canônico de conexão SQL Server multi-ambiente (Transportes V2): par Fernet KEY/CIPHERTEXT por base+ambiente NO CÓDIGO, `.env` só com `CONEXAO_PRD`/`API_ENV`; helpers mask_password/Encrypt/timeout/logging
- fix: banco.md e AMBIENTE §4 reescritos em torno do padrão canônico — as variantes "conn string no .env" e "Fernet com chave no .env" saem (feedback do owner: credencial NUNCA no .env, "no máximo o ambiente"); pares prontos das bases corporativas apontados no Transportes V2 (copiar entre projetos = decisão do owner)
- docs: fatos de porta verificados por decriptação local — SSC dev `10.170.210.36,1435`, tkgs_corp/MSS_TRP dev sem porta explícita, SSC prod `10.170.210.48`; instâncias 1434/1435 (owner), 1434 `<a confirmar>`

## 0.3.2 — 2026-07-08
- feat: regra de credencial no `/mss-spec:banco` + AMBIENTE §4 + catálogo de precedentes — antes de pedir usuário/senha ao owner, reusar o `.env` local de projeto precedente que já conecta (jedai), ajustando só `Database=`; nunca ecoar/commitar
- fix: AMBIENTE §4 não afirma mais "porta 1433" — porta real verificada no jedai é `10.170.210.36,1435`; confirmar sempre com o `.env` que funciona (anti-fabricação)

## 0.3.1 — 2026-07-08
- fix: ESTRUTURA.md alinhado ao layout REAL consolidado (MSS-SSC/estilo jedai): camadas na RAIZ (`main.py` + config/models/services/routers/utils) e `pages/` fora de `templates/` via ChoiceLoader — não mais pacote `app/`; Dockerfile (COPYs por camada + `uvicorn main:app`), regra do CLAUDE.md e ambiente.md (`config/settings.py`) acompanham

## 0.3.0 — 2026-07-08
- feat: `templates/ESTRUTURA.md` (estrutura de pastas em camadas: app/{config,models,services,routers,utils} + templates/static/tests/sql) — kickoff copia pra `docs/ESTRUTURA.md` e o CLAUDE.md ganha regra crítica; nasceu de projeto novo que saiu com tudo achatado em `app/`

## 0.2.0 — 2026-07-08 (rodada do review)
- fix: CA corporativa agora entra de fato na imagem (`COPY certs` faltava — o `RUN if` nunca achava o arquivo)
- feat: estratégia TLS canônica = CA embutida + `SSL_VERIFY=true` (false rebaixado a fallback de diagnóstico) — docs alinhadas (ambiente, AMBIENTE.md, HTML)
- fix: kickoff faz **merge** no `.claude/settings.json` existente (cópia por cima apagava permissões/hooks)
- fix: linha do INDEX.md varia por nível de cerimônia (no médio não nasce spec — nunca linkar arquivo inexistente)
- feat: regra "Git local-only" codificada no templates/CLAUDE.md (commits locais, stage nominal, push só a pedido); memory.md aponta pra ela
- feat: compose base repassa `HTTP(S)_PROXY`/`NO_PROXY` do `.env` também pro build (cobre apt); office.yml deduplicado via anchor YAML
- docs: nota honesta no Fernet (chave no mesmo `.env` = ofuscação; código com erro claro e aviso de `autocommit`)
- docs: Postgres padrão = `psycopg` v3; nit do `docker network create`; exceção Google Fonts documentada no /documentacao
- test: smoke-test do kit (`tests/test_smoke_kit.py`) — todo caminho citado nos commands existe, JSONs válidos, frontmatter presente

## 0.1.0 — 2026-07-02 a 2026-07-07
- Kit inicial: plugin + marketplace local, 9 comandos (kickoff, nova-feature, ambiente, banco, precedentes, plano-teste, modo, documentacao, memory), templates (CLAUDE/AMBIENTE/FRONTEND/Docker/settings/gitignore/doc HTML), skill precedentes-msig, memória versionada no repo.
