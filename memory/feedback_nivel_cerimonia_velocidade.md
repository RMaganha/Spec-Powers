---
name: feedback-nivel-cerimonia-velocidade
description: Ritual completo do superpowers (spec+plano+subagentes) é lento demais pro dia a dia; padrão = médio + effortLevel medium; alto só p/ feature grande
gatilho: quando escolher o ritual da tarefa (spec, plano, subagentes)
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

**2026-10-23 — quando o alto se paga:** na 0.42.0 (regras do kit pelo plugin + migração que reescreve o
`CLAUDE.md` de todo projeto) o owner escolheu revisor por tarefa. As revisões pegaram 8 problemas sérios antes do
merge: migração que travava pra sempre em projeto do molde anterior, seção "Contexto do negócio" engolida,
conservação por conjunto (linha repetida sumia sem alarme), migração pela metade se um arquivo estivesse aberto,
branch criada depois da gravação, regras do kit caladas por `CLAUDE.md` fora de UTF-8, regra vazia barrando
gravação. Custo: ~3 h e três reclamações de demora. Alto vale pra mudança que mexe em todo projeto — desde que
com aviso de progresso ([[feedback-avisar-progresso-em-execucao-longa]]).
