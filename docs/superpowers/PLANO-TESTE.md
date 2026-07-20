# Plano de teste base — kit mss-spec

**Comando:** `python -m pytest tests/ -q`

**O que o baseline cobre** (1 linha por teste):

`tests/test_smoke_kit.py` — smoke do próprio kit (referências, manifestos, wiring de cada capacidade):
- `test_plugin_root_refs_existem` — todo `${CLAUDE_PLUGIN_ROOT}/<caminho>` citado em commands/ e skills/ existe no repo (pega referência morta, ex-ff4d384)
- `test_templates_citados_existem` — todo `` `templates/...` `` citado nos commands existe
- `test_manifestos_validos_e_coerentes` — plugin.json e marketplace.json parseiam, nome bate, versões iguais
- `test_commands_tem_frontmatter` — todo comando tem frontmatter com `description`
- `test_compose_templates_sao_yaml_validos` — os dois compose templates parseiam como YAML (com `<servico>` substituído)
- `test_seguranca_wiring` — SEGURANCA.md + comando existem, kickoff copia, CLAUDE.md referencia
- `test_todolist_gitignorada` — `/to-dolist.md` ancorado no `templates/gitignore`
- `test_doctor_wiring` — comando doctor existe e o CLAUDE.md manda rodar o pré-vôo na 1ª tarefa
- `test_robustez_plugin_root_wiring` — doctor e kickoff citam o fallback de resolução do plugin (`plugins/cache`)
- `test_regra_senhas_wiring` — banco oferece variável de ambiente e SEGURANCA documenta App Settings
- `test_anotar_decisoes_wiring` — DECISOES.md existe, kickoff copia, CLAUDE.md mapeia, nova-feature acrescenta
- `test_log_wiring` — logging.py + comando existem, kickoff monta infra, `/logs/` ignorado, CLAUDE.md carrega a regra
- `test_protocolo_log_por_arquivo_wiring` — instrumentação opt-in por-arquivo (canônica no log.md; apontada por banco/nova-feature)
- `test_release_wiring` — release orquestra testes/segurança/CHANGELOG/compliance e é gate antes do finishing
- `test_regras_branch_e_escopo_wiring` — branch sempre da principal + regra "um assunto por janela" (CLAUDE/nova-feature/to-dolist)
- `test_compliance_wiring` — compliance checa estrutura/decisões/memória/spec-driven e delimita papel (seguranca/upgrade)
- `test_upgrade_dry_run_wiring` — modo `--dry-run` do upgrade: preview opt-in com diff unificado da categoria 1, sem escrever arquivo, e diz como aplicar (rodar sem a flag)
- `test_redes_de_seguranca_documentadas` — as 3 redes já existentes (auto-teste, git-rollback, changelog) explícitas no HTML/upgrade/kickoff/LEIA-ME
- `test_distribuicao_por_git_wiring` — item 9: marketplace.json com source relative-path + allowlist cross-marketplace; LEIA-ME com as duas vias e `<URL-do-git-interno>` como placeholder

`tests/test_ci.py` — CI com artefatos de teste (item 12), no estilo do wiring do item 9:
- `test_ci_declara_reports_junit_e_cobertura` — o job do `.gitlab-ci.yml` declara `artifacts.reports.junit` e `coverage_report` (formato `cobertura`)
- `test_ci_job_gera_junit_e_cobertura_no_comando` — o comando do job emite `--junitxml`, `--cov` e `--cov-report=xml`
- `test_flags_de_ci_nao_vazam_pro_pytest_local` — nenhum `addopts` de pytest carrega os flags de CI (mantém `pytest -q` local limpo)
- `test_run_output_gitignorado` — `report.xml`, `coverage.xml`, `htmlcov/`, `.coverage` ignorados (run output nunca entra no repo)
- `test_ci_sem_host_inventado_placeholder` — preparado, NÃO ativado: sem host git inventado; ativação é passo do owner (como o item 9)

`tests/test_logging_template.py` — comportamento do `templates/logging.py`:
- `test_stdout_no_nivel_default_info` — no nível default (INFO) manda pro stdout
- `test_log_level_filtra_abaixo` — `LOG_LEVEL` filtra o que está abaixo
- `test_log_ativo_false_so_warning_pra_cima` — `LOG_ATIVO=false` → só WARNING+
- `test_dev_grava_arquivo_rotativo` — em dev grava arquivo rotativo em `logs/`
- `test_azure_nao_grava_arquivo` — em Azure (prod) não grava arquivo (só stdout)
- `test_icone_por_nivel_so_em_dev` — ícone por nível só em dev
- `test_azure_sem_icone` — em Azure, texto limpo sem ícone
- `test_idempotente_nao_duplica_handlers` — chamar `setup_logging()` de novo não duplica handlers

**Fora do baseline (manual):** resolução de `${CLAUDE_PLUGIN_ROOT}` via junction em runtime — validar rodando `/mss-spec:kickoff` num projeto de teste.

**Último 100% verde:** 2026-07-20 · commit `e1b56b5` (branch feature/ci-artefatos-teste) · 32 passed
