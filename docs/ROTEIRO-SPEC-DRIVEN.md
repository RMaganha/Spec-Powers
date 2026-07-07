# Playbook Spec-Driven (mínimo) — manual do owner

> Referência (fica no repo do plugin; não vai pros projetos). O que faz o fluxo rodar num projeto é: o
> plugin **superpowers** + o plugin **mss-spec** (comandos `/mss-spec:kickoff`, `/mss-spec:nova-feature`,
> `/mss-spec:ambiente`, `/mss-spec:banco`, `/mss-spec:precedentes`, `/mss-spec:plano-teste`, `/mss-spec:modo`, `/mss-spec:documentacao`, `/mss-spec:memory`) + o `CLAUDE.md`.
> Aqui está o "como" e o "porquê", enxuto.

## Princípio: a disciplina já vem do superpowers
Não há hooks nem gates próprios — as skills do superpowers auto-ativam e **já forçam** o essencial:

| Quero garantir | Skill do superpowers (já força) |
|---|---|
| Não codar antes do OK | `brainstorming` (HARD-GATE: nada de código sem design aprovado) |
| Teste antes do código | `test-driven-development` (Iron Law) |
| Provar antes de "pronto" | `verification-before-completion` (evidência antes de afirmar) |
| Tratar bug com método | `systematic-debugging` |
| Revisar antes de integrar | `requesting-code-review` / `receiving-code-review` |
| Isolar e fechar | `using-git-worktrees` / `finishing-a-development-branch` |

O kit só adiciona o que falta: **atalhos nomeados** + um **`CLAUDE.md`** certo + **`settings.json`** correto.

**Nível de cerimônia** (o ritual completo do superpowers é lento): o fluxo tem 3 níveis — **mínimo** (executa direto), **médio** (padrão: design curto + plano curto + execução inline) e **alto** (ritual completo com subagentes/dupla revisão, só p/ feature grande). Troque com `/mss-spec:modo`. Ortogonal ao `effortLevel` do `settings.json` (padrão `medium`) — os dois juntos controlam velocidade × profundidade.

Além disso, o `CLAUDE.md` gerado instrui o assistente a **assumir o papel de especialista sênior do domínio de cada tarefa** (UI/UX, desenvolvimento, DBA, segurança…) e voltar ao padrão (arquiteto/engenheiro sênior de desenvolvimento) depois do OK — persona especialista eleva a qualidade (nasceu de entregas de layout genéricas ruins).

## Fluxo
1. **Constituir** — `/mss-spec:kickoff` entrevista (1 pergunta por vez via brainstorming), gera o `CLAUDE.md` e faz o scaffolding (memória, índice de tarefas, AMBIENTE). Serve para projeto novo **e existente** (faz scan antes de perguntar).
2. **Por feature** — `/mss-spec:nova-feature <nome>`: brainstorming → objetivo + **Critérios de Aceite** (suas validações) + fora de escopo → seu OK → `writing-plans` → tasks pequenas → executa **uma por vez** (TDD → roda → cola a saída → próxima).
3. **Fechar** — review → fecha a branch → se surgiu regra durável, 1 linha nas "Regras críticas" do `CLAUDE.md`.

## Tipos de mudança (sem cerimônia desnecessária)
- **feat** → fluxo completo acima.
- **fix** → o **teste que reproduz o bug é a spec**; corrige; verifica. Sem pasta de spec.
- **refactor** → sem ACs novos; o gate é "os testes continuam verdes".
- **chore/docs** → sem spec.
- **spike** → branch descartável, time-boxed; depois joga fora ou promove a feature.

## Definition of Done (antes de dizer "pronto")
- [ ] Cada Critério de Aceite tem teste **e os testes passam** (saída colada).
- [ ] **Plano de teste base 100% verde** (`/mss-spec:plano-teste`); baseline atualizado se cresceu.
- [ ] Review feito; findings resolvidos.
- [ ] Branch fechada; `CLAUDE.md` atualizado se nasceu regra/decisão durável.

## Memória e estado (não poluir o CLAUDE.md)
- **`CLAUDE.md`** = só regras/fatos sempre-verdadeiros. Nunca journal/registro.
- **Aprendizados persistentes** = pasta `memory/` **do projeto** (dentro do repo, versionada com git) + `MEMORY.md` como índice — NÃO em `~/.claude/projects/<proj>/memory/` (essa fica fora do repo, presa à máquina/usuário e não viaja com o código, e fragmenta entre worktrees por ser indexada por caminho absoluto).
- **Protocolo de leitura/escrita** = igual ao nativo: `MEMORY.md` é só índice (1 linha por item, até ~150-200 linhas); arquivos individuais em `memory/` só são abertos sob demanda, quando relevantes à tarefa. Nunca ler a pasta inteira de uma vez.
- **Manutenção** = rode a skill `anthropic-skills:consolidate-memory` de tempos em tempos (ou quando o índice começar a inchar) para mesclar duplicatas e podar entradas mortas — evita que vire um segundo sistema para manter.
- **Estado/handoff entre sessões** = os plan files do superpowers (`docs/superpowers/plans/`).

## Banco de dados (quando houver)
DDL versionada em `sql/NN_*.sql`, revisada pelo owner e rodada **fora do app**; acesso isolado por fonte;
credenciais só em `.env`. Mudança de schema = decisão + migração + seu OK antes de aplicar.

## Ambiente corporativo MSIG
Fatos e padrões de infraestrutura que se repetem entre projetos (rede Docker `mitiai_network`, proxy
corporativo, Postgres compartilhado, SQL Server, pipeline Azure) ficam em `docs/AMBIENTE.md` (copiado de
`templates/AMBIENTE.md`, embutido no plugin, pelo `/mss-spec:kickoff`) — não no `CLAUDE.md`, que fica só
com o que é específico deste projeto. Levantado em 2026-07-02 varrendo 7 projetos reais (ver
`templates/AMBIENTE.md` para o conteúdo). Pra gerar os arquivos de infra (docker-compose + override de
proxy) no padrão MSIG, use `/mss-spec:ambiente`. Pra saber se um problema de arquitetura (RAG/vetores,
extração de documento com LLM, etc.) já foi resolvido em outro projeto, use `/mss-spec:precedentes` (ou a
skill `precedentes-msig`, que dispara sozinha), embutida no plugin.

## Adiado (entra só quando um projeto pedir)
`docs/ESTADO.md` + um SessionStart **advisory** (não-bloqueante; reusar o wrapper polyglot que o superpowers já
traz, nunca shell cru) · `ROADMAP.md` · pasta de spec por feature · gate **AC→teste** no CI/merge (nunca no
Stop/PreToolUse) · qualquer hook bloqueante. Motivo: hooks bloqueantes quebravam no Windows, travavam o
bootstrap e duplicavam o que as skills do superpowers já forçam.
