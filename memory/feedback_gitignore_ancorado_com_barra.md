---
name: feedback_gitignore_ancorado_com_barra
description: Linha do .gitignore sem barra casa em qualquer pasta — já engoliu commands/to-dolist.md e commands/mapa-neural.md; arquivo da raiz se ancora com / no começo
gatilho: quando acrescentar uma linha ao .gitignore
sem_gatilho_de_acao: a ação é gravar arquivo (o .gitignore), que o gatilho de comando e de resposta não enxerga
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-07-20-mapa-de-contexto-e-mapa-neural.md:21
metadata:
  type: feedback
---

No `.gitignore`, um padrão **sem barra** casa com o nome em **qualquer pasta**. Para ignorar só o arquivo da raiz,
ancore com `/` no começo (`/to-dolist.md`, não `to-dolist.md`).

**Why:** aconteceu duas vezes no kit. Em 2026-07-16 `to-dolist.md` ignorou também `commands/to-dolist.md`
(memory/sessions/2026-07-16-analises-externas-backlog-e-features.md:16); em 2026-07-20 um padrão sem âncora engoliu
`commands/mapa-neural.md`, o arquivo do próprio comando (memory/sessions/2026-07-20-mapa-de-contexto-e-mapa-neural.md:21).
O arquivo some do git sem aviso nenhum.

**How to apply:** linha nova no `.gitignore` → é da raiz? começa com `/`. Depois, `git check-ignore -v <arquivo>`
nos arquivos de mesmo nome em outras pastas para ver que não foram pegos.
