<!-- Índice de memória do próprio kit mss-spec (dogfood). Ver templates/MEMORY.md.
     Agrupado por FAMÍLIA DE GATILHO (quando abrir), não por tipo nem por data.
     1 linha por memória, começando pelo gatilho. Teto: 200 linhas / 25 KB — acima disso o
     excedente nem carrega. Memória superada ganha `obsoleta:` no frontmatter e SAI daqui. -->

# Memória do projeto — índice por gatilho

## Na partida e ao escolher o ritual
- **quando precisar de contexto do projeto (partida ou reabrir assunto)** → [Consultar o destilado antes de reler a fonte](feedback_consultar_destilado_antes_da_fonte.md) — mapa/índice/memória primeiro; reler tudo é a amnésia que o mapa existe pra matar
- **quando a feature nascer de um item curto de to-dolist/backlog** → [Item de backlog não é design](feedback_item_de_backlog_nao_e_design.md) — o item é o sintoma; o design exige diagnóstico próprio
- **quando o desenho depender de como uma ferramenta funciona** → [Pesquisar a fonte primária antes de desenhar](feedback_pesquisar_fonte_primaria_antes_de_desenhar.md) — doc do fabricante, não memória nem terceiro
- **quando propor melhoria de custo, desempenho ou qualidade** → [Medir antes de afirmar ganho](feedback_medir_antes_de_afirmar_ganho.md) — número primeiro, peça depois; teto vira teste
- **quando escolher o ritual da tarefa** → [Nível de cerimônia / velocidade](feedback_nivel_cerimonia_velocidade.md) — padrão médio; alto só p/ feature grande
- **quando começar tarefa de domínio (UI, banco, segurança, infra)** → [Assumir papel de especialista](feedback_assumir_papel_especialista.md) — persona sênior do domínio; anuncia, faz, OK, volta
- **quando gravar memória ou aprendizado durável** → [Memória vive dentro do repo](project_memoria_local_ao_repo.md) — `memory/` do projeto, nunca só a pasta nativa volátil

## Ao falar com o owner
- **quando escrever qualquer resposta** → [Estilo de resposta direto](feedback_estilo_resposta_direto.md) — sem preâmbulo; negação intocável; técnico verbatim
- **quando fechar uma resposta ou entrega** → [Não encerrar com pergunta não pedida](feedback_nao_encerrar_com_pergunta.md) — entrega e para; o owner conduz o ritmo
- **quando citar caminho, host, container, variável ou recurso** → [Não inventar fatos concretos](feedback_nao_inventar_fatos_concretos.md) — só o que está no repo ou o owner confirmou
- **quando faltar um fato que o owner tem na cabeça** → [Perguntar em vez de vasculhar](feedback_perguntar_em_vez_de_vasculhar.md) — pergunta curta na hora; nunca `find` no disco (reclamado 2×)

## Ao mexer em código e arquivo
- **quando criar ou editar HTML, CSS ou JS de aplicação** → [Front-end: Tailwind + arquivos separados](feedback_frontend_tailwind_arquivos_separados.md) — nada inline (exceto doc standalone)
- **quando gerar HTML com JS inline** → [Testar o JS gerado com `node --check`](feedback_testar_js_gerado_node_check.md) — substring verde não pega erro de parse (a tela branca)
- **quando chamar processo externo por subprocess no Windows** → [`text=True` quebra a chamada ao git](project_subprocess_texto_windows_quebra_git.md) — use bytes + `-z`
- **quando escrever código que parseia `.md` do kit** → [Descartar comentário; placeholder só em campo curto](project_parse_md_do_kit_descartar_comentario.md) — filtro `<…>` na linha inteira engole texto real
- **quando gravar conteúdo levantado do projeto num arquivo de doc** → [Categoria 1 do upgrade sobrescreve](project_upgrade_categoria1_sobrescreve.md) — o levantado vai pro `ARQUITETURA.md`

## Ao decidir arquitetura e dependência
- **quando escolher biblioteca ou versão** → [Só dependência estável](feedback_so_dependencia_estavel.md) — nada de beta/rc/alpha
- **quando decidir o nível de front de uma tela** → [2 níveis + Mantine](project_front_moderno_mantine.md) — Jinja+Tailwind (simples) × React+TS+Mantine (densa)
- **quando propor configuração, flag ou seção declarativa** → [Regra única em vez de config](feedback_regra_unica_em_vez_de_config.md) — uma regra repetível + exceções de 1 linha
- **quando avaliar ferramenta ou plugin externo** → [Ideia vs. stack](feedback_avaliar_tool_externa_ideia_vs_stack.md) — integrar só se casar com os pilares; senão, reimplementar a ideia
- **quando propor visualização como ganho pro assistente** → [Visual é pro humano; dados pro assistente](feedback_visual_pro_humano_dados_pro_assistente.md) — o ganho vem de texto agregado

## Ao tocar outro projeto, brownfield ou infra
- **quando a tarefa mencionar outro projeto** → [Um projeto por janela: outro é read-only](feedback_projeto_ativo_read_only.md) — a âncora não migra; bug lá = reporte
- **quando trabalhar em projeto que já existia** → [Brownfield: entender e registrar](feedback_brownfield_entender_nao_aplicar.md) — nunca aplicar molde por cima do que funciona
- **quando o kit for gravar algo sobre infra** → [Kit não assume o ambiente de origem](project_kit_nao_assume_ambiente_de_origem.md) — infra é pergunta no kickoff, não premissa
- **quando montar build Docker com ODBC atrás do proxy** → [Build Docker + FortiGate](project_docker_build_fortigate.md) — 3 fixes de build + rotação de proxy/CA

## Ao mexer em banco, segredo ou rota
- **quando configurar conexão de banco ou segredo** → [Env-var (recomendado) ou Fernet](feedback_credencial_reusar_env_precedente.md) — nunca no código nem no commit
- **quando criar/alterar rota ou revisar segurança** → [Segurança AppSec no kit](project_seguranca_appsec_kit.md) — baseline `SEGURANCA.md`; integração = Bearer

## Ao versionar, publicar e fechar
- **quando abrir branch de feature ou fix** → [Feature sempre a partir da `main`](feedback_feature_a_partir_da_master.md) — nunca ramificar de outra branch
- **quando bumpar a versão do kit** → [Versão vive em dois manifestos](project_versao_em_dois_manifestos.md) — `plugin.json` + `marketplace.json`, e re-rode a suíte
- **quando fechar mudança em gerador ou CLI** → [Dogfood com diff antes × depois](project_dogfood_gerador_diff_antes_depois.md) — fixture não vê o que só o projeto real tem
- **quando publicar ou instalar o kit por marketplace** → [relative-path serve git E local](project_marketplace_relative_path_serve_git_e_local.md) — o mesmo `marketplace.json` resolve os dois
- **quando mexer em dependências no `plugin.json`** → [Dep cross-marketplace quebra o load](project_plugin_load_cross_marketplace.md) — some tudo enquanto carrega por symlink

## Ao testar
- **quando escrever teste pra comando ou skill do kit** → [Comando-prosa não se testa como código](feedback_comandos_prosa_nao_unit_test.md) — wiring no smoke, nunca unit test teatral
- **quando for validar uma tela ou UI** → [Validação de UI só determinística](feedback_validacao_ui_deterministica.md) — nunca dirigir o browser ao vivo; smoke visual = humano

## Ambiente desta máquina e pendências
- **quando pensar em atualizar ou reinstalar o mss-spec** → [Instalado por junction](project_mss_spec_instalado_por_junction.md) — edições são live; nada de update/pull
- **quando o mss-spec parar depois de o app atualizar** → [PENDÊNCIA: intermitência pós-update](project_pendencia_intermitencia_pos_update.md) — ABERTA; falta capturar o estado quebrado
- **quando revisar pendências antigas do kit** → [Review 2026-07](project_review_2026-07_pendencias.md) — aplicado na v0.2.0; resta o Dockerfile do painel
