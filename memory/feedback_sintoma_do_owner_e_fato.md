---
name: feedback_sintoma_do_owner_e_fato
description: o owner relatou que o assistente/plugin se perdeu ou errou → isso é fato; se a leitura não mostra, falta ler, e a resposta diz onde ainda não achou e pergunta — nunca "não se perdeu"
gatilho: quando o owner relatar que o assistente ou o plugin se perdeu, errou ou repetiu o problema
gatilho_resposta: (?i)(?:assistente|plugin|\bkit\b|comando|conversa|nova-feature|\bel[ea]\b)[^.\n]{0,40}\bn[ãa]o (?:se perdeu|errou)\b
metadata:
  type: feedback
---

O relato do owner ("se perdeu", "errou de novo") é o sintoma, e sintoma não se re-litiga. Quando o que você leu
(a conversa, o log, o código) não mostra o erro, a conclusão é que **falta leitura**, não que o erro não houve:
diga o que já leu, onde ainda não achou, e pergunte o que ele viu — numa frase.

**Why:** 2026-10-29, caso F-047. O owner relatou que o `nova-feature` "se perdeu todo" no Whats; a resposta leu a
conversa até a 1ª mensagem do assistente e escreveu *"Até onde consegui ver, o assistente não se perdeu"*. O resto
da conversa mostrou o desenho sem as memórias de ambiente, a pergunta dele sem resposta e uma pergunta já sabida.
O owner: *"toda vez os mesmos problemas se repetem!!!"*.

**How to apply:** o `gatilho_resposta` devolve uma vez a resposta que diz "não se perdeu / não errou / não houve
erro". O passo 2 do `/mss-spec:bug` diz o mesmo em prosa. Relacionado a [[feedback_ler_a_outra_conversa_antes_de_nao_sei]].
