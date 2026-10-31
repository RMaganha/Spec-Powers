---
name: project_sandbox_do_claude_nao_registra_tarefa_agendada
description: o sandbox em que o Claude roda comandos nesta máquina não registra tarefa agendada do Windows — Register-ScheduledTask, schtasks.exe e o COM Schedule.Service devolvem "Acesso negado" — e a ferramenta PowerShell pode ficar sem abrir processo (EPERM) depois; configuração de sistema é comando entregue ao owner, em passo a passo
gatilho: quando precisar criar ou alterar tarefa agendada, serviço, variável de ambiente de máquina ou outra configuração do Windows pelo Claude
gatilho_comando: (?i)Register-ScheduledTask|schtasks(\.exe)?\s+/create|ComObject\s+Schedule\.Service
metadata:
  type: project
---

Em 2026-10-30, ao ligar o guardião da junção, as três formas de registrar a tarefa agendada falharam de dentro
das ferramentas do Claude: `Register-ScheduledTask` → `Acesso negado (0x80070005)`; `schtasks /Create` → o
próprio `schtasks.exe` não pôde ser executado (`Acesso negado`); `New-Object -ComObject Schedule.Service` →
idem. Logo depois a ferramenta **PowerShell** parou de abrir qualquer processo (`EPERM: operation not permitted,
uv_spawn cmd.exe`) pelo resto da sessão; o **Bash** continuou normal, inclusive chamando `powershell -File`. O que
**funcionou** sem admin: remover uma variável de ambiente do **usuário**
(`[Environment]::SetEnvironmentVariable('LC_ALL', $null, 'User')`) e editar o `~/.claude/settings.json`.

**Why:** não é falta de admin do owner, é o sandbox da ferramenta — insistir queima rodadas e pode derrubar a
ferramenta PowerShell da sessão.

**How to apply:** tarefa agendada, serviço, variável de **máquina**, política: **não tente** — entregue o comando
ao owner em passo a passo (título em negrito, comando sozinho num bloco, o que conferir na saída) e deixe a
conferência no fluxo (`Get-ScheduledTask "<nome>"`). O `gatilho_comando` acima faz o hook negar uma vez com esta
memória no motivo. Se a ferramenta PowerShell ficar sem spawn, siga pelo Bash. Fallback sem agendador: atalho na
pasta Inicializar (`shell:startup`), que cobre só o logon. Relacionado: [[project_mss_spec_instalado_por_junction]],
[[project_pendencia_intermitencia_pos_update]].
