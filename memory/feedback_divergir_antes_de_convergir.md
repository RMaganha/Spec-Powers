---
name: feedback-divergir-antes-de-convergir
description: Decisão de design aberta e cara de reverter → propor o /mss-spec:divergir (ramos isolados por frame antes de convergir); a 1ª resposta é a de manual
gatilho: quando a decisão de design for aberta (2+ arquiteturas viáveis, sem precedente que decida) e cara de reverter
metadata:
  node_type: memory
  type: feedback
---

O raciocínio linear ancora na primeira resposta e as "2-3 abordagens" viram três variações dela.
Quando a decisão de design é **aberta** (2+ arquiteturas viáveis, nenhum precedente MSIG decide) **e
cara de reverter** (contrato de API, esquema de banco, mecanismo central), **proponha você mesmo**
rodar o `/mss-spec:divergir` — o owner não precisa lembrar que ele existe; anuncie o custo (~10
chamadas de agente) e espere o sim.

**Why:** avaliação do repo [adhd](https://github.com/uditakhourii/adhd) (2026-08-25): a separação
gerador × crítico tem que ser **mecânica** (ramos isolados que não se veem + crítica em passo
separado), não prometida num prompt só. O owner apontou o furo do opt-in puro ("pode ser que eu
esqueça de chamar e aí?") — por isso o gatilho vive no kit (auto-proposta no `nova-feature` + esta
memória pras janelas fora do ritual), nunca na cabeça do owner. O stack npm foi rejeitado
([[feedback-avaliar-tool-externa-ideia-vs-stack]], 3º precedente); a ideia virou prosa + Agent tool.

**How to apply:** avalie o gate no momento do design (também em refactor/bugfix grande, fora do
`nova-feature`): aberta? cara? → proponha o `/mss-spec:divergir` (leia `commands/divergir.md` e
execute — é `disable-model-invocation`). Reuso vence divergência: com precedente MSIG, use o
`/mss-spec:precedentes` e siga. Decisão fechada ou barata → o piso do brainstorm basta (frames
distintos + armadilha sedutora marcada, sem subagentes).
