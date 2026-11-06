# Próximo passo — detalhe

## 2026-11-06 — movido do MAPA.md

3. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy, quando abrir cada um** — nasce o `docs/AMBIENTES.md`; com a 0.53.0, escrever a linha **Hosts de produção (cerca)** na seção Produção (a cerca `banco_producao.py` passa a ser exata) e a regra `envio-externo.md` chega. `doctor` só mede; `upgrade` é quem traz.

## 2026-11-06 — movido do MAPA.md

1. ✅ **Owner: ordem de merge das duas branches abertas** — feito em 2026-11-06: 0.52.0 (`62e5239`) antes da 0.53.0 (`51b2160`), conflitos mantendo os dois lados; push do owner (`fd2d7fb`).

## 2026-11-03 — trocar a junção pelo marketplace local (escolha A)

Ordem importa: instalar ANTES de tirar a junção, senão o kit some no meio.
1. **Registrar a lojinha no `~/.claude/settings.json` do owner (com cópia de segurança, OK do owner):** nesta máquina não existe o comando `claude` (só o app Desktop, da Microsoft Store) e o menu do app não documenta adicionar marketplace de pasta local. É o mesmo jeito que o `superpowers` está registrado lá: `extraKnownMarketplaces.mss-local = {"source": {"source": "directory", "path": "C:/Ronaldo/_Mitsui/Python/Spec-Powers"}}` e `enabledPlugins["mss-spec@mss-local"] = true`. O app lê isso ao abrir a sessão seguinte (docs: plugins/loading). O `marketplace.json` já está na forma documentada (`"source": "./"`, commit `dade1db`).
2. **Conversa nova no kit:** `/mss-spec:doctor` → check 1 ✓ e os comandos `/mss-spec:` na lista; conferir em `~/.claude/plugins/installed_plugins.json` a entrada `mss-spec@mss-local` (como a do `superpowers`).
3. **Só então tirar a junção** `~/.claude/skills/mss-spec`: pelo Python (`os.rmdir` remove só o atalho, nunca o clone) — nada de PowerShell, nada de script — com o OK do owner; depois `/plugin` deve mostrar o kit uma vez só.
4. **Atualizar o kit:** memória `project_mss_spec_instalado_por_junction` (vira "instalado por marketplace local; edição não é live; atualizar pelo app depois de mesclar"), `project_plugin_load_cross_marketplace` (a dependência do superpowers pode voltar a ser declarada), check 11 do `doctor` e `LEIA-ME`; registrar como esta máquina atualiza o kit depois de uma mudança (conferir o comando no primeiro uso, não inventar).
5. **Prova:** mudar uma linha no clone, atualizar pelo app, abrir conversa nova e ver a mudança — e só aí fechar a pendência `project_pendencia_intermitencia_pos_update` como "sem junção, sem o que sumir".

