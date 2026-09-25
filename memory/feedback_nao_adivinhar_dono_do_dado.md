---
name: feedback_nao_adivinhar_dono_do_dado
description: Hook/script que precisa atribuir um dado a um dono (chat, sessão, usuário) que o dado não registra NÃO adivinha — fica com o que dá pra afirmar e declara o custo; a "foto do INDEX" errou nas duas direções
gatilho: quando um hook ou script precisar atribuir um dado a um dono (chat, sessão, usuário) que o próprio dado não registra
metadata:
  type: feedback
---

Na 0.34.0 (`hooks/um_item_por_janela.py`, contagem por chat), o hook precisava saber qual linha do
`docs/superpowers/INDEX.md` era a feature de cada chat — e a linha não diz qual chat a escreveu. Minha
1ª saída foi **adivinhar**: guardar uma "foto" das linhas na abertura e tratar como do chat toda linha
que nascesse depois. Errou nas **duas** direções, com vários chats na mesma pasta (o caso real do
Whats): prendeu o chat pela linha aberta do vizinho, e deixou um chat "retomar" a feature do outro
(F-022 de volta). Remendar a adivinhação (palavras em comum, fixar linha) só empilhava heurística.

**Why:** atribuição inventada parece funcionar no teste de um chat só e quebra justamente no uso
paralelo; numa cerca, o erro vira bloqueio indevido do owner (o pior modo de falha) ou furo da regra.

**How to apply:** pergunte "o dado registra o dono?". Não registra → decida só com o que dá pra
afirmar (ali: a linha achada pelo **nome**, por palavra inteira; sem ela, "nada aberto e algo fechou
desde a abertura") e **declare o custo** na spec e na mensagem ao owner ("não achei a linha dela pelo
nome… abra um chat novo") em vez de esconder o caso. **O que deu certo** e vale repetir: revisão de
código em rodadas, com o revisor rodando os cenários num script (`scratchpad/cenarios.py`, `rev2.py`,
`rev3.py`) — pegou 3 furos que a suíte verde não pegava (662 → 676 testes, cada cenário virou teste).
Ver [[feedback_regra_unica_em_vez_de_config]] e [[project_hook_ask_aparece_no_desktop]].
