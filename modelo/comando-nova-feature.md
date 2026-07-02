---
description: Abre uma feature no padrão spec → tasks (Critérios de Aceite + plano), sem codar antes do OK
argument-hint: "[nome-da-feature]"
disable-model-invocation: true
---

Feature: **$ARGUMENTS**

1. Invoque **superpowers:brainstorming** para esta feature: defina objetivo (1 frase), **Critérios de Aceite testáveis** (as validações do owner — formato "DADO… QUANDO… ENTÃO…") e o que está fora de escopo. **Espere o OK do owner** antes de qualquer código.
2. Invoque **superpowers:writing-plans**: quebre em **tasks pequenas e ordenadas**, cada uma com critério de pronto e cobrindo ≥1 Critério de Aceite por teste.
3. Execute **uma task por vez** (superpowers:executing-plans / subagent-driven-development): para cada task, TDD (escreva o teste do AC → vermelho → código → verde), depois **rode e cole a saída** (verification-before-completion). Só então passe para a próxima.
4. Ao concluir a feature: `requesting-code-review` → `finishing-a-development-branch`. Se surgiu uma regra/decisão durável, adicione 1 linha em "Regras críticas" do `CLAUDE.md`.

Mudanças que **não** são feature (não precisam de `/nova-feature`): **bugfix** → escreva o teste que reproduz o bug (ele é a spec) → corrija → verifique; **refactor** → gate é "testes continuam verdes"; **chore/docs** → sem spec; **spike** → branch descartável.
