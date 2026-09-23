# Ao decidir arquitetura e dependência

- **quando escolher biblioteca ou versão** → [Só dependência estável](../feedback_so_dependencia_estavel.md) — nada de beta/rc/alpha
- **quando decidir o nível de front de uma tela** → [2 níveis + Mantine](../project_front_moderno_mantine.md) — Jinja+Tailwind (simples) × React+TS+Mantine (densa)
- **quando propor configuração, flag ou seção declarativa** → [Regra única em vez de config](../feedback_regra_unica_em_vez_de_config.md) — uma regra repetível + exceções de 1 linha
- **quando a decisão de design for aberta e cara de reverter** → [Divergir antes de convergir](../feedback_divergir_antes_de_convergir.md) — proponha você mesmo o `/mss-spec:divergir` (ramos isolados por frame); a 1ª resposta é a de manual
- **quando desenhar hook que precisa alertar o owner ou pedir confirmação** → [No Desktop, só o `ask` aparece](../project_hook_ask_aparece_no_desktop.md) — systemMessage some; additionalContext depende de relato; `ask` = exit 0
- **quando o owner trouxer análise ou sugestões do kit feitas por outra IA** → [Cruzar análise externa com o repo](../feedback_analise_externa_cruzar_com_o_repo.md) — já existe? contraria decisão? tem caso real? metade cai no 1º ou 2º filtro
- **quando avaliar ferramenta ou plugin externo** → [Ideia vs. stack](../feedback_avaliar_tool_externa_ideia_vs_stack.md) — integrar só se casar com os pilares; senão, reimplementar a ideia
- **quando propor visualização como ganho pro assistente** → [Visual é pro humano; dados pro assistente](../feedback_visual_pro_humano_dados_pro_assistente.md) — o ganho vem de texto agregado
- **quando a feature pedir desenho, diagrama, grafo ou layout** → [Use a lib consagrada, vendorizada](../feedback_visualizacao_usa_lib_consagrada.md) — geometria à mão saiu com 4.000 px e 222 rótulos truncados; o kit já vendoriza lib
