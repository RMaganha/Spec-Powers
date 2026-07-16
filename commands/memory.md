---
description: Resgata a memória nativa (~/.claude/projects/<proj>/memory/) para <repo>/memory/ versionado — cópia não-destrutiva
argument-hint: ""
disable-model-invocation: true
---

Você vai **trazer pro repositório** a memória que porventura ficou na pasta nativa do Claude (volátil, fora do git). **Não-destrutivo**: só copia — a nativa fica intacta como fallback.

1. **Ache a pasta nativa deste projeto** em `~/.claude/projects/`. O nome dela é o caminho absoluto do projeto com os separadores virando `-` (ex.: `C:\projetos\MeuApp\Azure` → algo como `C--projetos-MeuApp-Azure`). Se não tiver certeza de qual é, **liste** `~/.claude/projects/*/memory/` e **confirme comigo** antes de copiar (não chute a pasta errada).
2. **Se ela existir e tiver arquivos:** copie os `*.md` (menos o `MEMORY.md`) para `<repo>/memory/`, criando a pasta se preciso. **Não sobrescreva** um arquivo de mesmo nome já existente no repo sem me avisar.
3. **Índice:** funda as linhas do `MEMORY.md` nativo no `memory/MEMORY.md` do repo (crie do template do plugin se não existir); não duplique linhas.
4. **Commit (fecha a durabilidade):** só a memória vira durável depois de commitada. Se for um repo git:
   - garanta que existe `.gitignore` protegendo `.env` (crie de `${CLAUDE_PLUGIN_ROOT}/templates/gitignore` se faltar);
   - stage **nominal** — `git add memory/` (e `docs/` se houver doc a versionar). **NUNCA** `git add .`/`-A` (varreria `.env`/segredos);
   - rode `git status` e confira que **nada sensível** entrou;
   - `git commit -m "chore: resgata memoria para o repo (versionada)"`. **Local, sem `git push`** (regra "Git local-only" do `CLAUDE.md`: push só a pedido do owner).
   - Se NÃO for repo git, avise e pergunte antes de `git init` (não inicialize sozinho).
5. **Reporte** o que foi copiado, de onde, e o commit. Lembre: ficam **duas cópias** (repo = fonte durável; nativa = fallback intocado); memórias **novas** já vão direto pro repo (regra no `CLAUDE.md`).
6. Se a pasta nativa não existir ou estiver vazia, diga que não há nada a resgatar — sem inventar.
