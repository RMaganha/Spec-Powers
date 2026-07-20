# mss-spec — plugin Spec-Driven MSIG (sobre superpowers)

Plugin do Claude Code que adiciona um fluxo **Spec-Driven** leve por cima do plugin **superpowers**.
A disciplina (não codar sem OK, TDD, verificação, code review) vem do superpowers; o `mss-spec`
adiciona comandos nomeados que fazem o *scaffolding* e carregam o padrão corporativo MSIG (rede
Docker, proxy, Postgres/SQL Server, Azure). Instala uma vez, vale em todo projeto — não se copia mais
arquivo à mão.

## Instalação (marketplace local)

Como ainda **não publicamos num git interno**, a distribuição pro time é por cópia de pasta: o autor
compacta o repositório, o colega extrai numa pasta **local qualquer** (ex.: `C:/ferramentas/mss-spec`,
sem espaços/acentos) e aponta o marketplace pra ela. Numa sessão do Claude Code:
```
/plugin marketplace add C:/ferramentas/mss-spec
/plugin install mss-spec@mss-local
```
Escolha escopo `user` (vale em todos os projetos da máquina). `mss-local` é o nome fixo da lojinha; só
o caminho antes muda de máquina pra máquina. Requer Claude Code **v2.1.140+**.

O **superpowers** é pré-requisito e **não** é instalado por dependência (a declaração cross-marketplace
quebrava o load via symlink — foi revertida): habilite-o à parte (`superpowers@claude-plugins-official`).
O `/mss-spec:kickoff` já o deixa ligado no `.claude/settings.json` do projeto.

Promoção pro time depois: trocar a `source` em `.claude-plugin/marketplace.json` de caminho local para
um repositório git — aí cada colega instala por URL e puxa atualizações, sem copiar pasta.

## Comandos

Na ordem de ciclo de vida (começar → montar base → construir → apoio → verificar/publicar → manter):

| Comando | O que faz |
|---|---|
| `/mss-spec:kickoff "ideia"` | Constitui o projeto (green/brownfield): entrevista e gera `CLAUDE.md`, `memory/MEMORY.md`, `docs/superpowers/INDEX.md`, `docs/AMBIENTE.md`, `docs/ESTRUTURA.md` (pastas em camadas), `docs/decisoes.md`, `config/logging.py`, `.claude/settings.json`, `.gitignore` e — se tiver UI — `docs/FRONTEND.md` + `static/img/logo.png` |
| `/mss-spec:doctor` | Pré-vôo do ambiente MSIG (proxy, CA, ODBC, rede docker, `.env`, superpowers, resolução do plugin) — veredito ✓/✗; só reporta. Roda manual e sozinho na 1ª tarefa |
| `/mss-spec:ambiente` | Gera infra no padrão MSIG (docker-compose com `mitiai_network`; override de proxy do escritório) |
| `/mss-spec:banco` | Gera o módulo de conexão (SQL Server via pyodbc, ou Postgres) no padrão MSIG |
| `/mss-spec:log [arquivo]` | Monta o padrão de log (stdout + arquivo rotativo em dev, ícone por nível só em dev; nunca PII/segredo) e instrumenta os arquivos escolhidos (opt-in por-arquivo) |
| `/mss-spec:nova-feature <nome>` | Abre feature: Critérios de Aceite → seu OK → plano → tasks (TDD + verificação); mantém o `INDEX.md`; no fecho roda o `release` |
| `/mss-spec:frontend` | Instala o front moderno (React + TS + Mantine, tema MSIG) para telas densas — scaffold Vite + guia ilha × rota SPA |
| `/mss-spec:precedentes <assunto>` | Consulta o catálogo do que já foi resolvido em outro projeto MSIG |
| `/mss-spec:modo <nível>` | Alterna o nível de cerimônia do fluxo: mínimo · médio (padrão) · alto |
| `/mss-spec:memory` | Resgata memória da pasta nativa (`~/.claude/...`) pro `memory/` do repo (não-destrutivo) |
| `/mss-spec:to-dolist <ação>` | Caixa de captura pessoal (adicionar/listar/feito), visível em qualquer branch, fora do git |
| `/mss-spec:plano-teste` | Roda o plano de teste base (pytest); se 100% verde, vira o novo baseline anti-regressão |
| `/mss-spec:seguranca` | Audita AppSec (OWASP + baseline MSIG) e corrige com seu OK; relatório HTML ordenado crítico→fácil |
| `/mss-spec:compliance` | Audita a aderência às convenções do kit (estrutura, docs, memória, gitignore); só reporta ✓/✗ |
| `/mss-spec:release` | Gate de pré-publicação: roda testes + confere versão/CHANGELOG + convenção (compliance) + segurança + specs; só reporta |
| `/mss-spec:upgrade` | Sincroniza um projeto existente com a evolução dos moldes (mescla `CLAUDE.md`, conflito pergunta; não mexe em código) |
| `/mss-spec:documentacao <tema>` | Gera documentação HTML no estilo editorial MSIG (arquivo único self-contained) |

## Fluxo

1. Num projeto (novo ou existente): `/mss-spec:kickoff "em 1 frase o que é e pra quem"` — entrevista e faz o scaffolding.
2. Por feature: `/mss-spec:nova-feature <nome>`.
3. Mudança pequena (bugfix/refactor/chore) não precisa de `/mss-spec:nova-feature` — só pedir.

## Memória e estado (não poluir o CLAUDE.md)
- **Aprendizados** → `memory/` (por-tópico, índice em `memory/MEMORY.md`), dentro do repo, versionado.
- **Tarefas** → spec **viva por assunto** em `docs/specs/<assunto>.md` (Estado atual + Histórico); planos datados/efêmeros em `docs/superpowers/plans/`; índice em `docs/superpowers/INDEX.md`.
- Ambos: índice barato lido no início; arquivos abertos **sob demanda**; `Grep`/`Glob` de fallback.
- `CLAUDE.md` = só regras/fatos sempre-verdadeiros; nunca journal/registro.

## Branch / git
`nova-feature` **não** cria branch nem worktree. Se quiser isolamento, peça explicitamente
(superpowers `using-git-worktrees`) antes ou durante a feature.

## Skill de precedentes
O plugin traz a skill `precedentes-msig` (em `skills/`), que dispara sozinha quando você vai
implementar algo que pode já existir em outro projeto (RAG/busca vetorial, extração de PDF com LLM,
etc.) — além do comando `/mss-spec:precedentes` para consulta explícita. Cresce por linha, sem
cerimônia.

## Autoteste do kit
`python -m pytest tests/ -q` — smoke que confere que todo caminho citado nos commands/skills existe
(`${CLAUDE_PLUGIN_ROOT}/...` e `templates/...`), que os manifestos são JSON válidos e coerentes, e que
os compose templates parseiam. Rode antes de commitar mudança em comando/template. Baseline em
`docs/superpowers/PLANO-TESTE.md`. Histórico de versões: `CHANGELOG.md` (bump no `plugin.json` a cada release).

## Redes de segurança
Três redes prontas para quando algo dá errado — nenhuma é comando novo:
- **Auto-teste** — `python -m pytest tests/ -q` (acima): pega referência morta antes de commitar.
- **Rollback = git** — não há comando de "desfazer". Como `kickoff` e `upgrade` só mexem em arquivos versionados sob árvore de trabalho limpa, `git restore`/descartar a branch já reverte. Sem comando dedicado de propósito (YAGNI).
- **CHANGELOG** — `CHANGELOG.md` versionado é a rede contra *drift* entre cópias (qual "v0.8" é qual, enquanto a distribuição for por cópia de pasta).

## Documentos deste repo (não vão pros projetos)
- `docs/ROTEIRO-SPEC-DRIVEN.md` — playbook do owner (princípio, fluxo, tipos de mudança, DoD, memória, ambiente).
- `docs/referencia-spec-driven.md` — o porquê do kit (comparação com o CLI `@igoruehara/spec-driven`, lições do ATM).
- `docs/superpowers/specs/2026-07-02-mss-spec-plugin-design.md` — design deste plugin.
- `docs/superpowers/plans/2026-07-02-mss-spec-plugin.md` — plano de implementação.
