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

**Conversão dos projetos que nasceram antes** (0.48.0): o `/mss-spec:upgrade` chama o
`templates/converter_to_dolist.py`, sozinho na rodada, com o OK do owner. Em dois tempos, pra nunca perder nada:
(1) `liberar` tira o to-dolist do `.gitignore` e ele é commitado **exatamente como está**; (2) `converter` mostra
a soma (linhas de origem = recados convertidos + títulos usados + lista do fim + marcação) e 3 linhas reais antes e
depois, e só grava com o OK, com o to-dolist já no git e os arquivos limpos. Recado (item com as linhas que
continuam embaixo) vira uma linha com o título da seção na frente e a data dele; fora de escopo vira
`- <item> #fora-de-escopo (decidido: <data>, <texto inteiro>)` — o texto não é encurtado, só muda de lugar; sem
data → a do dia; `DD/MM/AAAA` → `AAAA-MM-DD`; ordem pela data, a mais antiga em cima. Riscado/FEITA/CONCLUÍDO,
data sem ano, parágrafo solto, citação, tabela e código vão sem mudar uma letra pra uma lista no fim, pro owner
decidir. O `/mss-spec:doctor` (check 10) roda o `checar` e aponta o que falta converter. Prévia de 2026-10-28,
sem gravar: Whats 1.066 linhas (601 convertidas, 292 na lista), Energy 68 (5 na lista), Transportes 134 (19 na
lista), soma batendo nos três.

**Formato antigo, provisório até o upgrade converter cada projeto** (escolha do owner, 2026-10-28): o
`rodizio_partida.py` ainda tira uma seção "Fora de escopo" antiga do INDEX pro `FORA-DE-ESCOPO.md` quando o INDEX
passa do teto, o `um_item_por_janela.py` ainda não conta os itens dela como feature aberta, e o `doctor` cita
essa limpeza — tudo marcado como formato antigo.

Fora de escopo desta feature (no sentido da spec, não do to-dolist): rodar o upgrade nos outros projetos (o owner
roda, em cada um) · tirar do kit o código que aceita o formato antigo (depois de todos convertidos) · `CLAUDE.md` dos projetos (`docs/decisoes.md:48`) · o "fora de escopo" dentro da
spec de cada feature (`commands/nova-feature.md`), que é outra coisa.

## Histórico
- 2026-10-28 — criado (0.47.0): o mesmo conteúdo vivia em 3 lugares e formatos; a busca repetia o item a cada
  mensagem e três textos diziam "NÃO fazer" sem "naquele momento" — o assistente tratou como proibição
  (*"naquela data eu não iria fazer agora eu vou!"*). Os 61 itens do kit viraram linhas do to-dolist: data da
  decisão em `docs/decisoes.md` quando ela existe, senão a do 1º commit que registrou o item; "motivo não
  registrado" nos 7 da lista de 2026-07-17, que nunca tiveram motivo escrito; o `.bpmn` do Bizagi saiu (foi
  entregue depois, `docs/decisoes.md:31`).
- 2026-10-28 — o upgrade converte os projetos (0.48.0), na mesma conversa (motivo: o owner pediu os outros
  projetos "em definitivo"). A leitura dos três mostrou que "linha por linha" não servia: o to-dolist do Whats tem
  926 linhas e só 108 começam com "- " (recados numerados que continuam embaixo, títulos com data, código) — o
  owner escolheu recado = 1 linha com o título na frente, texto do fora de escopo inteiro (sem encurtar) e
  riscado/FEITO pra lista do fim; sem data → a do dia do upgrade, ordem pela data; to-dolist commitado como está
  antes de converter, porque o upgrade só promete voltar atrás em arquivo versionado. A busca segue sem ler o
  formato antigo em nenhum projeto (owner: vale o `docs/decisoes.md:51`).
