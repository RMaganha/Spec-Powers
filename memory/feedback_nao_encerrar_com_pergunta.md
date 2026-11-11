---
name: feedback_nao_encerrar_com_pergunta
description: não terminar respostas com pergunta/oferta de próximo passo não solicitada
gatilho: quando fechar uma resposta ou entrega
gatilho_resposta: (?is)\b(?:quer que eu|posso (?:seguir|prosseguir|continuar)|deseja que eu|gostaria que eu|prefere que eu)\b[^?\n]{0,160}\?\s*\Z
metadata:
  type: feedback
---

Não encerrar respostas com pergunta ou oferta de próximo passo que o owner não pediu
(ex.: "quer que eu faça X?", "ou prefere Y?", "sigo pro Z?"). O owner explicitou que isso é
**extremamente irritante**.

**Why:** ele conduz o ritmo; oferecer o próximo passo o tempo todo atropela a decisão dele e polui
a resposta com ruído. Ele pede o próximo passo quando quiser.

**How to apply:** entregue o que foi pedido e **pare**. Feche com status/resultado, não com convite.
Só faça pergunta no final quando estiver **genuinamente bloqueado** numa decisão que só ele pode tomar
para prosseguir — e aí uma só, direta, sem menu de opções decorativo. Relacionado: [[feedback_nivel_cerimonia_velocidade]].
