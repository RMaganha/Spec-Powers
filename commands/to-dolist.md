---
description: Caixa de captura rápida (to-do) e lugar do que ficou "pra depois" (#fora-de-escopo) — adicionar/listar/feito no to-dolist.md da raiz, versionado
argument-hint: "[adicionar <texto> [#fora-de-escopo] | listar [#fora-de-escopo] | feito <n>]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Caixa de captura de ideias/ajustes que surgem **fora do contexto** da tarefa atual (ex.: no meio de uma feature de banco você vê uma melhoria numa tela de outro assunto). Em vez de fazer fora de hora e poluir a branch, registre aqui e siga no que estava.

É o destino do protocolo **um assunto por janela** (regra no `CLAUDE.md`): quando um 2º assunto não relacionado aparece no meio de uma tarefa, ele é anotado aqui — `adicionar <assunto>` — e tratado depois, numa **nova janela**, em vez de emendar na atual.

Também é o destino da **bola de neve** — quando, pra fechar o assunto A, aparece o assunto B que "precisa ser entendido antes". Só **entender** B cabe na janela, e por **subagente** (lê em janela separada, devolve o resumo). **Mexer** em B vem pra cá — `adicionar <B> (trava: <A>)` — e a janela segue em A, ou para. E é o destino do que sobra quando o hook `alerta_contexto.py` avisa que a janela passou de **75%**: fecha-se A, anota-se o resto aqui e `/clear`.

E é o **único lugar do "fora de escopo"**, que quer dizer **"não agora"**: decidido numa conversa, numa data, com um motivo; volta quando o owner decidir — **nunca é proibição**. Uma linha por item, com a tag:

```
- <o que ficou para depois> #fora-de-escopo (decidido: AAAA-MM-DD, motivo curto)
```

Motivo longo vai pro `docs/decisoes.md`. **Você nunca cita um item `#fora-de-escopo` sozinho** — nem a busca automática o lê: ele aparece quando o owner pede (`listar #fora-de-escopo`).

A lista vive em **`to-dolist.md` na raiz do projeto** (não na pasta do plugin) e **vai pro git**, pra não se perder ao trocar de máquina. Custo: item anotado numa branch só aparece na `main` depois do merge.

Interprete `$ARGUMENTS`:

1. **`adicionar <texto>`** — acrescente uma linha no fim de `to-dolist.md` (crie o arquivo na raiz se não existir): `- <texto> (add: <data de hoje, AAAA-MM-DD>)`. Se o texto traz **`#fora-de-escopo`**, a linha sai no formato acima — `- <texto> #fora-de-escopo (decidido: <data de hoje>, <motivo>)`; sem motivo no texto, **pergunte** antes de gravar. Confirme o que anotou.
2. **`listar`** — leia `to-dolist.md` e mostre os itens **numerados** (1..N), na ordem do arquivo. **`listar #fora-de-escopo`** mostra só os que têm a tag, com a numeração do arquivo inteiro (a mesma do `feito`). Se não existir ou estiver vazio, diga que a lista está vazia.
3. **`feito <n>`** — remova a **n-ésima** linha da lista (numeração do `listar`). Confirme qual item saiu. Não arquive em outro canto — sai e pronto. Item `#fora-de-escopo` que o owner decidiu fazer sai assim quando vira feature.

Regras:
- Não invente itens; mexa só no que o texto pedir.
- É só captura rápida — não vira spec nem plano. Quando for realmente fazer um item: feature → `/mss-spec:nova-feature`; senão trate como bugfix/ajuste normal.

Entrada: **$ARGUMENTS**
