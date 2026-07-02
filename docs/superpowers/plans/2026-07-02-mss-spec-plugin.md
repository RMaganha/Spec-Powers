# mss-spec Plugin — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converter o kit Spec-Powers numa estrutura de plugin do Claude Code (`mss-spec`), instalável via marketplace local, com 5 comandos que fazem scaffolding em vez de cópia manual.

**Architecture:** Reestruturar a pasta `Spec-Powers` no layout de plugin (`.claude-plugin/`, `commands/`, `skills/`, `templates/`, `docs/`). Comandos leem os templates embutidos e escrevem no projeto-alvo. A disciplina (brainstorming, TDD, verificação) continua vindo do superpowers como dependência.

**Tech Stack:** Claude Code plugin (v2.1.140+), Markdown com frontmatter YAML, JSON (manifesto + marketplace). Sem código executável — a "implementação" é a estrutura de arquivos do plugin.

**Notas de execução:**
- Base do repo: `C:\Ronaldo\_Mitsui\Python\Spec-Powers` (será o repo do plugin).
- **Git é opcional** — se preferir adiar versionamento, pule os passos `git`.
- Ambiente Windows/PowerShell. Validação de JSON via `python -m json.tool`.
- Muitos arquivos já existem no kit; tarefas de "mover + editar" não repetem conteúdo grande já escrito — só mostram o move e os edits pontuais. Arquivos novos trazem conteúdo completo.
- **Assunção a verificar (Task 12):** comandos referenciam templates via `${CLAUDE_PLUGIN_ROOT}/templates/...`. Se essa variável não resolver na sua versão, o fallback é embutir o conteúdo do template dentro do próprio comando.

---

### Task 1: Esqueleto do repo do plugin

**Files:**
- Create dirs: `.claude-plugin/`, `commands/`, `skills/precedentes-msig/`, `templates/`, `docs/superpowers/`
- Move: manuais da raiz para `docs/`

- [ ] **Step 1: Inicializar git (opcional)**

Run:
```bash
cd "C:/Ronaldo/_Mitsui/Python/Spec-Powers" && git init && git add -A && git commit -m "chore: snapshot do kit antes de virar plugin"
```
Expected: repo criado, commit inicial com os arquivos atuais.

- [ ] **Step 2: Criar as pastas do plugin**

Run:
```bash
cd "C:/Ronaldo/_Mitsui/Python/Spec-Powers" && mkdir -p .claude-plugin commands skills/precedentes-msig templates docs
```

- [ ] **Step 3: Mover os manuais para docs/**

Run:
```bash
cd "C:/Ronaldo/_Mitsui/Python/Spec-Powers" && git mv LEIA-ME.md ROTEIRO-SPEC-DRIVEN.md referencia-spec-driven.md docs/ 2>/dev/null || mv LEIA-ME.md ROTEIRO-SPEC-DRIVEN.md referencia-spec-driven.md docs/
```
Expected: os 3 manuais agora em `docs/`. (O design doc já está em `docs/superpowers/specs/`.)

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: cria layout de plugin e move manuais para docs/"
```

---

### Task 2: Manifesto `plugin.json`

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Escrever o manifesto**

```json
{
  "name": "mss-spec",
  "displayName": "MSS Spec-Driven",
  "version": "0.1.0",
  "description": "Fluxo Spec-Driven MSIG sobre superpowers: kickoff, nova-feature, ambiente, banco e catalogo de precedentes.",
  "author": {
    "name": "Ronaldo Maganha",
    "email": "rmaganha@msig.com.br"
  }
}
```

- [ ] **Step 2: Validar o JSON**

Run: `python -m json.tool ".claude-plugin/plugin.json"`
Expected: imprime o JSON formatado, sem erro de parse.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json && git commit -m "feat: manifesto do plugin mss-spec"
```

---

### Task 3: Marketplace local `marketplace.json`

**Files:**
- Create: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Escrever o marketplace**

```json
{
  "name": "mss-local",
  "version": "0.1.0",
  "plugins": [
    {
      "name": "mss-spec",
      "description": "Fluxo Spec-Driven MSIG sobre superpowers.",
      "source": {
        "source": "relative-path",
        "path": "."
      }
    }
  ]
}
```

- [ ] **Step 2: Validar o JSON**

Run: `python -m json.tool ".claude-plugin/marketplace.json"`
Expected: JSON formatado, sem erro.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json && git commit -m "feat: marketplace local mss-local"
```

---

### Task 4: Templates embutidos

**Files:**
- Move: `modelo/CLAUDE.md.modelo` → `templates/CLAUDE.md`
- Move: `modelo/settings.json.modelo` → `templates/settings.json`
- Move: `modelo/MEMORY.md.modelo` → `templates/MEMORY.md`
- Move: `modelo/AMBIENTE.md.modelo` → `templates/AMBIENTE.md`
- Create: `templates/INDEX.md`

- [ ] **Step 1: Mover os 4 templates existentes**

Run:
```bash
cd "C:/Ronaldo/_Mitsui/Python/Spec-Powers"
git mv modelo/CLAUDE.md.modelo templates/CLAUDE.md 2>/dev/null || mv modelo/CLAUDE.md.modelo templates/CLAUDE.md
git mv modelo/settings.json.modelo templates/settings.json 2>/dev/null || mv modelo/settings.json.modelo templates/settings.json
git mv modelo/MEMORY.md.modelo templates/MEMORY.md 2>/dev/null || mv modelo/MEMORY.md.modelo templates/MEMORY.md
git mv modelo/AMBIENTE.md.modelo templates/AMBIENTE.md 2>/dev/null || mv modelo/AMBIENTE.md.modelo templates/AMBIENTE.md
```

- [ ] **Step 2: Ajustar `templates/CLAUDE.md`** — trocar a linha do "Mapa de arquivos" que cita `docs/superpowers/INDEX.md` para incluir também os dois índices no protocolo de leitura. Confirmar que a seção "Modo de trabalho" instrui ler `memory/MEMORY.md` **e** `docs/superpowers/INDEX.md` no início. Se faltar o INDEX, adicionar à bullet de memória:

```
- **Índices do projeto**: no início, leia `memory/MEMORY.md` (aprendizados) e `docs/superpowers/INDEX.md` (tarefas). Ambos são só índices (1 linha por item). Abra o arquivo individual só quando o índice apontar relevância; nunca leia a pasta inteira. Fallback: Grep/Glob sobre `docs/`.
```

- [ ] **Step 3: Criar `templates/INDEX.md`**

```markdown
<!-- Índice de TAREFAS do projeto (specs/planos em docs/superpowers/).
     Mantido pelo comando /mss-spec:nova-feature: 1 linha por tarefa.
     Formato: - [<tarefa>](specs/<arquivo>-design.md) — <objetivo em 1 frase> — <status: aberta|fechada> -->

# Índice de tarefas
```

- [ ] **Step 4: Validar `templates/settings.json`**

Run: `python -m json.tool "templates/settings.json"`
Expected: JSON válido; deve conter `enabledPlugins` com superpowers e `effortLevel`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: templates embutidos (CLAUDE, settings, MEMORY, AMBIENTE, INDEX)"
```

---

### Task 5: Skill `precedentes-msig` para dentro do plugin

**Files:**
- Create: `skills/precedentes-msig/SKILL.md` (conteúdo vindo de `~/.claude/skills/precedentes-msig/SKILL.md`)
- Delete depois: `~/.claude/skills/precedentes-msig/` (evitar skill duplicada)

- [ ] **Step 1: Copiar o SKILL.md para o plugin**

Run:
```bash
cp "C:/Users/rmaganha/.claude/skills/precedentes-msig/SKILL.md" "C:/Ronaldo/_Mitsui/Python/Spec-Powers/skills/precedentes-msig/SKILL.md"
```

- [ ] **Step 2: Verificar frontmatter**

Confirmar que o arquivo tem frontmatter com `name: precedentes-msig` e `description:` (não alterar conteúdo; só validar que veio inteiro).

- [ ] **Step 3: Commit**

```bash
git add skills/precedentes-msig/SKILL.md && git commit -m "feat: move skill precedentes-msig para dentro do plugin"
```

- [ ] **Step 4: Remover a skill pessoal antiga (após validar no Task 12)**

> ⚠️ NÃO executar agora — só depois que o Task 12 confirmar que a skill do plugin carrega. Então:
```bash
rm -rf "C:/Users/rmaganha/.claude/skills/precedentes-msig"
```

---

### Task 6: Comando `kickoff`

**Files:**
- Create: `commands/kickoff.md` (evolução de `modelo/comando-kickoff.md`, agora com scaffolding + scan brownfield + dependência)

- [ ] **Step 1: Escrever o comando**

```markdown
---
description: Constitui o projeto (green/brownfield) — entrevista, gera CLAUDE.md e faz scaffolding de memória, índice de tarefas e AMBIENTE
argument-hint: "[ideia em 1 linha, ou aponte para um repo existente]"
disable-model-invocation: true
---

Você vai **constituir este projeto**. NÃO escreva código de aplicação nesta etapa.

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
6. NÃO crie specs/planos agora — features vêm depois com `/mss-spec:nova-feature`.

Ideia/insumo do owner: $ARGUMENTS
```

- [ ] **Step 2: Verificar frontmatter e paths**

Confirmar que o arquivo tem frontmatter válido e que todos os caminhos de template batem com os criados no Task 4.

- [ ] **Step 3: Commit**

```bash
git add commands/kickoff.md && git commit -m "feat: comando kickoff com scaffolding e scan brownfield"
```

---

### Task 7: Comando `nova-feature`

**Files:**
- Create: `commands/nova-feature.md` (evolução de `modelo/comando-nova-feature.md`, agora mantendo o INDEX.md)

- [ ] **Step 1: Escrever o comando**

```markdown
---
description: Abre uma feature (spec → tasks) e mantém o índice de tarefas; não mexe em git (branch é explícita)
argument-hint: "[nome-da-feature]"
disable-model-invocation: true
---

Feature: **$ARGUMENTS**

1. Invoque **superpowers:brainstorming** para esta feature: objetivo (1 frase), **Critérios de Aceite testáveis** (formato "DADO… QUANDO… ENTÃO…") e fora de escopo. **Espere o OK do owner** antes de qualquer código.
2. Invoque **superpowers:writing-plans**: quebre em tasks pequenas e ordenadas, cada uma cobrindo ≥1 Critério de Aceite por teste.
3. **Atualize o índice de tarefas**: acrescente 1 linha em `docs/superpowers/INDEX.md`:
   `- [<nome-da-feature>](specs/<arquivo>-design.md) — <objetivo em 1 frase> — aberta`
4. Execute **uma task por vez** (superpowers:executing-plans / subagent-driven-development): TDD (teste do AC → vermelho → código → verde) e **rode e cole a saída** (verification-before-completion) antes da próxima.
5. Ao concluir: `requesting-code-review` → `finishing-a-development-branch`. Mude o status da linha no `INDEX.md` para `fechada`. Se surgiu regra durável, 1 linha em "Regras críticas" do `CLAUDE.md`; se surgiu aprendizado durável, grave em `memory/` (arquivo + linha no `MEMORY.md`).

**Git/branch:** este comando NÃO cria branch nem worktree. Se quiser isolamento, peça explicitamente (`superpowers:using-git-worktrees`) antes ou durante.

Mudanças que **não** são feature (não precisam deste comando): **bugfix** → teste que reproduz o bug é a spec → corrige → verifica; **refactor** → gate é "testes verdes"; **chore/docs** → sem spec.
```

- [ ] **Step 2: Commit**

```bash
git add commands/nova-feature.md && git commit -m "feat: comando nova-feature com manutencao do INDEX"
```

---

### Task 8: Comando `ambiente`

**Files:**
- Create: `commands/ambiente.md`

- [ ] **Step 1: Escrever o comando**

```markdown
---
description: Gera os arquivos de infra no padrão MSIG (docker-compose com rede mitiai_network; override de proxy do escritório se container)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar os **arquivos de infra** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` como referência dos valores fixos. Mostre o que vai gerar e **confirme com o owner antes de gravar**.

1. Pergunte: **este projeto será containerizado?** Se não, só oriente o setup de proxy no host (opção 1 do `docs/AMBIENTE.md`: `pip config`, `setx HTTP/HTTPS_PROXY`, Docker Desktop) e pare.
2. Se sim, gere `docker-compose.yml` com o serviço do projeto na rede externa compartilhada:
   ```yaml
   services:
     <servico>:
       build: .
       container_name: <nome>
       env_file: .env
       restart: unless-stopped
       networks:
         - mitiai_network
   networks:
     mitiai_network:
       name: mitiai_network
       external: true
   ```
3. Pergunte: **vai rodar no escritório (atrás do proxy corporativo)?** Se sim, gere `docker-compose.office.yml` como override, injetando `HTTP_PROXY`/`HTTPS_PROXY=http://10.170.200.120:8080` e `NO_PROXY` (localhost,127.0.0.1,::1,host.docker.internal,postgres-db,.ms-seg.com.br,.msig.com.br,.local) via `environment:`.
4. **Certificado corporativo está fora de escopo** — não injete `corp-ca.pem`. Se o container precisar de HTTPS externo atrás do proxy, avise que isso é tratado manualmente, fora do plugin.
5. Lembre o owner de criar a rede uma vez, se ainda não existir: `docker network create mitiai_network`.
```

- [ ] **Step 2: Commit**

```bash
git add commands/ambiente.md && git commit -m "feat: comando ambiente (docker-compose + override de proxy, sem cert)"
```

---

### Task 9: Comando `banco`

**Files:**
- Create: `commands/banco.md`

- [ ] **Step 1: Escrever o comando**

```markdown
---
description: Gera o boilerplate de conexão a banco no padrão MSIG (SQL Server via pyodbc, ou Postgres)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar o **módulo de conexão** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` para hosts e convenções. Mostre o código e **confirme antes de gravar**.

1. Pergunte: **SQL Server ou Postgres?**
2. **Postgres**: gere um `get_connection` usando `psycopg2`, lendo `PG_CONN_STR` do ambiente; host conforme `docs/AMBIENTE.md` (`postgres-db` na rede Docker; `mitiai-poc.msig.com.br` fora; `localhost`/`host.docker.internal` em dev). Acrescente `PG_CONN_STR=postgresql://<usuario>:<senha>@<host>:5432/miti_ai_<projeto>` no `.env.example`.
3. **SQL Server**: pergunte **modo simples ou Fernet?**
   - Simples: `get_connection_<banco>()` com `pyodbc`, lendo `SQL_CONNECTION_STRING_<BANCO>` do ambiente; se for Streamlit e reutilizar conexão, `@st.cache_resource`. `.env.example` recebe a connection string com `Driver={ODBC Driver 17 for SQL Server};Server=MSSQLD0;Database=<banco>;UID=;PWD=;TrustServerCertificate=yes;`.
   - Fernet: `get_connection()` que descriptografa `ENCRYPTED_CONN` com `ENCRYPTION_KEY` (lib `cryptography`) e conecta via `pyodbc` (`autocommit=True`). `.env.example` recebe `ENCRYPTION_KEY=` e `ENCRYPTED_CONN=`.
4. Se container precisar resolver `MSSQLD0`, lembre de adicionar `extra_hosts: ["MSSQLD0:10.170.210.36"]` no `docker-compose.yml`.
5. Nunca gere `.env` real nem valores de credencial — só `.env.example` com placeholders.
```

- [ ] **Step 2: Commit**

```bash
git add commands/banco.md && git commit -m "feat: comando banco (getconnection SQL Server/Postgres)"
```

---

### Task 10: Comando `precedentes`

**Files:**
- Create: `commands/precedentes.md`

- [ ] **Step 1: Escrever o comando**

```markdown
---
description: Consulta o catálogo de precedentes entre projetos MSIG (o que já foi resolvido em outro projeto)
argument-hint: "[assunto: ex. RAG, extração de PDF, conexão SQL]"
disable-model-invocation: true
---

Consulte o catálogo de precedentes em `${CLAUDE_PLUGIN_ROOT}/skills/precedentes-msig/SKILL.md` e responda: existe um projeto MSIG que já resolveu **$ARGUMENTS**? Se sim, aponte o projeto, o caminho e a abordagem, e lembre: **abra o código real de lá antes de replicar** — o catálogo é só um índice, o código pode ter evoluído.

Se nada no catálogo casar, diga isso claramente em vez de inventar um precedente.
```

- [ ] **Step 2: Commit**

```bash
git add commands/precedentes.md && git commit -m "feat: comando precedentes (consulta explicita ao catalogo)"
```

---

### Task 11: Limpeza dos arquivos obsoletos

**Files:**
- Delete: `rename.txt`, `PROMPT-MAPEAR-AMBIENTE.md`, `PROMPT-CONHECER-PROJETO.md`, pasta `modelo/` (já esvaziada)

- [ ] **Step 1: Remover obsoletos**

Run:
```bash
cd "C:/Ronaldo/_Mitsui/Python/Spec-Powers"
git rm rename.txt PROMPT-MAPEAR-AMBIENTE.md PROMPT-CONHECER-PROJETO.md 2>/dev/null || rm -f rename.txt PROMPT-MAPEAR-AMBIENTE.md PROMPT-CONHECER-PROJETO.md
rmdir modelo 2>/dev/null || true
```
Expected: arquivos removidos; `modelo/` some se estiver vazia.

- [ ] **Step 2: Atualizar `docs/LEIA-ME.md`** — reescrever a seção "Como usar" para o fluxo de plugin (instalar via marketplace local + rodar `/mss-spec:kickoff`), remover a tabela de cópia manual e as menções a `rename.txt`/prompts avulsos. Documentar os 5 comandos e a regra de branch explícita (Task 4 §7 do design).

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "chore: remove arquivos obsoletos e atualiza LEIA-ME para fluxo de plugin"
```

---

### Task 12: Instalação e verificação (passos manuais do owner)

> Estes passos usam comandos interativos `/plugin` que só rodam numa sessão real do Claude Code — não headless. Execute você mesmo e reporte o resultado.

- [ ] **Step 1: Registrar o marketplace local**

Numa sessão do Claude Code:
```
/plugin marketplace add C:/Ronaldo/_Mitsui/Python/Spec-Powers
```
Expected: marketplace `mss-local` reconhecido.

- [ ] **Step 2: Instalar o plugin (escopo user)**

```
/plugin install mss-spec@mss-local
```
Expected: `mss-spec` habilitado; escolher escopo `user`.

- [ ] **Step 3: Verificar comandos e skill**

Em sessão nova: `/help` (ou digitar `/mss-spec:`) deve listar `kickoff`, `nova-feature`, `ambiente`, `banco`, `precedentes`. A skill `precedentes-msig` deve aparecer na lista de skills disponíveis.

- [ ] **Step 4: Teste de scaffolding num projeto-rascunho**

Numa pasta vazia de teste, rodar `/mss-spec:kickoff "projeto de teste"` e confirmar que gera `CLAUDE.md`, `.claude/settings.json`, `memory/MEMORY.md`, `docs/superpowers/INDEX.md`, `docs/AMBIENTE.md`.
> Se `${CLAUDE_PLUGIN_ROOT}` não resolver os templates, aplicar o fallback: embutir o conteúdo dos templates dentro dos comandos.

- [ ] **Step 5: Teste dos demais comandos**

`/mss-spec:nova-feature teste` (confirmar spec+plan+linha no INDEX), `/mss-spec:banco`, `/mss-spec:ambiente`, `/mss-spec:precedentes RAG`.

- [ ] **Step 6: Limpar a skill pessoal duplicada**

Confirmado que a skill do plugin carrega, executar o Step 4 do Task 5 (remover `~/.claude/skills/precedentes-msig`).

- [ ] **Step 7: Commit final**

```bash
git add -A && git commit -m "chore: mss-spec validado e instalado"
```

---

## Self-Review (feita)

- **Cobertura do spec:** §3 estrutura → Tasks 1-5,11; §4 comandos → Tasks 6-10; §5 memória/índices → Tasks 4,6,7; §6 proxy → Task 8; §7 branch → Task 7; §8 dependência → Task 6; §9 o que sai → Task 11; §10 verificação → Task 12; §11 dívidas → registradas no design (precedentes caminhos absolutos permanece, sem task). Coberto.
- **Placeholders:** os `<...>` remanescentes são intencionais (valores por-projeto que o comando preenche em runtime), não lacunas do plano.
- **Consistência de nomes:** `mss-spec` (plugin), `mss-local` (marketplace), `mitiai_network`, `docs/superpowers/INDEX.md`, `${CLAUDE_PLUGIN_ROOT}/templates/` — usados igual em todas as tasks.
