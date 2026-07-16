---
description: Constitui o projeto (green/brownfield) — entrevista, gera CLAUDE.md e faz scaffolding de memória, índice de tarefas e AMBIENTE
argument-hint: "[ideia em 1 linha, ou aponte para um repo existente]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Você vai **constituir este projeto**. NÃO escreva código de aplicação nesta etapa.

**Nunca invente fatos concretos.** Caminhos, paths de deploy, hosts, portas, nomes de container/recurso, estrutura de pastas — use SÓ o que está no `projeto.md`, no repositório, ou o que o owner disser. Ao propor opções (A/B/C) ou um rascunho de contexto, não preencha um detalhe específico que você não verificou: deixe genérico ("um diretório de deploy", "o host do Postgres"), marque como `<a confirmar>`, ou pergunte. Um caminho chutado que não existe é pior que uma lacuna.

1. Invoque a skill **superpowers:brainstorming**.
2. **Garanta a dependência**: verifique se o superpowers está habilitado. Se **não existe** `.claude/settings.json`, crie copiando de `${CLAUDE_PLUGIN_ROOT}/templates/settings.json`. Se **já existe**, NUNCA copie por cima (apagaria permissões/hooks/env do projeto): faça **merge** — adicione `"superpowers@claude-plugins-official": true` dentro de `enabledPlugins` (criando a chave se faltar) e `effortLevel` só se ausente, preservando todo o resto do arquivo.
3. **Se já existe código** (brownfield): faça um scan primeiro — estrutura de pastas, stack, entrypoints (`main.py`/`app.py`), como roda, integrações — e proponha um rascunho do contexto e do propósito do projeto (nome + a que se destina) antes de perguntar.
4. **Entreviste o owner uma coisa por vez** (multiple choice quando der): objetivo em 1 frase · usuários · stack/runtime · como roda (CLI/serviço/porta/container/cron) · UI? (se sim, padrão FastAPI + Jinja) · integrações externas · banco (qual/como conecta) · restrições · critérios de sucesso.
5. **Scaffolding** — copie de `${CLAUDE_PLUGIN_ROOT}/templates/` para o projeto, criando as pastas se preciso, e preencha os `<...>` do `CLAUDE.md` com o que foi entrevistado:
   - `templates/CLAUDE.md`   → `CLAUDE.md` (raiz)
   - `templates/MEMORY.md`   → `memory/MEMORY.md`
   - `templates/INDEX.md`    → `docs/superpowers/INDEX.md`
   - `templates/AMBIENTE.md` → `docs/AMBIENTE.md` (ajuste os `<...>` do projeto; apague seções que não se aplicam, ex.: sem SQL Server)
   - `templates/SEGURANCA.md` → `docs/SEGURANCA.md` (baseline AppSec MSIG — vale pra todo projeto exposto; apague o checklist Azure se não for Azure)
   - `templates/ESTRUTURA.md` → `docs/ESTRUTURA.md` (estrutura de pastas em camadas — vale pra TODO projeto; adapte pelo tipo: sem UI, CLI/cron). **Todo arquivo novo nasce na pasta da sua camada — nunca achatado numa pasta única.**
   - `templates/settings.json` → `.claude/settings.json` (se ainda não existir do passo 2)
   - `templates/gitignore` → `.gitignore` (se não existir; se existir, garanta que `.env` está ignorado — adicione a linha se faltar). Protege segredo de subir.
   - **Se o projeto tem UI web:** `templates/FRONTEND.md` → `docs/FRONTEND.md` (design system MSIG — Nível 1 Jinja+Tailwind e Nível 2 React+Mantine) e `templates/assets/logo.png` → `static/img/logo.png` (logo MSIG). Se não tem UI, pule os dois. Para telas **densas** (grids/muitos campos), o front moderno (Nível 2) entra depois via `/mss-spec:frontend`.
6. NÃO crie specs/planos agora — features vêm depois com `/mss-spec:nova-feature`.

Ideia/insumo do owner: $ARGUMENTS
