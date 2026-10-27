---
name: feedback_captura_varre_a_conversa_inteira
description: Na captura de memória, varra a conversa inteira do começo — cada reclamação, correção ou decisão do owner é um item; conte e cite as falas exatas, e confira se algum item adiado teve a condição de reabertura cumprida
gatilho: quando rodar /mss-spec:memory capturar (ou montar o fecho de uma sessão longa)
metadata:
  type: feedback
---

A captura não pode deixar nada passar. Antes de mostrar o rascunho, **varra a conversa desde a 1ª mensagem**
e faça a lista: cada **reclamação** do owner, cada **correção** que ele fez (premissa derrubada), cada
**decisão** (inclusive "não fazer") e cada **acerto** que ele confirmou. Pra cada uma, o lar certo (decisão,
fora de escopo, EVALS, memória, diário). Ao citar o owner, **cite a fala exata e atribua certo** (reclamação
sobre a resposta de outra janela não é sobre a sua). E confira os itens **adiados com condição** ("só se o
F-0NN reincidir"): se a condição se cumpriu, isso entra na captura.

**Why:** 2026-10-21, captura do assunto azure (do "Terraform?" à 0.41.0): o 1º rascunho deixou de fora quatro
itens — a reincidência do F-033 neste chat, a reincidência do passo a passo de comando, a branch criada fora da
`main` e metade do "próximo" — e o owner perguntou *"tem certeza que está tudo capturado?"*, depois *"seja mais
preciso… nunca podemos deixar passar nada!!!"*. Na 2ª passada ainda saiu uma citação atribuída errado e a
contagem baixa de reclamações, e só então apareceu que o item adiado "hook `Stop` medindo a resposta" tinha a
condição de reabertura cumprida.

**Medir depois de gravar (2026-10-27):** a captura escreve no INDEX, que entra em toda janela. Na partida em
dois níveis a linha nova levou o INDEX do kit a 7.208 de 7.000 B e o `test_index_so_com_tarefa_viva` falhou:
rode a suíte antes do commit. Na mesma captura, a 1ª passada deixou de apontar o item adiado com condição
cumprida (o hook `Stop`) e registrou como escrito um guardrail que não existia: confira no arquivo
cada guardrail citado antes de gravar.

**How to apply:** no modo `capturar` do `/mss-spec:memory`, antes do rascunho: lista numerada dos itens da
conversa (início ao fim), com a fala exata e o lar de cada um; depois, os índices pra não duplicar. Parente de
[[feedback-diagnostico-disciplinado]] (evidência antes de concluir).
