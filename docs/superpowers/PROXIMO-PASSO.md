# Próximo passo — detalhe

## 2026-11-03 — trocar a junção pelo marketplace local (escolha A)

Ordem importa: instalar ANTES de tirar a junção, senão o kit some no meio.
1. **Owner, no app (comandos do próprio Claude Code, não são scripts):** `/plugin marketplace add C:/Ronaldo/_Mitsui/Python/Spec-Powers` e depois `/plugin install mss-spec@mss-local` (os mesmos passos do `docs/LEIA-ME.md`, seção de instalação).
2. **Conversa nova no kit:** `/mss-spec:doctor` → check 1 ✓ e os comandos `/mss-spec:` na lista; conferir em `~/.claude/plugins/installed_plugins.json` a entrada `mss-spec@mss-local` (como a do `superpowers`).
3. **Só então tirar a junção** `~/.claude/skills/mss-spec`: pelo Python (`os.rmdir` remove só o atalho, nunca o clone) — nada de PowerShell, nada de script — com o OK do owner; depois `/plugin` deve mostrar o kit uma vez só.
4. **Atualizar o kit:** memória `project_mss_spec_instalado_por_junction` (vira "instalado por marketplace local; edição não é live; atualizar pelo app depois de mesclar"), `project_plugin_load_cross_marketplace` (a dependência do superpowers pode voltar a ser declarada), check 11 do `doctor` e `LEIA-ME`; registrar como esta máquina atualiza o kit depois de uma mudança (conferir o comando no primeiro uso, não inventar).
5. **Prova:** mudar uma linha no clone, atualizar pelo app, abrir conversa nova e ver a mudança — e só aí fechar a pendência `project_pendencia_intermitencia_pos_update` como "sem junção, sem o que sumir".

