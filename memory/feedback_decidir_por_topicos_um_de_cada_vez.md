---
name: feedback-decidir-por-topicos-um-de-cada-vez
description: Assunto com vários itens a decidir vai em lista de tópicos (1 linha cada) e depois um tópico por vez, em português simples — "Hoje · A proposta · O que você ganha" — com a lista atualizada a cada decisão
gatilho: quando o assunto tiver vários itens para o owner decidir, ou quando ele disser que é muita coisa, que ficou perdido ou que a resposta está em linguagem de máquina
gatilho_resposta: (?m)(?:^.*\?[ \t*_]*$[\s\S]*?){4}
metadata:
  type: feedback
---

**O que deu certo (2026-11-10).** O resumo de "como melhorar o plugin" saiu enorme e o owner travou: *"é muita
coisa para eu absorver, vamos fazer o seguinte, separe por tópicos, e o minimo do resumo aqui, para irmos
decidindo"*. Na primeira tentativa por tópico ainda saiu jargão: *"já fiquei perdido no tópico 1, voce fala em
linguagem de máquina"*. O formato que ele seguiu até o fim (6 itens decididos) foi:

1. **Lista** dos tópicos, uma linha cada, com a coluna "Decisão".
2. **Um tópico por vez**, em quatro blocos curtos: **Hoje** (o que acontece) · **No outro lugar / A proposta** ·
   **O que você ganha** · (se houver) **O limite** — e uma pergunta de sim ou não.
3. A cada resposta, a **lista atualizada** com ✅ e o próximo tópico.
4. No fim, os tópicos **juntos por assunto** e na ordem de fazer.

**Vale só para o que ainda NÃO foi decidido (owner, 2026-11-11).** Na parte 2 da memória em tabela ele abriu a
conversa com 6 itens já decididos e eu comecei a fechar de novo, tópico por tópico: *"Os itens de 1 a 6 do meu
texto já estão decididos. Não me peça para confirmar de novo, tópico por tópico."* O que ele pediu no lugar: (1)
**uma lista única só com as escolhas do assistente** (o que ele não decidiu), uma linha cada, com o motivo; (2) o
que só ele pode decidir, perguntado **de uma vez, no fim**; (3) depois do OK na lista, seguir para o plano e o
código. O formato tópico a tópico fica para quando a decisão está em aberto.

**Why:** ele decide rápido quando vê uma coisa só, em palavras do dia a dia; comparação com algo conhecido
("como uma busca do Google", "fichário e estante") destrava mais que definição.

**How to apply:** nada de termo interno (nome de arquivo, de função, de variante) na explicação — só o que ele vai
digitar ou ver. Uma pergunta por mensagem. Se ele corrigir a ordem ou o agrupamento, a lista volta inteira,
corrigida. Parente de [[feedback_explicar_com_item_real_antes_depois]] e
[[feedback_resposta_do_tamanho_do_pedido]]. Caso F-056.
