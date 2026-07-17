# Spec-Driven como "default" para os próximos projetos — Documento de referência

## Contexto

O **ATM Robô V2** está praticamente finalizado e serve como **base de lições aprendidas**.
O objetivo aqui **não é implementar nada** nem mexer naquele projeto: é decidir qual
**Spec-Driven Development (SDD)** adotar como *default* nos **próximos projetos** (greenfield),
e entender concretamente o que o CLI do vídeo (`@igoruehara/spec-driven`) faz.

Inclinação do usuário: **formalizar o que já uso (superpowers)** — sem misturar com o projeto atual.

Descoberta-chave do levantamento: **o projeto ATM já foi construído com um fluxo SDD** — o
**superpowers** (plugin oficial Anthropic, habilitado em `~/.claude/settings.json`,
`effortLevel: xhigh`). Os `docs/superpowers/specs/*-design.md` e `docs/superpowers/plans/*.md`
daquele repo são a prova. O ciclo *brainstorm → spec → plano → execução → review → verificação*
**é** Spec-Driven. O vídeo mostra **outra ferramenta** (CLI de terceiros), com convenções próprias.

No projeto ATM **não há** nada custom em `.claude/` (sem `commands/`, `agents/`, `skills/`,
`hooks/`) — só permissões e `launch.json`. Logo, o "default" para os próximos projetos está em aberto.

---

## 1. O que o CLI do vídeo (`@igoruehara/spec-driven`) faz

**Natureza:** um *scaffolder* (gerador de estrutura) Node/npm, multi-cliente, que instala uma
"esteira" SDD completa num comando. Claude é o formato canônico; os demais clientes recebem "views".

**Instalar/rodar:**
- `npx @igoruehara/spec-driven` (diretório atual, menu interativo)
- `npx @igoruehara/spec-driven meu-projeto` (nova pasta)
- Flags: `--agent=claude,cursor`, `--all`, `--force`, `--yes`
- `npx @igoruehara/spec-driven update` → atualiza só a "maquinaria" (skills, hooks, templates,
  scripts, CI); **preserva** seus docs/specs.

**Clientes suportados:** Claude Code (`CLAUDE.md` + `.claude/skills/*/SKILL.md` + hook SessionStart),
Codex (`AGENTS.md`), Cursor, GitHub Copilot, Gemini CLI, Windsurf.

**Estrutura que ele cria:**
```
CLAUDE.md                         # constituição/convenções do agente
README.md                         # manual do pipeline
.claude/skills/                   # 15 skills (+ views por cliente)
.spec-driven/manifest.json        # rastreia clientes gerados
.github/workflows/esteira.yml     # gate de conformidade no CI
scripts/ audit-esteira.mjs · validate-mermaid.mjs · eval-spec-fidelity.mjs
docs/
  glossary.md · STATE.md
  product/        vision · personas · journeys · features · mvp-canvas · roadmap
  architecture/   overview · context-map · diagrams(Mermaid) · assessment · adr/
  engineering/    TESTING · metrics · integrations · _templates
specs/0001-feature/  domain.md · product.md · design.md · spec.md · tasks.md   (1 pasta/feature)
src/                 estrutura em camadas DDD
```

**15 comandos (slash):** `/kickoff` (constitui o projeto, green/brownfield), `/integracoes`
(liga ferramentas + MCPs), `/mapear` (codebase existente → `assessment.md`), `/diagramar`
(arquitetura Mermaid → `diagrams.md`), `/roadmap`, `/camada-agentica` (gera regras/subagents/
skills/CI), `/nova-feature` (abre feature SDD: tier → spec → tasks), `/clarificar` (revisão
adversarial da spec, 1 pergunta por vez), `/validar` (UAT: gates, AC→teste, SPEC_DEVIATION, DoD),
`/revisar-pr` (gate de conformidade no PR), `/setup-ci`, `/metricas` (Lead Time, Throughput,
maturidade CD), `/auditar` (frontmatter, links, rastreabilidade), `/evals` (fidelidade spec→código),
`/handoff` (pausa/retoma via `STATE.md`).

**4 pilares (pipeline):** Lean Inception (descoberta: visão/personas/MVP) → DDD (modelagem:
linguagem ubíqua/bounded contexts) → TDD (design técnico/RFC) → SDD (spec como fonte da verdade
→ tasks → implementação). Encadeado em `/kickoff` → `/nova-feature` → `/clarificar` → `/validar`.

**Gates que ele torna executáveis por máquina:** AC→teste, `SPEC_DEVIATION` (código divergiu da
spec), DoD, auditoria de frontmatter/links/rastreabilidade, eval de fidelidade spec→código,
gate de CI no PR (`esteira.yml`).

**Brownfield:** mantém arquivos existentes (sem `--force`); `/mapear` + `/diagramar` pra entender
o legado; checkpoint/continuidade via `docs/STATE.md`.

---

## 2. O que você JÁ tem (superpowers) mapeado no pipeline do vídeo

| Etapa do vídeo | Comando do CLI | Equivalente em superpowers (já instalado) |
|---|---|---|
| Lean Inception (descoberta) | `/kickoff` | `brainstorming` (perguntas 1 a 1 → design doc) |
| DDD (modelagem de domínio) | parte de `/kickoff`/`/nova-feature` | seção de domínio dentro do `brainstorming` |
| TDD (design + testes) | `/nova-feature` + disciplina | `test-driven-development` |
| SDD (spec → tasks → impl) | `/nova-feature`, `/validar` | `writing-plans` → `executing-plans` / `subagent-driven-development` |
| Revisão adversarial da spec | `/clarificar` | spec self-review do `brainstorming` + `receiving-code-review` |
| Validação / UAT / gates | `/validar`, `/revisar-pr` | `requesting-code-review` + `verification-before-completion` |
| Pausa/retoma entre sessões | `/handoff` (`STATE.md`) | os próprios *plan files* + gestão de contexto |
| Isolamento de trabalho | (não nativo) | `using-git-worktrees` |
| Encerrar branch | — | `finishing-a-development-branch` |

**Conclusão:** o superpowers já cobre praticamente todo o *workflow/disciplina* do vídeo.

---

## 3. CLI × superpowers — o que cada um adiciona de fato

**Só o CLI traz pronto (turnkey):**
- *Scaffolder* de toda a taxonomia de pastas/arquivos num comando (product/architecture/engineering
  + `specs/000X-feat` + `src` DDD).
- **Comandos nomeados** (`/kickoff`, `/nova-feature`…) = entrada explícita e memorizável.
- **Gates executados por máquina**: CI (`esteira.yml`) + scripts (`audit`, `validate-mermaid`,
  `eval-spec-fidelity`) — AC→teste, SPEC_DEVIATION, DoD, rastreabilidade.
- **Multi-cliente** (Claude, Codex, Cursor, Copilot, Gemini, Windsurf).
- **Métricas/evals** (Lead Time, Throughput, fidelidade spec→código).
- Artefatos **DDD/Lean explícitos** (context-map, ADRs, MVP canvas).

**Só superpowers traz (e você já usa):**
- Disciplina como **skills acionáveis pelo agente**: HARD-GATE de não codar sem design aprovado,
  `brainstorming` força perguntar 1 a 1, `test-driven-development`, `systematic-debugging`,
  dar/receber code review, `verification-before-completion`.
- **Plugin oficial Anthropic, Claude-native, sem dependência de terceiros** (mantido/atualizado).
- `subagent-driven-development` e `dispatching-parallel-agents` (paralelismo real).
- **Já provado no projeto ATM Robô V2.**

**Trade-off honesto:** em *workflow/disciplina* é empate (e o superpowers já é seu). Em
*scaffolding + gates de máquina + multi-cliente + métricas*, o CLI ganha de longe out-of-the-box;
reproduzir isso no superpowers é trabalho real.

---

## 4. Caminho recomendado: formalizar superpowers num "kit default" (para o PRÓXIMO projeto)

Bate com a inclinação do usuário e evita dependência de terceiros. O objetivo é **roubar as boas
ideias do CLI sem instalar o CLI**. O "kit" é um *starter* que você copia ao abrir projeto novo:

**A. Template de repositório (starter):**
- `CLAUDE.md` esqueleto com: visão (1 parágrafo), stack, bloco **MODO DE TRABALHO**,
  **"Regras críticas (nunca violar)"**, mapa de arquivos e a tabela "quem faz o quê" (vazia).
- `docs/superpowers/{specs,plans}/` (já é o padrão do superpowers).
- *Opcional p/ projeto grande:* `docs/product/` e `docs/architecture/` (vision, roadmap, ADRs) —
  emprestado do CLI.
- `.claude/settings.json` base com superpowers habilitado + `effortLevel`.

**B. 2 comandos nomeados** (thin wrappers que só invocam skills do superpowers) em `.claude/commands/`:
- `/kickoff` → dispara `brainstorming` enquadrado como "constituição do projeto" e gera o `CLAUDE.md` inicial.
- `/nova-feature` → dispara `brainstorming` (feature) → `writing-plans`, criando o par spec+plano datado.
- **Esse é o principal ganho prático**: hoje você re-invoca skills na mão; os comandos dão o atalho memorizável que o vídeo vende.

**C. Gate leve (opcional, quando quiser rigor de máquina):**
- Um checklist de **Definition of Done** no template + (se houver CI) um passo que roda testes e a
  `verification-before-completion` antes do merge. Não precisa replicar os `.mjs` do CLI.

**D. Handoff:** continuar usando os *plan files* como "STATE" entre sessões (já funciona).

---

## 5. Lições do projeto ATM Robô V2 para embutir no default

1. **CLAUDE.md como fonte viva da verdade.** O daquele repo é exemplar (tabela "quem grava cada
   coluna", "Regras críticas", mapa de arquivos). Esse nível de doc **é** a "constituição" que o
   `/kickoff` do CLI produziria. Lição: todo projeto novo começa com esse esqueleto e cresce.
2. **Bloco "MODO DE TRABALHO"** (diagnosticar → plano curto → esperar OK → verificar no real) — o
   antídoto contra *vibe-coding*. Vai fixo no template.
3. **"Regras críticas (nunca violar)" numeradas, nascidas de bugs reais** (openpyxl getter,
   WinError 32 ao mover ZIP, nunca modificar `get_connection`). É exatamente o loop "lição → regra"
   que o SDD quer capturar. Manter.
4. **Par spec+plano datado** em `docs/superpowers/` funciona bem; para projeto grande, considerar a
   **pasta-por-feature** do CLI (`specs/000X-feat/`).
5. **O que faltou lá:** comandos nomeados. O atrito de re-invocar skills na mão é o que `/kickoff`
   e `/nova-feature` eliminam.

---

## Atualização (2026-07-16): a spec virou "viva por assunto" (spec-anchored)

Decisão tomada e implementada no kit (design em
`docs/superpowers/specs/2026-07-16-spec-viva-por-assunto-design.md`).

**Enquadramento (Birgitta Böckeler):** *spec-first* (spec antes, código depois, spec congela) ·
*spec-anchored* (spec continua viva, atualizada na evolução) · *spec-as-source* (humano só edita a
spec). O kit era spec-first puro — par spec+plano datado, congelado no nascimento.

**O que mudou:** a **spec** passou a ser **spec-anchored** — 1 arquivo por assunto em
`docs/specs/<assunto>.md`, editado no próprio lugar, com **Estado atual** (verdade de hoje) +
**Histórico** (1 linha por mudança). O **plano/tasks continua spec-first** (datado/efêmero em
`docs/superpowers/plans/`), porque plano é retrato de uma rodada, não tem estado a manter.

**Por que valeu (não era só rótulo):** hoje o `INDEX.md` já fazia a *descoberta* da spec funcionar,
mas (a) no nível médio — o default — nem existia doc de spec, e (b) no alto o doc era o retrato de
nascimento, que envelhecia. A spec viva conserta o "estar atualizada": ao voltar num assunto o
assistente lê o "Estado atual" direto, e `fix`/`refactor` que mudam comportamento **atualizam** a
spec, pra ela nunca mentir e induzir o assistente a reintroduzir bug numa tarefa futura. Operacional
no `docs/ROTEIRO-SPEC-DRIVEN.md`.

## 6. Quando reconsiderar adotar o CLI de fato

- Trabalho em **time** querendo padrão turnkey que outros instalam com um `npx`.
- Querer **gates executados por máquina** no CI (AC→teste, spec-fidelity, SPEC_DEVIATION).
- Usar **múltiplos clientes** (Cursor/Copilot/Codex/Gemini) com specs compartilhadas.
- Querer **métricas** de entrega (Lead Time, Throughput).
- Caso contrário (solo, Claude Code, controle total, sem dependência de terceiros): **formalizar
  superpowers é o caminho mais enxuto** — e é o recomendado.

---

## Próximo passo real (fora do projeto ATM)

Nada muda no ATM Robô V2. Quando você abrir um **projeto novo**, aplicar o item 4 ali (template +
2 comandos). Se quiser, dá pra montar esse "starter kit" como repositório-modelo separado numa
próxima conversa.

## Fontes
- https://github.com/igoruehara/spec-driven
- https://github.com/github/spec-kit (referência geral de SDD)
