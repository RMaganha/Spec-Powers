---
name: project_versao_em_dois_manifestos
description: a versão do kit vive em DOIS manifestos (plugin.json + marketplace.json) e há teste de coerência — bumpe os dois juntos e re-rode a suíte APÓS o bump
metadata:
  type: project
---

A versão do mss-spec fica em **dois** arquivos: `.claude-plugin/plugin.json` **e**
`.claude-plugin/marketplace.json`. O smoke `test_manifestos_validos_e_coerentes` **exige que sejam
iguais** (`plugin["version"] == market["version"]`).

No release: **bumpe os dois juntos** e **re-rode `pytest` DEPOIS do bump**. Bumpar só o `plugin.json`
deixa a `main` vermelha — aconteceu na v0.11.0 (rodei a suíte antes do bump, mergeei, e o
`marketplace.json` defasado quebrou o teste de coerência). Lição casada com o
[[feedback_nao_encerrar_com_pergunta]] só no espírito de "verifique antes de declarar pronto":
**qualquer bump/edição pós-suíte pede re-rodar a suíte**.

Relacionado: [[project_marketplace_relative_path_serve_git_e_local]] (o mesmo `marketplace.json`
serve add por pasta local e por URL git).
