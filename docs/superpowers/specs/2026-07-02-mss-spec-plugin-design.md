# Design — Plugin `mss-spec` (Claude Code)

Data: 2026-07-02 · Status: aprovado para planejamento

## 1. Objetivo

Transformar o kit Spec-Powers (hoje uma pasta de templates copiados manualmente por projeto) em um
**plugin do Claude Code** instalado uma vez e disponível em todo projeto — igual ao `superpowers`.
O plugin entrega a maquinaria ativa (comandos + skills) e, via comando, faz o *scaffolding* dos
arquivos que são inerentemente por-projeto. Elimina o `rename.txt` e a cópia manual de arquivos.

## 2. Distribuição e escopo

- **Agora (solo):** marketplace local (`marketplace.json` apontando para a pasta do plugin) +
  `/plugin install` em escopo `user`. Disponível em todos os projetos da máquina.
- **Depois (time):** trocar a `source` do `marketplace.json` para um repositório git; escopo pode
  passar a `project` onde fizer sentido. Sem retrabalho de estrutura.
- Requisito: Claude Code v2.1.140+ (recursos maduros de plugin).

## 3. Estrutura do plugin

A própria pasta `Spec-Powers` é reestruturada no layout de plugin:

```
mss-spec/                              (repo do plugin; ex-Spec-Powers)
├── .claude-plugin/
│   ├── plugin.json                    ← manifesto (name: mss-spec)
│   └── marketplace.json               ← marketplace local (source → git na promoção)
├── commands/
│   ├── kickoff.md
│   ├── nova-feature.md
│   ├── ambiente.md
│   ├── banco.md
│   └── precedentes.md
├── skills/
│   └── precedentes-msig/SKILL.md      ← catálogo de auto-disparo (movido de ~/.claude/skills)
├── templates/                         ← embutidos; os comandos copiam pro projeto
│   ├── CLAUDE.md
│   ├── settings.json                  ← habilita superpowers + effort
│   ├── MEMORY.md                      ← índice de memória (vazio)
│   ├── INDEX.md                       ← índice de tarefas (vazio)
│   └── AMBIENTE.md                    ← referência de infra MSIG
└── docs/                              ← manuais do repo (não vão pros projetos)
    ├── LEIA-ME.md · ROTEIRO-SPEC-DRIVEN.md · referencia-spec-driven.md
    └── superpowers/specs/2026-07-02-mss-spec-plugin-design.md  (este doc)
```

Comandos ficam namespaced: `/mss-spec:kickoff`, `/mss-spec:banco`, etc.

## 4. Comandos

| Comando | Responsabilidade | O que escreve no projeto |
|---|---|---|
| **`kickoff`** | Constitui o projeto (green/brownfield). Entrevista via `brainstorming`; se brownfield, faz scan (absorve o antigo `PROMPT-CONHECER-PROJETO`). Garante a dependência do superpowers. | `CLAUDE.md`, `.claude/settings.json`, `memory/MEMORY.md`, `docs/superpowers/INDEX.md`, `docs/AMBIENTE.md` (dos templates) |
| **`nova-feature`** | Abre feature: `brainstorming` → Critérios de Aceite → OK → `writing-plans` → tasks (uma por vez, TDD + verificação). **Não mexe em git** — branch é pedida explicitamente pelo usuário (ver §7). | Cria `spec` + `plan`; acrescenta linha no `INDEX.md`; ao fechar, atualiza status |
| **`ambiente`** | Gera os arquivos de infra no padrão MSIG. Pergunta "containerizado? roda no escritório?" e gera conforme. | `docker-compose.yml` (rede `mitiai_network` externa) e, se container-no-escritório, `docker-compose.office.yml` (override de proxy). **Sem certificado** (ver §6) |
| **`banco`** | Gera o boilerplate de conexão no padrão MSIG. Pergunta SQL Server ou Postgres; p/ SQL Server, modo simples ou Fernet. Mostra e confirma antes de gravar. | Módulo de conexão (`get_connection.py`) + entradas no `.env.example` |
| **`precedentes`** | Consulta explícita ao catálogo de precedentes entre projetos. A skill homônima também dispara sozinha. | Nada — só lê o catálogo e aponta projeto/arquitetura |

**Deliberadamente NÃO são comandos:** fechar feature/code review (skills `finishing-a-development-branch`
/ `requesting-code-review`); gravar/consolidar memória (inline + skill `consolidate-memory`); conteúdo
do `AMBIENTE.md` (é template + doc, entregue pelo `kickoff`).

## 5. Modelo de memória (2 camadas, 2 índices, leitura sob demanda)

Objetivo: não lotar contexto; cada coisa no seu arquivo; índice barato carregado no início.

- **Camada 1 — Aprendizados** (`memory/`, por-tópico, valem pro projeto inteiro):
  `memory/MEMORY.md` (índice, 1 linha por item) + `memory/<slug>.md` (1 aprendizado/arquivo,
  frontmatter + corpo curto). Manutenção: skill `consolidate-memory`.
- **Camada 2 — Artefatos de tarefa** (`docs/superpowers/`, por-tarefa):
  `specs/<data>-<tarefa>-design.md` + `plans/<data>-<tarefa>-plan.md`, indexados por
  `docs/superpowers/INDEX.md` (1 linha por tarefa: nome, objetivo, status). Caminho alinhado com o
  padrão onde `brainstorming`/`writing-plans` já escrevem.
- **Comportamento:** no início da sessão o `CLAUDE.md` instrui ler só os dois índices; arquivos
  pesados abrem sob demanda; `Grep`/`Glob` como fallback.
- **Manutenção do índice de tarefas:** feita pelo comando `nova-feature` (determinístico), não por
  skill que "talvez" rode.

## 6. Ambiente e proxy

- **Host (dev local, `pip install`):** opção 1 do padrão MSIG — `pip config set global.proxy`,
  `setx HTTP_PROXY/HTTPS_PROXY`, proxy no Docker Desktop. **Sem certificado** (Windows já confia na
  CA corporativa).
- **Certificado corporativo:** fora de escopo deste plugin. Assume-se que containers rodam em Azure
  (sem o proxy corporativo) ou não fazem chamada externa local. Se um projeto precisar de container
  fazendo HTTPS atrás do proxy do escritório, o cert é tratado manualmente, fora do plugin.
- Fatos fixos (rede `mitiai_network`, hosts, Postgres/SQL Server, pipeline Azure) documentados no
  template `AMBIENTE.md`.

## 7. Git / branches

`nova-feature` **não** cria branch nem worktree automaticamente. Branch nova é uma ação explícita do
usuário (via `using-git-worktrees` do superpowers, quando quiser isolamento). A documentação de uso do
plugin (§ README) explica quando e como pedir isso.

## 8. Dependência do superpowers

O `mss-spec` usa as skills do superpowers (brainstorming, TDD, verification, debugging, code review).
O `kickoff` verifica se o superpowers está habilitado e, se não estiver, escreve no
`.claude/settings.json` do projeto. Validação empírica (não há confirmação de que um plugin force
habilitar outro).

## 9. O que sai (em relação ao kit atual)

- `rename.txt` e a cópia manual de arquivos → substituídos pelo scaffolding via `kickoff`.
- `PROMPT-CONHECER-PROJETO.md` → dissolvido dentro do `kickoff` (scan brownfield).
- `PROMPT-MAPEAR-AMBIENTE.md` → descartado (coberto por `ambiente` + `AMBIENTE.md`).
- Injeção de certificado corporativo → fora de escopo (ver §6).

## 10. Verificação (como saber que funciona)

1. Instalar o plugin local (`/plugin marketplace add` + `/plugin install`, escopo `user`) — passo
   manual do owner (comandos interativos).
2. Num projeto-rascunho vazio, rodar `/mss-spec:kickoff` e confirmar que os 5 arquivos são gerados
   corretamente.
3. Rodar `/mss-spec:nova-feature` e confirmar spec+plan criados e `INDEX.md` atualizado.
4. Rodar `/mss-spec:banco` e `/mss-spec:ambiente` e revisar os arquivos gerados.
5. Confirmar que a skill `precedentes-msig` aparece na lista de skills numa sessão nova.

## 11. Dívidas / evolução futura

- **`precedentes` com caminhos absolutos** (`C:\Ronaldo\...`) — funciona solo; ao promover pro time
  via git, migrar para caminhos relativos ou uma convenção portável.
- Promoção do `marketplace.json` de fonte local para git quando validado.

## 12. Fora de escopo

Hooks bloqueantes; `docs/ESTADO.md`/`ROADMAP.md`; gate AC→teste em CI; qualquer coisa que o
superpowers já force via skills. Nada de mudança nos projetos existentes (IA Bot Agent, Jeday, etc.)
— eles são apenas fonte de referência do padrão.
