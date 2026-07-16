# Design — Segurança AppSec no kit mss-spec

**Data:** 2026-07-16 · **Status:** aprovado (brainstorming) · **Branch:** plugin-v2

## Objetivo
Assar segurança de aplicação no kit `mss-spec`, para que projetos MSIG expostos na nuvem
(Azure Web App) nasçam seguros e possam ser auditados sob demanda. Duas frentes:
1. **Preventiva** — regra secure-by-default no `CLAUDE.md` + baseline `docs/SEGURANCA.md`, valendo desde o `kickoff`.
2. **Corretiva** — comando `/mss-spec:seguranca` que mapeia vulnerabilidades e corrige com aprovação.

## Modelo de ameaça
- Alvo: apps FastAPI/Jinja (Nível 1) e React+TS (Nível 2), banco SQL Server/Postgres, deploy Azure Web App.
- Exposição varia por projeto; o pior caso a cobrir é **internet pública + login** (atacante anônimo + usuário autenticado mal-intencionado).
- Realidade de dev: **local e homologação sem HTTPS e sem login** — não engessar isso.

## Princípios (o "porquê" que guia tudo)
- **Segurança ≠ obscuridade.** Esconder/criptografar URL de asset, renomear caminho, ofuscar JS: o
  browser recebe a URL de bandeja (Ctrl+U / DevTools) e a chave de descriptografia viaja junto do
  código. Não protege nem contra júnior. Vira anti-padrão **documentado** (ver abaixo).
- **Frontend é público.** Assuma que o atacante lê 100% do bundle. A segurança tem que sobreviver a
  isso: nada de segredo, URL interna ou lógica-de-confiança no browser; o servidor sempre re-decide.
- **Kerckhoffs aplicado:** conhecer nome de função/endpoint não pode abrir brecha — a defesa está no
  servidor validando, não no atacante não saber que o endpoint existe.
- **Gate por ambiente** (mesmo espírito do `CONEXAO_SQL`): dev aberto, prod fechado — via flag, sem engessar.

## Entregáveis

### 1. `templates/SEGURANCA.md` — baseline AppSec MSIG
Checklist OWASP Top 10 (2021) traduzido ao stack. Cada item: *risco → regra MSIG → como fica no seu
código → como verificar*. Áreas:
1. **Autorização (A01)** — default-deny em prod; permissão checada **no backend** por request; IDOR.
2. **Autenticação & sessão (A07)** — modelo de auth em dois baldes (ver seção Auth).
3. **Injeção (A03)** — SQL **sempre** parametrizado (nunca f-string/concat em pyodbc/psycopg); Pydantic valida payload; **upload** checado (tipo/tamanho/conteúdo); path traversal.
4. **XSS/saída (A03)** — autoescape do Jinja ligado; React escapa (cuidado `dangerouslySetInnerHTML`).
5. **Frontend & assets** — assuma leitura total; higiene de build prod (minify, **sem source-map**, sem `console.log` sensível); directory listing **desligado**; não servir `.env`/`.git`/backup; nada de segredo/URL interna no bundle.
6. **Headers & HTTPS (A05)** — HSTS, CSP, X-Content-Type-Options, frame-ancestors, Referrer-Policy; HTTPS-only **em prod** (middleware FastAPI).
7. **Config/segredos (A02/A05)** — reforça o existente (`.env` fora do commit, Fernet, `SSL_VERIFY=true`, sem `DEBUG` em prod); em Azure = Key Vault/App Settings.
8. **Erros & vazamento** — sem stack trace pro cliente em prod; logs sem PII/segredo (já há `mask_password`).
9. **Dependências/CVE (A06)** — `pip-audit` / `npm audit`; base image atualizada.
10. **CORS/rate limit (A04/A05)** — CORS fechado (sem `*` com credencial); rate limit em rotas caras; teto de payload/upload.
11. **CSRF** — token em forms com cookie de sessão (quando houver login).
12. **Checklist Azure/infra (👤 humano)** — HTTPS Only, TLS ≥1.2, auth no App Service/App Gateway, secrets em Key Vault, restrição de rede, managed identity pro banco.

Inclui a seção **Anti-padrões** (ver abaixo).

### 2. Regra no `templates/CLAUDE.md`
**Uma** regra crítica nova "Segurança (secure-by-default)", enxuta (~6 sub-pontos) + ponteiro pro
`docs/SEGURANCA.md` e pro `/mss-spec:seguranca`: default-deny em prod + authz no backend · SQL
parametrizado + entrada validada + upload checado · browser nunca vê segredo/URL interna · sem erro
verboso/PII em log · headers+HTTPS(prod)+CORS fechado · **obscuridade não é segurança** + deps sem CVE.

### 3. Comando `/mss-spec:seguranca`
- `disable-model-invocation: true` (você dispara, como o `plano-teste`); persona **AppSec sênior**.
- Fluxo:
  1. Lê exposição/stack (`AMBIENTE.md`).
  2. **Audita o app inteiro** contra `SEGURANCA.md` + OWASP: varre rotas, SQL, templates, config,
     bundle do front, `requirements`, Dockerfile, compose, pipeline Azure; roda `pip-audit` (se o
     proxy permitir) e grep de padrões perigosos (f-string em SQL, `DEBUG=True`,
     `dangerouslySetInnerHTML`, CORS `*`, segredo hardcoded, source-map em prod, endpoint sem authz).
  3. Grava relatório priorizado em **HTML** (`docs/superpowers/SEGURANCA-AUDITORIA.html`), no **estilo
     editorial MSIG** (copia `templates/doc/template.html`, o mesmo do `/mss-spec:documentacao`):
     hero com resumo/contagem por severidade + carimbo data/commit; uma seção por severidade ordenada
     **Crítico→Baixo**; cada achado num `callout` colorido pela gravidade (crit/danger/warn/info) com
     ref OWASP · arquivo:linha · risco concreto · fix proposto · status. Leitura fácil, do crítico ao fácil.
  4. **Item a item, do mais crítico:** propõe → aplica **com seu OK** → re-verifica rodando o
     `plano-teste` base (não regredir). UI continua **determinística** (sem clicar ao vivo).
  5. Não declara "seguro" (segurança é contínua); carimba data/commit.
- **Complementaridade:** o `/security-review` nativo cobre o *diff*; este cobre a *postura do app inteiro*.

### 4. Integração
`kickoff` copia `SEGURANCA.md` e cita a regra no `CLAUDE.md`; `nova-feature` lembra de revisar o
baseline ao criar rota/entrada nova; atualiza `COMO-FUNCIONA.html`, `CHANGELOG`, memória.

### 5. Meta-testes do kit
Padrão já existente: `SEGURANCA.md` existe e é referenciado; o comando tem frontmatter; `kickoff` cita `SEGURANCA.md`.

## Modelo de auth — dois baldes
| Balde | Quem chama | Proteção | Hoje (local) |
|---|---|---|---|
| **Consumo próprio** | o front do app → o backend do próprio app | auth de **usuário** (login) — **nunca** o bearer de integração (viraria público no browser) | **aberto** |
| **Integração** | **outro sistema** (servidor) → seu backend | **Bearer `TOKEN_API`** (server-to-server) | token off/descartável |

- **`AUTH_TOKEN_ATIVO`** (`.env`): `false` = não exige token (local/homolog); `true` = exige (prod).
- **`TOKEN_API`** (`.env`, server-side): segredo compartilhado do balde Integração; **nunca** no
  commit nem no browser; ideal **um por sistema consumidor** (revoga/audita cada um).
- **HTTPS**: regra de **produção**; local/homolog pode HTTP; o **token de prod nunca trafega em HTTP**
  (em homolog, use valor diferente/descartável se ligar o token).
- **`valida_token()`**: dependency do FastAPI que roda **antes** das rotas de integração; confere o
  Bearer contra o `.env`; sem token válido → **401** (sem explicar o motivo). É o *seam* onde, no
  futuro, entra também a validação de token de usuário — as rotas não mudam.
- **Fora de escopo agora:** login de usuário no browser (JWT/sessão, idle/teto absoluto, rotação).
  Fica anotado como *seam* futuro; em prod, endpoints de consumo próprio ficarão atrás desse login
  (lembrete: "é meu próprio app que chama" **não** é proteção — o atacante replica a chamada por fora do front).

## Anti-padrões documentados (no `SEGURANCA.md`)
- **Ofuscar/criptografar URL de asset** (`/static/...` → `/x/y/z.css`): zero segurança (o HTML entrega
  a URL; o arquivo não tem segredo). Faça: directory listing off, não servir arquivo sensível, sem source-map em prod.
- **Browser cunhar o próprio token** (segredo/algoritmo no JS): público → o atacante gera tokens
  válidos igual. Tokens só se validam contra chave **server-side**.
- **Token único como login de usuário**: um `TOKEN_API` compartilhado só serve **server-to-server**;
  no browser vira público e não identifica/revoga ninguém.

## Verificação
- Meta-testes do kit passam (`python -m pytest -q`).
- Auto-auditoria: rodar `/mss-spec:seguranca` num projeto-canário (MSS-SSC) e conferir que o relatório
  pega os achados esperados (ex.: endpoint sem authz, CORS aberto) sem falsos "tudo seguro".

## YAGNI (deixado de fora de propósito)
Login de usuário/JWT agora · criptografia de token caseira · ofuscação de URL · WAF/observabilidade
avançada (fica no checklist Azure como item humano).
