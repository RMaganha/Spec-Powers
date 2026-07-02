# mss-spec — plugin Spec-Driven MSIG (sobre superpowers)

Plugin do Claude Code que adiciona um fluxo **Spec-Driven** leve por cima do plugin **superpowers**.
A disciplina (não codar sem OK, TDD, verificação, code review) vem do superpowers; o `mss-spec`
adiciona comandos nomeados que fazem o *scaffolding* e carregam o padrão corporativo MSIG (rede
Docker, proxy, Postgres/SQL Server, Azure). Instala uma vez, vale em todo projeto — não se copia mais
arquivo à mão.

## Instalação (marketplace local)

Numa sessão do Claude Code:
```
/plugin marketplace add C:/Ronaldo/_Mitsui/Python/Spec-Powers
/plugin install mss-spec@mss-local
```
Escolha escopo `user` (vale em todos os projetos da máquina). Requer o **superpowers** habilitado e
Claude Code **v2.1.140+**.

Promoção pro time depois: trocar a `source` em `.claude-plugin/marketplace.json` de caminho local para
um repositório git.

## Comandos

| Comando | O que faz |
|---|---|
| `/mss-spec:kickoff "ideia"` | Constitui o projeto (green/brownfield): entrevista e gera `CLAUDE.md`, `memory/MEMORY.md`, `docs/superpowers/INDEX.md`, `docs/AMBIENTE.md` e `.claude/settings.json` |
| `/mss-spec:nova-feature <nome>` | Abre feature: Critérios de Aceite → seu OK → plano → tasks (TDD + verificação); mantém o `INDEX.md` |
| `/mss-spec:ambiente` | Gera infra no padrão MSIG (docker-compose com `mitiai_network`; override de proxy do escritório) |
| `/mss-spec:banco` | Gera o módulo de conexão (SQL Server via pyodbc, ou Postgres) no padrão MSIG |
| `/mss-spec:precedentes <assunto>` | Consulta o catálogo do que já foi resolvido em outro projeto MSIG |
| `/mss-spec:plano-teste` | Roda o plano de teste base (pytest); se 100% verde, vira o novo baseline anti-regressão |

## Fluxo

1. Num projeto (novo ou existente): `/mss-spec:kickoff "em 1 frase o que é e pra quem"` — entrevista e faz o scaffolding.
2. Por feature: `/mss-spec:nova-feature <nome>`.
3. Mudança pequena (bugfix/refactor/chore) não precisa de `/mss-spec:nova-feature` — só pedir.

## Memória e estado (não poluir o CLAUDE.md)
- **Aprendizados** → `memory/` (por-tópico, índice em `memory/MEMORY.md`), dentro do repo, versionado.
- **Tarefas** → `docs/superpowers/specs` + `plans`, índice em `docs/superpowers/INDEX.md`.
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

## Documentos deste repo (não vão pros projetos)
- `docs/ROTEIRO-SPEC-DRIVEN.md` — playbook do owner (princípio, fluxo, tipos de mudança, DoD, memória, ambiente).
- `docs/referencia-spec-driven.md` — o porquê do kit (comparação com o CLI `@igoruehara/spec-driven`, lições do ATM).
- `docs/superpowers/specs/2026-07-02-mss-spec-plugin-design.md` — design deste plugin.
- `docs/superpowers/plans/2026-07-02-mss-spec-plugin.md` — plano de implementação.
