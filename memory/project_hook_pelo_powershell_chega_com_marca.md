---
name: project_hook_pelo_powershell_chega_com_marca
description: Provar um hook do kit como processo — pelo pipe do PowerShell 5.1 o evento chega com a marca de codificação no começo e o hook sai calado; chame pelo Bash, lendo o evento de um arquivo
gatilho: quando provar um hook do kit como processo, mandando o evento JSON pela entrada do programa
gatilho_comando: \|\s*python(?:\.exe)?\s+["']?\S*hooks[\\/]\w+\.py
metadata:
  type: project
---

Nesta máquina (PowerShell 5.1), o texto mandado pelo pipe a um programa chega com a marca de codificação no
começo (`\xef\xbb\xbf`). Os hooks do kit leem o evento com `json.load(sys.stdin)`: com a marca a leitura falha, e
como todo hook falha aberto, ele **sai calado** — parece que "deixou passar" quando na verdade nem leu o evento.
O app não chama hook assim; só acontece em teste manual.

**Como provar um hook como processo (funciona):** no Bash, lendo o evento de um arquivo.

```bash
python hooks/regra_antes_de_gravar.py < "<caminho do evento>.json"
```

**O que sai calado (não use):** no PowerShell, pelo pipe.

```powershell
Get-Content "<caminho do evento>.json" -Raw | python hooks\regra_antes_de_gravar.py
```

**Como conferir a marca:** no PowerShell,

```powershell
'{"a": 1}' | python -c "import sys; print(repr(sys.stdin.buffer.read()))"
```

mostrou `b'\xef\xbb\xbf{"a": 1}\r\n'` em 2026-11-12 (`$OutputEncoding` em utf-8).

**Why:** 2026-11-12, prova do `hooks/_comando_inteiro.py` (0.60.0). A 1ª chamada pelo PowerShell saiu vazia duas
vezes e eu cheguei a suspeitar do hook; carregando o mesmo evento de um arquivo, a conferência negava como devia.
Pelo Bash: a 1ª chamada negou com o trecho no motivo e a repetição passou.

**How to apply:** evento num arquivo `.json` (no scratchpad), hook chamado pelo Bash com `<`. Use um número de
conversa novo a cada prova: as conferências de "uma vez por conversa" guardam estado no temp do SO. Hook calado
num teste manual → confira primeiro como o evento chegou, antes de mexer no hook. Decidir se os hooks passam a
tolerar a marca está no `to-dolist.md` (2026-11-12). Parente de
[[project_rode_a_peca_com_os_padroes_antes_de_dizer_pronto]].
