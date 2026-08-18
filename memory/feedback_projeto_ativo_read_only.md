---
name: feedback-projeto-ativo-read-only
description: Um projeto por janela — o projeto ativo é a âncora de escrita e não migra; qualquer outro projeto é referência somente-leitura
gatilho: quando a tarefa mencionar outro projeto além do desta janela
metadata:
  node_type: memory
  type: feedback
---

O **projeto ativo** — a raiz onde a janela abriu — é a **âncora**: o único destino de escrita da sessão,
e ela **não migra** no meio da conversa. Ler outro projeto é legítimo e às vezes obrigatório (o
`/mss-spec:precedentes` manda abrir o código real de lá antes de replicar), mas **ler é tudo o que se faz
lá**: `Read`/`Grep`/`Glob` sim; `Write`/`Edit`, `git`, `pytest`, build, `npm install` ou "consertar de
passagem", **nunca**. O padrão encontrado se **traz pra cá** (cópia pra dentro da âncora, com OK do
owner); nunca se edita o repo de origem.

**Why:** aconteceu de verdade — trabalhando no projeto A, o owner disse *"olha, o projeto B tem isso, veja
como está lá e faça igual"*, e o assistente **adotou o B como projeto de trabalho**, alterou arquivos lá e
**quebrou o B**. Não foi malícia, foi **deriva de contexto**: sem âncora declarada, o último caminho lido
passa a parecer "o projeto". Duas regras que pareciam cobrir isso não cobriam — "um assunto por janela"
falava de *assunto*, não de *projeto*, e o `precedentes` mandava abrir o código de lá sem dizer que era
só leitura.

**How to apply:** se a mudança é no outro projeto, **pare e diga**: *"isso é trabalho no projeto X — feche
esta janela e abra uma nova na raiz dele"*. Se enxergou bug/defasagem lá, **reporte** (ofereça
`/mss-spec:to-dolist adicionar <assunto>`) — não conserte: você não conhece o estado daquele repo nem tem
os testes dele verdes na frente. Vale além do kit, pra qualquer leitura de código de outro time. O kit tem
a cerca determinística (`hooks/projeto_ativo.py`, nega escrita fora da âncora), mas ela é 2ª linha — e só
existe em sessão nova; a regra é a 1ª. Parente de
[[feedback-brownfield-entender-nao-aplicar]] (entrar em código alheio = entender e registrar, não
consertar) e de [[feedback-nao-inventar-fatos-concretos]].
