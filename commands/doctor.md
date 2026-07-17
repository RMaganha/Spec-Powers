---
description: Pré-vôo do ambiente MSIG — checa resolução do plugin, proxy, CA, ODBC, rede docker, .env e superpowers e dá um veredito ✓/✗ (só reporta, não conserta)
argument-hint: ""
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Pré-vôo do ambiente: confere os pré-requisitos do ambiente MSIG e reporta **✓/✗** — pra pegar erro cedo, não no build. **Só reporta**: não conserta nada e não bloqueia.

Leia os valores esperados de `docs/AMBIENTE.md` (IP do proxy, nome da rede, host do SQL…) — **não** hardcode. Rode **só os checks que se aplicam** ao projeto (detecte pelos arquivos presentes); um check que não se aplica é **pulado**, não vira ✗.

Checks:
1. **mss-spec acha os próprios templates?** (sempre, primeiro — é o alicerce) — `${CLAUDE_PLUGIN_ROOT}/templates/` existe e tem os moldes? Se a variável não resolveu, procure nos locais padrão do Code: `~/.claude/plugins/cache/*/mss-spec/*/templates/` (via marketplace) ou `~/.claude/skills/mss-spec/templates/` (auto-load). **Não achou em nenhum → ✗ com aviso claro**: o plugin não está resolvendo; registre/instale (ver instalação). Se este falha, os comandos que copiam template (kickoff, ambiente, banco, frontend, seguranca) também falham.
2. **superpowers habilitado** (sempre) — `superpowers@claude-plugins-official` está em `enabledPlugins` do `.claude/settings.json` (ou instalado)?
3. **`.env` × `.env.example`** (se existe `.env.example`) — o `.env` existe e tem todas as **chaves** do `.env.example`? (só as chaves; **nunca** ecoe valores/segredo.)
4. **Proxy corporativo alcançável** (se o projeto usa rede corporativa) — teste o proxy do `docs/AMBIENTE.md` (ex.: `curl -x <proxy> -sI https://pypi.org` ou `Test-NetConnection <host> -Port <porta>`).
5. **`certs/corp-ca.pem` presente** (se tem Docker) — o arquivo existe no projeto?
6. **Rede `mitiai_network` existe** (se tem `docker-compose.yml`) — `docker network ls` mostra a rede do `AMBIENTE.md`? (se o Docker não estiver rodando, marque "a verificar", não ✗.)
7. **ODBC Driver 17** (se o projeto usa SQL Server / `pyodbc`) — `python -c "import pyodbc; print(pyodbc.drivers())"` lista `ODBC Driver 17 for SQL Server`?

Saída: uma linha por check aplicável com **✓** ou **✗** (com o porquê no ✗) e um **veredito** final de uma linha (ex.: "tudo pronto" / "2 pendências: …"). Não conserte; num ✗, aponte o caminho provável (ex.: fora da VPN, CA desatualizada — ver `docs/AMBIENTE.md`).
