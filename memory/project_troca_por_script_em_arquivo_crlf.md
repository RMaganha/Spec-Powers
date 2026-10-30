---
name: project_troca_por_script_em_arquivo_crlf
description: os .md do kit são CRLF — troca de texto por script com "\n" no trecho não acha nada; normalize o fim de linha e deixe o script rodar de novo sem estragar
gatilho: quando trocar texto num arquivo do kit por script Python (troca de trecho com mais de uma linha)
metadata:
  type: project
---

Os `.md` do kit (`docs/EVALS.md`, `CHANGELOG.md`, `docs/decisoes.md`, os índices de `memory/`…) usam fim de
linha CRLF. Lido com `newline=""`, o texto traz `\r\n`; o trecho escrito no script traz `\n`. A troca de um
trecho de **uma** linha funciona; a de **várias** linhas não acha nada (`count == 0`).

**Why:** no fecho da 0.49.0 (2026-10-29) o script de fecho fez duas trocas no `docs/EVALS.md`, gravou, e quebrou
na terceira (trecho de 2 linhas). O arquivo ficou pela metade, e rodar de novo falharia nas duas que já tinham
entrado.

**How to apply:**
- se o arquivo tem `\r\n`, troque `\n` por `\r\n` no trecho velho e no novo antes de procurar;
- a função de troca pula quando o texto novo já está lá e o velho não — assim o script roda de novo sem estragar;
- confira `count == 1` antes de gravar (achou 0 ou 2 → pare).
- Ver também [[project_heredoc_grande_com_acento_quebra_no_git_bash]]: grave o script com `Write`, não por heredoc.
