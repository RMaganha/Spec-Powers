---
name: feedback-um-comando-com-o-porque
description: Ao indicar ao owner um comando do kit, diga UM só e, em 1 linha, se ele diagnostica (doctor) ou conserta (upgrade) — e confira se a mensagem dos hooks diz a mesma coisa
gatilho: quando indicar ao owner qual comando do kit rodar
metadata:
  type: feedback
---

Um comando por passo, com o porquê em uma linha. Alternar entre dois comandos sem explicar a diferença confunde.

**Why:** 2026-10-23, o owner: *"uma hora voce falar para rodar o docto ou o upgrade"*. O aviso de abertura da
0.41.0 mandava oferecer o `/mss-spec:doctor` quando o `CLAUDE.md` passava do teto; na 0.42.0 o conserto passou a
ser o `/mss-spec:upgrade`, e a conversa misturou os dois. O `doctor` só **mede e mostra**; o `upgrade` **muda**
arquivo (migra o `CLAUDE.md`).

**How to apply:** "rode `/mss-spec:upgrade` (é ele que migra); o `/mss-spec:doctor` é só pra conferir depois,
se quiser". Ao mudar o conserto de um problema, troque também o texto dos hooks que apontam pra ele
(`hooks/orcamento_partida.py`, `hooks/teto_ao_gravar.py`). Parente de [[feedback_resposta_do_tamanho_do_pedido]].
