---
name: project_claude_code_apaga_conversa_antiga
description: O Claude Code apaga sozinho as conversas paradas há mais de cleanupPeriodDays dias (padrão 30; nesta máquina 730) — conversa antiga é volátil, evidência vai pro diário
gatilho: quando contar com uma conversa gravada antiga (sono da memória, ler outra conversa, citar uma conversa como fonte)
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-10-14-protecao-do-historico-de-conversas.md:13
metadata:
  type: project
---

O Claude Code apaga sozinho as conversas paradas há mais de `cleanupPeriodDays` dias (o padrão é 30). `0` falha na
validação e um plugin não consegue definir essa chave. Nesta máquina ela estava em 730 em 2026-10-14. O owner já
perdeu conversas do ATA por isso ("Sessão não encontrada no disco")
(memory/sessions/2026-10-14-protecao-do-historico-de-conversas.md:13).

**Consequência:** conversa gravada é volátil. Por isso o sono da memória lê as conversas e põe a evidência no diário
(`memory/sessions/`) antes de citar — fonte gravada nunca aponta para o `.jsonl` (`docs/specs/sono-da-memoria.md`,
decisão 18).
