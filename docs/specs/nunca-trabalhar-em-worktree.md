# Nunca trabalhar em worktree, nunca abrir conversa a partir de outra

## Estado atual
O owner não usa worktree e não quer conversa aberta por outra conversa (memória
`memory/feedback_nunca_worktree_nem_conversa_filha.md`). Trava mecânica, ligada por padrão, em duas peças:

- **`hooks/sem_worktree.py`** — `WorktreeCreate` **falha sempre** (é a porta única de criação do Claude Code:
  ferramenta `EnterWorktree`, subagente com `isolation: "worktree"`, workflow, sessão de fundo); `PreToolUse`
  **nega** `EnterWorktree` (cobre entrar num worktree que já existe), `Agent` com `isolation: "worktree"`,
  `Write`/`Edit`/`MultiEdit`/`NotebookEdit` com o alvo **dentro de um worktree**, e
  `mcp__ccd_session__start_session`/`mcp__ccd_session__hand_off_to_session` (abrir, propor ou passar conversa) —
  nesse caso a mensagem manda entregar o **texto pronto pra colar** e parar: o owner abre a conversa pelo **+**;
  `SessionStart` **avisa** quando a conversa já começa dentro de um worktree.
- **`hooks/git_publicacao.py`** (5ª cerca, mesmo processo do shell) — nega `git worktree add` e todo comando que
  **grava** dentro de um worktree (git de escrita, `>`/`>>`/`tee`), pela mesma leitura de alvos da cerca de outro
  projeto.

"Dentro de um worktree" = subindo do caminho, o 1º `.git` é **arquivo** com `gitdir:` apontando pra
`…/worktrees/…` (submódulo aponta pra `…/modules/…` e não conta) — lido do disco, sem rodar o git.
Modos de falha: **criar/entrar/abrir conversa nega sempre** (não depende de nada); **"está dentro?" falha
ABERTA** (arquivo ilegível → libera). Escape só do owner: `MSS_WORKTREE_OFF=1` — **exceto** no
`WorktreeCreate`: o hook substitui a criação do Claude Code, então desligado ele também não cria; worktree, se
um dia precisar, o owner cria no terminal dele. O texto do kit que mandava "abra num worktree"
(`commands/nova-feature.md`, aviso do `um_item_por_janela.py`) passou a dizer: pasta na branch de outra
feature → **pare e pergunte ao owner**; nunca worktree nem conversa nova.

Fora de escopo: apagar worktrees que já existem · `CLAUDE.md` dos projetos (`docs/decisoes.md:48`) · trava
contra o owner (o terminal dele não passa pelos hooks).

## Histórico
- 2026-10-27 — criado (0.46.0): a conversa da 0.44.0 abriu sozinha `.claude/worktrees/partida-em-dois-niveis`
  porque o aviso do kit mandava ("abra esta num worktree") e deixou 2 commits e memória fora da `main`; duas
  conversas abertas a partir de outra ficaram penduradas uma na outra na barra lateral ("eu me perdi").
