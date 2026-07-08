# Plano de teste base — kit mss-spec

**Comando:** `python -m pytest tests/ -q`

**O que o baseline cobre** (1 linha por teste):
- `test_plugin_root_refs_existem` — todo `${CLAUDE_PLUGIN_ROOT}/<caminho>` citado em commands/ e skills/ existe no repo (pega referência morta, ex-ff4d384)
- `test_templates_citados_existem` — todo `` `templates/...` `` citado nos commands existe
- `test_manifestos_validos_e_coerentes` — plugin.json e marketplace.json parseiam, nome bate, versões iguais
- `test_commands_tem_frontmatter` — todo comando tem frontmatter com `description`
- `test_compose_templates_sao_yaml_validos` — os dois compose templates parseiam como YAML (com `<servico>` substituído)

**Fora do baseline (manual):** resolução de `${CLAUDE_PLUGIN_ROOT}` via junction em runtime — validar rodando `/mss-spec:kickoff` num projeto de teste.

**Último 100% verde:** 2026-07-08 · commit `25abbf9` · 5 passed
