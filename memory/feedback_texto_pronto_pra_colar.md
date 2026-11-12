---
name: feedback_texto_pronto_pra_colar
description: Quando o owner precisa repassar algo a outra janela, a um aprovador ou à infra, entregue o texto pronto pra colar — completo, com os valores reais preenchidos e um exemplo de como fica; nunca placeholder sem dizer de onde tirar
gatilho: quando o owner precisar repassar algo a outra janela do Claude, a um aprovador ou à equipe de infra
gatilho_resposta: (?i)\b(?:conversa nova|outra janela|janela nova|outro chat|chat novo)\b[^\n]{0,120}\b(?:col[ea]|colar|texto pronto)\b|\b(?:col[ea]|colar|texto pronto)\b[^\n]{0,120}\b(?:conversa nova|outra janela|janela nova|outro chat|chat novo)\b
metadata:
  type: feedback
---

Quando o próximo passo é o owner **repassar** algo — pra janela de outro projeto, pra quem aprova no Azure
DevOps, pra infra num chamado —, entregue o **texto pronto pra colar** num bloco: completo, com os **valores
reais já preenchidos** (nome, endereço, código da identidade) e, se sobrar algo a trocar, **de onde tirar,
clique a clique, com um exemplo de como fica**.

**Why:** foi o que funcionou no MSS-UTILS (2026-10-16 a 20): o texto pra colar na janela de lá (desfazer o
`networkConfig`; avisar a etapa 5), o pedido de aprovação pro aprovador e os comandos da infra destravaram cada
passo. O que **não** funcionou foi o contrário: `<nome ou id do passo 1>` e `COLE-AQUI` foram colados
literalmente no terminal da infra (*"de onde vem esse cole-aqui, não está claro novamente"*), e o owner pediu
que os comandos do chamado já viessem *"com o id certo"*. Ele também pediu que esses textos virassem padrão do
kit (*"esse texto deve estar no plugin também"*).

**Texto pra conversa nova (2026-10-28):** antes do texto, diga em linguagem simples o que vai mudar e como
conserta, com a causa e `arquivo:linha`. Todo fato do texto é conferido agora, nunca copiado de outra conversa
(F-044). Diga o escopo com todas as letras: "mexe só no kit; outros projetos são só para LER; quem leva pra eles
é o `/mss-spec:upgrade`". Frase do owner com duas leituras vai verbatim e você pergunta antes de montar o texto.
Owner: *"não ficou claro o que isso vai fazer e como ele irá consertar, só há um texto para ler e mais nada"*.

**Texto pra conversa nova tem três partes de título fixo (0.59.0, 2026-11-11):** `Já decidido — não reabrir:`
(numerado, com `arquivo:linha` quando houver), `Falta decidir:` (ou "nada") e `Regras desta conversa:` — e nunca
"um tópico por vez". O texto de 2026-11-11 pedia isso e não dizia para não reabrir; a conversa que recebeu reabriu 6
itens decididos (F-058). O hook `hooks/passagem_de_conversa.py` devolve o texto fora do molde e traz o molde.

**How to apply:** vale em qualquer comando que delegue ação a terceiros. No `/mss-spec:azure-ambiente` já mora
na regra 10 da condução, no texto do aprovador (etapa 6) e no chamado `templates/azure-ambiente/permissoes-infra.md`
(com o código real da conexão). Parente de [[feedback_comando_pro_owner_passo_a_passo]] (o formato dos comandos
que o próprio owner roda) e de [[feedback_nao_inventar_fatos_concretos]] (valor real só com fonte).

**Um texto por vez, com o item explicado antes, e leitura mínima (2026-11-11, F-065).** O owner pediu "os prompts
das próximas tarefas" e recebeu 7 blocos seguidos: *"Esse monte de prompt é das decisões que fechamos nessa
conversa??? O item 1 ,2 e 4 não entendi nada!!!"*. E a conversa que recebeu um deles releu spec, dossiê, hooks e
falhas: *"ele rele tudo para todo lado!!!"*. Passa a valer: entregue **só o texto da próxima conversa**; antes
dele, o item em português simples ("Hoje · O que muda · O que você ganha"); e na parte `Regras desta conversa:`
diga **o mínimo a ler** (a seção exata da spec), nunca "leia a spec e o dossiê". Os textos dos itens seguintes
ficam guardados no documento do assunto, não na resposta.
