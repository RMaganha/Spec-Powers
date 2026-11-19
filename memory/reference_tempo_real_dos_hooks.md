---
name: reference_tempo_real_dos_hooks
description: quanto cada hook do kit demorou de verdade está no arquivo da conversa — durationMs no attachment hook_success e no stop_hook_summary; medir por imitação deu conclusão errada
gatilho: quando medir, comparar ou discutir quanto um hook do kit demora, ou propor conserto de lentidão dos hooks
metadata:
  type: reference
---

Visto em 2026-11-18 (diário `memory/sessions/2026-11-18-custo-dos-hooks.md`): o Claude anota, no `.jsonl` de cada
conversa em `~/.claude/projects/<pasta-do-projeto>/`, quanto cada hook levou:

- registro `"type": "attachment"` com `attachment.type == "hook_success"`: `hookEvent`, `command`, `durationMs`,
  `exitCode`, `stderr` (abertura da conversa e parte dos hooks de ferramenta);
- registro `"type": "system"`, `"subtype": "stop_hook_summary"`: `hookInfos[]` com `command` e `durationMs` de cada
  hook do fim da resposta — aparece em toda resposta.

Os hooks de um evento rodam **em paralelo** (documentação do Claude Code, code.claude.com/docs/en/hooks): a espera
é o hook mais lento, não a soma. Ler sempre a partir de **cópia** das conversas, numa pasta descartável.

Por que importa: a imitação (`python hook.py` com JSON no stdin) apontou "os hooks releem a conversa inteira, 3,3 s
com 18 MB"; no real a conversa não pesou (0,9 s acima de 10 MB). Real medido: ~1 a 2 s por ação; abertura ~3 s.
Ajudantes rodando em paralelo (o sono abre 6 a 7) levam o fim da resposta a até 9 s — separe esses momentos antes
de comparar.
