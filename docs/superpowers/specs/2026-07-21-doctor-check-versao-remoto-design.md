# doctor — check de versão do plugin contra o remoto (design)

Data: 2026-07-21 · feature do próprio kit mss-spec.

## Estado atual
O `/mss-spec:doctor` ganha um **último check "versão do kit"**: compara a versão **instalada** do plugin com a **publicada** no remoto git e reporta o veredito — pra o owner/time saber, de qualquer projeto, se o kit instalado (global, no `~/.claude`) está atrás do que foi publicado. Antes desta feature o doctor declarava explicitamente que **não** comparava versão; agora compara, mantendo a filosofia do doctor de **só reportar** (não roda `marketplace update`, não bloqueia).

**Como funciona:**
- **Instalada:** lê o campo `version` do `plugin.json` no clone que o doctor já localiza (`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` → locais padrão do Code).
- **Publicada:** no mesmo clone, `git fetch` silencioso + lê a `version` de `origin/<ref>` (`git show origin/<ref>:.claude-plugin/plugin.json`) — **mesmo canal git que o `marketplace update` usa**, sem depender de HTTP raw/proxy separado.
- **Compara semver** (número de versão, não commit) e reporta:
  - iguais → **✓** "kit atualizado (X)"
  - instalada `<` publicada → **⚠** "há atualização: X → Y — rode `claude plugin marketplace update <nome>`"
  - instalada `>` publicada → **ℹ** "à frente (dev): X local · Y publicada"
- **Degrada gracioso — nunca ✗ vermelho** (igual o doctor faz com Docker): fetch falha (offline/sem VPN) → "não alcancei o remoto (offline?) — instalada: X" (a verificar); clone sem remote git (instalado por pasta local / dev via symlink) → check **pulado**, mostra só a versão instalada.

Por que **versão** e não **commit**: legível ("0.11.0 → 0.12.0" vs hash), alinha com o `release`/CHANGELOG (a versão vive nos dois manifestos e é bumpada a cada publicação), e não acusa falso-desatualizado nos muitos commits que não mexem no plugin (docs, `memory/`, MAPA).

Por que no **doctor** e não no **upgrade**: são dois níveis distintos. O doctor **diagnostica o plugin** (global) — está atrás do remoto? O upgrade **conserta os arquivos do projeto** (local) contra os templates da versão **já instalada** e nunca olha o remoto. A feature é 100% do doctor; o upgrade fica intacto.

## Critérios de aceite
- DADO um projeto com o kit instalado por git (clone com remote), QUANDO rodo `/mss-spec:doctor`, ENTÃO vejo a linha "versão do kit" com instalada vs publicada e um veredito ✓/⚠/ℹ.
- DADO que a versão instalada é igual à publicada, QUANDO rodo o doctor, ENTÃO o check é **✓** "kit atualizado".
- DADO que a versão instalada é **menor** que a publicada, QUANDO rodo o doctor, ENTÃO é **⚠** com o comando `marketplace update` a rodar (mas o doctor **não** roda).
- DADO que a versão instalada é **maior** que a publicada (dev à frente), QUANDO rodo o doctor, ENTÃO é **ℹ** "à frente (dev)", não ✗.
- DADO que o remoto não é alcançável (offline) ou o clone não tem remote git, QUANDO rodo o doctor, ENTÃO o check é "a verificar"/pulado (mostra a instalada) — **nunca ✗**.
- DADO qualquer resultado, ENTÃO o doctor só **reporta** (não roda update, não bloqueia).

## Arquivos tocados
- `commands/doctor.md` — novo check "versão do kit" (instalada vs publicada via git fetch)
- `docs/superpowers/INDEX.md` — status da tarefa
- `tests/test_smoke_kit.py` — smoke test: o `doctor.md` referencia o check de versão

## Fora de escopo
Rodar `marketplace update` automaticamente (só reporta) · comparar por commit git · híbrido versão+commit · check de versão via HTTP raw · verificar versão de outros plugins (só o mss-spec).

## Histórico
- 2026-07-21 — criado: design do check de versão contra o remoto no `doctor`, aprovado no chat. Escolhas do owner: viver no **doctor** (diagnóstico do plugin, ≠ upgrade que conserta arquivos do projeto); remoto via **git fetch no clone** (mesmo canal do `marketplace update`, não HTTP raw); comparar por **versão semver** (não commit — ilegível e falso-positivo nos commits que não mexem no plugin); só reporta (filosofia doctor); degrada gracioso offline/dev (nunca ✗).
