# Segurança AppSec no kit mss-spec — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Assar segurança no kit — baseline `SEGURANCA.md`, regra secure-by-default no `CLAUDE.md`, e comando `/mss-spec:seguranca` que audita e corrige com aprovação.

**Architecture:** Tudo são arquivos de prompt/doc do plugin (markdown) + meta-testes pytest do próprio kit. O "teste" de cada entregável é um assert de fiação em `tests/test_smoke_kit.py` (o baseline anti-regressão do repo). Sem código de runtime — o kit é um conjunto de templates/comandos copiados pros projetos.

**Tech Stack:** Markdown (commands/templates), pytest (meta-testes do kit), git local (branch `plugin-v2`).

**Spec:** `docs/superpowers/specs/2026-07-16-seguranca-appsec-design.md`

---

## File Structure
- Create: `templates/SEGURANCA.md` — baseline AppSec MSIG (OWASP-adaptado + anti-padrões + modelo de auth)
- Modify: `templates/CLAUDE.md` — nova regra crítica "Segurança (secure-by-default)"
- Create: `commands/seguranca.md` — comando de auditoria (`disable-model-invocation`)
- Modify: `commands/kickoff.md` — copiar `SEGURANCA.md` no scaffolding
- Modify: `commands/nova-feature.md` — lembrete de revisar segurança em rota/entrada nova
- Modify: `tests/test_smoke_kit.py` — `test_seguranca_wiring`
- Modify: `docs/COMO-FUNCIONA.html`, `CHANGELOG.md` — documentação
- Create: `memory/project_seguranca_appsec_kit.md` + linha em `memory/MEMORY.md`

---

## Task 1: Meta-teste de fiação (TDD — vermelho primeiro)

**Files:**
- Modify: `tests/test_smoke_kit.py` (acrescentar função ao fim)

- [ ] **Step 1: Escrever o teste que falha**

Acrescente ao fim de `tests/test_smoke_kit.py`:

```python
def test_seguranca_wiring():
    """A capacidade de segurança está montada e referenciada."""
    assert (REPO / "templates" / "SEGURANCA.md").exists(), "falta templates/SEGURANCA.md"
    assert (REPO / "commands" / "seguranca.md").exists(), "falta commands/seguranca.md"
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "templates/SEGURANCA.md" in kickoff, "kickoff não copia SEGURANCA.md"
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/SEGURANCA.md" in claude, "CLAUDE.md não referencia docs/SEGURANCA.md"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_smoke_kit.py::test_seguranca_wiring -q`
Expected: FAIL — `AssertionError: falta templates/SEGURANCA.md`

- [ ] **Step 3: Commit do teste vermelho**

```bash
git add tests/test_smoke_kit.py
git commit -m "test(seguranca): fiação do baseline+comando+CLAUDE.md (vermelho)"
```

---

## Task 2: Criar `templates/SEGURANCA.md` (baseline)

**Files:**
- Create: `templates/SEGURANCA.md`

- [ ] **Step 1: Escrever o baseline**

Crie `templates/SEGURANCA.md` com um comentário-guia no topo (como `templates/AMBIENTE.md`: "MODELO — copie para `docs/SEGURANCA.md`") e ESTAS seções, cada uma no formato *risco → regra MSIG → como fica no stack → como verificar* (conteúdo vindo da spec §Entregáveis-1 e §Anti-padrões):

1. **Princípio (topo):** segurança ≠ obscuridade; frontend é público (assuma leitura total do bundle); Kerckhoffs (saber nome/endpoint não abre brecha); gate por ambiente (dev aberto / prod fechado).
2. **Autorização (A01):** default-deny em prod; permissão no **backend** por request; IDOR (o recurso é do usuário logado?).
3. **Autenticação & sessão (A07):** aponta para a seção "Modelo de auth — dois baldes" (abaixo).
4. **Injeção (A03):** SQL sempre parametrizado (exemplo ✅ parametrizado × ❌ f-string em pyodbc/psycopg); Pydantic valida payload; upload checado (tipo/tamanho/conteúdo); path traversal.
5. **XSS/saída (A03):** autoescape do Jinja ligado; React escapa (evitar `dangerouslySetInnerHTML`).
6. **Frontend & assets:** higiene de build prod (minify, **sem source-map**, sem `console.log` sensível); directory listing **off**; não servir `.env`/`.git`/backup; nada de segredo/URL interna no bundle.
7. **Headers & HTTPS (A05):** HSTS, CSP, X-Content-Type-Options, frame-ancestors, Referrer-Policy; HTTPS-only em prod (middleware FastAPI).
8. **Config/segredos (A02/A05):** `.env` fora do commit, Fernet, `SSL_VERIFY=true`, sem `DEBUG` em prod; Azure = Key Vault/App Settings.
9. **Erros & vazamento:** sem stack trace pro cliente em prod; logs sem PII/segredo (há `mask_password`).
10. **Dependências/CVE (A06):** `pip-audit` / `npm audit`; base image atualizada.
11. **CORS/rate limit (A04/A05):** CORS fechado (sem `*` com credencial); rate limit; teto de payload/upload.
12. **CSRF:** token em forms com cookie de sessão (quando houver login).
13. **Checklist Azure/infra (👤 humano):** HTTPS Only, TLS ≥1.2, auth no App Service/App Gateway, secrets em Key Vault, restrição de rede, managed identity pro banco.

Seção **"Modelo de auth — dois baldes"** (copie a tabela e as regras da spec §Modelo de auth): consumo próprio (login futuro, nunca o bearer de integração) × integração (Bearer `TOKEN_API` server-to-server); `AUTH_TOKEN_ATIVO`; `TOKEN_API` só server-side; HTTPS só em prod; `valida_token()` como dependency+seam; bloco `.env` de exemplo:

```
AUTH_TOKEN_ATIVO=          # false em dev/homolog (não exige token); true em prod (exige Bearer)
TOKEN_API=                 # segredo server-to-server; SÓ backend, nunca commit/browser; ideal 1 por sistema consumidor
```

Seção **"Anti-padrões (não faça)"** (spec §Anti-padrões): ofuscar/criptografar URL de asset; browser cunhar o próprio token; token único como login de usuário — com o "faça X" de cada.

- [ ] **Step 2: Rodar o teste de fiação (ainda falha em outro assert)**

Run: `python -m pytest tests/test_smoke_kit.py::test_seguranca_wiring -q`
Expected: FAIL — agora em `falta commands/seguranca.md` (o assert do SEGURANCA.md já passou)

- [ ] **Step 3: Commit**

```bash
git add templates/SEGURANCA.md
git commit -m "feat(seguranca): baseline SEGURANCA.md (OWASP-adaptado + anti-padroes + auth 2 baldes)"
```

---

## Task 3: Regra "Segurança" no `templates/CLAUDE.md`

**Files:**
- Modify: `templates/CLAUDE.md` (bloco "Regras críticas", antes do item `<regra específica do seu projeto…>`)

- [ ] **Step 1: Inserir a regra**

No `templates/CLAUDE.md`, localize a linha `5. <regra específica do seu projeto…>` e insira ANTES dela esta regra (renumerando: a nova é 5, a genérica vira 6):

```markdown
5. **Segurança (secure-by-default)** — o app fica exposto na nuvem; trate como alvo. **Prod**: default-deny + autorização no **backend** por request (o front nunca autoriza). SQL **sempre** parametrizado; entrada validada (Pydantic); **upload** checado (tipo/tamanho). O **browser nunca** vê segredo nem URL interna (assuma leitura total do bundle) — segredo só no `.env`/Key Vault em runtime. Sem stack trace/erro verboso pro cliente e sem PII/segredo em log. Headers de segurança + HTTPS-only (prod) + CORS fechado. **Obscuridade não é segurança** (não criptografar/ofuscar URL de asset). Deps sem CVE. Endpoints de **integração** (outro sistema chama) exigem `Authorization: Bearer` (`TOKEN_API` no `.env`, server-to-server), ligados por `AUTH_TOKEN_ATIVO` (false em dev, true em prod). **Detalhe e checklist em `docs/SEGURANCA.md`; auditoria com `/mss-spec:seguranca`.**
```

E troque a linha genérica seguinte para `6. <regra específica do seu projeto…>`.

- [ ] **Step 2: Rodar o teste de fiação**

Run: `python -m pytest tests/test_smoke_kit.py::test_seguranca_wiring -q`
Expected: FAIL — agora só em `kickoff não copia SEGURANCA.md` (o assert do CLAUDE.md já passou)

- [ ] **Step 3: Commit**

```bash
git add templates/CLAUDE.md
git commit -m "feat(seguranca): regra secure-by-default no CLAUDE.md template"
```

---

## Task 4: Criar `commands/seguranca.md`

**Files:**
- Create: `commands/seguranca.md`

- [ ] **Step 1: Escrever o comando**

Crie `commands/seguranca.md` com este conteúdo:

```markdown
---
description: Audita a segurança (AppSec) do projeto contra docs/SEGURANCA.md + OWASP e corrige com seu OK; grava relatório priorizado
argument-hint: ""
disable-model-invocation: true
---

Você é **engenheiro AppSec sênior**. Vai auditar a **postura de segurança do app inteiro** contra `docs/SEGURANCA.md` + OWASP Top 10, e corrigir **item a item com o OK do owner**. Complementa o `/security-review` nativo (que só olha o diff) — aqui é o app todo.

1. **Contexto:** leia `docs/SEGURANCA.md` e `docs/AMBIENTE.md` (exposição, stack). Se não houver `docs/SEGURANCA.md`, copie de `${CLAUDE_PLUGIN_ROOT}/templates/SEGURANCA.md` e avise.
2. **Auditoria (mapear):** varra rotas, SQL, templates/bundle do front, config, `requirements`/`package.json`, `Dockerfile`, `docker-compose*`, pipeline Azure. Rode `pip-audit` (se o proxy permitir; senão registre "manual") e procure padrões perigosos:
   - SQL por f-string/concat/`.format` (deve ser parametrizado);
   - `DEBUG=True`, stack trace exposto, `console.log` com dado sensível, **source-map em build de prod**;
   - segredo/token/URL interna hardcoded ou no bundle do front;
   - CORS `*` (com credencial), directory listing ligado, arquivo sensível servido;
   - endpoint **sem** exigência de auth/`Authorization`;
   - dependência com CVE conhecido.
3. **Relatório priorizado** em `docs/superpowers/SEGURANCA-AUDITORIA.md`: por achado → **severidade** (Crítico/Alto/Médio/Baixo) · **ref OWASP** · **arquivo:linha** · **risco concreto** · **fix proposto**. Ordene Crítico→Baixo.
4. **Corrigir, do mais crítico:** para cada item, **proponha o fix e espere o OK** antes de aplicar. Depois de cada correção, **rode o `pytest` do `PLANO-TESTE.md`** (não regredir) e cole a saída. **Não** valide tela dirigindo o browser ao vivo — cobertura de UI é teste determinístico.
5. **Fechamento:** **não** declare "seguro" (segurança é contínua). Carimbe data + commit (`git rev-parse --short HEAD`) no topo do relatório. Liste o que ficou pendente (ex.: itens do checklist Azure, que são 👤 humanos).

Regra de ouro: nada de **obscuridade** como "correção" (criptografar/ofuscar URL não é fix). Segredo só server-side (`.env`/Key Vault); o browser nunca cunha token nem carrega segredo.
```

- [ ] **Step 2: Rodar o teste de fiação**

Run: `python -m pytest tests/test_smoke_kit.py::test_seguranca_wiring -q`
Expected: FAIL — agora em `kickoff não copia SEGURANCA.md` (os asserts de `SEGURANCA.md`, `seguranca.md` e `CLAUDE.md` já passam). Resolve na Task 5. `test_commands_tem_frontmatter` já cobre o frontmatter do novo comando.

- [ ] **Step 3: Commit**

```bash
git add commands/seguranca.md
git commit -m "feat(seguranca): comando /mss-spec:seguranca (auditoria + fix com OK)"
```

---

## Task 5: Fiar o `kickoff` (entrega o baseline)

**Files:**
- Modify: `commands/kickoff.md` (lista de scaffolding do passo 5)

- [ ] **Step 1: Adicionar SEGURANCA.md ao scaffolding**

No `commands/kickoff.md`, no passo 5 (lista de cópias `templates/... → ...`), acrescente esta linha logo após a do `AMBIENTE.md`:

```markdown
   - `templates/SEGURANCA.md` → `docs/SEGURANCA.md` (baseline AppSec MSIG — vale pra todo projeto exposto; apague o checklist Azure se não for Azure)
```

- [ ] **Step 2: Rodar a suíte inteira**

Run: `python -m pytest tests/ -q`
Expected: PASS — todos os testes, incluindo `test_seguranca_wiring` (agora o kickoff cita `templates/SEGURANCA.md`, que existe) e `test_templates_citados_existem`.

- [ ] **Step 3: Commit**

```bash
git add commands/kickoff.md
git commit -m "feat(seguranca): kickoff entrega docs/SEGURANCA.md no scaffolding"
```

---

## Task 6: Fiar o `nova-feature` (lembrete de segurança)

**Files:**
- Modify: `commands/nova-feature.md` (passo 5, ao concluir)

- [ ] **Step 1: Adicionar o lembrete**

No `commands/nova-feature.md`, no passo 5 (o de conclusão, que já chama `requesting-code-review` e `/mss-spec:plano-teste`), acrescente ao fim da frase, antes do `finishing-a-development-branch`:

Texto a inserir (após "...só é atualizado se passar 100%)"):

```markdown
 → se a feature criou/alterou **rota ou endpoint** (ainda mais de **integração**, que outro sistema chama), revise contra `docs/SEGURANCA.md` (authz, entrada validada, `AUTH_TOKEN_ATIVO`/Bearer) — ou rode `/mss-spec:seguranca`
```

- [ ] **Step 2: Rodar a suíte inteira**

Run: `python -m pytest tests/ -q`
Expected: PASS — nada quebra (o `test_templates_citados_existem` não é afetado; `nova-feature` não cita novo template).

- [ ] **Step 3: Commit**

```bash
git add commands/nova-feature.md
git commit -m "feat(seguranca): nova-feature lembra de revisar seguranca em rota/endpoint novo"
```

---

## Task 7: Documentação + memória

**Files:**
- Modify: `docs/COMO-FUNCIONA.html` (tabela/lista de comandos)
- Modify: `CHANGELOG.md`
- Create: `memory/project_seguranca_appsec_kit.md`
- Modify: `memory/MEMORY.md`

- [ ] **Step 1: COMO-FUNCIONA.html**

Em `docs/COMO-FUNCIONA.html`, na lista/tabela de comandos, adicione uma linha para `/mss-spec:seguranca` descrevendo "audita AppSec (OWASP + baseline) e corrige com OK; complementa o /security-review nativo". Siga o formato das linhas vizinhas.

- [ ] **Step 2: CHANGELOG.md**

Adicione sob `## 0.7.0` uma linha:

```markdown
- feat: **segurança AppSec** — `templates/SEGURANCA.md` (baseline OWASP-adaptado + anti-padrões + auth 2 baldes), regra secure-by-default no `CLAUDE.md`, comando `/mss-spec:seguranca` (audita + corrige com OK), `kickoff` entrega o baseline. Princípios: obscuridade ≠ segurança; frontend é público; integração exige Bearer `TOKEN_API` (server-to-server) via `AUTH_TOKEN_ATIVO`; login de usuário fica como seam futuro
```

- [ ] **Step 3: Memória**

Crie `memory/project_seguranca_appsec_kit.md`:

```markdown
---
name: project-seguranca-appsec-kit
description: Capacidade de segurança do kit — baseline SEGURANCA.md, /mss-spec:seguranca, e os princípios decididos (obscuridade≠segurança, frontend público, auth 2 baldes)
metadata:
  type: project
---

O kit ganhou frente de segurança (spec `specs/2026-07-16-seguranca-appsec-design.md`): baseline
`templates/SEGURANCA.md` (OWASP-adaptado ao stack), regra secure-by-default no `CLAUDE.md`, e comando
`/mss-spec:seguranca` (audita o app inteiro, relatório priorizado, corrige com OK; complementa o
`/security-review` nativo que só vê o diff).

Princípios cravados com o owner (valem em decisões futuras): **obscuridade não é segurança** — não
criptografar/ofuscar URL de asset (o HTML entrega a URL; a chave viaja no código). **Frontend é
público** — nada de segredo/URL interna no bundle; higiene de build (minify, sem source-map, sem
console sensível). **Auth em dois baldes**: consumo próprio (front→backend do próprio app) = login de
usuário (seam futuro), nunca o bearer de integração; **integração** (outro sistema→backend) = Bearer
`TOKEN_API` server-to-server no `.env`, ligado por `AUTH_TOKEN_ATIVO` (false dev / true prod). HTTPS só
em prod (o token de prod nunca trafega em HTTP). Login de usuário no browser (JWT/sessão) ficou **fora
de escopo** agora. Ver [[feedback-validacao-ui-deterministica]].
```

E acrescente ao `memory/MEMORY.md`:

```markdown
- [Segurança AppSec no kit](project_seguranca_appsec_kit.md) — baseline SEGURANCA.md + /mss-spec:seguranca; princípios: obscuridade≠segurança, frontend público, auth 2 baldes (integração=Bearer TOKEN_API via AUTH_TOKEN_ATIVO), login de usuário = seam futuro
```

- [ ] **Step 4: Rodar a suíte inteira**

Run: `python -m pytest tests/ -q`
Expected: PASS — tudo verde.

- [ ] **Step 5: Commit**

```bash
git add docs/COMO-FUNCIONA.html CHANGELOG.md memory/project_seguranca_appsec_kit.md memory/MEMORY.md
git commit -m "docs(seguranca): COMO-FUNCIONA, CHANGELOG e memoria da capacidade de seguranca"
```

---

## Task 8: Verificação final

- [ ] **Step 1: Suíte inteira verde**

Run: `python -m pytest tests/ -q`
Expected: PASS (todos), incluindo `test_seguranca_wiring`.

- [ ] **Step 2: Conferência manual da fiação**

Confirme à vista: `templates/SEGURANCA.md` existe; `commands/seguranca.md` tem frontmatter com `disable-model-invocation: true`; `kickoff` cita `templates/SEGURANCA.md`; `templates/CLAUDE.md` tem a regra 5 de segurança apontando pra `docs/SEGURANCA.md`.

- [ ] **Step 3: (Opcional) atualizar o baseline do próprio kit**

Se quiser, rode `/mss-spec:plano-teste` (você, humano) pra regravar `docs/superpowers/PLANO-TESTE.md` com o novo `test_seguranca_wiring` no baseline. **Sem `git push`** — commits ficam locais até o owner pedir.

---

## Self-Review (feito na redação)
- **Cobertura da spec:** baseline (T2), regra CLAUDE.md (T3), comando (T4), integração kickoff/nova-feature (T5/T6), meta-teste (T1), docs/memória (T7). Modelo de auth 2 baldes + anti-padrões estão em T2/T3/T4. ✓
- **Placeholders:** nenhum "TBD/depois"; snippets pequenos têm texto exato; o baseble (doc grande) tem outline de seção obrigatória vindo da spec (não é placeholder — é content-spec). ✓
- **Consistência de nomes:** `AUTH_TOKEN_ATIVO`, `TOKEN_API`, `valida_token()`, `docs/SEGURANCA.md`, `test_seguranca_wiring` usados igual em todas as tasks. ✓
