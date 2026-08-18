<!-- Corpus de falhas do assistente neste projeto (dogfood do próprio kit).
     Uma falha que já aconteceu vira CASO; caso vira GUARDRAIL; guardrail vira TESTE.
     Caso sem guardrail fica `aberto` — dívida visível. Caso fechado com teste vive só na
     linha da tabela (o teste é o guardrail vivo); o bloco detalhado existe enquanto está aberto
     ou enquanto o guardrail é só prosa. Alimentado pelo /mss-spec:memory capturar. -->

# Falhas — corpus de casos

O que **já custou caro** mora aqui. O que **ainda vale** mora em `memory/MEMORY.md`.
Leia a coluna **gatilho**: se ela descreve o que você está prestes a fazer, o caso é seu.

| id | data | gatilho | classe | guardrail | status |
|---|---|---|---|---|---|
| F-001 | 2026-07-24, 2026-07-30 | quando faltar um caminho/nome que o owner tem na cabeça | memória não carregou | `templates/CLAUDE.md` (pergunte, não vasculhe) · `test_perguntar_nao_vasculhar` | fechado |
| F-002 | 2026-07-31 | quando gerar o mapa de um projeto cujo framework não foi declarado | premissa não-dita | `templates/mapa_neural.py` (rota por conteúdo) · `test_extrai_rota_flask` | fechado |
| F-003 | 2026-07-31 | quando o kit for gravar algo sobre infra (rede, proxy, CA, banco) | premissa não-dita | `commands/kickoff.md` (pergunta a infra) · `test_infra_pergunta_no_kickoff` | fechado |
| F-004 | 2026-07-30 | quando a tarefa citar outro projeto como referência | premissa não-dita | regra crítica 8 + hook `PreToolUse` · `test_bloqueia_outro_repo` | fechado |
| F-005 | 2026-07-31 | quando chamar processo externo por subprocess no Windows | falha silenciosa | `templates/mapa_neural.py` (bytes + `-z`) · `test_camada_no_gitignore_fica_fora` | fechado |
| F-006 | 2026-07-31 | quando escrever código que parseia `.md` do kit | regressão de parser | filtro só no campo curto · `test_placeholder_do_molde_nao_vira_fato` | fechado |
| F-007 | 2026-07-21 | quando gerar HTML com JS inline | falta de check | `node --check` no teste · `test_html_js_tem_sintaxe_valida` | fechado |
| F-008 | 2026-07-28 | quando gravar no projeto conteúdo levantado dele mesmo | fronteira não sabida | `commands/upgrade.md` (não nasceu do kit) · `test_upgrade_respeita_preexistente` | fechado |
| F-009 | 2026-07-31 | quando um gerador tiver que cortar a saída | falha silenciosa | `_LIMITE` + rastro `… (+N)` · `test_limite_corta_com_marcador` | fechado |
| F-010 | 2026-07-31 | quando explicar um desenho novo ao owner | comunicação | `commands/nova-feature.md` (desenho em termos do owner) · `test_desenho_em_termos_do_owner` | fechado |
| F-011 | 2026-08-18 | quando o owner delimitar o escopo numa nota curta (to-dolist, mensagem de uma linha) | premissa não-dita | `commands/nova-feature.md` (premissa com fonte) · `test_premissa_com_fonte` | fechado |
| F-012 | 2026-08-18 | quando confiar que a memória durável do repo já está no contexto | memória não carregou | ponteiro na nativa + check 8 do `doctor` · `test_ponteiro_memoria_nativa` | fechado |
| F-013 | 2026-08-18 | quando o pedido nomear dois assuntos coordenados ("A **e** B") | entrega pela metade | `commands/nova-feature.md` (cubra cada assunto) · `test_pedido_com_mais_de_um_assunto` | fechado |

