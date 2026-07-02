---
description: Abre uma feature (spec → tasks) e mantém o índice de tarefas; não mexe em git (branch é explícita)
argument-hint: "[nome-da-feature]"
disable-model-invocation: true
---

Feature: **$ARGUMENTS**

1. Invoque **superpowers:brainstorming** para esta feature: objetivo (1 frase), **Critérios de Aceite testáveis** (formato "DADO… QUANDO… ENTÃO…") e fora de escopo. **Espere o OK do owner** antes de qualquer código.
2. Invoque **superpowers:writing-plans**: quebre em tasks pequenas e ordenadas, cada uma cobrindo ≥1 Critério de Aceite por teste.
3. **Atualize o índice de tarefas**: acrescente 1 linha em `docs/superpowers/INDEX.md`:
   `- [<nome-da-feature>](specs/<arquivo>-design.md) — <objetivo em 1 frase> — aberta`
4. Execute **uma task por vez** (superpowers:executing-plans / subagent-driven-development): TDD (teste do AC → vermelho → código → verde) e **rode e cole a saída** (verification-before-completion) antes da próxima.
5. Ao concluir: `requesting-code-review` → `finishing-a-development-branch`. Mude o status da linha no `INDEX.md` para `fechada`. Se surgiu regra durável, 1 linha em "Regras críticas" do `CLAUDE.md`; se surgiu aprendizado durável, grave em `memory/` (arquivo + linha no `MEMORY.md`).

**Git/branch:** este comando NÃO cria branch nem worktree. Se quiser isolamento, peça explicitamente (`superpowers:using-git-worktrees`) antes ou durante.

Mudanças que **não** são feature (não precisam deste comando): **bugfix** → teste que reproduz o bug é a spec → corrige → verifica; **refactor** → gate é "testes verdes"; **chore/docs** → sem spec.
