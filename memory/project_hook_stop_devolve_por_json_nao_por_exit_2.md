---
name: project_hook_stop_devolve_por_json_nao_por_exit_2
description: hook Stop que devolve a resposta sai por JSON {"decision":"block","reason":…} com exit 0 — exit 2 + motivo no stderr era lido nesta máquina como "Hook script appears to be missing" (setlocale do Git Bash) e nunca chegou; hook novo se prova no transcript, não só no registro
gatilho: quando escrever ou alterar um hook do kit que bloqueia ou devolve, ou quando um hook parecer não agir ao vivo
metadata:
  type: project
---

Nesta máquina o Git Bash imprime `setlocale: LC_ALL: cannot change locale (enu): No such file or directory` no
stderr de **todo** hook (a variável `LC_ALL` do Windows está em `enu`). Com **exit 2**, o Claude Code lê esse
"No such file or directory" como *"Hook script appears to be missing"* e grava a saída como erro
**não-bloqueante**: a devolução do `Stop` nunca chegou ao assistente. Medido em 2026-10-30 nas transcrições
(`~/.claude/projects/<proj>/*.jsonl`, entradas `attachment` do tipo `hook_non_blocking_error`): **pelo menos 40
devoluções do `confere_citacoes.py` de 25/09 a 30/10, nenhuma entregue** — enquanto o registro local dizia
`devolveu`. F-034, F-035 e F-047 nunca agiram ao vivo. O que sempre funcionou com o mesmo stderr: `PreToolUse`
negando com exit 2 (o `git_publicacao.py`) e qualquer hook com **exit 0 + JSON** (recall, regras do kit).

**Why:** caso F-048 — a rede de segurança do fecho de resposta foi construída e ampliada por cinco semanas
sobre um hook que não entregava, e o owner viu "cada vez pior".

**How to apply:** `Stop` (e `UserPromptSubmit` que bloqueia) → `print(json.dumps({"decision": "block",
"reason": motivo}))` + `sys.exit(0)`, em ASCII puro (`json.dumps` sem `ensure_ascii=False`). `PreToolUse` →
JSON `permissionDecision` + exit 2, como está. Hook novo ou alterado só se declara funcionando depois de
**achar a devolução no transcript ao vivo** (`attachment` com o motivo, ou a resposta corrigida logo depois),
não pelo `registro-hooks.jsonl`. O `doctor` (check 12) avisa o `LC_ALL`; o conserto da variável é do owner.
Relacionado: [[project_hook_ask_aparece_no_desktop]], [[project_heredoc_grande_com_acento_quebra_no_git_bash]],
[[reference-historico-mostra-o-que-carregou]].
