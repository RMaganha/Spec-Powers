---
description: Define o nível de cerimônia do fluxo Spec-Driven para a sessão (mínimo | médio | alto)
argument-hint: "[mínimo | médio | alto]"
disable-model-invocation: true
---

Ajuste o **nível de cerimônia** do fluxo Spec-Driven para: **$ARGUMENTS**. Vale a partir de agora, até eu trocar (o padrão do projeto é **médio**). Confirme o nível ativo e siga nesse ritmo.

Em **todos** os níveis, o que NÃO muda: não codar sem o meu OK, TDD (teste antes do código) e verificação (rodar + colar a saída real). O que varia é só o **peso do planejamento**:

- **mínimo** — sem spec nem plano formais; no máximo 1-2 perguntas de alinhamento; TDD leve; executa direto e cola a saída. Para ajuste pequeno/claro (equivale a fix/chore).
- **médio** (padrão) — design curto (poucas frases, sem doc de spec grande) + plano curto em tópicos + execução **inline** (`executing-plans`), sem subagentes nem dupla revisão.
- **alto** — ritual completo: `brainstorming` → spec (doc) + `writing-plans` detalhado + `subagent-driven-development` com dupla revisão. Só para feature grande/crítica.

Se $ARGUMENTS vier vazio, apenas informe qual é o nível ativo e liste as opções.
