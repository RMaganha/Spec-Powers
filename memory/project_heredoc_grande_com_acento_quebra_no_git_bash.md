---
name: project_heredoc_grande_com_acento_quebra_no_git_bash
description: heredoc grande (dezenas de linhas) com acentos passado ao Bash tool corrompe bytes (locale enu) e parte strings; script com acento vai pro scratchpad via Write e roda por arquivo
gatilho: quando rodar pelo Bash tool um script Python de mais de ~30 linhas com acentos ou travessão
metadata:
  type: project
---

2026-09-15: um `python - <<'PYEOF'` com ~140 linhas de substituições em português quebrou com
`SyntaxError: unterminated triple-quoted string` e "here-document delimited by end-of-file" — os
caracteres acentuados chegaram corrompidos (`me�a`) e a estrutura de linhas se perdeu. O shell avisa
`setlocale: LC_ALL: cannot change locale (enu)` em todo comando. Heredocs **curtos** com acento passaram
na mesma sessão; o problema aparece com volume.

**How to apply:** script com acento/travessão → grave no scratchpad com `Write` (UTF-8) e rode
`python "<scratchpad>/arquivo.py"`. Vale também pra mensagens de commit longas (`git commit -F arquivo`).
Relacionado: a memória do Whats `powershell-quebra-argumento-nativo` (mesma família: passe por arquivo).
