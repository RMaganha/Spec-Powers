# distribuição por git — instalar/atualizar o kit por URL (design)

Data: 2026-07-20 · feature do próprio kit mss-spec (item 9 do INDEX).

## Estado atual
O `mss-spec` é **distribuível por git**: o `marketplace.json` na raiz usa `source` relative-path, que o Claude Code resolve tanto ao adicionar o marketplace por **pasta local** (`marketplace add ./pasta`) quanto por **URL git** (`marketplace add <url>#ref` → clona o repo → resolve o plugin em `.` dentro do clone) — o **mesmo manifesto serve às duas vias**, sem trocar o source. O `LEIA-ME.md` documenta as duas: a via **git** para o time (add por URL → `install mss-spec@mss-local` → atualizar por `marketplace update mss-local`, que dá `git pull` e re-resolve) e a via **local por pasta** preservada para dev/teste. O `marketplace.json` declara `allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]` (deixa a dependência do superpowers a 1 linha de distância), mas **não** declara `dependencies` no `plugin.json` — superpowers segue como pré-requisito documentado + habilitado via `settings.json`, porque o dev ainda carrega via skills-dir/symlink e declarar `dependencies` quebra esse load (ver `memory/project_plugin_load_cross_marketplace.md`).

Este é o mecanismo **preparado**: a URL do git interno entra como placeholder `<URL-do-git-interno>` no LEIA-ME — não há host git configurado ainda (`git remote` vazio), então publicar num remote real / `git push` fica como passo manual do owner quando o host existir. Desbloqueia o item 12 (CI).

## Critérios de aceite
- DADO o `marketplace.json` na raiz, QUANDO valido o manifesto, ENTÃO o plugin `mss-spec` usa `source` relative-path (mesma raiz do marketplace) — coerente com add por pasta local **e** por URL git, sem source separado.
- DADO o `marketplace.json`, QUANDO valido o manifesto, ENTÃO ele declara `allowCrossMarketplaceDependenciesOn` incluindo `claude-plugins-official`.
- DADO o `LEIA-ME.md`, QUANDO um colega vai instalar, ENTÃO há a via **git** (`marketplace add <url>` → `install mss-spec@mss-local` → `marketplace update mss-local`) **e** a via **local por pasta** preservada.
- DADO o `LEIA-ME.md`, QUANDO leio a via git, ENTÃO a URL aparece como placeholder marcado (`<URL-do-git-interno>`), não um host inventado.

## Design
1. **`marketplace.json`** — source relative-path inalterado (já serve git); acrescenta `allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]`.
2. **`LEIA-ME.md`** — reescreve a seção de instalação: via git para o time (com `#ref` opcional pra fixar tag/branch) + via local por pasta para dev/teste; superpowers como pré-requisito.
3. **Smoke test** — novo teste em `tests/test_smoke_kit.py` trava o mecanismo: source relative-path + `allowCrossMarketplaceDependenciesOn` presente + LEIA-ME com as duas vias.

## Fora de escopo
Publicar num remote real / `git push` (não há host; passo manual do owner) · declarar `dependencies` no `plugin.json` (adiado até o dev sair do symlink) · migrar `precedentes` de caminhos absolutos (dívida técnica, assunto próprio) · item 12 (CI, que este desbloqueia).

## Arquivos tocados
- `.claude-plugin/marketplace.json` (allowlist cross-marketplace)
- `docs/LEIA-ME.md` (seção de instalação: duas vias)
- `tests/test_smoke_kit.py` (novo teste do mecanismo)

## Histórico
- 2026-07-20 — criado: design da distribuição por git (item 9), aprovado no chat. Escolhas do owner: preparar o mecanismo sem push (não há host), manter as duas vias (local + git), não declarar a dependência superpowers agora (só a allowlist).
