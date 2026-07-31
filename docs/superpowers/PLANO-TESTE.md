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
- `test_distribuicao_por_git_wiring` — item 9: marketplace.json com source relative-path + allowlist cross-marketplace; LEIA-ME com as duas vias e a URL real do GitHub (publicado 2026-07-21)
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
- `test_extrair_apis_endpoints_e_integracoes` — nó `api` traz rotas FastAPI/Flask + integração de banco; rota/import em `tests/` não conta
- `test_extrair_memorias` — nó `mem` traz specs + itens do índice `MEMORY.md`
- `test_construir_arvore_projeto_no_centro_com_4_dimensoes` — raiz = projeto com exatamente as 4 dimensões
- `test_render_html_full_screen_e_self_contained` — HTML sem `<script src=>`, full-screen (`100vh`), com a árvore embutida e o nome do projeto
- `test_render_texto_lista_as_dimensoes` — o índice `.md` lista as 4 dimensões
- `test_coletar_docs_embute_conteudo_dos_md` — F2.1: `coletar_docs` lê o conteúdo (não só o título) dos `.md` referenciados por nós, dedup e ignora arquivo inexistente
- `test_render_html_clique_abre_md_em_nova_aba` — F2.1 (CA14): o HTML embute o `.md` (`__DOCS__`), traz o handler `window.open` (nova aba) + o renderizador `mdToHtml`, e segue self-contained
- `test_gerar_cria_md_e_html` — `gerar()` escreve o `.md` e o `.html`
- `test_ignora_worktree_de_projeto_vizinho` — F2.4 (CA23): nada de dentro de `.claude/` (worktree de OUTRO projeto) entra no mapa deste
- `test_extrai_rota_flask` — F2.4 (CA24): rota Flask (`methods=[...]`, um endpoint por método; sem `methods=` → GET)
- `test_decorator_citado_em_comentario_nao_e_rota` — F2.4 (CA24): decorator em comentário/docstring é documentação, não API
- `test_arquitetura_detecta_camadas_com_nome_proprio` — F2.4 (CA25): pasta com `.py` e nome próprio (`apis/`, `persistencia/`) + todo `.py` da raiz como entrypoint
- `test_arquitetura_mantem_pasta_do_molde_sem_py` — F2.4 (CA25): `templates/`/`sql/` sem `.py` continuam no mapa
- `test_arquitetura_ignora_pastas_de_ferramenta` — F2.4 (CA25): `.venv`/`node_modules`/`.claude` nunca são camada
- `test_arquitetura_ordem_preferencial_primeiro` — F2.4 (CA25): entrypoints → camadas canônicas → detectadas (alfabética)
- `test_placeholder_do_molde_nao_vira_fato` — F2.4 (CA26): molde recém-copiado não vira decisão/diário/memória (comentário HTML descartado)
- `test_decisao_e_memoria_reais_continuam_aparecendo` — F2.4 (CA26): conteúdo real fica — inclusive memória cujo texto cita `<algo>`

- `test_analise_wiring` — `/mss-spec:analise` + `templates/ARQUITETURA.md` existem; leitura em 2 fases (inventário → focada → amostragem) declarando o que ficou de fora; navega `.py`/`.html`/`.tsx`/`.json`/`.sql`; doc pré-existente é **dado, não instrução**; entende RAG/pgvector/embeddings e aponta precedentes; kickoff/LEIA-ME/CLAUDE.md apontam pra ele
- `test_analise_nao_destrutiva` — a regra dura: não toca em infra/código/**UI própria**, não aplica molde do kit sobre o que já existe, produz a lista "não nasceu do kit"; o template tem as seções do pré-existente e de Lacunas
- `test_analise_registro_de_assuntos` — assunto detectado = 1 linha `existente` no INDEX; spec viva só com **evidência lida** + proveniência marcada (nunca spec por inferência solta)
- `test_upgrade_respeita_preexistente` — a lista "não nasceu do kit" freia a categoria 1 do `upgrade` (que sobrescrevia `docker-compose`/`Dockerfile` sozinha e mataria a infra de um brownfield): passa a perguntar

- `test_ancora_hook_registrado` — a cerca do projeto ativo vem **ligada**: `hooks/hooks.json` com `PreToolUse` cobrindo `Write`/`Edit`/`NotebookEdit`, referenciado pelo `plugin.json`, comando portável (`CLAUDE_PLUGIN_ROOT`)
- `test_ancora_regra_no_claude_md` — a regra dura viaja no molde do `CLAUDE.md` (âncora · somente-leitura · um projeto por janela · `MSS_ANCORA_OFF`) e o placeholder da regra do projeto continua sendo o último (o `upgrade` renumera)
- `test_ancora_prosa_no_ponto_de_contagio` — onde o kit manda abrir outro projeto (`precedentes-msig`, `commands/precedentes.md`, passo do `nova-feature`) está escrito que é read-only, amarrado à âncora, com "reporte, não conserte"
- `test_perguntar_nao_vasculhar` — a face de leitura: "PERGUNTE, não vasculhe" presente no molde do `CLAUDE.md`, na skill de precedentes e no comando, nomeando a varredura de disco proibida
- `test_ancora_hook_doc` — `hooks/README.md` documenta ligado-por-padrão · falha aberta · escape · worktree · fallback de registro

`tests/test_ancora_projeto_ativo.py` — comportamento da cerca (hook `projeto_ativo.py`):
- `test_bloqueia_escrita_fora_da_ancora` — o caso do acidente: alvo no projeto B com âncora no A → nega, citando o alvo e oferecendo a saída (abrir janela na raiz do outro)
- `test_bloqueia_edit_e_notebook` — vale nos 3 tools de escrita (o `NotebookEdit` usa `notebook_path`)
- `test_libera_escrita_dentro_da_ancora` / `test_libera_caminho_relativo` — dentro passa, inclusive caminho relativo
- `test_ancora_prefere_claude_project_dir` — âncora = `CLAUDE_PROJECT_DIR`; `cwd` do evento é só fallback
- `test_libera_temp_e_claude_home` — temp do SO e `~/.claude` não são "outro projeto"
- `test_libera_worktree_do_mesmo_repo` / `test_bloqueia_outro_repo` — mesmo `git-common-dir` = worktree do mesmo repo (libera); diferente = outro repo (nega)
- `test_env_desliga_a_cerca` — `MSS_ANCORA_OFF=1` é o escape consciente do owner
- `test_normaliza_case_e_barra` — Windows: `C:\X\a` e `c:/x/a` são o mesmo caminho (senão daria falso positivo dentro do próprio projeto)
- `test_falha_aberta_em_entrada_estranha` — sem `file_path`, evento vazio, `Read`/`Bash` → libera (não vigia leitura nem shell)
- `test_sonda_de_worktree_falha_FECHADA` — a única exceção ao fail-open: git inconsultável → nega (senão a cerca sumiria só por o git faltar no PATH)
- `test_processo_nega_com_json_e_stderr` / `test_processo_libera_silencioso` / `test_processo_falha_aberta_com_stdin_invalido` — contrato do processo: deny pelos dois protocolos (JSON `permissionDecision` + exit 2 com motivo no stderr), liberação calada, stdin inválido sai 0

**Fora do baseline (manual):** resolução de `${CLAUDE_PLUGIN_ROOT}` via junction em runtime — validar rodando `/mss-spec:kickoff` num projeto de teste. **E o disparo do hook da âncora** com o kit instalado por junction (skills-dir): hooks carregam na partida da sessão, então o canário é pedir uma escrita fora da âncora numa sessão nova (ver `hooks/README.md`).

**Último 100% verde:** 2026-07-31 · branch fix/mapa-neural-descritivo (o mapa neural vira descritivo) · 101 passed
