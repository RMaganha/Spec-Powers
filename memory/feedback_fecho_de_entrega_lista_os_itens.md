---
name: feedback_fecho_de_entrega_lista_os_itens
description: O fecho de uma entrega com vários itens lista cada item com onde ele está (commit), antes do passo do owner — quem só lê a última mensagem (ou chega depois de compactar) tem de ver o quadro inteiro
gatilho: quando fechar uma entrega de vários itens, ou escrever a 1ª resposta depois de compactar a janela
sem_gatilho_de_acao: o fecho de entrega não tem frase fixa — o que marca é a ausência da tabela, que um regex não mede
metadata:
  type: feedback
---

O fecho de uma entrega de N itens lista os N, cada um com onde ele está (commit, arquivo), e só depois o
passo que é do owner. Quem só lê a última mensagem, ou volta depois de um `/compact`, tem de ver o quadro
inteiro: o estado da entrega, não só o estado do git.

**Why:** 2026-11-06, benchmark MSIG_Agentes: 13 itens implementados por esforço (baixo → médio → alto), um
commit por item, mesclados na `main`. O fecho depois do merge falou só dos merges, da suíte e do push. O owner,
lendo só essa mensagem: *"Eu não entendi fiz o push já, você não tocou só as tarefas com esforço baixo, ainda
faltam a média e alta"* — tudo estava feito; a resposta certa foi a tabela item → commit, agrupada por esforço.

**How to apply:** tabela item → commit (ou item → arquivo), agrupada do jeito que o owner pediu a entrega (por
esforço, por parte, por ordem). Não substitui [[feedback_resposta_do_tamanho_do_pedido]]: o inventário **é** a
resposta ao pedido "implementar os 13"; o passo do owner (push, OK) vem depois dele, em passo numerado
([[feedback_comando_pro_owner_passo_a_passo]]).
