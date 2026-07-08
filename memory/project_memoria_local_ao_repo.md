---
name: project-memoria-local-ao-repo
description: "Decisão do owner — memória persistente do kit Spec-Powers vive em memory/ dentro do repo do projeto, não em ~/.claude/projects/<proj>/memory/"
metadata: 
  node_type: memory
  type: project
  originSessionId: c2de51e1-1688-4cbf-a01e-3947b1d77c12
---

No kit Spec-Powers, a memória persistente de cada projeto adotante deve ficar em uma pasta `memory/`
**dentro do próprio repositório** (versionada com git, com `MEMORY.md` como índice) — e NÃO no mecanismo
nativo padrão do Claude Code em `~/.claude/projects/<proj>/memory/`.

**Why:** o owner corrigiu isso explicitamente em 2026-06-30 como "ponto chave muito importante". A pasta
home (`~/.claude/projects/...`) fica presa à máquina/usuário e não viaja com o código — não serve para um
projeto que pode ser clonado por outra pessoa ou rodar em outra máquina. Colocando `memory/` dentro do
repo, a memória acompanha o projeto.

Razão extra (técnica): a memória nativa é indexada por caminho absoluto do diretório de trabalho, então
fragmenta entre git worktrees (caminhos diferentes) — o kit recomenda `using-git-worktrees` do superpowers,
então memória em arquivo no repo evita essa fragmentação. E a nativa é **volátil**: some se o `.claude` for
limpo/reinstalado (risco de perda que o owner levantou em 2026-07-07).

**Cobertura universal (2026-07-07):** projetos SEM `/mss-spec:kickoff` caem no default nativo (`~/.claude`),
porque a regra repo-local do plugin é por-projeto. Fix: (1) regra no **`~/.claude/CLAUDE.md` global**
(carregado em todo projeto) mandando memória nova sempre no repo; (2) comando **`/mss-spec:memory`**
(cópia não-destrutiva da pasta nativa → `<repo>/memory/`). Backup do `~/.claude` antes de mexer no global:
`C:\Ronaldo\_Mitsui\_backup-claude\<timestamp>\`.

**Protocolo replicado do nativo** (não é um sistema novo, só relocado):
- `memory/MEMORY.md` é só **índice** (1 linha por item, até ~150-200 linhas) — nunca o conteúdo.
- Arquivos individuais em `memory/` (frontmatter: name/description/metadata.type) são lidos **sob demanda**,
  só quando o índice aponta relevância — nunca a pasta inteira de uma vez.
- Manutenção/poda: skill `anthropic-skills:consolidate-memory`, rodada periodicamente.
- Versionamento: anda nos commits normais do repo (sem ritual de commit dedicado por memória).

**How to apply:** ao trabalhar em qualquer projeto que adote o kit Spec-Powers (`CLAUDE.md.modelo`,
`LEIA-ME.md`, `ROTEIRO-SPEC-DRIVEN.md`, `MEMORY.md.modelo`, `comando-kickoff.md`), sempre referenciar/gravar
memória persistente em `<projeto>/memory/` (+ `<projeto>/memory/MEMORY.md` como índice), nunca em
`~/.claude/projects/<proj>/memory/`. Os arquivos do kit já foram atualizados para refletir isso (instrução
de leitura no `CLAUDE.md.modelo`, template `MEMORY.md.modelo`, passo no `/kickoff`, nota de manutenção no
ROTEIRO). Ver [[spec-powers-kit-overview]] se existir, para o resumo geral do kit.
