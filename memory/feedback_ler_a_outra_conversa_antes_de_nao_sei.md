---
name: feedback_ler_a_outra_conversa_antes_de_nao_sei
description: o owner cita outra conversa → ler a transcrição dela (~/.claude/projects/<pasta>/*.jsonl) e comparar ponto a ponto antes de responder; "não sei" sem ler é resposta sem fonte
gatilho: quando o owner citar outra conversa ("em outro chat você disse…", "a outra conversa falou…")
gatilho_resposta: (?i)não (sei|tenho acesso).{0,40}(outra conversa|outro chat)
metadata:
  type: feedback
---

As conversas do projeto ficam gravadas em `~/.claude/projects/<pasta-do-projeto>/*.jsonl` (ver
[[reference-historico-mostra-o-que-carregou]]). Quando o owner cita o que outra conversa disse, leia antes de
responder: liste os .jsonl por data, extraia por um script no scratchpad (rodado com `python -I`) as mensagens
com o termo do assunto, e compare ponto a ponto com o que esta conversa fez. Divergência achada → mostre as duas
com a fonte e pergunte de novo. Nunca "não sei" antes de ler.

**Why:** 2026-10-28, caso F-045. O owner: *"está no projeto as outras conversas e memoria, como não sabe???"*.
Ler a outra conversa mostrou uma divergência real (a busca no formato antigo), que mudou a decisão.

**How to apply:** o gatilho é a frase do owner sobre outra conversa. O `gatilho_resposta` devolve uma vez a
resposta que diz "não sei / não tenho acesso … outra conversa".
