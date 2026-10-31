---
name: project_rode_a_peca_com_os_padroes_antes_de_dizer_pronto
description: teste que passa o parâmetro não prova o valor padrão — antes de dizer "pronto", rode a peça de verdade como ela será chamada (sem parâmetros); no PowerShell 5.1 com -File, $PSScriptRoot chega vazio no default do param
gatilho: quando declarar pronto um script, hook ou comando que tem valor padrão (default de param, variável de ambiente, caminho calculado) e os testes só passam valores explícitos
metadata:
  type: project
---

O guardião da junção (`templates/guardiao-da-juncao.ps1`, 0.51.0) passou nos 8 testes e **falhou na 1ª rodada de
verdade**: `Split-Path : Não é possível associar o argumento ao parâmetro 'Path' porque ele é uma cadeia de
caracteres vazia`. Os testes passavam `-Alvo` explícito; chamado sem parâmetros, como o hook e a tarefa agendada
chamam, o default `[string]$Alvo = (Split-Path -Parent $PSScriptRoot)` recebia `$PSScriptRoot` **vazio** — no
PowerShell 5.1 invocado com `-File`, essa variável ainda não existe quando os defaults do `param` são avaliados.

**Why:** a peça que vale é a que roda sozinha, do jeito que o sistema a chama. Suíte verde com parâmetros
explícitos é prova do caminho que ninguém usa.

**How to apply:** (1) calcule o padrão **no corpo**, não no `param`: `if (-not $Alvo) { $Alvo = Split-Path -Parent
(Split-Path -Parent $MyInvocation.MyCommand.Path) }`; (2) todo script/hook com default ganha **um teste sem o
parâmetro** (`test_sem_alvo_usa_o_clone_onde_o_script_mora`); (3) antes de dizer "pronto", **rode a peça uma vez
como ela será chamada** (sem argumentos, do diretório que o chamador usa) e cole a saída — foi isso que pegou o
erro. Vale para hook (`python hook.py < evento.json`), tarefa agendada, comando do kit lido "à mão". Caso F-049.
Relacionado: [[project_hook_stop_devolve_por_json_nao_por_exit_2]] (hook se prova no transcript, não no registro).
