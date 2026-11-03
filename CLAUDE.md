<!-- CLAUDE.md do PROJETO: entra em toda sessão (orçamento 10 KB; passou, o hook avisa). As regras do kit NÃO ficam aqui —
     vêm do plugin mss-spec em toda janela (hook SessionStart). Fato do projeto, por extenso, na seção Contexto; regra de como
     escrever cada tipo de arquivo em `.claude/rules/`. Passou do teto? Mova um bloco pro comando/rules/spec com ponteiro; nunca comprima. -->
<!-- mss-spec:regras-do-kit -->

# mss-spec — kit de spec-driven development (plugin do Claude Code)

## Regras obrigatórias do projeto
1. **Nunca codar direto na `main`**: toda tarefa nasce numa branch a partir da `main` atualizada (antes do `switch -c`, `git status -sb` tem de dizer `## main...origin/main`); stage pelo nome, nunca `git add .`/`-A` (`memory/feedback_feature_a_partir_da_master.md`).
2. **Nunca worktree, nunca conversa aberta a partir de outra**: o trabalho é na pasta principal; conversa nova o owner abre pelo + com o texto pronto que você entrega (`memory/feedback_nunca_worktree_nem_conversa_filha.md`).
3. **`git push` e publicação só a pedido do owner**; merge/rebase de feature com a aprovação dele — o hook `hooks/git_publicacao.py` nega push pra `main` (`memory/feedback_publicacao_e_ato_do_owner.md`).

## Contexto
- **Infra:** **própria** — nenhuma: este repo é o kit (plugin do Claude Code), não um serviço — sem proxy no `.env`, sem `docker-compose.office.yml`, sem `get_connection.py`, sem banco, sem Docker; o doctor pula os checks 4, 5 e 6. É esta linha que os comandos leem; nunca perguntar de infra neste repo (owner, 2026-11-03).
- **Stack/runtime:** Python — hooks em `hooks/`, scripts dos moldes em `templates/*.py`, CI em `python:3.12-slim` (`.gitlab-ci.yml`); comandos-prosa em Markdown (`commands/`).
- **Como roda:** plugin do Claude Code, carregado nesta máquina pela junção `~/.claude/skills/mss-spec` → este clone (`docs/LEIA-ME.md`, "Instalação"); hooks registrados em `hooks/hooks.json`; suíte: `python -m pytest tests/ -q`.
- **UI:** não — os comandos geram HTML self-contained em `docs/` (`anatomia.html`, `mapa-neural.html`, `COMO-FUNCIONA.html`).
- **Ambientes:** só local; o publicado é `origin/main` no GitHub, de onde os projetos instalam (`docs/AMBIENTES.md`).
- **Banco:** não.
- **Integrações externas:** nenhuma em runtime (`docs/superpowers/MAPA.md`, Conexões); pré-requisito: plugin `superpowers@claude-plugins-official`.
- **Versionamento:** branch por tarefa a partir da `main`; integra com merge `--no-ff` na `main`; push é ato do owner; versão nos dois manifestos `.claude-plugin/plugin.json` + `marketplace.json`, iguais (`memory/project_versao_em_dois_manifestos.md`).

## Mapa de arquivos (só o que não se infere lendo o repo)
- `docs/decisoes.md` — decisões **transversais** ("X em vez de Y — porque Z"); decisão de um assunto só vai no "Histórico" da spec em `docs/superpowers/specs/`
- `docs/EVALS.md` — corpus de falhas do assistente neste projeto (dogfood do próprio kit), com o guardrail de cada caso
- `docs/LEIA-ME.md` — referência do kit (instalação, comandos); `docs/PRIMEIRO-DIA.md` — o caminho curto de quem chega
- `templates/regras-do-kit/` — os 2 blocos que o plugin injeta em toda janela (`hooks/regras_do_kit.py`); o `CLAUDE.md` do projeto só carrega a marca
- `hooks/README.md` — o que cada hook faz; seção "Fora do kit": a junção e as atualizações do app
- `.claude-plugin/plugin.json` + `marketplace.json` — os dois manifestos do plugin (versão igual nos dois)
- `docs/superpowers/MAPA.md` · `INDEX.md` · `PROXIMO-PASSO.md` — partida (onde estamos · tarefas abertas · detalhe do próximo passo); o que sai do rodízio vai pra `MAPA-historico.md` / `INDEX-historico.md`
- `memory/MEMORY.md` — índice por gatilho; subíndices em `memory/indice/`

## Índice de regras por tipo de arquivo
- `.claude/rules/banco-e-segredo.md` — Banco e segredo — carrega ao tocar `**/*.sql`, `**/db/**`, `**/*banco*.py`, `**/*conn*.py`, `**/*repositor*.py`
- `.claude/rules/frontend.md` — Front-end deste projeto — carrega ao tocar `**/*.html`, `**/*.css`, `**/*.jsx`, `**/*.tsx`
- `.claude/rules/rota-e-endpoint.md` — Rota e endpoint — carrega ao tocar `**/api/**`, `**/routes/**`, `**/app.py`, `**/main.py`, `**/views.py`
