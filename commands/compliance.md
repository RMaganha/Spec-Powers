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
3. **Segurança (presença)** — `docs/SEGURANCA.md` presente **e** a regra secure-by-default chega ao projeto: **com a marca** (check 4) ela vem no bloco `2-regras-criticas.md` do plugin; **sem a marca**, o `CLAUDE.md` do projeto a carrega nas Regras críticas. Auditoria de verdade → aponte `/mss-spec:seguranca` (não a faça aqui).
4. **Regras do kit no projeto** — o `CLAUDE.md` da raiz tem a marca `<!-- mss-spec:regras-do-kit -->` (as regras do kit — idioma pt-BR, não-inventar-fatos, camadas, git branch-por-tarefa, logging, spec viva — vêm do plugin, não ficam copiadas no arquivo). Marca presente → ✓; `## Regras obrigatórias do projeto` é opcional (a migração a omite quando fica vazia), então seção ausente com a marca também é ✓. **Sem a marca**, vale o bloco antigo: "Regras críticas" no `CLAUDE.md`, presente e não esvaziado — e aponte o `/mss-spec:upgrade` pra migrar. Sem a marca e sem o bloco → ✗.
5. **.gitignore protege segredo + âncoras** — `.env` ignorado (e `!.env.example`), e ancorado na raiz: `/logs/` (log dev). Sem a barra inicial a âncora pega pasta/arquivo errado — âncora faltando → ✗. (O `to-dolist.md` vai pro git desde a 0.47.0 — não precisa estar ignorado.)
6. **docs/decisoes.md** — existe (log de decisões transversais). Ausente → ✗.
7. **memory/ versionada** — `memory/MEMORY.md` presente **dentro do repo** (índice de aprendizados). Regra dura da casa: memória mora no repo, **nunca** só em `~/.claude/projects/<proj>/memory/`. Sem `memory/` no repo → ✗ (rode `/mss-spec:memory` pra resgatar).
8. **Front (só se tem UI web)** — segue o design system MSIG: Tailwind + `@tailwindcss/typography`, JS/CSS em pastas próprias (`static/js`, `static/css`), **nada inline** num HTML só (exceto doc standalone). Sem UI → pule.

Saída: uma linha por check aplicável com **✓** ou **✗** (com o porquê no ✗) e um **veredito** final de uma linha (ex.: "aderente" / "2 desvios: falta docs/decisoes.md · memory/ fora do repo"). Num ✗, aponte a **convenção violada** e o caminho pra corrigir (qual template/comando) — **sem** corrigir.
