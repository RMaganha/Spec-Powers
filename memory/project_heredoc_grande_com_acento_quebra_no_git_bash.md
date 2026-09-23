---
name: project_heredoc_grande_com_acento_quebra_no_git_bash
description: heredoc grande (dezenas de linhas) com acentos passado ao Bash tool corrompe bytes (locale enu) e parte strings; script com acento vai pro scratchpad via Write e roda por arquivo
gatilho: quando rodar pelo Bash tool um script Python com acentos, travessão ou regex
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
**2026-09-23 — não é só volume:** um heredoc de 8 linhas com acento também falhou (o `assert` não achou
a âncora do INDEX), e regex escrito em string **não-raw** dentro de script de edição virou caractere
de controle (`\\b` gravou um backspace real no hook — 76 testes vermelhos). Regra: edição de arquivo
com acento ou regex vai pelo `Edit` ou por script gravado com `Write`, nunca por heredoc.

**E a cerca de publicação lê o heredoc como comando:** mensagem de commit que cite `docker push` ou
`(gh pr merge` no começo de uma linha é negada. É de propósito — pular o corpo do heredoc abriria
`bash <<EOF … git push origin main … EOF`. Mensagem de commit que fala dos comandos vai por
`git commit -F <arquivo>`.

Relacionado: a memória do Whats `powershell-quebra-argumento-nativo` (mesma família: passe por arquivo).
