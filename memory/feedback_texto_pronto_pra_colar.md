---
name: feedback_texto_pronto_pra_colar
description: Quando o owner precisa repassar algo a outra janela, a um aprovador ou à infra, entregue o texto pronto pra colar — completo, com os valores reais preenchidos e um exemplo de como fica; nunca placeholder sem dizer de onde tirar
gatilho: quando o owner precisar repassar algo a outra janela do Claude, a um aprovador ou à equipe de infra
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

**How to apply:** vale em qualquer comando que delegue ação a terceiros. No `/mss-spec:azure-ambiente` já mora
na regra 10 da condução, no texto do aprovador (etapa 6) e no chamado `templates/azure-ambiente/permissoes-infra.md`
(com o código real da conexão). Parente de [[feedback_comando_pro_owner_passo_a_passo]] (o formato dos comandos
que o próprio owner roda) e de [[feedback_nao_inventar_fatos_concretos]] (valor real só com fonte).
