---
description: Resgata a memória nativa (~/.claude/projects/<proj>/memory/) para <repo>/memory/ versionado — cópia não-destrutiva
argument-hint: ""
disable-model-invocation: true
---

Você vai **trazer pro repositório** a memória que porventura ficou na pasta nativa do Claude (volátil, fora do git). **Não-destrutivo**: só copia — a nativa fica intacta como fallback.

1. **Ache a pasta nativa deste projeto** em `~/.claude/projects/`. O nome dela é o caminho absoluto do projeto com os separadores virando `-` (ex.: `C:\Ronaldo\...\IA Jeday Cosseguro\Azure` → algo como `C--Ronaldo--...-IA-Jeday-Cosseguro-Azure`). Se não tiver certeza de qual é, **liste** `~/.claude/projects/*/memory/` e **confirme comigo** antes de copiar (não chute a pasta errada).
2. **Se ela existir e tiver arquivos:** copie os `*.md` (menos o `MEMORY.md`) para `<repo>/memory/`, criando a pasta se preciso. **Não sobrescreva** um arquivo de mesmo nome já existente no repo sem me avisar.
3. **Índice:** funda as linhas do `MEMORY.md` nativo no `memory/MEMORY.md` do repo (crie do template do plugin se não existir); não duplique linhas.
4. **Reporte** o que foi copiado e de onde. Lembre: ficam **duas cópias** (repo = fonte durável versionada; nativa = fallback intocado), e memórias **novas** já devem ir direto pro repo (regra no `CLAUDE.md` global e do projeto).
5. Se a pasta nativa não existir ou estiver vazia, diga que não há nada a resgatar — sem inventar.
