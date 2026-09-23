---
name: feedback_analise_externa_cruzar_com_o_repo
description: Análise do kit feita por outra IA (sem acesso ao repo) se avalia item a item contra decisoes.md, o "Fora de escopo" do INDEX e o código — metade já existe ou contraria decisão tomada
gatilho: quando o owner trouxer análise, review ou sugestões sobre o kit feitas por outra IA ou por terceiro
metadata:
  type: feedback
---

2026-09-23: o owner trouxe duas análises do kit (ChatGPT e Gemini) feitas só a partir do catálogo.
Cruzadas com o repo: o Gemini errou 3 fatos (disable-model-invocation "manual", alerta de 75% "quebra
a sessão", um_item "precisa de exceção pra hotfix"); o ChatGPT propôs como novo o que já existia
(fonte da verdade por categoria, golden tests, PRIMEIRO-DIA) e, como remédio, o que o owner já tinha
cortado (runtime declarativo = config nova; recall semântico). Das ~25 sugestões, 2 viraram entrega
(0.30.0).

**Why:** quem analisa sem o repo não vê as decisões negativas — e a sugestão mais sedutora costuma
ser justamente uma delas. O owner confirmou o formato: tabela sugestão × nosso cenário × veredito
(✅/🟡/❌), com o motivo de cada ❌ citando a decisão.

**How to apply:** pra cada sugestão, antes de opinar: (1) já existe? (Grep no código/docs);
(2) contraria `docs/decisoes.md` ou o "Fora de escopo" do INDEX?; (3) tem caso real que doeu
(EVALS, git log)? Só o que passa nos três vira proposta — e aí vale [[feedback-medir-antes-de-afirmar-ganho]].
Relacionado: [[feedback_avaliar_tool_externa_ideia_vs_stack]] (mesma postura, para ferramentas).
