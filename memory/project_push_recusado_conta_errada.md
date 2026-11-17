---
name: project_push_recusado_conta_errada
description: git push recusado com 403 "Permission … denied to <conta>" é o gerenciador de credenciais do Git guardando a outra conta do owner, sem permissão no repositório
gatilho: quando o git push for recusado com 403
metadata:
  type: project
---

Em 2026-11-17 o `git push` deu `remote: Permission to RMaganha/Spec-Powers.git denied to <conta>` e
`The requested URL returned error: 403`, logo depois de um push que tinha passado. O gerenciador de credenciais do Git
(`credential.helper = manager`) tinha guardado a outra conta do owner, que não tem escrita no repositório (o nome dela
aparece na própria mensagem do erro; fica fora daqui porque o repositório é público).

Passos (o owner roda; a senha é dele):
1. `git credential-manager github list` — confira as contas guardadas.
2. `git credential-manager github logout <conta da mensagem do erro>`
3. `git push` — na janela de login, entre com a conta dona do repositório.
