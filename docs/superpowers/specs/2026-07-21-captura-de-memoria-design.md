# captura de memória — decisões + diário de sessão — design

Data: 2026-07-21 · feature do próprio kit mss-spec.

> Inspiração: avaliação do [claude-mem](https://github.com/thedotmack/claude-mem). **Integração da ferramenta: rejeitada** — é serviço de runtime (worker Bun + SQLite + Chroma vetorial) que auto-captura o firehose e comprime com IA, e isso bate de frente com 3 pilares do kit (não-serviço · memória **curada** 1-fato/arquivo revisada por humano · "o ganho é texto consultável, não busca semântica/vetorial — knowledge-graph fora de escopo"). Aproveitamos as **ideias** que cabem (captura nos limites · progressive disclosure · `<private>`), em **markdown versionado**, sem stack nova.

## Estado atual
O kit passa a ter um **ritual de captura consolidado** que destila a sessão do contexto atual (sem reler arquivos → captura barata) e a roteia pros lares duráveis certos, com filtro `<private>` e **sempre com OK do owner** antes de gravar. Não é comando novo: é um **2º modo do `/mss-spec:memory`**.

A memória fica em **3 camadas**, cada uma no seu lar, sem misturar:
- **Fatos** (já existia) — aprendizado atemporal, 1-fato/arquivo, em `memory/*.md` + índice `memory/MEMORY.md`. Lido **em toda partida** (tem que ser leve).
- **Decisões** (já existia) — o que foi decidido, **inclusive "decidiu-se NÃO fazer X porque Y"**: transversal → `docs/decisoes.md`; escopo "não fazer" → seção **"Fora de escopo"** do `INDEX.md`; narrativa do assunto → **Histórico** da spec viva. Também lido na partida — é o que mata o **re-litígio** ("3 semanas depois peço o que já foi decidido não fazer, e a memória responde a data e o porquê").
- **Diário de sessão** (**novo**) — resumo compacto do que foi conversado/feito/decidido, **isolado por captura**: `memory/sessions/<data>-<assunto>.md` (um arquivo pequeno por sessão) + `memory/DIARIO.md` (índice por dia → assunto → 1 linha → aponta o arquivo). Lido **sob demanda**: lê o índice (leve) e abre **só** o arquivo do dia/assunto — nunca varre tudo. Isso mantém o custo de leitura baixo (o requisito duro do owner) e o `MEMORY.md` de fatos enxuto na partida. **O que o resumo prioriza é a *evolução* das decisões** — não o estado final (esse já vive na spec), mas os **pivôs**: o que se cogitou, por que foi repensado, pra onde ajustou. É esse rastro do raciocínio que hoje se perde e que dá clareza quando o assunto volta.

Comandos:
- **`/mss-spec:memory`** ganha dois modos claros: **`resgatar`** (o de hoje — memória nativa volátil → repo, intacto) e **`capturar`** (novo — destila a sessão e roteia pras 3 camadas).
- **`/mss-spec:mapa`** continua sendo o único dono do `MAPA.md`; `capturar` **chama** o `mapa`, não reimplementa nada dele.

Gatilhos (porque o dev vai esquecer de rodar o comando):
- **Determinístico (a garantia):** o fecho do **`nova-feature`** e o **finishing (merge → master)** passam a **delegar** a `capturar` + `/mss-spec:mapa`, em vez de re-descrever a escrita de memória inline. O merge → master é o momento natural de consolidar as decisões do assunto.
- **Hook opt-in (a rede, best-effort):** **não existe hook nativo "a cada X minutos"** no Claude Code (eventos são por-evento). O mais próximo real: **`Stop`** com *throttle* por arquivo de timestamp (cutuca a cada ~N min/turnos) + **`PreCompact`** (captura antes de a conversa compactar e perder contexto). O hook **só emite nudge** ("rode `/mss-spec:memory capturar`") — **nunca grava sozinho, nunca bloqueia**, **desligado por padrão**. Como o owner já pegou hook falhando em silêncio: se o hook não disparar, o passo determinístico do fecho/finishing cobre — **nada se perde**. A fonte da verdade é o comando; o hook é conveniência.

Convenções: **`<private>…</private>`** marca trecho que **nunca** vai pra nada versionado (memória/diário/decisões); documentada nos templates. **Progressive disclosure** (índice → só o arquivo certo; "nunca leia a pasta inteira") já é a regra — reforço explícito de 1 linha nos templates.

## Critérios de aceite
- **CA1** — DADO uma sessão com decisões (inclusive "decidiu-se NÃO fazer X"), QUANDO rodo `/mss-spec:memory capturar`, ENTÃO ele apresenta rascunhos **roteados pro lar certo** (transversal→`decisoes.md`; "não fazer"→INDEX "Fora de escopo"; narrativa→Histórico da spec; aprendizado→`memory/*.md`; resumo→`memory/sessions/<data>-<assunto>.md`) e **nada é gravado sem meu OK**.
- **CA2** — DADO um rascunho aprovado, QUANDO confirmo, ENTÃO grava nos destinos com índice atualizado (`MEMORY.md` pro fato / `DIARIO.md` pro diário), **sem duplicar** o que já existe.
- **CA3** — DADO conteúdo marcado `<private>`, QUANDO o `capturar` roda, ENTÃO esse conteúdo **nunca** aparece em nada versionado.
- **CA4 (regressão)** — DADO o modo `resgatar`, QUANDO leio `commands/memory.md`, ENTÃO o comportamento de hoje (nativa→repo, não-destrutivo, commit local) continua descrito e intacto.
- **CA5** — DADO o fluxo, QUANDO leio `commands/nova-feature.md` (fecho) e a doc de finishing, ENTÃO ambos **delegam** a `capturar` + `/mss-spec:mapa` (não re-descrevem a escrita de memória inline).
- **CA6** — DADO o diário, QUANDO leio `memory/DIARIO.md`, ENTÃO acho a entrada por **data + assunto** em 1 linha e abro **só** o `memory/sessions/<data>-<assunto>.md` correspondente — sem reler tudo.
- **CA7 (o caso matador)** — DADO uma decisão negativa registrada, QUANDO reabro o assunto semanas depois e a partida lê `MEMORY.md`/`decisoes.md`/INDEX, ENTÃO a decisão aparece de forma recuperável ("em `<data>` decidiu-se NÃO fazer X porque Y") — anti-re-litígio.
- **CA8** — DADO o hook opt-in habilitado que dispara, ENTÃO ele só emite nudge não-bloqueante (não grava, não bloqueia); DADO hook desligado/não-disparado, ENTÃO o passo determinístico do fecho/finishing cobre.
- **CA9 (smoke/wiring)** — DADO a suíte, QUANDO rodo `python -m pytest tests/ -q`, ENTÃO `test_captura_memoria_wiring` cobre: os 2 modos em `commands/memory.md`; a delegação em `nova-feature`+finishing; o hook opt-in/não-bloqueante; os templates com `<private>`+índice-primeiro; e a existência de `templates/DIARIO.md` — e a suíte passa 100%.

## Design
1. **`commands/memory.md`** — vira o comando de memória com **dois modos** (arg `resgatar`|`capturar`; sem arg = pergunta qual). `resgatar` = o texto atual, intacto. `capturar` = destila a sessão do contexto → monta rascunhos roteados pras 3 camadas → filtra `<private>` → mostra pro OK → grava sem duplicar → chama `/mss-spec:mapa` pro *Onde estamos/Próximo passo*. Escreve **do contexto atual** (não relê arquivos).
2. **`templates/DIARIO.md`** (novo) — skeleton do índice do diário: comentário-guia + formato `## <data>` / `- [<assunto>] <gist 1 linha> → sessions/<data>-<assunto>.md`. O `kickoff` copia pro projeto.
3. **`memory/sessions/`** — pasta dos resumos compactos (um `.md` por captura). Estrutura do arquivo: cabeçalho `# <data-hora> — <assunto>` + seções curtas: **Conversamos** (o tema) · **Pivôs / decisões repensadas** (o coração: cada mudança de rumo como `cogitou X → repensou por Y → ajustou pra Z`) · **Rejeitado** (com motivo) · **Fizemos** · **Próximo**. Pequeno por construção, mas o rastro do raciocínio é o que não pode faltar.
4. **`templates/CLAUDE.md`** / **`templates/MEMORY.md`** — regra `<private>` + reforço do índice-primeiro (consultar `MEMORY.md`/`DIARIO.md` antes de abrir arquivo; nunca ler a pasta inteira) + ponteiro pro diário.
5. **`commands/nova-feature.md`** — o passo de fecho (hoje "grave em memory/…") passa a **delegar**: "rode `/mss-spec:memory capturar` + `/mss-spec:mapa`".
6. **finishing (doc/fluxo de integração)** — antes do merge → master, delega a `capturar` (consolida decisões do assunto) + `mapa`.
7. **Hook opt-in** — script mínimo não-bloqueante (Stop com throttle por timestamp + PreCompact) que emite o nudge; **desligado por padrão**, documentado como experimental, com a ressalva "se não disparar, o determinístico cobre".
8. **`kickoff`** — copia `templates/DIARIO.md` → `memory/DIARIO.md` e cria `memory/sessions/` no scaffolding.
9. **`tests/test_smoke_kit.py`** — `test_captura_memoria_wiring` trava CA1–CA6, CA8–CA9 (comando-prosa se testa por wiring, não por unit). Linha no `PLANO-TESTE.md`.
10. **Índices/docs** — linha `aberta` no `INDEX.md` (link pra esta spec); atualização da linha do `/mss-spec:memory` no `LEIA-ME.md`; 1 linha em `docs/decisoes.md` (decisão transversal: 3 camadas + captura consolidada no memory, hook só como rede).

## Fora de escopo
Transcript cru / firehose do chat · SQLite/Chroma/busca vetorial/semântica · worker/daemon/serviço em runtime · sync pra nuvem · hook bloqueante ou hook como fonte da verdade · comando novo separado (`/mss-spec:capturar`) — consolidado no `/mss-spec:memory`.

## Arquivos tocados
- `commands/memory.md` (2 modos: resgatar + capturar)
- `templates/DIARIO.md` (novo — índice do diário)
- `templates/CLAUDE.md` e/ou `templates/MEMORY.md` (`<private>` + índice-primeiro + ponteiro pro diário)
- `commands/nova-feature.md` (fecho delega a capturar+mapa)
- `commands/kickoff.md` (scaffolding: `memory/DIARIO.md` + `memory/sessions/`)
- doc/fluxo de finishing (delegação antes do merge → master)
- hook opt-in (script + config + doc; desligado por padrão) — **última task, experimental**
- `tests/test_smoke_kit.py` (`test_captura_memoria_wiring`)
- `docs/superpowers/PLANO-TESTE.md` · `docs/superpowers/INDEX.md` · `docs/LEIA-ME.md` · `docs/decisoes.md`
- cross-link com `docs/superpowers/specs/2026-07-20-mapa-de-contexto-design.md` (o `capturar` usa o `/mss-spec:mapa` daquele assunto)

## Histórico
- 2026-07-21 — criado: design da captura de memória, aprovado no chat. Refinamentos do owner ao longo do brainstorming: (1) **não integrar o claude-mem** — bate nos pilares (serviço/firehose/vetorial); só capturar as ideias que cabem; (2) **nada de comando novo** — o dev alertou pro risco de "2 comandos, mesmas funções" e de deixar o plugin perdido → consolidado como 2º modo do `/mss-spec:memory`, com o `MAPA.md` seguindo dono do `/mss-spec:mapa`; (3) o **essencial são as decisões, inclusive as negativas** (anti-re-litígio "3 semanas depois"); (4) **mais** que decisões — um **resumo do que foi conversado**, isolado por assunto, datado e indexado, com trava dura de **custo** (barato de gravar do contexto e de reler via índice → 1 arquivo) → nasce a **3ª camada (diário de sessão)** com `memory/sessions/<data>-<assunto>.md` + `memory/DIARIO.md` (escolha do owner: 1 arquivo por captura + índice datado, contra inchar o `MEMORY.md` de partida); (5) gatilho **determinístico no fecho/finishing** como garantia + **hook opt-in** só como rede (o owner já pegou hook falhando em silêncio — a fonte da verdade nunca é o hook); (6) **conteúdo do diário = a evolução das decisões, não o estado final** — o owner apontou esta própria conversa (quantas decisões foram repensadas/ajustadas) como o insumo que dá clareza e hoje se perde → o resumo de sessão prioriza os **pivôs** (`cogitou X → repensou por Y → ajustou pra Z`). Dogfood natural: a 1ª captura real será a desta sessão.
