---
name: project_hooks_dependem_do_git_bash
description: Os hooks do kit rodam pelo Git Bash; quando ele some (`bash.exe' not found`), o Claude trata como erro que não bloqueia e todas as cercas ficam desligadas sem aviso
gatilho: quando suspeitar que uma cerca ou hook do kit não agiu numa conversa
conferida: 2026-11-23 — confirmada — fonte: memory/sessions/2026-11-23-kit-de-fora-na-edicao.md:16
metadata:
  type: project
---

Os hooks do kit são chamados em linha única (`python "${CLAUDE_PLUGIN_ROOT}/hooks/x.py"`), e no Windows o Claude
Code roda essa linha pelo Git Bash. Quando o Git Bash falha, cada hook devolve:

`Skipping command-line '"C:\Program Files\Git\bin\..\usr\bin\bash.exe"' ('C:\Program Files\Git\bin\..\usr\bin\bash.exe' not found)`

O Claude trata isso como erro que **não bloqueia** (`attachment.type == "hook_non_blocking_error"`): a ferramenta
roda, e **todas** as cercas (publicação, banco de produção, kit primeiro, recall, Stop) ficam desligadas, sem aviso
ao owner nem ao assistente.

Aconteceu em 2026-11-19, das 19:58:55 às 20:33:43 UTC, com 192 falhas, só na conversa "Análise de consultas de
apólice e boleto" do Atendimento WhatsApp; o clone do kit não mudou de branch nessa hora e hoje o `bash.exe` existe.
Por que sumiu, não se sabe.

**Como conferir:** na conversa gravada (`~/.claude/projects/<pasta>/<sessão>.jsonl`), conte os registros
`hook_non_blocking_error` com `bash.exe` e veja a primeira e a última hora. **Alternativa sem o Git Bash:** o
commit `d6a0c01` (branch `fix/hooks-sem-bash`, exec form), descartado por velocidade em `docs/decisoes.md:87`;
voltar a ele é decisão do owner (`to-dolist.md`). Relacionado: [[reference-historico-mostra-o-que-carregou]],
[[reference_tempo_real_dos_hooks]].
