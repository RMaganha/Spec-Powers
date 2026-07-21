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
5. **Scaffolding** — copie de `${CLAUDE_PLUGIN_ROOT}/templates/` para o projeto, criando as pastas se preciso, e preencha os `<...>` do `CLAUDE.md` com o que foi entrevistado. **Antes de copiar, ache os templates:** confirme que existem em `${CLAUDE_PLUGIN_ROOT}/templates/`; se a variável não resolveu, procure em `~/.claude/plugins/cache/*/mss-spec/*/templates/` ou `~/.claude/skills/mss-spec/templates/`. **Não achou em nenhum → PARE com erro claro** (o plugin não está resolvendo — registre/instale), nunca invente caminho nem copie de lugar quebrado. Arquivos a copiar:
   - `templates/CLAUDE.md`   → `CLAUDE.md` (raiz)
   - `templates/MEMORY.md`   → `memory/MEMORY.md`
   - `templates/DIARIO.md`   → `memory/DIARIO.md` (índice do diário de sessão) **+ crie a pasta `memory/sessions/`** (onde o `/mss-spec:memory capturar` grava os resumos datados por assunto — versionada; se precisar de um placeholder pro git rastrear a pasta vazia, um `.gitkeep`)
   - `templates/INDEX.md`    → `docs/superpowers/INDEX.md`
   - `templates/MAPA.md`     → `docs/superpowers/MAPA.md` (mapa de contexto anti-amnésia; preencha **Onde estamos** = "recém-constituído" e **Próximo passo** = "primeira feature via /mss-spec:nova-feature". **Conexões:** no brownfield, **proponha** as integrações que achar no código — routers/endpoints que outro sistema chama, clients HTTP p/ outros serviços, filas, banco compartilhado — e confirme comigo; **nunca invente**. Sem integração conhecida, deixe "nenhuma conhecida ainda".)
   - `templates/AMBIENTE.md` → `docs/AMBIENTE.md` (ajuste os `<...>` do projeto; apague seções que não se aplicam, ex.: sem SQL Server)
   - `templates/SEGURANCA.md` → `docs/SEGURANCA.md` (baseline AppSec MSIG — vale pra todo projeto exposto; apague o checklist Azure se não for Azure)
   - `templates/ESTRUTURA.md` → `docs/ESTRUTURA.md` (estrutura de pastas em camadas — vale pra TODO projeto; adapte pelo tipo: sem UI, CLI/cron). **Todo arquivo novo nasce na pasta da sua camada — nunca achatado numa pasta única.**
   - `templates/DECISOES.md` → `docs/decisoes.md` (log de decisões transversais — nasce skeleton; o `nova-feature` acrescenta 1 linha quando houver decisão de arquitetura/lib/padrão)
   - `templates/logging.py` → `config/logging.py` (padrão de log MSIG — infra barata: `setup_logging()` manda pro **stdout** sempre, o Azure captura em prod, + arquivo rotativo `logs/` só em dev). Chame `setup_logging()` uma vez no `main.py`. Garanta `LOG_ATIVO`/`LOG_LEVEL`/`LOG_ICONES` no `.env.example` e `/logs/` no `.gitignore`. A **instrumentação por-arquivo** (quais módulos ganham `logger`) NÃO é feita agora — é opt-in, via `/mss-spec:log` ou pelo protocolo de geração de arquivos (abaixo).
   - `templates/settings.json` → `.claude/settings.json` (se ainda não existir do passo 2)
   - `templates/gitignore` → `.gitignore` (se não existir; se existir, garanta que `.env` está ignorado — adicione a linha se faltar). Protege segredo de subir.
   - **Se o projeto tem UI web:** `templates/FRONTEND.md` → `docs/FRONTEND.md` (design system MSIG — Nível 1 Jinja+Tailwind e Nível 2 React+Mantine) e `templates/assets/logo.png` → `static/img/logo.png` (logo MSIG). Se não tem UI, pule os dois. Para telas **densas** (grids/muitos campos), o front moderno (Nível 2) entra depois via `/mss-spec:frontend`.
6. **Registre o backlog (não as specs).** NÃO crie specs/planos agora — features vêm depois com `/mss-spec:nova-feature`. **Mas** as necessidades/ideias levantadas na conversa não podem se perder: grave cada uma como 1 linha **`aberta`** no `docs/superpowers/INDEX.md` (só a linha — `- <assunto> — <objetivo em 1 frase> — aberta`, sem spec/link ainda). Assim o backlog do projeto fica versionado; o `nova-feature` depois pega uma e cria a spec. (Isso é backlog do projeto — não confundir com o `to-dolist`, que é recado pessoal fora do git.)

**Rollback: o git é o rollback.** Não há comando de "desinstalar o kickoff" — não precisa. Como o kickoff só cria/copia arquivos versionáveis, para desfazer basta descartar o que ele gerou: `git restore`/`git clean` nos arquivos novos, ou, se você constituiu o projeto numa branch dedicada, descartar a branch. Sem comando dedicado de propósito (YAGNI).

Ideia/insumo do owner: $ARGUMENTS
