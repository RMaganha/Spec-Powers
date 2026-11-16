---
name: feedback_conferir_a_branch_antes_do_commit
description: Commit que vem depois de um tempo gravando (captura, fecho) confere antes a branch — o owner pode ter feito o merge no meio e o commit cai direto na main
gatilho: quando for commitar depois de um tempo gravando (captura, fecho), ou quando o owner pode ter feito merge no meio da tarefa
sem_gatilho_de_acao: o commit é passo de toda tarefa; negar o 1º de cada conversa seria ruído — a conferência é ler o `git status -sb` antes
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-10-29-memoria-na-hora-da-proposta.md:44
metadata:
  type: feedback
---

Antes do commit que fecha uma captura ou uma entrega, rode `git status -sb` e leia a branch. Se o owner fez o merge
enquanto você gravava, a pasta voltou para a `main` e o commit cai **direto nela**.

**Why:** aconteceu duas vezes seguidas. Em 2026-10-28 o owner fez o merge e o push enquanto a captura era gravada:
*"meu commit da captura entrou nela"* (memory/sessions/2026-10-28-upgrade-converte-to-dolist.md:39); em 2026-10-29 o
commit `7e5d505` caiu direto na `main`: *"eu não conferi a branch antes"*
(memory/sessions/2026-10-29-memoria-na-hora-da-proposta.md:44). O hook de publicação deixa o commit passar.

**How to apply:** `git status -sb` num comando, sozinho; leia a saída; está na `main` com mudança por commitar → pare
e pergunte ao owner (abrir branch curta a partir dali ou commitar na `main`, decisão dele). Parente de
[[feedback_feature_a_partir_da_master]] (a mesma conferência, na abertura).
