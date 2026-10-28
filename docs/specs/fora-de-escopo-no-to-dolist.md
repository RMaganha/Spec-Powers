# Fora de escopo vira item do to-dolist com a tag #fora-de-escopo

## Estado atual
"Fora de escopo" quer dizer **"não agora"**: decidido numa conversa, numa data, com um motivo; volta quando o
owner decidir — nunca é proibição (`docs/decisoes.md`, 2026-10-28). Mora num lugar só, o **`to-dolist.md`** da
raiz, uma linha por item:

```
- <o que ficou para depois> #fora-de-escopo (decidido: AAAA-MM-DD, motivo curto)
```

O motivo longo fica em `docs/decisoes.md`. O `to-dolist.md` **vai pro git** (o molde `templates/gitignore` não o
ignora mais); custo aceito: item anotado numa branch só aparece na `main` depois do merge. Quem grava: o
`/mss-spec:to-dolist adicionar <texto> #fora-de-escopo` (pergunta o motivo se faltar) e o
`/mss-spec:memory capturar` (decisão "não agora" da sessão). O assistente **nunca cita fora de escopo sozinho**:
a busca automática (`templates/memoria_indice.py`) não lê o to-dolist nem o antigo `FORA-DE-ESCOPO.md`; o item
aparece quando o owner pede — `/mss-spec:to-dolist listar #fora-de-escopo`. Não existem mais a seção
"Fora de escopo" do INDEX (molde e kit) nem o `docs/superpowers/FORA-DE-ESCOPO.md` do kit.

**Formato antigo, provisório até o upgrade converter cada projeto** (escolha do owner, 2026-10-28): o
`rodizio_partida.py` ainda tira uma seção "Fora de escopo" antiga do INDEX pro `FORA-DE-ESCOPO.md` quando o INDEX
passa do teto, o `um_item_por_janela.py` ainda não conta os itens dela como feature aberta, e o `doctor` cita
essa limpeza — tudo marcado como formato antigo.

Fora de escopo desta feature (no sentido da spec, não do to-dolist): converter os outros projetos (feature do
doctor/upgrade, INDEX item 3) · `CLAUDE.md` dos projetos (`docs/decisoes.md:48`) · o "fora de escopo" dentro da
spec de cada feature (`commands/nova-feature.md`), que é outra coisa.

## Histórico
- 2026-10-28 — criado (0.47.0): o mesmo conteúdo vivia em 3 lugares e formatos; a busca repetia o item a cada
  mensagem e três textos diziam "NÃO fazer" sem "naquele momento" — o assistente tratou como proibição
  (*"naquela data eu não iria fazer agora eu vou!"*). Os 61 itens do kit viraram linhas do to-dolist: data da
  decisão em `docs/decisoes.md` quando ela existe, senão a do 1º commit que registrou o item; "motivo não
  registrado" nos 7 da lista de 2026-07-17, que nunca tiveram motivo escrito; o `.bpmn` do Bizagi saiu (foi
  entregue depois, `docs/decisoes.md:31`).
