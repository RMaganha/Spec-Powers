# Changelog do mss-spec

1 linha por mudança relevante; bump de versão no `plugin.json` a cada release.

## 0.7.0 — 2026-07-13 (front moderno: React + TS + Mantine) [branch plugin-v2]
- feat: **segurança AppSec** — `templates/SEGURANCA.md` (baseline OWASP-adaptado + anti-padrões + auth 2 baldes), regra secure-by-default no `CLAUDE.md`, comando `/mss-spec:seguranca` (audita + corrige com OK, **relatório HTML no estilo editorial ordenado crítico→fácil**), `kickoff` entrega o baseline. Princípios: obscuridade ≠ segurança; frontend é público; integração exige Bearer `TOKEN_API` (server-to-server) via `AUTH_TOKEN_ATIVO`; login de usuário fica como seam futuro
- fix: **plano-teste — validação de UI só determinística; agente nunca clica ao vivo**. Um piloto (MSS-SSC) mandou o agente executar o "smoke manual" dirigindo o browser: sem seletor estável clicava errado, em fluxo destrutivo desfazia/refazia, e sem critério observável julgava como falha algo que passou → ~30 min em loop. plano-teste.md ganha seção "Validação de UI/tela — SÓ determinística" (rota via `TestClient`; e2e real = Playwright roteirizado com asserts; smoke manual = roteiro 👤 humano, não tarefa do assistente)
- fix: **erro `disable-model-invocation` do plano-teste** — o CLAUDE.md mandava o modelo "rodar `/mss-spec:plano-teste`", mas o comando é user-only → erro ao invocar via Skill. Corrigido o wording (template + comando): pra verificar, o assistente roda o `pytest` do PLANO-TESTE.md **direto**; o slash-command é disparado por você pra regravar o baseline
- fix: **proxy corporativo mudou `10.170.200.120` → `10.170.200.1:8080`** — atualizado em AMBIENTE §2 (2 pontos), ambiente.md (comentário do `.env`) e COMO-FUNCIONA.html. O plano histórico `plans/2026-07-02-*` mantém o IP antigo (registro datado)
- fix: **`certs/corp-ca.pem` atualizado (68 → 69 certs)** — o FortiGate novo (`10.170.200.1`) faz SSL-inspection assinando com a CA do appliance (`CN=FG2H0GT924902724`), que não estava no bundle antigo → `apt-get update` HTTPS falhava com "certificate issuer is unknown". Bundle reexportado das raízes do Windows (via Transportes/V2, que buildava OK). AMBIENTE §2 ganha as pegadinhas: (a) **Docker Desktop `config.json` injeta proxy em TODO build** (corrige a nota anterior — não é "só o pull do `FROM`"); (b) "issuer unknown" = corp-ca.pem defasado quando troca o appliance FortiGate
- feat: `/mss-spec:frontend` agora **re-sincroniza `docs/FRONTEND.md` do template a cada run** (projeto pega as melhorias do molde sem depender de foto antiga); o **scaffold** só é copiado na 1ª vez (não sobrescreve os componentes do projeto num re-run)
- feat: **`/mss-spec:frontend`** — instala o front moderno (Nível 2) para telas densas
- feat: `templates/frontend/` — scaffold Vite + React + TS + Mantine com tema MSIG (`src/theme.ts`: brand/navy), `ExemploGrid` com mantine-datatable, README com ilha×SPA e o atrito de build/proxy
- feat: `templates/FRONTEND.md` reestruturado em **dois níveis** (Nível 1 Jinja+Tailwind server-rendered · Nível 2 React+TS+Mantine SPA) com regra de decisão por-tela; Tailwind e Mantine não se misturam no mesmo app
- docs: LEIA-ME, COMO-FUNCIONA.html (node C5 + renumeração) e kickoff citam o front moderno
- nota: Next/Remix ficaram de fora de propósito — para app interno autenticado, SPA (Vite) é mais simples que SSR
- fix (feedback do 1º piloto MSS-SSC): scaffold ganha **`@mantine/dates` + `DatePickerInput` pt-BR** (`DatesProvider locale=pt-br` + `dayjs`) — o exemplo usava `<input type="date">` nativo (cru); nunca mais o nativo
- **regra: só dependências ESTÁVEIS (nada de beta/rc)** — decisão do owner; codificada no FRONTEND.md, scaffold e memória. A `mantine-react-table` ("parruda") fica **de fora** (sem estável pro Mantine atual: latest 1.3.4 é Mantine antigo, v2 só alpha/beta); grid = `mantine-datatable` estável
- fix: **scaffold estava 2 majors atrás** — pinado Mantine 7/React 18 (de cabeça). Verificado no npm e corrigido pro estável atual: **Mantine 9.4.1 + React 19 + mantine-datatable 9.3.1 + clsx** (`@mantine/*` na mesma versão exata; Mantine 9 exige React 19). Docs/comando/README ganham nota "versões envelhecem — confira o latest no npm + typecheck no install". Lição: não cravar versão de memória (mesmo padrão do trixie/bookworm no Docker)
- feat: componente **`StatusBadge`** no scaffold — etiqueta de status colorida (verde/amarelo/vermelho/cinza) via `Badge` do Mantine, no lugar de ícone/texto cru; em uso no `ExemploGrid` (pensando em telas com status como o ATM-Transportes)
- change: busca na grid = **funil na coluna (estilo Excel)** via `filter`/`filtering` da `mantine-datatable`, NÃO barra separada acima — `ExemploGrid` reescrito com o funil no cabeçalho da coluna Nº; FRONTEND.md atualizado (escolha do owner)
- fix: `ExemploGrid` **não traz mais coluna de status falsa** ("Com anexos/Sem anexos") — a sessão do MSS-SSC copiou esse status inventado pra uma tela sem status e ficou redundante/feio. Regra dura no FRONTEND.md: status/legenda **só para estado real e múltiplo** (ex. ATM); **não inventar** de contagem/boolean; **não é peça de toda grid**. Componentes `StatusBadge`/`StatusLegend` seguem no scaffold, mas fora do exemplo (opcional/sob julgamento)
- feat: componente **`StatusLegend`** + regra — quando a grid tem status, **sempre uma legenda acima** explicando cada cor; os status são **por-projeto** (não generalizar; o ATM-TRP tem mais itens) — o plugin dá o componente, a lista vem do projeto. Codificado no FRONTEND.md e na memória `front-moderno-mantine`
- feat: padrões de grid no FRONTEND.md + scaffold — **busca na grid** (filtra records em várias colunas; client-side p/ pouco, `?busca=` server-side p/ muito) e **exportar Excel no SERVIDOR** (FastAPI + `openpyxl`, nunca lib de export no front — evita mais dep de terceiro). `ExemploGrid` agora com busca multi-campo.
- build tools no **último estável**: **vite 8 + `@vitejs/plugin-react` 6 + TypeScript 7** (todos GA). Régua corrigida: "só estável" é contra beta/rc, NÃO contra major GA recém-saído — usa o mais novo estável. Segurança p/ TS 7: o build (vite/esbuild) não usa `tsc`; ele só roda no `typecheck` — se reclamar, cai pra `typescript ^5.6` numa linha

## 0.6.0 — 2026-07-10 (seletor de ambiente CONEXAO_SQL — validado no MSS-SSC)
- feat: `.env` passa a ter **`CONEXAO_SQL`** (`D0`|`HML`|`PRD`, padrão D0) no lugar de `CONEXAO_PRD` — escolhe o par Fernet; e **`CONEXAO_SQL_PORTA`** opcional (vazio = porta padrão do SQL; preenchida sobrescreve o Server via regex, mantendo o host cifrado)
- feat: `get_connection.py` interpreta os dois seletores num só ponto (`_ambiente()` + `_PARES`); `is_ambiente_prd()` deriva de `CONEXAO_SQL`; funções `_hml()` separadas removidas (HML agora é `CONEXAO_SQL=HML`)
- fix: `_build_conn_str` faz `rstrip(';')` — par terminando em `;` gerava `;;` (segmento vazio) → connection string inválida `[87]`
- fix: **comentário no `.env` SEMPRE em linha própria** — inline o Docker Compose `env_file` passa o comentário junto do valor (quebrou a porta em teste real). Documentado em banco.md, AMBIENTE §4, template
- Validado no MSS-SSC com conexão real (D0 default, override de porta, guardas de ambiente inválido/placeholder)

## 0.5.1 — 2026-07-08 (build real MSS-SSC no escritório expôs 3 bugs)
- fix: base `python:3.x-slim` → **`-slim-bookworm`** — a tag sem sufixo migrou pra trixie/Debian 13 e o `apt-get update` do repo ODBC `debian/12` quebrava
- fix: `apt` do build via **HTTPS** (mirrors Debian) — porta 80 é interceptada pelo FortiGate em cleartext (`Bad header data`); em HTTPS a CA embutida torna o intercept confiável (funciona sem proxy explícito)
- fix: linha do repo ODBC da MS escrita à mão (um `[ ]` com `signed-by`) no lugar de `curl prod.list | sed` — o prod.list já traz `[arch=...]` e o segundo colchete gerava `Malformed entry (URI parse)`
- docs: AMBIENTE §2 com as 3 pegadinhas; memória `project_docker_build_fortigate`. **Validado com build real** (`pyodbc.drivers()` → ODBC Driver 17)

## 0.5.0 — 2026-07-08 (deriva MSS-SSC → plugin)
- fix: `templates/docker/Dockerfile` ganha a receita do **ODBC Driver 17** (msodbcsql17, repo Microsoft debian/12) — furo real: projetos SQL nasciam sem driver e o `pyodbc` não conectava. Portado do canário MSS-SSC
- change: base `python:3.14-slim` → **`3.12-slim`** (padrão da casa: Transportes/jedai/MSS-SSC; casa com o repo ODBC debian/12)
- change: mecanismo de proxy alinhado ao MSS-SSC — `ARG HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` predefinidos (pip/apt usam sozinhos), no lugar do `PIP_PROXY` custom; base compose sem build.args, `office.yml` injeta o proxy do `.env` (sem IP hardcoded — fecha a contradição do review)
- docs: AMBIENTE §2, ambiente.md e COMO-FUNCIONA.html atualizados (3.12, novo fluxo de proxy)

## 0.4.0 — 2026-07-08
- feat: `templates/get_connection.py` — padrão canônico de conexão SQL Server multi-ambiente (Transportes V2): par Fernet KEY/CIPHERTEXT por base+ambiente NO CÓDIGO, `.env` só com `CONEXAO_PRD`/`API_ENV`; helpers mask_password/Encrypt/timeout/logging
- fix: banco.md e AMBIENTE §4 reescritos em torno do padrão canônico — as variantes "conn string no .env" e "Fernet com chave no .env" saem (feedback do owner: credencial NUNCA no .env, "no máximo o ambiente"); pares prontos das bases corporativas apontados no Transportes V2 (copiar entre projetos = decisão do owner)
- docs: fatos de porta verificados por decriptação local — SSC dev `10.170.210.36,1435`, tkgs_corp/MSS_TRP dev sem porta explícita, SSC prod `10.170.210.48`; instâncias 1434/1435 (owner), 1434 `<a confirmar>`

## 0.3.2 — 2026-07-08
- feat: regra de credencial no `/mss-spec:banco` + AMBIENTE §4 + catálogo de precedentes — antes de pedir usuário/senha ao owner, reusar o `.env` local de projeto precedente que já conecta (jedai), ajustando só `Database=`; nunca ecoar/commitar
- fix: AMBIENTE §4 não afirma mais "porta 1433" — porta real verificada no jedai é `10.170.210.36,1435`; confirmar sempre com o `.env` que funciona (anti-fabricação)

## 0.3.1 — 2026-07-08
- fix: ESTRUTURA.md alinhado ao layout REAL consolidado (MSS-SSC/estilo jedai): camadas na RAIZ (`main.py` + config/models/services/routers/utils) e `pages/` fora de `templates/` via ChoiceLoader — não mais pacote `app/`; Dockerfile (COPYs por camada + `uvicorn main:app`), regra do CLAUDE.md e ambiente.md (`config/settings.py`) acompanham

## 0.3.0 — 2026-07-08
- feat: `templates/ESTRUTURA.md` (estrutura de pastas em camadas: app/{config,models,services,routers,utils} + templates/static/tests/sql) — kickoff copia pra `docs/ESTRUTURA.md` e o CLAUDE.md ganha regra crítica; nasceu de projeto novo que saiu com tudo achatado em `app/`

## 0.2.0 — 2026-07-08 (rodada do review)
- fix: CA corporativa agora entra de fato na imagem (`COPY certs` faltava — o `RUN if` nunca achava o arquivo)
- feat: estratégia TLS canônica = CA embutida + `SSL_VERIFY=true` (false rebaixado a fallback de diagnóstico) — docs alinhadas (ambiente, AMBIENTE.md, HTML)
- fix: kickoff faz **merge** no `.claude/settings.json` existente (cópia por cima apagava permissões/hooks)
- fix: linha do INDEX.md varia por nível de cerimônia (no médio não nasce spec — nunca linkar arquivo inexistente)
- feat: regra "Git local-only" codificada no templates/CLAUDE.md (commits locais, stage nominal, push só a pedido); memory.md aponta pra ela
- feat: compose base repassa `HTTP(S)_PROXY`/`NO_PROXY` do `.env` também pro build (cobre apt); office.yml deduplicado via anchor YAML
- docs: nota honesta no Fernet (chave no mesmo `.env` = ofuscação; código com erro claro e aviso de `autocommit`)
- docs: Postgres padrão = `psycopg` v3; nit do `docker network create`; exceção Google Fonts documentada no /documentacao
- test: smoke-test do kit (`tests/test_smoke_kit.py`) — todo caminho citado nos commands existe, JSONs válidos, frontmatter presente

## 0.1.0 — 2026-07-02 a 2026-07-07
- Kit inicial: plugin + marketplace local, 9 comandos (kickoff, nova-feature, ambiente, banco, precedentes, plano-teste, modo, documentacao, memory), templates (CLAUDE/AMBIENTE/FRONTEND/Docker/settings/gitignore/doc HTML), skill precedentes-msig, memória versionada no repo.
