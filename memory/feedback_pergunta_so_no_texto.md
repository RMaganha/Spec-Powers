---
name: feedback-pergunta-so-no-texto
description: No app do Claude Code a pergunta ao owner vai só no texto da resposta — nunca repetida na caixa de "próximo passo" do fim da rodada (com botões), que o confunde
gatilho: quando fechar uma rodada com pergunta ou decisão pendente para o owner no app do Claude Code (caixa de próximo passo, botões de resposta)
sem_gatilho_de_acao: a ação é preencher a caixa do fim da rodada, que não é comando de shell nem texto da resposta
metadata:
  type: feedback
---

Em 2026-11-10 o owner mandou o print da caixa que o app mostra no fim da rodada (resumo + pergunta + botões) e
disse: *"eu não sei pq no final voce da essas mensagens do print, me deixa completamente confuso"*. A caixa
repetia, com outras palavras, a pergunta que já estava no texto.

**Why:** ele lê a resposta; a caixa vira uma segunda mensagem dizendo quase a mesma coisa, com um resumo que
compete com o texto. Duas perguntas na tela = não sabe qual responder.

**How to apply:** a caixa do fim da rodada recebe **só o resumo** (o que mudou e o que falta), sem pergunta e sem
botões. A pergunta — **uma só** — vai no fim do texto, em frase simples. Vale junto com
[[feedback_nao_encerrar_com_pergunta]] (pergunta só quando a decisão é dele e trava o próximo passo) e
[[feedback_resposta_do_tamanho_do_pedido]]. Caso F-056.
