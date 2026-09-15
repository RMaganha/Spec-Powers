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
| F-014 | 2026-08-25 | quando propor mecanismo novo cuja utilidade depende de o owner lembrar de chamá-lo | opt-in sem gatilho no kit | auto-proposta no `commands/nova-feature.md` + memória com `gatilho:` (o gatilho vive no kit, não na cabeça do owner) · `test_divergir_wiring` | fechado |
| F-015 | 2026-08-26 | quando diagnosticar falha que não fecha e existir precedente que funciona | ancoragem / loop de hipóteses | regra crítica 11 (diff antes de pedir evidência; fato do owner não se re-litiga) + `commands/diagnostico.md` · `test_diagnostico_wiring` | fechado |
| F-016 | 2026-09-02 | quando um gerador resolver símbolo (função, rota, classe) por **nome simples** | saída errada com cara de certa | resolução `mesmo arquivo → import declarado → qualquer arquivo` em `templates/bpmn.py` · `test_chamada_resolve_no_modulo_do_chamador` + `test_chamada_resolve_pelo_import_declarado` | fechado |
| F-017 | 2026-09-02 | quando uma página gerada precisar de JS pra mostrar o conteúdo | tela vazia pro owner | falha LEGÍVEL: `<noscript>` + texto de espera em cada moldura apontando o `.bpmn`/`bpmn.md`, e índice por âncora · `test_sem_js_a_pagina_explica_em_vez_de_ficar_branca` + `test_indice_navega_por_ancora` | fechado |
| F-018 | 2026-09-02 | quando a feature pedir desenho/grafo/layout de diagrama | reinventei o que já estava vendorizado | biblioteca de verdade embutida (bpmn-js + bpmn-auto-layout em `templates/vendor/`, precedente do `vis-network.min.js`) · `test_html_self_contained` | fechado |
| F-019 | 2026-09-02 | quando o owner disser "acho que X funcionaria" sobre o MEIO da entrega | hesitação virou requisito | regra no `commands/nova-feature.md`: suposição do owner não é premissa com fonte — aconselhe o padrão da área antes do OK · `test_suposicao_do_owner_nao_e_requisito` | fechado |
| F-020 | 2026-09-02 | quando a página gerada tiver um `id` derivado de nome que pode repetir | seção mostrou o dado de OUTRA | slug leva o nome do processo (`base--N-nome`) e acento translitera · `test_slug_de_diagrama_e_unico_no_documento` + `test_slug_transliteta_acento_em_vez_de_apagar` | fechado |
| F-021 | 2026-09-02 | quando o desenho for montado por lib que mede o container | tela vazia com o painel estreito | monta sob demanda (IntersectionObserver), espera a moldura ter tamanho e nunca aplica escala/altura não-finita · `test_montagem_espera_a_moldura_ter_tamanho` | fechado |
| F-022 | 2026-09-14 | quando surgir um 2º assunto na janela de uma feature, ou quando for publicar/integrar (`git push`/`merge`/`rebase`, deploy) | janela sequestrada + publicação pelo assistente | hooks **ligados**: `git_publicacao.py` (PreToolUse Bash/PowerShell nega push/merge/rebase/deploy — falha fechada) + `um_item_por_janela.py` (UserPromptSubmit bloqueia `nova-feature` com feature aberta) · passo 0 do `nova-feature.md` · regra do `CLAUDE.md` deixa de ser "alerta, não trava" · `tests/test_hook_git_publicacao.py` + `tests/test_hook_um_item_por_janela.py` | fechado |
| F-023 | 2026-09-14 | quando um chamador externo recebe erro (4xx/5xx) e o teu teste com "o payload certo" passa | uma variante virou "API saudável" | prosa: passo 3 do `commands/diagnostico.md` — saúde de endpoint só se prova com a **matriz de variantes que o chamador pode produzir** (Content-Type ausente/`text/plain`, charset/BOM, corpo vazio), nomeando cada diferença entre o teu teste e a chamada real; e o diff contra o deploy que funcionava cobre o **deploy inteiro** (requirements/versão de framework, Dockerfile, App Settings), não um arquivo · `test_diagnostico_wiring` | fechado |
| F-024 | 2026-09-14 | quando um teto/limite copiado de outro contexto mandar PODAR conteúdo | premissa não verificada virou prescrição | topo 6 KB = orçamento, "não carrega" só na nativa, conserto = mover (`memoria_indice.py dividir` / `rodizio_partida.py`) · `test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega` + `test_doctor_aponta_o_conserto_mecanico` | fechado |
| F-025 | 2026-09-15 | quando o comando de teste e o `git commit` forem encadeados no mesmo comando de shell | commit com suíte vermelha (pipe mascarou o exit) | memória `feedback_pipe_mascara_o_exit_do_teste` (`set -o pipefail` ou pytest em passo próprio) · sem teste | aberto |

### F-025 — pipe mascarou o exit do pytest (aberto)

- **Falhou:** `python -m pytest … | tail -1 && git commit …` commitou (`edc0ab9`, 2026-09-15) com 2 testes vermelhos — o exit do pipe é o do `tail`, que devolveu 0. Descoberto duas tarefas depois, ao rodar a suíte inteira.
- **Verdade:** o código de saída de um pipe é o do último comando; `&&` só olha esse. "Rodou sem erro" era o `tail`, não o pytest.
- **Guardrail:** `set -o pipefail` antes do pipe, ou pytest num passo próprio com a contagem lida antes do commit. Memória `feedback_pipe_mascara_o_exit_do_teste` (família "Ao versionar, publicar e fechar").
- **Teste:** nenhum — é hábito de shell, não código do kit. Fica aberto até virar cerca ou provar-se que a memória basta (reincidência zero em 3 sessões).
