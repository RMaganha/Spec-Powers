---
name: feedback-nivel-cerimonia-velocidade
description: Ritual completo do superpowers (spec+plano+subagentes) é lento demais pro dia a dia; padrão = médio + effortLevel medium; alto só p/ feature grande
metadata: 
  node_type: memory
  type: feedback
  originSessionId: db2be446-fcee-4afe-88da-ad226447067e
---

O fluxo completo do superpowers (brainstorming 1-pergunta-por-vez → spec doc → writing-plans
detalhado → subagent-driven-development com dupla revisão) funciona mas é **muito lento** para o dia
a dia. Preferência do owner: rodar em cerimônia **média** por padrão e subir pra **alta** só em
feature grande/crítica.

**Why:** o owner sentiu isso no 1º projeto real (painel de atas) — o resultado foi bom, mas o
planejamento/spec demorou demais. Ele já roda Opus com bastante raciocínio, então o ritual pesado é
redundante no geral.

**How to apply:** o plugin mss-spec agora tem `/mss-spec:modo <mínimo|médio|alto>` e o `CLAUDE.md`
define médio como padrão. Em qualquer nível, TDD + verificação (rodar/colar saída) continuam
inegociáveis — só o peso do planejamento varia. Além disso, `effortLevel` do settings foi para
`medium` (template + global do owner, que estava `xhigh`) — dial ortogonal, pede restart. Se ele
pedir "rápido/leve", pense médio/mínimo; se "caprichado/crítico", alto. Relacionado a
[[feedback-assumir-papel-especialista]].
