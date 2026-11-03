---
name: project_sandbox_do_claude_nao_registra_tarefa_agendada
description: scripts PowerShell (.ps1) e tarefas agendadas NÃO SÃO PERMITIDOS pela Segurança da Informação na máquina do owner (2026-11-03) — nem pelo Claude, nem pelo owner; e o sandbox em que o Claude roda comandos não registra tarefa agendada do Windows — Register-ScheduledTask, schtasks.exe e o COM Schedule.Service devolvem "Acesso negado" — e a ferramenta PowerShell pode ficar sem abrir processo (EPERM) depois; configuração de sistema é comando entregue ao owner, em passo a passo
gatilho: quando a solução pedir script PowerShell (.ps1), tarefa agendada, serviço, junção ou outra configuração persistente do Windows — pelo Claude ou pelo owner
gatilho_comando: (?i)Register-ScheduledTask|schtasks(\.exe)?\s+/create|ComObject\s+Schedule\.Service|powershell(\.exe)?[^\n]*-File\s+\S*\.ps1|New-Item\s+-ItemType\s+Junction
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

**How to apply (revisto em 2026-11-03):** script `.ps1`, tarefa agendada, serviço, junção, atalho na pasta
Inicializar ou qualquer outra persistência na máquina: **não execute e não proponha, nem como comando pro owner
rodar** — a política da Segurança da Informação vale pra ele também (foi contactado ao registrar a tarefa). O
`gatilho_comando` acima faz o hook negar uma vez com esta memória no motivo. Precisa de automação na máquina?
A resposta é "isso passa pela SI antes", e o desenho espera. Se a ferramenta PowerShell ficar sem spawn, siga
pelo Bash para o que é leitura. Relacionado: [[project_mss_spec_instalado_por_junction]],
[[project_pendencia_intermitencia_pos_update]].

**2026-11-03 — não é só o sandbox: é POLÍTICA.** O owner registrou a tarefa agendada do guardião (0.51.0) na janela dele e foi contactado pela infra e pela Segurança da Informação: scripts PowerShell e tarefas agendadas **não são permitidos** na máquina. Consequência: o assistente **não executa nem propõe** `.ps1`, `Register-ScheduledTask`, `schtasks`, COM do agendador, nem comandos de criar junção; o `gatilho_comando` acima nega esses comandos uma vez por sessão com esta memória no motivo. Automação na máquina do owner = pergunta à SI antes, nunca premissa (mesma família de F-003: infra é pergunta, não suposição). Python chamado pelos hooks do próprio app segue como está (roda há meses sem objeção) — mas qualquer mecanismo novo de persistência passa pela SI primeiro. Caso F-050.
