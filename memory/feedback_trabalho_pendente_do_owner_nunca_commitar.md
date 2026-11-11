---
name: feedback_trabalho_pendente_do_owner_nunca_commitar
description: árvore suja em outra branch quando a tarefa pede branch nova da principal — guardar UMA vez com git stash (com o OK), nunca propor "commitar e seguir", devolver no fim na branch do owner com conferência colada
gatilho: quando a tarefa pedir branch nova a partir da principal e `git status` mostrar modificados sem commit em outra branch do owner
gatilho_comando: (?m)(?:^|[;&|(])\s*git\s+stash\b(?!\s+(?:list|show)\b)
metadata:
  type: feedback
---

O trabalho pendente na branch do owner é **dele**: o commit é dele, a mensagem é dele, o momento é dele.
Quando um comando do kit (upgrade, nova-feature, kickoff) precisa abrir branch a partir da principal e
a árvore está suja em outra branch:

1. **Guardar uma vez, com o OK**: `git stash push -m "<comando>: pendente de <branch>"` guarda os
   **modificados**; **não rastreados ficam no lugar** (nenhum comando do kit os toca; se um deles tiver o
   nome de um arquivo que o kit criaria, o arquivo que existe vence — não é criado).
2. Abrir a branch da principal, fazer o trabalho, commitar **só o do kit**, pelo nome.
3. **Devolver no fim, na branch do owner**: `git switch <branch do owner>` → principal pra ela
   (`git merge --ff-only <principal>`; divergiu → pare e pergunte) → `git stash pop`.
4. **Conferência colada antes de "pronto"**: `git branch --show-current` · `git log --oneline -5` ·
   `git status --short` (os mesmos arquivos de antes) · `git stash list` (sem a entrada).

Nunca: propor "commito as pendências e sigo" · perguntar a mesma coisa a cada passe · deixar o owner
numa branch sem a principal (toda janela nova dela acusaria o `CLAUDE.md` antigo).

**Why:** no Transportes V2 (2026-11-09) o `/mss-spec:upgrade` da 0.53.0 parou três conversas na mesma
pergunta sobre 3 arquivos modificados sem commit na `fix/atm-virada-outubro`, e na 1ª ofereceu
"Commitar e migrar". O que destravou foi o owner ditar exatamente o roteiro acima — que virou o
`commands/upgrade.md` da 0.54.0 (seção "Git: uma branch, trabalho pendente guardado uma vez").

**How to apply:** o `templates/upgrade_plano.py checar` já imprime a situação do git num bloco só; em
outro comando, rode `git status --porcelain` e siga os 4 passos. Relacionado:
[[feedback_feature_a_partir_da_master]] (branch sempre da principal),
[[feedback_publicacao_e_ato_do_owner]] (merge pede aprovação; push é do owner).
