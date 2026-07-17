# compliance — aderência às convenções do mss-spec (design)

Data: 2026-07-16 · feature do kit mss-spec. **Implementada 2026-07-17.**

## Objetivo
Comando `/mss-spec:compliance` — verifica se **este projeto** segue as convenções do mss-spec. (Não é o ambiente — isso é o `doctor`; nem AppSec — isso é o `seguranca`.)

## Problema
Num time, projetos derivam do padrão com o tempo. Falta um jeito de checar "este projeto ainda está no jeito da casa?" — que é a essência de um **framework opinativo**.

## Critérios de aceite (rascunho)
- DADO um projeto, QUANDO rodo `/mss-spec:compliance`, ENTÃO reporta ✓/✗: estrutura em camadas (`ESTRUTURA.md`) · `docs/specs/` + `INDEX` presentes · `docs/SEGURANCA.md` presente · `CLAUDE.md` com as Regras críticas · `.gitignore` protege `.env` · `docs/decisoes.md` existe.
- DADO algo ✗, ENTÃO **só reporta** e aponta a convenção violada (não conserta).

## Design (fechado 2026-07-17)
- Comando `/mss-spec:compliance` (`disable-model-invocation`) — auditoria de **convenções/estrutura**, distinta do `doctor` (ambiente) e do `seguranca` (AppSec). **Só reporta** ✓/✗ + veredito; pula check inaplicável.
- **Fonte = checklist fixo** de convenções (não drift-vs-templates). Papéis separados: **compliance audita, `upgrade` sincroniza** template desatualizado. Confere só **presença/wiring** — a auditoria AppSec profunda fica no `seguranca`.
- **Checklist (8):** (1) estrutura em camadas (ESTRUTURA.md + não-achatada) · (2) spec-driven (`docs/specs/` + INDEX) · (3) SEGURANCA.md + regra no CLAUDE.md · (4) CLAUDE.md com Regras críticas · (5) `.gitignore` protege `.env` + ancora `/logs/` e `/to-dolist.md` · (6) `docs/decisoes.md` · (7) `memory/MEMORY.md` versionada no repo · (8) front Tailwind/arquivos-separados se tem UI.
- Valor maior na **adoção pelo time**: consistência entre projetos.

## Fora de escopo
Corrigir automaticamente (é o `upgrade`) · avaliar qualidade de código (é aderência a convenção, não lint/performance) · auditoria AppSec profunda (é o `seguranca`).

## Histórico
- 2026-07-16 — criado: spec inicial. Detalhar (brainstorming) e implementar em outro chat.
- 2026-07-17 — implementado: `commands/compliance.md` (8 checks, só reporta, pula inaplicável), `test_compliance_wiring` no smoke. Decisões em brainstorming: checklist fixo (não drift) · compliance audita / upgrade conserta · confere presença, defere AppSec profundo ao seguranca · inclui os 4 extras (memory, estrutura, âncoras gitignore, front). 23/23 verde.
