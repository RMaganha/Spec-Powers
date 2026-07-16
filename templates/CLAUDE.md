<!-- MODELO de CLAUDE.md — copie para a RAIZ do projeto novo como `CLAUDE.md` e preencha os <...>.
     Regra de ouro: ENXUTO. Só o que o Claude NÃO infere do código (visão, como roda, convenções, regras).
     Detalhe de feature vai na spec; histórico/memória NÃO entram aqui. -->

# <Projeto> — <objetivo em 1 frase>

## Modo de trabalho (nunca violar)
- **Idioma**: responda **sempre em português (pt-BR)** — mensagens, docs e relatórios gerados. Vale mesmo quando o gatilho for um slash-command sem texto (não caia no inglês por padrão).
- **Base do projeto (ler PRIMEIRO)**: se existir um `projeto.md` na raiz, leia-o antes de qualquer outra coisa — é a base/contexto fundamental do projeto. Se não existir, siga normalmente.
- **Não codar antes do meu OK explícito**: diagnosticar → plano curto → esperar OK → verificar no real (nada de "análise de memória").
- **Não inventar fatos concretos**: caminhos, paths de deploy, hosts, portas, nomes de recurso/container, estrutura de pastas — use só o que está no repo/`projeto.md` ou o que eu confirmar. Na dúvida, deixe genérico, marque `<a confirmar>` ou pergunte; nunca chute um valor concreto (um caminho errado é pior que uma lacuna).
- **Siga as skills do superpowers à risca** (brainstorming, test-driven-development, verification-before-completion, systematic-debugging, requesting-code-review). Precisão acima de velocidade.
- **Assuma o papel de especialista sênior do domínio da tarefa**: UI/layout → especialista sênior em UI/UX; código → engenheiro sênior; banco → DBA sênior; e assim por diante para segurança, infra, etc. (a lista é aberta — infira o domínio). Anuncie brevemente o papel assumido, trabalhe sob essa ótica até concluir/ter o meu OK, e então volte ao papel padrão: **arquiteto/engenheiro sênior de desenvolvimento**. Entrega genérica sai pior que a de um especialista.
- **Nível de cerimônia** (padrão **médio**; troque com `/mss-spec:modo <nível>`): **mínimo** = executa direto, sem spec/plano · **médio** = design curto + plano curto + execução inline (sem subagentes/dupla revisão) · **alto** = ritual completo (spec + `writing-plans` + `subagent-driven-development`). Alto só para feature grande/crítica. Em qualquer nível, TDD e verificação (rodar + colar saída) são inegociáveis — o que varia é só o peso do planejamento.
- **Git — branch por tarefa + local-only**: **cada nova tarefa/feature abre a sua branch** (`git checkout -b <tipo>/<nome>`, ex.: `feature/…`, `fix/…`) — **nunca** codar direto na branch principal (`main`/`master`). Commits são locais e com stage **nominal** (`git add <caminhos>`; nunca `git add .`/`-A`, que varreria `.env`/segredos). **`git push` só quando eu pedir explicitamente.**
- **Índices do projeto**: no início, leia `memory/MEMORY.md` (aprendizados) e `docs/superpowers/INDEX.md` (tarefas). Ambos são só índices (1 linha por item). Abra o arquivo individual só quando o índice apontar relevância; nunca leia a pasta inteira. Fallback: Grep/Glob sobre `docs/`.
- **Plano de teste base (anti-regressão)**: antes de declarar qualquer coisa pronta (feature nova OU alteração), **rode o comando de teste do `docs/superpowers/PLANO-TESTE.md` direto** (ex.: `python -m pytest -q`) e **cole a saída**. Só afirme sucesso com **100% verde**; suíte nova só vira baseline quando passa inteira. O slash-command `/mss-spec:plano-teste` é **disparado por você (humano)** pra regravar o baseline — o assistente **não** o invoca (é `disable-model-invocation`; tentar dá erro). **Validação de tela é só determinística** (rota via `TestClient`; e2e real = teste Playwright roteirizado, dentro da suíte) — o assistente **nunca** valida UI dirigindo o browser ao vivo (clicar/screenshot em loop); "smoke manual" é roteiro pra você rodar.

## Contexto
- **Stack/runtime:** <ex.: Python 3.x / Node / ...>
- **Como roda:** <CLI | serviço/porta | container | cron>
- **UI:** <não | web — servidor FastAPI + Jinja; CSS = Tailwind + `@tailwindcss/typography`; descreva guias e ações>   <!-- HTML de aplicação: ver regra de front-end nas Regras críticas -->
- **Integrações externas:** <sites / APIs / filas, ou "nenhuma">
- **Banco:** <não | qual> — DDL versionada em `sql/NN_*.sql`, revisada por mim e rodada **FORA** do app; acesso isolado por fonte; credenciais só em `.env` (nunca commit/hardcode).

## Mapa de arquivos
- `projeto.md` — base/contexto fundamental do projeto (lido primeiro; pode não existir)
- `docs/AMBIENTE.md` — referência de ambiente corporativo MSIG (rede Docker, proxy, Postgres, SQL Server, Azure)
- `docs/ESTRUTURA.md` — estrutura de pastas em camadas (onde cada arquivo novo nasce)
- `docs/FRONTEND.md` — design system MSIG (só se tiver UI web): tokens, layout admin, ícones, JS, componentização
- `docs/superpowers/INDEX.md` — índice das tarefas (specs/planos)
- `<arquivo>` — <responsabilidade>

## Regras críticas (nunca violar) — cada uma nasce de um bug ou decisão real
1. **Registro/memória/notas NUNCA em um arquivo `CLAUDE.md`** (ele é instrução sempre-ativa e polui o contexto). Memória persistente = pasta `memory/` deste projeto (dentro do repo, versionada com `MEMORY.md` como índice — NÃO em `~/.claude/projects/<proj>/memory/`); estado/handoff = plan files do superpowers.
2. Nunca commitar `.env` nem segredos; nunca hardcode de credencial.
3. **Front-end de aplicação sempre com Tailwind CSS + plugin `@tailwindcss/typography`**; separe JS, CSS e estilos em arquivos e pastas próprias (ex.: `static/js/`, `static/css/`), nunca tudo inline num único HTML. Siga o **design system MSIG em `docs/FRONTEND.md`** (tokens navy/brand-red/canvas, sidebar admin colapsável, ícones SVG inline estilo Lucide, JS vanilla com hooks `data-*`, componentização Jinja). Exceção: **documentação/relatório** standalone (arquivo único portável) — mantém self-contained, no **estilo editorial MSIG** via `/mss-spec:documentacao`.
4. **Estrutura de pastas em camadas, sempre** (`docs/ESTRUTURA.md`): `main.py` + config/, models/, services/, routers/, utils/, templates/, pages/, static/, tests/, sql/ — cada um na sua pasta na raiz. **Nunca criar arquivos achatados numa pasta única** (nasceu de scaffolding que saiu com tudo jogado em `app/`). Router fino, regra no service, imports só "pra baixo".
5. **Segurança (secure-by-default)** — o app fica exposto na nuvem; trate como alvo. **Prod**: default-deny + autorização no **backend** por request (o front nunca autoriza). SQL **sempre** parametrizado; entrada validada (Pydantic); **upload** checado (tipo/tamanho). O **browser nunca** vê segredo nem URL interna (assuma leitura total do bundle) — segredo só no `.env`/Key Vault em runtime. Sem stack trace/erro verboso pro cliente e sem PII/segredo em log. Headers de segurança + HTTPS-only (prod) + CORS fechado. **Obscuridade não é segurança** (não criptografar/ofuscar URL de asset). Deps sem CVE. Endpoints de **integração** (outro sistema chama) exigem `Authorization: Bearer` (`TOKEN_API` no `.env`, server-to-server), ligados por `AUTH_TOKEN_ATIVO` (false em dev, true em prod). **Detalhe e checklist em `docs/SEGURANCA.md`; auditoria com `/mss-spec:seguranca`.**
6. <regra específica do seu projeto…>

<!-- Mantenha este arquivo curto. Se uma seção crescer demais, mova o detalhe para a spec da feature
     (docs/superpowers/specs/) ou para um doc em docs/, e deixe aqui só um ponteiro. -->
