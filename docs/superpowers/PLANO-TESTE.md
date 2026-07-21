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
- `test_mapa_contexto_wiring` — mapa de contexto F1: `templates/MAPA.md` (3 seções + Conexões do código real/não inventar), comando `/mss-spec:mapa` (lê+reconcilia git/INDEX/Conexões), e os 4 pontos de integração (kickoff cria · CLAUDE lê na partida · nova-feature mantém)
- `test_mapa_neural_wiring` — mapa mental F2: gerador `templates/mapa_neural.py` + comando `/mss-spec:mapa-neural` existem, o comando aponta o script e descreve as 4 dimensões, saída derivada gitignorada, LEIA-ME lista o comando
- `test_captura_memory_dois_modos` — `/mss-spec:memory` com 2 modos: `resgatar` (intacto) + `capturar` (roteia decisões/`decisoes.md`, "não fazer"/INDEX, `memory/sessions/`+`DIARIO.md`, `<private>`, chama `/mss-spec:mapa`, pede OK, não duplica, foca pivôs)
- `test_captura_diario_template` — `templates/DIARIO.md` existe (índice `## <data>` → `sessions/`, foco nos pivôs) + dogfood `memory/DIARIO.md`
- `test_captura_kickoff_scaffold` — kickoff copia `templates/DIARIO.md` → `memory/DIARIO.md` e cria `memory/sessions/`
- `test_captura_private_e_indice` — `templates/CLAUDE.md` documenta `<private>`, aponta o diário e reforça o índice-primeiro (nunca a pasta inteira)
- `test_captura_delegacao_fecho` — o fecho do `nova-feature` delega a captura ao `/mss-spec:memory capturar` (não re-descreve inline) + junto ao finishing
- `test_captura_hook_throttle` — `hooks/capturar_nudge.py::deve_cutucar` respeita o intervalo (sem histórico/passou → cutuca; dentro → não)
- `test_captura_hook_optin_doc` — hook opt-in existe e é documentado como off por padrão, não-bloqueante, só cutuca (Stop/PreCompact) pra rodar `/mss-spec:memory capturar`
- `test_captura_docs_leiame` — LEIA-ME documenta o modo `capturar`

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

`tests/test_mapa_neural.py` — comportamento do gerador do mapa mental do projeto (F2):
- `test_extrair_conexoes` — nó `conn` traz os projetos vizinhos declarados no `MAPA.md` (ignora `nenhuma`/`<a confirmar>`)
- `test_extrair_arquitetura` — nó `arq` lista as camadas presentes (`main.py`, `routers/`, `services/`)
- `test_arquitetura_traz_resumo_da_peca` — o índice traz o resumo de 1 linha (docstring/`description`) por peça — fonte de consulta, não só nomes
- `test_extrair_apis_endpoints_e_integracoes` — nó `api` traz rotas FastAPI + integração de banco; rota/import em `tests/` não conta
- `test_extrair_memorias` — nó `mem` traz specs + itens do índice `MEMORY.md`
- `test_construir_arvore_projeto_no_centro_com_4_dimensoes` — raiz = projeto com exatamente as 4 dimensões
- `test_render_html_full_screen_e_self_contained` — HTML sem `<script src=>`, full-screen (`100vh`), com a árvore embutida e o nome do projeto
- `test_render_texto_lista_as_dimensoes` — o índice `.md` lista as 4 dimensões
- `test_gerar_cria_md_e_html` — `gerar()` escreve o `.md` e o `.html`

**Fora do baseline (manual):** resolução de `${CLAUDE_PLUGIN_ROOT}` via junction em runtime — validar rodando `/mss-spec:kickoff` num projeto de teste.

**Último 100% verde:** 2026-07-21 · commit `b2de5fb` (branch feature/captura-de-memoria) · 51 passed
