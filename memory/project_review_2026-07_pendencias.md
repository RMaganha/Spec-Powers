---
name: review-2026-07-pendencias
description: Review completo do kit (2026-07-08) — achados confirmados, correções APLICADAS na v0.2.0; resta o Dockerfile real do painel
metadata:
  type: project
---

Review do kit em 2026-07-08, validado ponto a ponto pelo owner. **Correções aplicadas na v0.2.0**
(ver CHANGELOG.md): núcleo 1/2/3/7 + decisão TLS = **opção (a)** (CA embutida via `COPY certs` +
`SSL_VERIFY=true`; `false` rebaixado a fallback de diagnóstico) + menores (compose base passa proxy
do .env pro build; office.yml com anchor; nota honesta Fernet; psycopg v3; Google Fonts documentado)
+ smoke-test do kit em `tests/test_smoke_kit.py` (baseline em docs/superpowers/PLANO-TESTE.md).

**PENDÊNCIAS que sobraram:**
- **O Dockerfile real do painel (Atas Teams) tem o MESMO bug da CA** — o template veio de lá; falta
  aplicar o `COPY certs` + revisar `SSL_VERIFY` no projeto do painel (caminho a confirmar com o owner).
- Extrair só a(s) CA(s) do FortiGate do bundle de 68 (baixa prioridade; hoje o bundle inteiro entra).
- Testar `${CLAUDE_PLUGIN_ROOT}` resolvendo via junction na prática (rodar /mss-spec:kickoff num
  projeto de teste) — o smoke só valida os alvos com a raiz resolvida.

**Núcleo de maior retorno (ordem acordada): 1 → 4 → 2 → 3 → 7**
1. **[grave] CA nunca entra na imagem** — `templates/docker/Dockerfile`: o `RUN if [ -f certs/corp-ca.pem ]` roda antes de qualquer `COPY` e não existe `COPY certs`; o bloco nunca executa. **Também vivo no Dockerfile real do painel** (o template veio de lá). A "camada 4" do AMBIENTE.md nunca funcionou; quem segura o TLS hoje é `SSL_VERIFY=false` + `--trusted-host` do pip. Fix: `COPY certs ./certs` antes do bloco.
2. **[decisão do owner — trava o resto] CA embutida × `SSL_VERIFY=false` se anulam** — escolher a estratégia canônica: (a) consertar a CA + `verify=true` no escritório (correto; inclinação do owner), ou (b) assumir `false` e apagar a história da CA. Manter os dois é o pior.
3. **kickoff pode destruir `.claude/settings.json`** — passo 2 manda "copiar" o template sobre arquivo existente; tem que ser merge explícito da chave `enabledPlugins`.
4. **link morto no INDEX no nível médio (padrão)** — `nova-feature` registra `specs/<arquivo>-design.md`, mas no médio não nasce doc de spec. Formato da linha deve variar por nível.
5. **regra fantasma "git-local-only"** — `commands/memory.md` cita a regra, mas ela só existe como memória do projeto Jeday; codificar no kit ou remover a citação.

**Válidos, menores:** office.yml × ".env nunca em código" (contradição real + NO_PROXY triplicado; MAS office.yml não é 100% redundante — `apt` no build precisa de `HTTP_PROXY` em build.args, que só ele passa; base passar `HTTP_PROXY: ${HTTP_PROXY:-}` restauraria a redundância total) · Fernet = ofuscação se chave e cifra estão no mesmo `.env` (nota honesta; `.encode()` estoura sem a var; `autocommit=True` merece comentário) · `psycopg2` vs `psycopg` (unificar; v3 como default) · corp-ca.pem = bundle inteiro (68 CAs; extrair só FortiGate — moot até consertar o item 1) · dados internos no kit (repo privado ao promover).

**Acréscimos do owner (o review não pegou):** `${CLAUDE_PLUGIN_ROOT}` nunca verificado via junction/skills-dir — deve ser o teste raiz do smoke · template editorial usa Google Fonts via CDN, contradizendo o "self-contained" (aceitar fallback ou embutir woff2 base64).

**Polimento acordado:** bump de versão + CHANGELOG (parado em 0.1.0) · smoke-test do próprio kit (todo caminho `${CLAUDE_PLUGIN_ROOT}/...` citado nos commands existe — dogfood; já houve regressão disso no ff4d384) · nit "falha silenciosamente avisando".

Relacionado: [[memoria-local-ao-repo]]
