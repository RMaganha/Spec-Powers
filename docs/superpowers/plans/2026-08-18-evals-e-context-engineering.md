# Plano — evals e context engineering (2026-08-18)

Efêmero. A spec viva é `docs/superpowers/specs/2026-08-18-evals-e-context-engineering-design.md`.
Branch: `feature/evals-e-context-engineering` (da `main`@0.18.0). Uma task por vez, TDD, saída colada.

| T | Task | CA | Toca |
|---|---|---|---|
| **T1** | **Gatilho + migração das 33 memórias.** `gatilho:` no frontmatter de toda memória; `memory/MEMORY.md` reescrito **agrupado por família de gatilho**, cada linha começando pelo gatilho; teto 200 linhas/25 KB. | CA5, CA6 | `memory/*.md`, `memory/MEMORY.md`, `templates/MEMORY.md`, `tests/test_memoria_gatilho.py` (novo) |
| **T2** | **`docs/EVALS.md` — a memória só de falhas.** Tabela-índice (`id · gatilho · classe · status`) + bloco por caso aberto; semeado com os 10 casos reais reconstruídos do repo; molde em `templates/EVALS.md`. | CA4 | `docs/EVALS.md`, `templates/EVALS.md`, `tests/test_memoria_gatilho.py` |
| **T3** | **Premissa com fonte no `nova-feature`.** Passo 2: passar no destilado → declarar premissas não-ditas com fonte ou `sem fonte` (as `sem fonte` primeiro) → premissa derrubada vira caso no fecho. | CA1, CA2 | `commands/nova-feature.md`, `tests/test_smoke_kit.py` |
| **T4** | **`capturar` colhe premissa derrubada, o que deu certo, e poda.** | CA3 | `commands/memory.md`, `tests/test_smoke_kit.py` |
| **T5** | **`.claude/rules/` path-scoped.** Molde `templates/rules/*.md` (`paths:`, ≤ 40 linhas, aponta a memória); dogfood em `.claude/rules/`; `kickoff`/`upgrade` instalam (categoria 1). | CA7, CA8 | `templates/rules/`, `.claude/rules/`, `commands/kickoff.md`, `commands/upgrade.md`, testes |
| **T6** | **Fim das duas cópias.** `memory resgatar` deixa o **ponteiro** na nativa; `doctor` checa o ponteiro. | CA9 | `commands/memory.md`, `commands/doctor.md`, testes |
| **T7** | **`release` cobra casos abertos** sem guardrail (⚠ que lista, não trava). | CA10 | `commands/release.md`, testes |
| **T8** | **Fecho.** `templates/CLAUDE.md` (schema com `gatilho:` + `docs/EVALS.md` no destilado de partida), bump **0.19.0** nos 2 manifestos, CHANGELOG, suíte inteira. | CA11 | `templates/CLAUDE.md`, `.claude-plugin/*.json`, `CHANGELOG.md` |

**Ordem obrigatória:** T1 → T2 antes de T3/T4 (que citam `docs/EVALS.md` e o gatilho). T8 por último (bump depois da suíte verde).
