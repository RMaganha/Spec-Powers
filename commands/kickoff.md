---
description: Constitui o projeto (green/brownfield) — entrevista, gera CLAUDE.md e faz scaffolding de memória, índice de tarefas e AMBIENTE
argument-hint: "[ideia em 1 linha, ou aponte para um repo existente]"
disable-model-invocation: true
---

Você vai **constituir este projeto**. NÃO escreva código de aplicação nesta etapa.

**Nunca invente fatos concretos.** Caminhos, paths de deploy, hosts, portas, nomes de container/recurso, estrutura de pastas — use SÓ o que está no `projeto.md`, no repositório, ou o que o owner disser. Ao propor opções (A/B/C) ou um rascunho de contexto, não preencha um detalhe específico que você não verificou: deixe genérico ("um diretório de deploy", "o host do Postgres"), marque como `<a confirmar>`, ou pergunte. Um caminho chutado que não existe é pior que uma lacuna.

1. Invoque a skill **superpowers:brainstorming**.
2. **Garanta a dependência**: verifique se o superpowers está habilitado. Se não houver `.claude/settings.json` ou ele não listar o superpowers, crie/atualize copiando de `${CLAUDE_PLUGIN_ROOT}/templates/settings.json`.
3. **Se já existe código** (brownfield): faça um scan primeiro — estrutura de pastas, stack, entrypoints (`main.py`/`app.py`), como roda, integrações — e proponha um rascunho do contexto e do propósito do projeto (nome + a que se destina) antes de perguntar.
4. **Entreviste o owner uma coisa por vez** (multiple choice quando der): objetivo em 1 frase · usuários · stack/runtime · como roda (CLI/serviço/porta/container/cron) · UI? (se sim, padrão FastAPI + Jinja) · integrações externas · banco (qual/como conecta) · restrições · critérios de sucesso.
5. **Scaffolding** — copie de `${CLAUDE_PLUGIN_ROOT}/templates/` para o projeto, criando as pastas se preciso, e preencha os `<...>` do `CLAUDE.md` com o que foi entrevistado:
   - `templates/CLAUDE.md`   → `CLAUDE.md` (raiz)
   - `templates/MEMORY.md`   → `memory/MEMORY.md`
   - `templates/INDEX.md`    → `docs/superpowers/INDEX.md`
   - `templates/AMBIENTE.md` → `docs/AMBIENTE.md` (ajuste os `<...>` do projeto; apague seções que não se aplicam, ex.: sem SQL Server)
   - `templates/settings.json` → `.claude/settings.json` (se ainda não existir do passo 2)
   - `templates/gitignore` → `.gitignore` (se não existir; se existir, garanta que `.env` está ignorado — adicione a linha se faltar). Protege segredo de subir.
   - **Se o projeto tem UI web:** `templates/FRONTEND.md` → `docs/FRONTEND.md` (design system MSIG) e `templates/assets/logo.png` → `static/img/logo.png` (logo MSIG). Se não tem UI, pule os dois.
6. NÃO crie specs/planos agora — features vêm depois com `/mss-spec:nova-feature`.

Ideia/insumo do owner: $ARGUMENTS
