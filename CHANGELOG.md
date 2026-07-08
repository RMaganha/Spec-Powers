# Changelog do mss-spec

1 linha por mudança relevante; bump de versão no `plugin.json` a cada release.

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
