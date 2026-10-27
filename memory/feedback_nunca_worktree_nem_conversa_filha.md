---
name: feedback_nunca_worktree_nem_conversa_filha
description: Nunca trabalhar em worktree e nunca abrir uma conversa a partir de outra — tudo na pasta principal, numa branch saída da main; conversa nova o owner abre pelo + e cola o texto pronto que você entrega
gatilho: quando pensar em worktree (git worktree, EnterWorktree, subagente isolado) ou em abrir/passar trabalho pra outra conversa
metadata:
  type: feedback
---

Duas regras do owner, de 2026-10-27:

1. **Nunca trabalhar em worktree.** *"nunca deixar trabalhar em um worktree"* · *"geralmente eu não uso nenhum
   worktree; se foi usado, foi indevidamente"*. O trabalho é sempre na **pasta principal**, numa branch saída da
   `main` ([[feedback_feature_a_partir_da_master]]). A pasta está na branch de outra feature? **Pare e pergunte**
   ao owner — não abra worktree pra contornar.
2. **Nunca abrir uma conversa a partir de outra.** Quando o trabalho pedir conversa nova, **entregue o texto pronto
   pra colar** ([[feedback_texto_pronto_pra_colar]]) e o owner abre a conversa pelo **+** e cola. Vale pra iniciar,
   propor ou passar adiante uma conversa.

**Why:** em 2026-10-27 uma conversa (0.44.0) abriu sozinha o worktree `.claude/worktrees/partida-em-dois-niveis`
porque a pasta principal estava na `feature/bug-e-duvida`; deixou 2 commits e memória fora da `main` (limpo em
`eeba6a9`). O próprio kit mandava: o aviso de "outra feature aberta" dizia *"abra esta num worktree"*. No mesmo
dia, duas conversas foram abertas a partir de outra (a do worktree e a desta regra) e ficaram penduradas uma na
outra na barra lateral — *"eu me perdi"*.

**How to apply:** trava mecânica na `feature/nunca-worktree` (0.46.0): criar ou entrar em worktree, gravar
dentro de um, e abrir ou passar conversa a partir desta são negados. Sem a trava (ou com ela desligada pelo
owner), a regra vale igual: entregue o texto pronto e pare.
