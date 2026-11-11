# Ambiente desta máquina e pendências

- **quando trocar de máquina, a tabela de memória sumir ou o status acusar** → [Remontar a tabela de memória](../project_remontar_a_tabela_de_memoria.md) — PROCEDIMENTO: um `montar` por projeto; a tabela é cópia, mora em `~/mss-spec/`
- **quando pensar em atualizar ou reinstalar o mss-spec** → [Instalado por junction](../project_mss_spec_instalado_por_junction.md) — edições são live; nada de update/pull
- **quando o mss-spec parar depois de o app atualizar** → [PENDÊNCIA: intermitência pós-update](../project_pendencia_intermitencia_pos_update.md) — ABERTA; falta capturar o estado quebrado
- **quando revisar pendências antigas do kit** → [Review 2026-07](../project_review_2026-07_pendencias.md) — aplicado na v0.2.0; resta o Dockerfile do painel
- **quando a solução pedir script PowerShell, tarefa agendada, serviço, junção ou outra persistência na máquina do owner** → [Script e tarefa agendada não são permitidos (SI)](../project_sandbox_do_claude_nao_registra_tarefa_agendada.md) — a Segurança da Informação contactou o owner ao registrar a tarefa do guardião (2026-11-03): não execute nem proponha, nem pro owner; o `gatilho_comando` nega; o sandbox já negava; variável de usuário e `settings.json` funcionam (F-050)
