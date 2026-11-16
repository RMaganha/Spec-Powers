---
name: project_armadilhas_do_powershell_desta_maquina
description: PowerShell 5.1 desta máquina — continuação com \, %VAR% do cmd, here-string pro git, Set-Content com BOM, bash do WSL e acento no git log quebram comando que parece certo
gatilho: quando montar um comando para o PowerShell desta máquina — mensagem de commit, variável de ambiente, gravar arquivo, chamar bash
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-10-21-azure-ambiente.md:69
metadata:
  type: project
---

O terminal do owner e o do assistente nesta máquina é o **Windows PowerShell 5.1**. Comando que funciona no bash ou
no cmd quebra aqui, em silêncio ou com erro estranho. Casos que já aconteceram:

- **Continuação de linha com `\`** quebra no PowerShell (memory/sessions/2026-07-16-spec-viva-por-assunto.md:18).
  Um comando por bloco, numa linha só ([[feedback_comando_pro_owner_passo_a_passo]]).
- **`%USERPROFILE%` é do cmd**; no PowerShell é `$env:USERPROFILE` (conversa de 2026-09-15, falas 031-032).
- **Mensagem de commit por here-string** (`@'...'@`) passada ao `git` não chega como texto: no shell Bash o título
  virou `@`, e `git merge -F -` não lê da entrada padrão
  (memory/sessions/2026-07-20-mapa-de-contexto-e-mapa-neural.md:22); no PowerShell 5.1 o `git commit -F -` com
  here-string virou nomes de arquivo (sono de 2026-11-16). Grave a mensagem num arquivo temporário e use
  `git commit -F <arquivo>`.
- **`Set-Content`/`Out-File` gravam com BOM** e os testes recusaram os manifestos
  (memory/sessions/2026-10-21-azure-ambiente.md:71) — já tinha acontecido em 2026-08-25. Grave por script Python ou
  pela ferramenta de escrita.
- **O 1º `bash` do PATH é o do WSL** (`System32\bash.exe`), que não roda: os testes que chamam bash pulam
  (memory/sessions/2026-10-21-azure-ambiente.md:69).
- **Acento no `git log`** aparece como `d<C3><BA>vida` e parece arquivo corrompido — não é
  (memory/sessions/2026-10-27-bug-e-duvida-pelo-kit.md:17).

Parentes: [[project_heredoc_grande_com_acento_quebra_no_git_bash]] e [[project_troca_por_script_em_arquivo_crlf]].
