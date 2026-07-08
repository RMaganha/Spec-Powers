---
description: Abre uma feature (spec → tasks) e mantém o índice de tarefas; não mexe em git (branch é explícita)
argument-hint: "[nome-da-feature]"
disable-model-invocation: true
---

Feature: **$ARGUMENTS**

Conduza no **nível de cerimônia atual** (padrão **médio**; troque com `/mss-spec:modo`). Os passos abaixo descrevem o nível **alto**; ajuste ao nível ativo:
- **médio**: design curto (poucas frases, sem doc de spec grande) + plano curto em tópicos + execução **inline** — sem subagentes nem dupla revisão. Ainda: OK antes de codar, TDD, verificação.
- **mínimo**: pule spec/plano; alinhe em 1-2 perguntas e vá direto ao código com TDD leve.
- **alto**: siga os passos como estão (spec doc + `writing-plans` + `subagent-driven-development`).

1. Invoque **superpowers:brainstorming** para esta feature: objetivo (1 frase), **Critérios de Aceite testáveis** (formato "DADO… QUANDO… ENTÃO…") e fora de escopo. **Espere o OK do owner** antes de qualquer código.
2. Invoque **superpowers:writing-plans**: quebre em tasks pequenas e ordenadas, cada uma cobrindo ≥1 Critério de Aceite por teste.
3. **Atualize o índice de tarefas**: acrescente 1 linha em `docs/superpowers/INDEX.md`. O link aponta pro doc que **existe de fato** no nível ativo:
   - **alto** (tem doc de spec): `- [<nome-da-feature>](specs/<arquivo>-design.md) — <objetivo em 1 frase> — aberta`
   - **médio/mínimo** (sem doc de spec): `- <nome-da-feature> — <objetivo em 1 frase> — aberta` (sem link; se houver plan file, linke-o no lugar). Nunca linke arquivo que não foi criado.
4. Execute **uma task por vez** (superpowers:executing-plans / subagent-driven-development): TDD (teste do AC → vermelho → código → verde) e **rode e cole a saída** (verification-before-completion) antes da próxima.
5. Ao concluir: `requesting-code-review` → **rode `/mss-spec:plano-teste`** (a suíte inteira; as validações desta feature dobram no baseline anti-regressão, que só é atualizado se passar 100%) → `finishing-a-development-branch`. Mude o status da linha no `INDEX.md` para `fechada`. Se surgiu regra durável, 1 linha em "Regras críticas" do `CLAUDE.md`; se surgiu aprendizado durável, grave em `memory/` (arquivo + linha no `MEMORY.md`).

**Git/branch:** este comando NÃO cria branch nem worktree. Se quiser isolamento, peça explicitamente (`superpowers:using-git-worktrees`) antes ou durante.

Mudanças que **não** são feature (não precisam deste comando): **bugfix** → teste que reproduz o bug é a spec → corrige → verifica; **refactor** → gate é "testes verdes"; **chore/docs** → sem spec.
