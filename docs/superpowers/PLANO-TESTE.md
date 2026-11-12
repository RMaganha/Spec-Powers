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
- (0.47.0) o to-dolist vai pro git — o antigo `test_todolist_gitignorada` virou `test_todolist_vai_pro_git_no_molde_e_no_kit` em `tests/test_fora_de_escopo_no_to_dolist.py`
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
- `test_upgrade_em_uma_rodada_wiring` — (0.54.0) o upgrade abre pelo `upgrade_plano.py checar`, trata os 3 passes na ordem e na mesma conversa (sem "Termine aqui"), stash único do pendente do owner (nunca commitar), uma branch `chore/upgrade-kit`, um commit por passe, `--ff-only` de volta pra branch do owner e conferência colada; `test_upgrade_migra_primeiro_num_commit_so` / `test_upgrade_branch_antes_da_migracao_na_ordem` seguem o desenho novo
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
- `test_limite_corta_com_marcador` — F2.5 (CA27): corte deixa `… (+N)`; nunca silencioso
- `test_limite_padrao_nao_corta_projeto_real` — F2.5 (CA28): 36 memórias aparecem inteiras no default
- `test_camada_entra_por_conteudo_nao_por_extensao` — F2.5 (CA29): `web/` (HTML), `prompts/` (MD) e `n8n/` (JSON) são camadas; `docs/`/`memory/`/pasta vazia não
- `test_camada_desce_nas_subpastas` — F2.5 (CA30): a arquitetura desce (`apis/` → `v1/` → `esquemas/` → `item.py`)
- `test_camada_no_gitignore_fica_fora` — F2.5 (CA31): o que o projeto manda o git ignorar não entra no mapa
- `test_camada_ignorada_por_parametro` — F2.5 (CA31): `--ignorar` tira pasta versionada
- `test_rota_de_pasta_ignorada_nao_conta` — F2.5 (CA31): pasta fora do mapa não expõe endpoint
- `test_arquivo_morto_e_certificado_ficam_fora` — F2.5/0.17.1 (CA32): `backup/` e `certs/` fora por default (cópia arquivada não pode aparecer como par do arquivo vivo)
- `test_n8n_continua_sendo_camada` — F2.5/0.17.1 (CA32): a exceção é só arquivo morto/insumo — `n8n/` (fluxos do projeto) continua camada
- `test_resumo_de_modulo_com_docstring_longa` — F2.5 (regressão): resumo sai da abertura da docstring, sem exigir o fecho na janela

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

`tests/test_hook_git_publicacao.py` — cerca de publicação POR DESTINO (hook `git_publicacao.py`, F-022; 0.31.0):
- `test_nega_push_protegido_indeterminado_e_deploy` (×33) — push pra main/master/dev/develop/production/homolog*/hml*/prod*/release/* (refspec, `HEAD:dev`, `x:main`, `+x:master`, `refs/heads/…`, `--delete`, dois refspecs, `-C`, encadeado, `VAR=x`, tab, multilinha), `--all`/`--mirror`/`--tags`/`:`, `gh pr merge`, `docker push`, `az …` → negados, motivo cita o owner e o `/mss-spec:release`
- `test_push_sem_refspec_nega_quando_o_destino_e_protegido_ou_incerto` (×6) / `test_git_inconsultavel_nega_push_sem_destino_explicito` — `git push` puro em protegida, feature rastreando `origin/dev`, HEAD destacado, git que não responde → negado (falha fechada)
- `test_nega_tambem_no_powershell` / `test_negacao_vence_pedido_no_mesmo_comando` — PowerShell; negar vence perguntar (inclusive a cerca do pipe)
- `test_pede_aprovacao_pra_integrar_e_push_de_feature` (×12) — merge, rebase, push de feature/fix (explícito, `HEAD:feature`, puro, `-u origin HEAD`, `cd … &&`) → `ask`
- `test_consulta_o_git_na_pasta_do_comando` / `test_push_com_destino_explicito_nao_consulta_o_git` — `-C` › `cd` › cwd; destino explícito não chama o git
- `test_libera_o_resto` (×26) — inclui `merge-base`/`merge-tree`/`merge-file` (falso positivo da 0.30.0) e `git pull`
- `test_outro_tool_nao_e_avaliado` / `test_escape_do_owner` / `test_evento_sem_comando_libera_calado` / `test_bug_na_avaliacao_falha_fechada` / `test_decidir_segue_devolvendo_o_motivo`
- `test_processo_*` (×5) — deny = JSON + exit 2 + stderr; **ask = JSON + exit 0, stderr vazio**; libera calado; não-JSON libera; **repo git real** (dev nega, feature pergunta)
- `test_hook_registrado_em_bash_e_powershell` / `test_documentado_no_readme_e_no_molde` — `hooks.json`, README (escape, falha fechada, aprovação, `release/*`) e `CLAUDE.md` (push de homologação/produção do owner, resto com aprovação)

`tests/test_hook_um_item_por_janela.py` — comportamento da cerca "um item por janela" (hook `um_item_por_janela.py`, F-022; por chat desde a 0.34.0):
- `test_lista_abertas_ignora_fechada_e_pausada` / `test_em_andamento_conta_como_aberta` / `test_indice_vazio_nao_tem_aberta` — parser do INDEX: `aberta` e `em andamento` contam; `fechada`/`pausada` não
- `test_chat_novo_passa_mesmo_com_outra_aberta` / `test_chat_novo_com_outra_aberta_avisa_e_lembra_worktree` / `test_outro_chat_nao_herda_a_trava` — o caso de 2026-09-24: chat novo abre; outras abertas viram aviso (lista, worktree, `pausada`)
- `test_mesmo_chat_pedindo_outra_bloqueia` / `test_feature_do_chat_fora_do_index_segue_valendo` / `test_mesmo_chat_em_outro_projeto_nao_herda` — o F-022: o mesmo chat não abre 2ª feature (manda chat novo), mesmo antes de a linha nascer no INDEX
- `test_mesma_feature_retoma` / `test_retomar_nao_avisa_da_propria_feature` / `test_feature_do_chat_encerrada_libera_a_proxima` / `test_fechada_movida_pro_historico_libera_a_proxima` — retomar (nome, slug, grafia) passa; `fechada`/`pausada` no INDEX ou no histórico libera a próxima
- `test_nome_da_feature_e_so_a_primeira_linha` / `test_comando_sem_nome_na_mesma_linha_nao_grava_o_paragrafo` — o prompt real tem comando + parágrafos: o nome é o resto da linha do comando
- `test_titulo_do_passo_3_contido_no_nome_digitado_liga_ao_chat` / `test_nome_com_erro_de_digitacao_trava_enquanto_houver_aberta` / `test_linha_nova_do_backlog_nao_prende_o_chat` / `test_retomar_pelo_nome_digitado_sempre_passa` — o título que o passo 3 grava ≠ o nome digitado: casa por palavra inteira; retomar pelo nome digitado passa; fechada a linha, o chat abre a próxima
- `test_linha_de_outro_chat_nao_vira_do_chat` / `test_nome_sem_linha_com_outra_aberta_bloqueia_e_manda_chat_novo` / `test_nome_sem_linha_e_nada_aberto_libera` — 2ª revisão: linha nova sem nome em comum não é do chat (F-022 pelo vizinho); sem linha pelo nome, o bloqueio diz que não achou e manda chat novo; nada aberto + algo fechado desde a abertura libera (ponteiro do rodízio não prende)
- `test_v1_fechada_nao_encerra_a_v2_aberta` / `test_v1_fechada_que_casa_melhor_nao_encerra_a_linha_aberta_do_chat` / `test_nome_curto_fechado_nao_encerra_por_pedaco_de_palavra` / `test_linha_de_terceiro_nao_vira_ponte_entre_assuntos` — casamento por palavra inteira, a linha que casa melhor vence (F-022 não passa por semelhança)
- `test_voltar_ao_projeto_anterior_mantem_a_trava_dele` / `test_retomar_renova_a_validade` — chave `chat + projeto`; retomar renova os 30 dias
- `test_sem_argumento_passa` / `test_so_age_no_comando_de_abrir_feature` / `test_aceita_forma_curta_do_comando` / `test_projeto_sem_index_passa` — só `/mss-spec:nova-feature` e `/nova-feature`; sem nome ou sem INDEX passa
- `test_escape_do_owner` / `test_entrada_malformada_libera` / `test_estado_corrompido_libera_e_se_refaz` / `test_sem_session_id_passa_sem_gravar` / `test_estado_descarta_chat_com_mais_de_30_dias` — `MSS_UM_ITEM_OFF=1`; falha aberta; estado com validade de 30 dias
- `test_processo_*` (×4) — via subprocess: `{"decision":"block"}` + exit 2 + stderr; aviso = exit 0 com `systemMessage` + `additionalContext`; libera calado; não-JSON libera
- `test_hook_registrado_no_user_prompt_submit` / `test_segunda_camada_em_prosa` — `hooks.json` (UserPromptSubmit), passo 0 do `nova-feature.md`, `CLAUDE.md` sem "alerta, não trava", README

`tests/test_hook_pipe_teste.py` — cerca do pipe no `git_publicacao.py` (F-025):
- `test_nega_pytest_mascarado_por_pipe_antes_do_commit` (×7) / `test_nega_tambem_no_powershell` — os comandos reais de `edc0ab9` e `f9388e5`, `py.test`, `python3`, `-C`, `python.exe`, `Select-Object`
- `test_libera_o_resto` (×10) — `pytest && git commit`, pipe sem commit, `pipefail`, pipe sem pytest, `pytest` como texto, teste depois do commit
- `test_escape_*` (×3) / `test_bug_na_cerca_do_pipe_*` (×2) — `MSS_PIPE_TESTE_OFF` próprio; uma cerca não liga nem desliga a outra; bug aqui libera (ABERTA) sem abrir a de publicação
- `test_processo_nega_pelos_dois_protocolos` / `test_documentado_no_readme` — deny + exit 2 via subprocess; README

`tests/test_fora_de_escopo_no_to_dolist.py` — fora de escopo = "não agora", linha `#fora-de-escopo` no to-dolist (0.47.0):
- `test_todolist_vai_pro_git_no_molde_e_no_kit` / `test_comando_todolist_fala_do_formato_novo` / `test_captura_roteia_nao_agora_pro_todolist` / `test_molde_do_index_sem_secao_fora_de_escopo`
- `test_nenhum_texto_vivo_diz_que_fora_de_escopo_e_proibicao` — comandos, hooks, moldes, LEIA-ME e COMO-FUNCIONA sem "NÃO fazer"
- `test_kit_converteu_o_proprio_fora_de_escopo` — sem `FORA-DE-ESCOPO.md` nem seção no INDEX; cada linha no formato combinado
- (em `tests/test_hook_recall_memoria.py`) `test_recall_nao_cita_fora_de_escopo_sozinho` — a busca não lê to-dolist nem `FORA-DE-ESCOPO.md`

`tests/test_upgrade_plano.py` — a abertura do upgrade numa rodada só (0.54.0; `templates/upgrade_plano.py`, só lê):
- `test_sem_marca_e_to_dolist_antigo_sao_tres_passes_na_ordem` / `test_com_marca_e_to_dolist_no_desenho_so_as_categorias` / `test_com_marca_e_to_dolist_antigo_sao_dois_passes` / `test_sem_claude_md_a_migracao_nao_se_aplica_e_o_relatorio_diz` — os passes que se aplicam, na ordem migração → to-dolist → categorias, e a linha de status `✓/⬜`
- `test_arvore_suja_em_outra_branch_sai_num_bloco_so` — o caso do Transportes: branch de fix, 3 modificados, 2 não rastreados → um bloco `Git:` só, "guardar uma vez … devolver no fim"
- `test_arvore_limpa_na_principal_nada_a_guardar` / `test_arvore_limpa_em_outra_branch_ainda_assim_volta_pra_ela_no_fim` / `test_principal_master_e_remoto_sao_reconhecidos` / `test_sem_principal_conhecida_o_relatorio_pede_ao_owner` / `test_fora_de_git_o_relatorio_diz_isso` — principal `main`/`master`, remoto (`pull --ff-only`), principal desconhecida ("não sei"), fora de git
- `test_cli_checar_imprime_o_status_e_nao_grava_nada` / `test_o_kit_esta_no_proprio_desenho` — a CLI só lê (hash dos arquivos igual antes e depois, branch intacta); o kit só precisa das categorias

`tests/test_converter_to_dolist.py` — o upgrade leva o to-dolist e o fora de escopo pro desenho do kit (0.48.0):
- `test_checar_*` (×3) — aponta o formato antigo; projeto e kit no desenho não apontam nada
- `test_liberar_*` / `test_recado_numerado_*` / `test_fora_de_escopo_mantem_o_texto_inteiro` / `test_negrito_no_meio_*` / `test_data_*` / `test_sem_data_*` / `test_ordem_*` / `test_linha_ja_no_formato_fica_igual`
- `test_riscado_feito_e_data_incompleta_vao_pra_lista_sem_mudar` / `test_nenhuma_linha_some_a_soma_bate` / `test_index_perde_so_a_secao_*` / `test_exemplos_*`
- `test_aplicar_recusa_*` (×2) / `test_aplicar_grava_depois_do_tempo_1` / `test_crlf_*` / `test_cli_previa_nao_grava` / `test_upgrade_e_doctor_chamam_o_conversor`

`tests/test_hook_registro.py` — registro local dos hooks (`hooks/_registro.py`):
- `test_hook_que_age_grava_uma_linha` (×7) — cada hook, quando age, grava 1 linha com hook/decisão/detalhe/sessão
- `test_nunca_grava_o_texto_do_prompt_nem_do_comando` (×7) — segredo falso no comando, prompt e caminho não aparece
- `test_hook_que_passa_calado_nao_grava` (×4) — passar calado não gera linha
- `test_registro_que_nao_grava_nao_muda_a_decisao` (×7) / `test_cerca_de_publicacao_segue_negando_com_registro_quebrado` — saída byte a byte igual com o registro quebrado
- `test_escape_do_owner_nao_grava` / `test_acima_do_teto_faz_rodizio` / `test_detalhe_curto_e_numa_linha_so` / `test_padrao_e_na_pasta_do_kit_no_home` / `test_resumo_*` (×2) / `test_documentado_no_readme`

**Fora do baseline (manual):** resolução de `${CLAUDE_PLUGIN_ROOT}` via junction em runtime — validar rodando `/mss-spec:kickoff` num projeto de teste. **E o disparo do hook da âncora** com o kit instalado por junction (skills-dir): hooks carregam na partida da sessão, então o canário é pedir uma escrita fora da âncora numa sessão nova (ver `hooks/README.md`). Mesmo canário pras cercas da 0.26.0: `git push --dry-run origin main` pedido ao assistente tem que vir `[mss-spec] BLOQUEADO` (e `git push --dry-run` numa feature tem que PEDIR aprovação), e `/mss-spec:nova-feature outra-coisa` com feature `aberta` no INDEX tem que ser bloqueado com a lista.

- `test_infra_pergunta_no_kickoff` — CA1: o kickoff pergunta MSIG × própria e grava na linha `Infra:` do `CLAUDE.md`
- `test_infra_declarada_no_molde_do_claude_md` — CA2: a linha viaja no molde, nomeando o que MSIG implica e o que não se aplica
- `test_infra_propria_nao_recebe_ca_nem_office` — CA3: sem `corp-ca.pem`, sem `docker-compose.office.yml`, compose base sem a rede externa
- `test_infra_propria_no_banco_e_no_doctor` — CA4/CA5: `banco` vai ao genérico; `doctor` **pula** proxy/CA/rede (não ✗)
- `test_infra_propria_freia_o_upgrade` — CA6: a categoria 1 não reintroduz os arquivos MSIG

`tests/test_hook_memoria_da_proposta.py` — memória na hora da proposta e sintoma do owner é fato (0.49.0, F-047):
- `test_proposta_de_build_volta_com_as_memorias_que_a_vetam` / `test_memoria_fora_do_tema_nao_entra` / `test_proposta_que_cita_as_memorias_passa` — a proposta volta com as memórias do tema que não cita, e só essas
- `test_volta_so_uma_vez_por_sessao` / `test_relato_que_so_menciona_build_passa` / `test_projeto_sem_memoria_passa` / `test_escape_do_owner` — uma vez por sessão; relato e projeto sem `memory/` passam; `MSS_MEMORIA_ACAO_OFF`
- `test_resposta_que_contraria_o_relato_volta` (×3) / `test_frase_sobre_outra_coisa_passa` — "não se perdeu/não errou" com sujeito volta com a memória; "para não se perder" passa

`tests/test_memoria_tabela.py` — a tabela local de memória (0.55.0; `templates/memoria_tabela.py`, só lê o projeto):
- `test_caminho_padrao_fica_na_pasta_do_usuario_fora_do_claude` / `test_variavel_troca_o_caminho` / `test_montar_cria_a_pasta_da_tabela` / `test_esquema_de_outra_versao_e_refeito` — onde a tabela mora (`~/mss-spec/`, nunca no `.claude`) e o esquema
- `test_cada_fonte_vira_linha_com_o_tipo_certo` e os 9 seguintes — anotação com a frase do subíndice, diário com a linha do `DIARIO.md`, decisão e falha por item, documento por seção com `arquivo:linha`, `.html` sem tags, `<private>`/`.env`/`.txt` fora, seção gigante em pedaços, bytes fora de UTF-8, nome do projeto pelo `CLAUDE.md`
- `test_montar_grava_e_conta_por_tipo` … `test_filtro_por_projeto_tipo_e_data_e_busca_por_palavra` (9) — remontagem parcial (muda um → refaz um; apaga → tira; subíndice muda → refaz a anotação), dois projetos sem um tocar o outro, pastas de mesmo nome, `SELECT` e `MATCH`
- `test_dono_e_data_vem_da_criacao_no_git` / `test_ignorado_pelo_git_fica_fora` / `test_arquivo_novo_ainda_nao_commitado_entra_e_vira_pendencia` / `test_projeto_sem_git_segue_sem_erro` — `git init` de verdade em `tmp_path`
- `test_status_*` (3) e `test_cli_*` (3) — tabela ausente/desatualizada avisa e diz como remontar; a CLI roda **com os padrões** (pasta do usuário trocada por variável de ambiente)
- `test_tabela_presa_por_outro_programa_da_erro_claro_e_sai_com_2` / `test_arquivo_grande_demais_fica_fora_e_vira_pendencia` / `test_pasta_com_espaco_e_acento` — os casos de risco: tabela aberta no DBeaver, arquivo acima do teto, caminho como o do Whats
- `test_comando_memory_guarda_o_modo_tabela_fora_da_vista_do_owner` / `test_procedimento_de_troca_de_maquina_esta_na_memoria_do_kit` — o modo `tabela` fora da descrição e da ajuda (0.56.0), o texto de uso interno e o procedimento na memória do kit

`tests/test_memoria_tabela_busca.py` — a busca usa a tabela e a tabela se atualiza sozinha (0.56.0; decisões 13 a 22 da spec):
- `test_atualizar_*` (5) / `test_linha_de_controle_e_uma_por_projeto_e_nao_conta_como_memoria` / `test_tabela_da_parte_1_sem_linha_de_controle_e_conferida_uma_vez` / `test_arquivo_ignorado_pelo_git_que_muda_nao_vira_remontagem_sem_fim` / `test_montar_do_zero_segue_trazendo_dono_e_data_de_tudo` / `test_trocar_o_nome_do_projeto_e_visto_pela_conferencia` — conferência rápida: em dia não lê arquivo nem chama o git; mudado, novo e apagado entram; o git só é perguntado pelo que mudou
- `test_buscar_*` (5) / `test_palavra_longa_casa_pelo_comeco_e_acento_nao_atrapalha` / `test_contexto_da_conversa_entra_na_busca` / `test_pedido_sem_palavra_util_ou_com_simbolos_nao_da_erro` — 30 linhas de 30 arquivos, só o projeto da janela, a linha de controle nunca aparece, tabela ausente dá erro tratável
- `test_formatar_*` (2) — dois blocos (Anotações · Documentos), título até 80 e trecho até 170 letras
- `test_pedidos_da_conversa_*` (3) / `test_o_pedido_atual_entra_mesmo_curto_e_o_curto_do_meio_fica_fora` / `test_arquivo_da_conversa_vem_do_numero_da_sessao` — o último pedido + os 3 anteriores, cortados em 600; texto colado conta, corpo de comando e de skill não
- `test_cli_buscar_*` (7) — a linha de comando **com os padrões**: monta a tabela, usa a conversa, vê o arquivo mudado por fora, sai com 1 ou 2 mandando ir nos arquivos
- `test_as_tres_portas_buscam_na_tabela_e_tem_os_arquivos_como_reserva` / `test_memory_buscar_usa_a_tabela_e_cai_no_indice_se_precisar` / `test_ninguem_manda_o_owner_montar_a_tabela` — prosa das portas e do `/mss-spec:memory`

`tests/test_hook_memoria_tabela_em_dia.py` — o hook que mantém a tabela em dia (0.56.0; `hooks/memoria_tabela_em_dia.py`):
- `test_abertura_*` (3) / `test_segundo_projeto_na_mesma_tabela_tambem_e_montado_na_abertura` — abertura da conversa: monta na hora (recado só pro assistente), em dia fica calada, arquivo mudado por fora entra
- `test_gravou_*` (2) / `test_gravacao_fora_do_alcance_nao_mexe_em_nada` / `test_caminho_relativo_e_resolvido_pela_raiz_do_projeto` / `test_a_raiz_e_a_do_projeto_da_janela_nao_a_pasta_do_evento` — depois de gravar: só `.md`/`.html` de `memory/`, `docs/` e os soltos deste projeto
- `test_projeto_sem_pasta_memory_nao_ganha_tabela` / `test_escape_do_owner_desliga` / `test_tabela_presa_nao_trava_a_abertura_e_manda_buscar_nos_arquivos` / `test_evento_torto_nunca_levanta` / `test_copias_das_constantes_sao_iguais_as_do_motor` — quando não age e a falha aberta
- `test_processo_*` (2) / `test_hook_ligado_na_abertura_e_depois_de_gravar_e_documentado` — como processo, com os padrões, e a ligação no `hooks/hooks.json` e no README

`tests/test_memoria_gatilho_de_acao.py` — gatilho de ação em toda anotação de regra (0.57.0; decisão 24 da spec):
- `test_anotacao_nova_de_regra_sem_gatilho_de_acao_e_acusada_pelo_nome` / `test_anotacao_nova_com_gatilho_de_acao_ou_com_o_motivo_passa` (3) / `test_so_a_anotacao_de_regra_e_cobrada` (4) / `test_anotacao_obsoleta_nao_e_cobrada` — a cobrança do `memoria_indice.py verificar`: só `type: feedback`, só a nova, e os três campos que resolvem
- `test_antiga_nao_vira_problema_e_entra_na_lista_do_owner` / `test_sem_git_ninguem_e_nova` / `test_no_repositorio_a_nova_e_a_que_ainda_nao_tem_commit` — nova = sem commit (git de verdade); antiga vai pro `fila`, nunca vira problema
- `test_regex_quebrado_no_gatilho_de_acao_e_acusado` / `test_cli_verificar_avisa_das_antigas_sem_virar_problema` / `test_cli_fila_lista_as_antigas_sem_gatilho_de_acao` — regex que não compila e a linha de comando com os padrões
- `test_toda_regra_do_kit_tem_gatilho_de_acao_ou_o_motivo` / `test_gatilho_aprovado_casa_o_caso_real_e_nao_casa_o_vizinho` (21) / `test_sao_os_aprovados_pelo_owner_mais_os_5_que_ja_existiam` — o próprio kit: cada gatilho aprovado pelo owner contra o comando ou a frase real e 2 ou 3 vizinhos
- `test_a_captura_cobra_o_gatilho_de_acao_da_anotacao_de_regra` / `test_o_molde_da_memoria_explica_os_tres_campos` — prosa da captura e do molde
- em `tests/test_hook_memoria_de_acao.py`: `test_sem_numero_de_sessao_a_memoria_nao_age` — evento sem sessão não dispara nem gasta a vez do gatilho

`tests/test_ajudante_pesquisador.py` — o ajudante pesquisador (0.58.0; `agents/pesquisador.md`, decisão 25):
- `test_ajudante_existe_com_nome_e_descricao` / `test_ajudante_so_tem_ferramentas_de_leitura` / `test_ajudante_usa_o_modelo_da_conversa_e_nao_traz_campo_ignorado` — cabeçalho lido como YAML: só `Read, Grep, Glob`, modelo da conversa, sem campo que o Claude Code ignora em ajudante de plugin
- `test_descricao_diz_os_tres_casos_e_que_nao_e_pra_toda_tarefa` / `test_corpo_traz_o_formato_da_resposta` — quando chamar (e quando não) e o que devolve (primeira linha, `arquivo:linha`, não achei, não li, 3.000 letras, sem colar arquivo)
- `test_regra_bola_de_neve_nomeia_o_ajudante` / `test_comandos_e_aviso_de_janela_nomeiam_o_ajudante` / `test_portas_tem_o_passo_do_ajudante_com_o_comando_do_script` / `test_leia_me_apresenta_o_ajudante` — onde a regra aparece; nenhuma porta com número de passo repetido

`tests/test_conversa_texto.py` — outra conversa em texto (0.58.0; `templates/conversa_texto.py`, só lê a conversa):
- `test_falas_so_do_owner_e_do_assistente` / `test_o_turno_do_assistente_vira_uma_fala_com_o_que_ele_gravou` / `test_comando_do_kit_aparece_com_o_nome_e_o_pedido` / `test_texto_colado_pelo_owner_fica_e_retorno_de_hook_sai` / `test_linha_torta_e_arquivo_que_nao_abre_nao_derrubam` — o que é fala e o que não é
- `test_fala_digitada_enquanto_o_assistente_trabalhava_entra` / `test_fala_que_veio_pela_fila_e_pelo_registro_entra_uma_vez` / `test_aviso_do_app_nao_vira_fala` / `test_private_nao_escapa_com_tag_dentro_nem_sem_fechar` / `test_o_que_o_owner_escreveu_entre_sinais_de_menor_e_maior_fica` / `test_nome_de_comando_citado_no_meio_da_fala_nao_vira_comando` — os achados da revisão, vistos nas conversas reais do kit
- `test_gravar_texto_numera_as_falas_e_nao_tem_linha_gigante` / `test_fala_comprida_e_quebrada_em_linhas` / `test_conversa_sem_fala_nao_grava` / `test_pasta_de_saida_padrao_fica_fora_do_repo_e_do_claude` — o texto gravado (linhas de até 160 letras) e onde ele mora
- `test_listar_*` (2) / `test_achar_por_comeco_do_id_por_caminho_e_por_palavra` / `test_palavra_que_tambem_e_comeco_de_id_traz_as_duas` / `test_pasta_das_conversas_pelo_caminho_do_projeto` — achar a conversa
- `test_cli_*` (5) — a linha de comando: listar, texto, mais de uma ou nenhuma (sai com 1), sem a pasta (sai com 2), caminho direto, conversa sem fala

`tests/test_hook_passagem_de_conversa.py` — conversa nova não se perde (0.59.0; `hooks/passagem_de_conversa.py`, casos F-058 e F-053):
- `test_le_os_itens_decididos_do_pedido_real` / `test_formas_do_titulo` (5) / `test_pedido_colado_tambem` / `test_pedido_sem_lista_decidida_nao_tem_itens` / `test_pedido_com_decididos_entrega_a_regra_so_ao_assistente` — o pedido real da conversa do F-058: os 6 itens sob `O que eu já decidi`, a linha de continuação, o fim da lista, e a regra entregue só ao assistente
- `test_resposta_real_do_f058_volta` / `test_sem_decididos_o_topico_a_topico_passa` / `test_resposta_real_que_deu_certo_sai` / `test_perguntas_de_uma_vez_no_fim_saem` — as duas respostas reais: a que reabriu tópico a tópico volta; a lista única sai
- `test_pergunta_que_repete_item_decidido_volta` / `test_perguntas_espalhadas_pelo_meio_voltam` / `test_devolve_uma_vez_por_tipo_na_conversa` — pergunta que repete item, perguntas espalhadas, e cada conferência age uma vez por conversa
- `test_recusa_sem_regra_e_sem_pergunta_volta` (6) / `test_recusa_com_regra_e_pergunta_sai` / `test_recusa_so_com_regra_ainda_volta` / `test_o_que_nao_e_recusa_passa` (9) — "o kit não aceita / o hook negou" só com `arquivo:linha` e pergunta; "Nada no kit proíbe", "nunca bloqueou", aspas, bloco e citação passam
- `test_texto_pronto_sem_as_tres_partes_volta_com_o_molde` / `test_texto_pronto_com_as_tres_partes_sai` / `test_texto_pronto_com_um_topico_por_vez_volta` / `test_o_molde_do_proprio_hook_e_um_texto_valido` / `test_o_que_nao_e_texto_pronto_de_passagem_passa` (3) — quem entrega
- `test_stop_hook_active_deixa_sair` / `test_escape_do_owner` / `test_entrada_malformada_libera` (7) / `test_conversas_sao_independentes` / `test_processo_*` (3) / `test_registro_guarda_que_devolveu_sem_o_texto` — garantias e o contrato do processo (JSON `block` + saída 0; contexto sem `systemMessage`)
- em `tests/test_hook_kit_primeiro.py` e `tests/test_hook_um_item_por_janela.py`: `test_comando_colado_conta_como_entrada` / `test_comando_citado_no_meio_do_colado_nao_conta` / `test_nova_feature_colado_e_enxergado` — o comando do kit dentro de `<pasted_content …>` (F-053)

`tests/test_hook_pasta_e_branch.py` — duas conversas na mesma pasta não trocam a branch uma da outra (0.59.0; `hooks/_pasta_e_branch.py`, 6ª cerca do `git_publicacao.py`, caso F-059):
- `test_criar_branch_na_principal_passa` / `test_branch_que_a_conversa_abriu_e_dela` / `test_outra_conversa_nao_herda_a_branch` — na principal ou na branch que a conversa abriu, passa; outra conversa não herda
- `test_caso_f059_criar_branch_na_branch_de_outra_conversa_e_negado` / `test_criar_dizendo_que_sai_da_principal_vira_troca` / `test_trocar_com_mudanca_pendente_e_negado` / `test_trocar_com_a_pasta_limpa_pergunta_ao_owner` / `test_sem_saber_se_ha_mudanca_pergunta` — a sequência real do F-059; mudança por commitar nega; pasta limpa pede a aprovação do owner
- `test_nao_e_troca_de_branch` (11) / `test_powershell_tambem` / `test_git_c_e_cd_apontam_a_pasta` — `git checkout <arquivo>` e texto de mensagem não são troca; `-C` e `cd`
- `test_sem_numero_de_conversa_nao_age` / `test_escape_do_owner` / `test_pasta_sem_git_ou_head_solto_libera` / `test_o_hook_nega_e_pergunta` / `test_merge_aprovado_nao_perde_a_pergunta` / `test_processo_com_git_de_verdade` / `test_documentado_no_readme_e_na_spec` — garantias, dentro do hook e com repositório git real (`ask` sai 0; `deny` sai 2)

`tests/test_hook_comando_inteiro.py` — comando guardado inteiro (0.60.0; `hooks/_comando_inteiro.py`, dentro do `regra_antes_de_gravar.py`; decisão 23 da memória em tabela):
- `test_detector_acha_comando_ou_sql_com_reticencias` (8) / `test_detector_deixa_passar_o_que_nao_e_corte` (12) / `test_detector_devolve_a_linha_do_comando` / `test_detector_nao_levanta_com_entrada_estranha` — o que é comando cortado (bloco de SQL, de terminal, sem língua, entre crases) e o que não é (`*****`, intervalo do git, marcador entre `<` e `>`, outra língua, saída de programa, prosa)
- `test_so_anotacao_e_diario_sao_conferidos` (9) / `test_arquivo_que_nao_e_anotacao_nem_diario_nao_e_conferido` (4) — só `memory/<nome>.md` e `memory/sessions/<nome>.md`
- `test_write_de_anotacao_com_sql_cortado_nega_uma_vez_e_a_repeticao_passa` / `test_write_de_diario_com_comando_cortado_nega` / `test_uma_vez_por_arquivo_e_por_conversa` / `test_write_de_anotacao_sem_corte_passa_calado` (12) — nega uma vez, com o trecho no motivo
- `test_edit_dentro_de_bloco_que_ja_existe_e_pego_pelo_arquivo_resultante` / `test_corte_que_ja_estava_no_arquivo_nao_e_cobrado_de_quem_edita_outro_trecho` / `test_multiedit_soma_as_trocas` / `test_edit_cujo_trecho_antigo_nao_existe_confere_so_o_texto_novo` — confere o arquivo como vai ficar; só o corte novo é cobrado
- `test_escape_do_owner_desliga_so_esta_conferencia` / `test_sem_numero_de_conversa_nao_age` / `test_defeito_na_conferencia_nao_trava_a_gravacao` / `test_regra_por_tipo_de_arquivo_e_comando_cortado_saem_numa_negacao_so` — garantias, dentro do hook
- `test_modo_capturar_manda_gravar_o_comando_inteiro` / `test_readme_dos_hooks_fala_da_conferencia` — a frase da captura e a documentação
- `test_com_comando_cortado_lista_anotacoes_e_diarios` / `test_verificar_avisa_quantas_sao_e_nao_altera_nenhuma` / `test_verificar_sem_corte_nao_avisa` — o `verificar` só conta as antigas

**Último 100% verde:** 2026-11-12 · branch feature/comando-guardado-inteiro (comando guardado inteiro) · commit 874296f · 1564 passed
