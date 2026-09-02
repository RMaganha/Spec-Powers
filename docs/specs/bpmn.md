# bpmn — desenho do processo a partir do código

## Estado atual
O `/mss-spec:bpmn` (`commands/bpmn.md`) roda o gerador determinístico `templates/bpmn.py` — Python
puro, sem Node nem npm — que lê o código do projeto por **`ast`** e produz **três saídas**, todas em
`docs/` e **fora do git**:

| saída | o que é | pra quem |
|---|---|---|
| `docs/bpmn.html` | o desenho, renderizado pelo **bpmn-js 18.27.0** sobre coordenadas do **bpmn-auto-layout 1.3.0** (bpmn.io), ambos **vendorizados** em `templates/vendor/` — self-contained, zero CDN | **humano** |
| `docs/bpmn/<slug>.bpmn` | um **BPMN 2.0 XML** por diagrama; abre no **Bizagi**/Camunda Modeler pra editar, organizar e publicar | **humano**, na ferramenta dele |
| `docs/bpmn.md` | os processos em texto: passos, tipo de elemento, raia, desfechos, integrações | **assistente** |

**O gerador não calcula coordenada.** Emite XML semântico; quem posiciona é o `bpmn-auto-layout`,
empacotado uma vez com `esbuild` (`--format=iife`, 83 KB) e rodando **no navegador** — é isso que
mantém o comando Python puro. Layout escrito à mão foi o erro da 0.24.x e virou o caso **F-018**.

**Estrutura em níveis:** um diagrama por **porta de entrada** — rota Flask/FastAPI, ou `main()` em
cascata (raiz → qualquer módulo) — **mais um por subprocesso** com 2+ elementos (drill-down logo
abaixo do diagrama pai, com âncora própria). Índice lista só as portas de entrada.

**Mapeamento** (numeração do infográfico do Bizagi que o owner usou como modelo): rota/`main` →
início (1) · chamada a função **do projeto** → tarefa (4), rótulo da 1ª frase do docstring, senão o
nome · função com decisão/chamadas por dentro → subprocesso (5) · `if/elif/else` → gateway exclusivo
(6) · `asyncio.gather`/pool → gateway paralelo (7) · `return` → fim (3) · `raise` → fim de erro ·
`try/except` → evento de borda (19) · `cursor.execute`/SQLAlchemy/pyodbc → armazenamento de dados
(16) · `requests`/`httpx` **e SDK de LLM** (`google.generativeai`, `openai`, `anthropic`, `vertexai`,
wrappers langchain) → fluxo de mensagem (11) pra piscina (13), detectado pelo **import no arquivo**
(mesmo tardio, dentro do método — a chamada real é método de instância) · módulo/pasta → raia (14) ·
docstring → anotação (17) · função usada por 2+ fluxos → chamada de atividade (20).

**Rótulo em pt-BR, inglês só onde é texto de programação** (pedido do owner): a condição vira
pergunta (`Falta anexos?`, `linha está vazio?`, `valor maior que 100000?`), o ramo vira `sim`/`não`,
o SQL dá o verbo (`Consulta o banco`, `Grava no banco`), o serviço externo vira `Chama Gemini`, e o
desfecho vira `Retorna JSONResponse` / `Erro: ValidacaoError`. O **modelo e o `bpmn.md` seguem
verbatim**; a abreviação é só de apresentação, pra caber na caixa.

**Dois tipos de buraco, os dois declarados na página** — desenho que parece completo sem ser é pior
que buraco visível: **(a) não derivável do código** (gateway inclusivo 8, por evento 9, objeto de
dados 15, grupo 18, rota dinâmica, framework fora de Flask/FastAPI, linguagem fora do Python);
**(b) não posicionado pelo auto-layout** — raia, piscina, fluxo de mensagem, anotação e associação,
limitação declarada pela própria lib, que por isso vivem no `bpmn.md`, na ficha de cada diagrama e
no `.bpmn` pro Bizagi. Mais: `.py` que não parseia vai pra **não lido** e a geração segue (falha
aberta); corte no teto deixa `… (+N)`; ativo de `vendor/` faltando **para** a geração com erro claro;
e a página **falha legível** (`<noscript>` + texto em cada moldura apontando o `.bpmn`/`bpmn.md`),
porque com o bpmn-js o desenho passa a exigir JS — F-017 mudou de forma, não de lição.

Verificado no **MSS-SSC** (FastAPI real): 24 portas de entrada, 36 diagramas, 19 arquivos `.py`,
0 não lido, piscina `Gemini` detectada. Testes: `tests/test_bpmn.py` (57) + `test_bpmn_wiring` e
`test_suposicao_do_owner_nao_e_requisito` no smoke.

Fora de escopo: linguagem fora do Python (JS/TS, SQL, JSON de fluxo do n8n) · processo de **negócio**
que não está no código · editar o desenho no HTML (é leitura; quem edita é o Bizagi) · o `.html`
virar fonte de leitura do assistente · análise semântica profunda de tipos/chamada dinâmica.

## Histórico
- 2026-09-02 — criado: pedido do owner com o infográfico "Elementos do Bizagi" como modelo de notação;
  desenho **A** (fluxo por porta de entrada, raias por camada) aprovado contra B (diagrama único do
  sistema) e C (sem gerador, o assistente desenha a cada pedido).
- 2026-09-02 — 0.24.1, cinco consertos vindos de rodar no MSS-SSC: esconder das seções passou a
  depender do JS · ordem por riqueza · SDK de LLM virou piscina · mensagem do filho sobe pro
  subprocesso colapsado · `return servico(x)` virou tarefa. Caso F-017.
- 2026-09-02 — **0.25.0, o renderizador foi trocado**: o owner abriu o HTML da 0.24.1 e o veredito
  foi *"ficou péssimo, não dá visibilidade alguma"* — medido, o maior diagrama tinha **3.964 px de
  largura e 222 rótulos truncados**. Saiu o layout SVG artesanal, entrou **BPMN 2.0 XML +
  bpmn-auto-layout + bpmn-js vendorizados** (o kit já vendorizava `vis-network`; o precedente estava
  na mesma pasta). Ganhou também o `.bpmn` que abre no Bizagi e o rótulo em pt-BR. Motivo raiz de eu
  não ter feito assim de saída: tratei *"acho que até algo html funcionaria"* como decisão fechada,
  com fonte na frase do owner, em vez de aconselhar o padrão da área — e cheguei a pôr o XML do
  Bizagi em "fora de escopo" citando essa frase. Casos **F-018** (reinventei layout) e **F-019**
  (suposição do owner virou requisito), com regra no `commands/nova-feature.md`.
- 2026-09-02 — 0.25.1, três defeitos que o owner viu antes de mim (ele abriu o dogfood do próprio
  kit e o desenho de um módulo aparecia sob o cabeçalho de outro): **slug de diagrama colidia** —
  três `gerar` no mesmo projeto viravam três `1-gerar`, o `getElementById` devolvia o primeiro e a
  seção renderizava o XML alheio (no MSS-SSC eram duas seções trocadas) · **import com apelido**
  (`from x import y as z`) fazia a tarefa **desaparecer**, porque eu guardava só o nome local ·
  e **todos os 36 desenhos falhavam com o painel estreito** (`SVGMatrix scale: non-finite`),
  porque o `fit-viewport` mede o container e ele ainda não tinha tamanho — agora monta sob demanda
  e espera o tamanho. Casos **F-020** e **F-021**. Junto: acento no slug translitera
  (`extração` → `extracao`, era `extra-o`) e `fn` do nó passou a ser a identidade da **definição**,
  não o nome no ponto de chamada.
