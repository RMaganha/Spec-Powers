---
name: plugin-load-cross-marketplace
description: NÃO declarar dependência cross-marketplace no plugin.json enquanto o mss-spec carrega via skills-dir/symlink — quebra o load e somem TODOS os comandos
metadata:
  type: project
---

O `mss-spec` (dev) carrega via **skills-dir auto-load**: `~/.claude/skills/mss-spec` é um **symlink pro
repo** (`/c/Ronaldo/_Mitsui/Python/Spec-Powers`). Nesse caminho o Claude Code **não lê** o
`marketplace.json` do `mss-local` — então uma **dependência cross-marketplace** no `plugin.json`
(`dependencies: [{ name: superpowers, marketplace: claude-plugins-official }]`) fica **sem allowlist
aplicável** e o Code **recusa carregar o plugin** → somem TODOS os comandos `/mss-spec:` (só voltam com
restart completo, depois de remover o campo). Aconteceu em 2026-07-16.

**Why:** a `allowCrossMarketplaceDependenciesOn` só vale quando o plugin carrega **por marketplace**; no
load via skills-dir/symlink ela nem é lida. Funcionou a sessão toda porque plugin só recarrega no
restart — o bug ficou latente até o reload.

**How to apply:** enquanto o mss-spec rodar via symlink/skills-dir, **não** declarar `dependencies`
cross-marketplace no `plugin.json`. O superpowers fica habilitado via `settings.json` (já basta). A
dependência declarada (auto-install) só entra **junto do marketplace git** (INDEX item 9), onde a
allowlist funciona. Relacionado: [[nao-inventar-fatos-concretos]].
