---
name: reference-historico-mostra-o-que-carregou
description: Os históricos .jsonl do Claude Code mostram quando uma regra, memória ou arquivo de instrução entrou de fato na janela — attachment nested_memory (no meio da conversa) e instructions (na abertura)
gatilho: quando precisar saber se uma regra, memória ou CLAUDE.md entrou de fato na janela de um projeto
metadata:
  type: reference
---

Os históricos ficam em `~/.claude/projects/<pasta-do-projeto>/*.jsonl` (o nome da pasta é o caminho do projeto
com os separadores virando `-`). Cada linha é um JSON:
- `"attachment": {"type": "nested_memory", "path": ...}` → regra/arquivo de instrução carregado **no meio** da
  conversa (é assim que aparece uma regra de `.claude/rules/` com `paths:`);
- `"attachment": {"type": "instructions", "files": [...]}` → o que carregou **na abertura** (CLAUDE.md, regras
  sem `paths:`);
- `message.content[]` com `type: "tool_use"` e `name` `Read`/`Edit`/`Write` → o arquivo que o assistente tocou
  (`input.file_path`).
Cruzando os dois por conversa dá pra contar "tocou arquivo que casa e a regra NÃO carregou".

**Armadilha (2026-10-23):** filtre pelo **timestamp** de quando a regra passou a existir (`git log
--diff-filter=A`). A 1ª contagem no Whats, sem esse filtro, deu de 24 a 37 "falhas" por regra — eram conversas de
antes de as regras nascerem. Com o filtro, sobraram as falhas reais (banco 5, testes 2).

**How to apply:** script descartável no scratchpad, lendo os `.jsonl` como dado (`python -I`). Foi a medição que
trocou a opinião ("o índice deve funcionar") por número antes do desenho — [[project-regra-por-tipo-carrega-ao-ler]].

**Mais sinais no `.jsonl` (2026-10-30, F-048):** `"type": "attachment"` com `attachment.type` =
`hook_additional_context` (o que um hook `UserPromptSubmit`/`SessionStart` **injetou** — o recall aparece aqui) ·
`hook_non_blocking_error` com *"Hook script appears to be missing"* (devolução de `Stop` que o Claude Code
**engoliu**: exit 2 + "No such file or directory" no stderr) · mensagem `user` começando com `Stop hook feedback:`
(devolução **entregue**). Contar os dois últimos por data foi o que mostrou 40+ devoluções perdidas em 5 semanas.
`<pasta>/<sessão>/custom-title.json` traz o título da conversa; a ferramenta `list_sessions` do app liga título →
pasta do projeto, e o registro local (`~/.claude/mss-spec/registro-hooks.jsonl`, campo `sessao` = 8 primeiros
caracteres do id) diz o que cada hook **achou** que fez — cruzar os dois é a prova. Relacionado:
[[project_hook_stop_devolve_por_json_nao_por_exit_2]].
