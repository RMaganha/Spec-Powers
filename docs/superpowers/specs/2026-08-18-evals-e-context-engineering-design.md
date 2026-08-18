# Evals e context engineering no kit — design

> Spec viva do assunto **"o kit aprende com a própria falha e carrega a memória certa na hora certa"**.
> Ver também: [captura de memória](2026-07-21-captura-de-memoria-design.md) (o ritual que alimenta esta máquina)
> e [mapa de contexto](2026-07-20-mapa-de-contexto-design.md) (o destilado lido na partida).

## Estado atual

O kit fecha o laço **falha → caso → guardrail → teste** e para de depender de o owner lembrar.

**1. Premissa com fonte (`/mss-spec:nova-feature`, passo 2).** Antes de pedir o OK do owner, o assistente
declara em bloco próprio **o que está assumindo sem ter sido dito** — framework/lib, infra, formato de
saída, alcance da mudança, "todo projeto tem X". Cada premissa carrega a **fonte** (`CLAUDE.md`,
`docs/ARQUITETURA.md#seção`, `memory/<arquivo>.md`, "você disse nesta sessão") ou o rótulo **`sem fonte`**;
as `sem fonte` vêm **primeiro**, porque são as que quebram. Antes de listar, o assistente passa no
destilado (MAPA → INDEX → `memory/MEMORY.md` → `docs/EVALS.md` → `CLAUDE.md`): se a resposta está lá, não
é premissa, é fato com fonte. Sem premissa não-dita → diz isso; não inventa premissa pra preencher.

**2. `docs/EVALS.md` — a memória só de falhas.** Um arquivo, no destilado, com **tabela-índice** no topo
(`id · gatilho · classe · status`) e **bloco por caso** abaixo (`Gatilho · Falhou · Verdade · Guardrail ·
Teste`). Regra dura: caso **sem guardrail** fica **`aberto`** — dívida visível, não some. Caso **fechado
com teste** encolhe pra linha da tabela (o teste passa a ser o guardrail vivo), o que faz o arquivo se
podar sozinho. Alimentado pelo `/mss-spec:memory capturar`: premissa derrubada e reincidência viram caso. Nasce com o projeto (`kickoff`) e chega ao projeto antigo (`upgrade`) **vazio de casos** — caso é conteúdo do owner, nunca sobrescrito pela categoria 1.

**3. Gatilho na memória (recall, não storage).** Todo arquivo de `memory/` tem `gatilho:` no frontmatter —
a **condição observável** em que aquela memória deve ser aberta ("quando editar HTML de app", "quando
faltar caminho de outro projeto"). O índice `memory/MEMORY.md` é **agrupado por família de gatilho** e cada
linha começa pelo gatilho, não pela descrição — o índice deixa de dizer *o que a memória é* e passa a dizer
*quando abrir*. Teto do índice: **≤ 200 linhas e ≤ 25 KB** (o mesmo que o Claude Code aplica ao índice de
auto-memory; acima disso o excedente nem carrega).

**4. Regras path-scoped (`.claude/rules/`).** As memórias cujo gatilho é **arquivo** viram regra com
`paths:` no frontmatter — o Claude Code as carrega **sozinho** quando um arquivo casa com o glob, sem
custo de contexto quando não casa. O molde vive em `templates/rules/` e é instalado por
`/mss-spec:kickoff` e `/mss-spec:upgrade` (categoria 1, só-molde). Regra path-scoped é **curta** (≤ 40
linhas) e nunca duplica o corpo da memória: aponta pra ela.

**5. Fim das duas cópias de memória.** A pasta nativa (`~/.claude/projects/<proj>/memory/`) é volátil e
auto-carrega; a do repo é durável e não. Depois do `/mss-spec:memory resgatar`, o `MEMORY.md` **nativo**
vira um **ponteiro de uma linha** pro índice do repo — o mínimo de tokens que garante que o índice durável
entre na sessão. O `/mss-spec:doctor` checa o ponteiro (existe? aponta pro repo certo?).

**6. `capturar` registra o que deu certo, e poda.** O modo `capturar` passa a colher também **abordagem
confirmada** (prompt/caminho que funcionou, não só correção) e, ao gravar, **poda**: memória superada é
marcada `obsoleta:` e sai do índice (o arquivo fica, para não perder a narrativa). O `/mss-spec:release`
reporta no veredito quantos casos de `docs/EVALS.md` estão **abertos sem guardrail** — ⚠ que lista, não
trava a publicação.

### Critérios de Aceite

- **CA1** — DADO `commands/nova-feature.md`, QUANDO leio o passo 2, ENTÃO ele manda declarar as premissas
  não-ditas antes do OK, cada uma com fonte ou `sem fonte`, com as `sem fonte` primeiro.
- **CA2** — DADO o mesmo passo, ENTÃO ele manda passar no destilado antes de listar e diz que premissa
  derrubada vira caso em `docs/EVALS.md` no fecho, via `/mss-spec:memory capturar`.
- **CA3** — DADO `commands/memory.md` no modo `capturar`, ENTÃO o roteamento cita **premissa derrubada →
  `docs/EVALS.md`**, **o que deu certo → `memory/feedback_*`** e a **poda** (obsoleta sai do índice).
- **CA4** — DADO `docs/EVALS.md`, ENTÃO ele tem a tabela-índice com as colunas fixas, todo caso tem id
  único `F-NNN`, status ∈ {`aberto`, `fechado`}, e todo caso `fechado` aponta um guardrail.
- **CA5** — DADO qualquer `memory/*.md` que não seja índice (`MEMORY.md`, `DIARIO.md`), ENTÃO ele tem
  `gatilho:` no frontmatter.
- **CA6** — DADO `memory/MEMORY.md`, ENTÃO ele tem ≤ 200 linhas e ≤ 25 KB, e cada linha de memória começa
  pelo gatilho.
- **CA7** — DADO `templates/rules/*.md`, ENTÃO cada regra tem `paths:` no frontmatter, tem ≤ 40 linhas e
  aponta a memória de origem; e o `.claude/rules/` deste repo espelha o molde (dogfood).
- **CA8** — DADO `commands/kickoff.md` e `commands/upgrade.md`, ENTÃO ambos instalam `templates/rules/` em
  `.claude/rules/` (categoria 1, só-molde).
- **CA9** — DADO `commands/doctor.md`, ENTÃO existe check do ponteiro da memória nativa pro índice do repo.
- **CA10** — DADO `commands/release.md`, ENTÃO o veredito reporta os casos abertos sem guardrail.
- **CA11** — DADO a suíte, QUANDO rodo `python -m pytest -q`, ENTÃO passa 100% (116 anteriores + os novos: **136**).

### Fora de escopo

Harness/plataforma de eval que roda modelo e julga resposta (lento, não-determinístico, e o kit já decidiu
que validação de comportamento ao vivo é do humano) · tipo novo de memória (premissa derrubada e abordagem
confirmada reusam `feedback_*`) · premissas explícitas fora do `nova-feature` (`analise`/`kickoff`/regra
sempre-ativa no `CLAUDE.md`) · mexer na estrutura do diário de sessão (premissa derrubada já é um **Pivô**)
· `release` **bloquear** por caso aberto (é dívida de prosa, ⚠ basta) · embeddings/busca semântica sobre a
memória (o gatilho é texto casado por leitura, não vetor).

## Histórico

- 2026-08-18 — criado: nasceu do item 4 do to-dolist (evals + context engineering, a partir do artigo da
  OpenAI) e do diagnóstico do owner de que o desenho inicial — 3 bullets de prosa — era raso. A pesquisa em
  fonte Anthropic (context rot e "smallest possible set of high-signal tokens"; `.claude/rules/` com
  `paths:`; teto de 200 linhas/25 KB do índice de auto-memory; "Bloated CLAUDE.md files cause Claude to
  ignore your actual instructions") + a varredura do próprio `memory/` deram os 5 achados que viraram as 6
  peças. Achados: **27 das 33 memórias duráveis nunca entram na sessão sozinhas** (o índice que
  auto-carrega é o nativo, com 6 linhas); o índice é **descrição, não gatilho**; o kit **não usava** nenhum
  mecanismo de carga automática do Claude Code; 100 KB de memória atrás de um índice sem teto nem poda; e
  das 10 falhas reais reconstruídas do repo, **3 eram premissa não-dita** e **1 era memória que existia e
  não foi lida**.
- 2026-08-18 — entregue na 0.19.0: 8 tasks, 34 memórias migradas, 12 casos no corpus, 3 regras
  path-scoped, suíte **136 verde** (era 116). Acrescentado ao desenho original durante a execução: a
  proteção do corpus no `upgrade` (caso é conteúdo do owner, categoria 1 não pode sobrescrever) e o
  teste `test_evals_so_cita_teste_que_existe` (corpus que cita teste fantasma é teatro).
