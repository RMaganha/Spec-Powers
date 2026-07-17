---
description: Audita a aderência do projeto às convenções do mss-spec (estrutura, docs, regras, memória, gitignore) e dá um veredito ✓/✗ (só reporta, não conserta)
argument-hint: ""
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Audita se **este projeto** ainda segue as convenções do mss-spec — a essência de um framework opinativo: "está no jeito da casa?". Reporta **✓/✗**. **Só reporta** — não conserta e não bloqueia.

Fronteira (não confundir os três irmãos): **ambiente** (proxy/CA/ODBC/rede) é o `/mss-spec:doctor`; **AppSec** (authz, injeção, headers…) é o `/mss-spec:seguranca`; aqui é **convenção/estrutura**. Este comando confere só a **presença/wiring** das convenções — a auditoria AppSec profunda fica no `/mss-spec:seguranca`. E **não sincroniza** template desatualizado: quem faz o diff/merge com o molde atual é o `/mss-spec:upgrade` (compliance audita, upgrade conserta).

Rode **só os checks que se aplicam** (detecte pelos arquivos presentes); check inaplicável é **pulado**, não vira ✗.

Checks:
1. **Estrutura em camadas** — `docs/ESTRUTURA.md` presente **e** o código está em camadas (`config/`, `models/`, `services/`, `routers/`, `utils/`… na raiz), **não** achatado numa pasta única (bug real de scaffolding). Projeto sem app (só docs) → pule.
2. **Spec-driven** — `docs/superpowers/INDEX.md` presente e `docs/specs/` (specs vivas por assunto) existindo quando há features fechadas. INDEX sumido → ✗.
3. **Segurança (presença)** — `docs/SEGURANCA.md` presente **e** o `CLAUDE.md` carrega a regra secure-by-default (Regras críticas). Auditoria de verdade → aponte `/mss-spec:seguranca` (não a faça aqui).
4. **CLAUDE.md com as Regras críticas** — o bloco "Regras críticas" existe e não foi esvaziado (idioma pt-BR, não-inventar-fatos, camadas, git branch-por-tarefa, logging, spec viva). Ausente/vazio → ✗.
5. **.gitignore protege segredo + âncoras** — `.env` ignorado (e `!.env.example`), e ancorados na raiz: `/logs/` (log dev) e `/to-dolist.md` (captura pessoal). Sem a barra inicial a âncora pega pasta/arquivo errado — âncora faltando → ✗.
6. **docs/decisoes.md** — existe (log de decisões transversais). Ausente → ✗.
7. **memory/ versionada** — `memory/MEMORY.md` presente **dentro do repo** (índice de aprendizados). Regra dura da casa: memória mora no repo, **nunca** só em `~/.claude/projects/<proj>/memory/`. Sem `memory/` no repo → ✗ (rode `/mss-spec:memory` pra resgatar).
8. **Front (só se tem UI web)** — segue o design system MSIG: Tailwind + `@tailwindcss/typography`, JS/CSS em pastas próprias (`static/js`, `static/css`), **nada inline** num HTML só (exceto doc standalone). Sem UI → pule.

Saída: uma linha por check aplicável com **✓** ou **✗** (com o porquê no ✗) e um **veredito** final de uma linha (ex.: "aderente" / "2 desvios: falta docs/decisoes.md · memory/ fora do repo"). Num ✗, aponte a **convenção violada** e o caminho pra corrigir (qual template/comando) — **sem** corrigir.
