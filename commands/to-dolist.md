---
description: Caixa de captura rápida (to-do) visível em qualquer branch — adicionar/listar/feito num to-dolist.md local, fora do git
argument-hint: "[adicionar <texto> | listar | feito <n>]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Caixa de captura de ideias/ajustes que surgem **fora do contexto** da tarefa atual (ex.: no meio de uma feature de banco você vê uma melhoria numa tela de outro assunto). Em vez de fazer fora de hora e poluir a branch, registre aqui e siga no que estava.

A lista vive em **`to-dolist.md` na raiz do projeto** (não na pasta do plugin) e é **ignorada pelo git** de propósito: por não ser rastreada, o git não a toca ao trocar de branch — então ela aparece em **qualquer branch**. É pessoal, local e não versionada.

Interprete `$ARGUMENTS`:

1. **`adicionar <texto>`** — acrescente uma linha no fim de `to-dolist.md` (crie o arquivo na raiz se não existir): `- <texto> (add: <data de hoje, AAAA-MM-DD>)`. Confirme o que anotou. Garanta que o `.gitignore` da raiz ignora o arquivo com o padrão **ancorado** `/to-dolist.md` (com a barra — sem ela pegaria qualquer `to-dolist.md` em subpastas); adicione a linha se faltar. Essa lista nunca sobe pro git.
2. **`listar`** — leia `to-dolist.md` e mostre os itens **numerados** (1..N), na ordem do arquivo. Se não existir ou estiver vazio, diga que a lista está vazia.
3. **`feito <n>`** — remova a **n-ésima** linha da lista (numeração do `listar`). Confirme qual item saiu. Não arquive em outro canto — sai e pronto.

Regras:
- **Nunca commite `to-dolist.md`** nem rode `git add` nela — é local por design.
- Não invente itens; mexa só no que o texto pedir.
- É só captura rápida — não vira spec nem plano. Quando for realmente fazer um item: feature → `/mss-spec:nova-feature`; senão trate como bugfix/ajuste normal.

Entrada: **$ARGUMENTS**
