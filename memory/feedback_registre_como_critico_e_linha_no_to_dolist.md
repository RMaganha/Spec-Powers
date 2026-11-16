---
name: feedback_registre_como_critico_e_linha_no_to_dolist
description: "Registre como crítico" é uma linha no to-dolist.md marcada CRÍTICO — não abre branch, não vira caso do EVALS nem feature
gatilho: quando o owner pedir para registrar algo como crítico, anotar um problema ou "deixar registrado"
sem_gatilho_de_acao: a ação é gravar arquivo (o to-dolist.md), que o gatilho de comando e de resposta não enxerga
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-10-28-agentes-ou-comandos-e-upgrade-do-mss-utils.md:16
metadata:
  type: feedback
---

Quando o owner diz "registre como crítico" (ou "anota isso"), ele quer **uma linha no `to-dolist.md`** com a marca
CRÍTICO — nada mais. Não abra branch, não grave caso no `docs/EVALS.md`, não abra feature.

**Why:** em 2026-10-28 o assistente abriu branch para registrar no EVALS; o owner: *"Não era para abrir branch nem
nada era para por no to-dolist!"* (memory/sessions/2026-10-28-agentes-ou-comandos-e-upgrade-do-mss-utils.md:16).

**How to apply:** a linha diz o problema e onde foi visto; o conserto vem depois, numa conversa própria. Caso do
EVALS só nasce na captura, com o OK dele (`commands/memory.md`, modo capturar).
