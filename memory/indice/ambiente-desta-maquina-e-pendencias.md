# Ambiente desta máquina e pendências

- **quando pensar em atualizar ou reinstalar o mss-spec** → [Instalado por junction](../project_mss_spec_instalado_por_junction.md) — edições são live; nada de update/pull
- **quando o mss-spec parar depois de o app atualizar** → [PENDÊNCIA: intermitência pós-update](../project_pendencia_intermitencia_pos_update.md) — ABERTA; falta capturar o estado quebrado
- **quando revisar pendências antigas do kit** → [Review 2026-07](../project_review_2026-07_pendencias.md) — aplicado na v0.2.0; resta o Dockerfile do painel
- **quando precisar criar ou alterar tarefa agendada, serviço ou configuração do Windows pelo Claude** → [Sandbox não registra tarefa agendada](../project_sandbox_do_claude_nao_registra_tarefa_agendada.md) — `Register-ScheduledTask`, `schtasks` e o COM deram "Acesso negado" e a ferramenta PowerShell ficou sem spawn; comando vai pro owner em passo a passo; variável de usuário e `settings.json` funcionam
