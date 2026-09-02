---
description: Desenha os processos do projeto em BPMN a partir do código (leitura estática por ast) — um diagrama por porta de entrada + drill-down por subprocesso, renderizado pelo bpmn-js (bpmn.io) e com os .bpmn que abrem no Bizagi
argument-hint: "(sem argumento — usa o diretório atual)"
---

**Responda sempre em português (pt-BR).**

Gera o **desenho BPMN dos processos deste projeto lendo o código**. Um diagrama por **porta de entrada** — rota Flask/FastAPI (`POST /cotacao`) ou, se o projeto não expõe rota, os `main()` dos arquivos da raiz — **mais um diagrama por subprocesso** (drill-down), que é como um modelo BPMN de verdade se organiza. **Três saídas**, todas em `docs/` e **fora do git**:

- **`docs/bpmn.html`** — o desenho, renderizado pelo **bpmn-js** (o motor do bpmn.io/Camunda) sobre coordenadas do **bpmn-auto-layout**, os dois **vendorizados** em `templates/vendor/`. Self-contained, zero CDN. É o que o **humano** vê;
- **`docs/bpmn/<processo>.bpmn`** — um **BPMN 2.0 XML** por diagrama. Abre no **Bizagi**/Camunda Modeler, onde você edita, organiza e publica — e onde raia e piscina ganham a posição que o auto-layout não dá;
- **`docs/bpmn.md`** — os processos em texto (passos, tipo de elemento, raia, desfechos, integrações). É o que o **assistente** consulta.

1. **Rode o gerador** (script testável do plugin, **Python puro** — sem Node, sem npm):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/templates/bpmn.py" --proj .
   ```

   Opcionais: `--out <dir>` · `--profundidade N` (níveis de subprocesso, default 2) · `--limite N` (teto de nós por processo, default 60) · `--ignorar pasta1,pasta2` · `--entrada <funcao>` (repetível — aponta uma porta que não é rota nem `main`, ex.: um job de cron). Se `${CLAUDE_PLUGIN_ROOT}` não resolver, ache o script nos locais padrão (`~/.claude/plugins/cache/.../mss-spec/templates/bpmn.py` ou o clone do junction/skills-dir). Não achou → **PARE com erro claro**; nunca invente caminho.

2. **Reporte os três caminhos** (absolutos) e, se quiser o quadro agora, **leia o `bpmn.md`** e resuma pro owner: quantas portas de entrada, onde o fluxo decide, o que fala com banco e com serviço externo.

3. **De onde sai cada elemento** (numeração do infográfico do Bizagi): rota/`main` → **início (1)** · chamada a função do projeto → **tarefa (4)**, rótulo da 1ª frase do **docstring** (senão o nome) · função com decisão/chamadas por dentro → **subprocesso (5)** com drill-down próprio · `if/elif/else` → **gateway exclusivo (6)**, com a condição virada **pergunta em pt-BR** e ramos `sim`/`não` · `asyncio.gather`/pool → **gateway paralelo (7)** · `return` → **fim (3)** e `raise` → **fim de erro** · `try/except` → **evento de borda (19)** · `cursor.execute`/SQLAlchemy/pyodbc → **armazenamento de dados (16)**, com o verbo saindo do próprio SQL ("Consulta o banco", "Grava no banco") · `requests`/`httpx` e **SDK de LLM** (`google.generativeai`, `openai`, `anthropic`…) → **fluxo de mensagem (11)** pra **piscina (13)**, detectado pelo **import no arquivo** (mesmo tardio, dentro do método) · módulo/pasta → **raia (14)** · docstring → **anotação (17)** · função usada por 2+ fluxos → **chamada de atividade (20)**.

4. **Conteúdo em pt-BR; inglês só onde é texto de programação.** O rótulo que vai na caixa é frase curta em português com o identificador do código dentro (`Falta anexos?`, `Consulta o banco`, `Erro: ValidacaoError`, `Retorna JSONResponse`). O texto verbatim do código fica no `bpmn.md` e na anotação.

5. **Dois tipos de buraco, os dois declarados na saída** (desenho que parece completo sem ser é pior que buraco visível): **(a)** o que a leitura estática **não deriva do código** — gateway inclusivo (8), por evento (9), objeto de dados (15), grupo (18), rota dinâmica (`add_url_rule`, prefixo de Blueprint), framework fora de Flask/FastAPI, linguagem fora do Python; **(b)** o que o **auto-layout do bpmn.io não posiciona** (limitação declarada pela própria lib): **raia, piscina, fluxo de mensagem, anotação e associação** — isso vive no `bpmn.md`, na ficha de cada diagrama e no `.bpmn` pro Bizagi. `.py` que não parseia vai pra **não lido** e a geração segue (falha aberta). Corte no teto deixa `… (+N)`.

6. **Poda antes de fidelidade.** Só vira caixa chamada a função do próprio projeto ou decisão que muda o desfecho. Faltou detalhe? suba `--profundidade`. Sobrou ruído? desça.

7. **O desenho é pro humano** — o assistente segue lendo `MAPA.md`/`INDEX.md`/`memory/MEMORY.md` como fonte; a camada de texto dele aqui é o `bpmn.md`. Não use o HTML como insumo de raciocínio.

**Layout não se escreve à mão.** O `bpmn-js` e o `bpmn-auto-layout` estão vendorizados porque desenhar geometria de processo à mão já falhou aqui (caso **F-018**: tira de 4.000 px, 222 rótulos truncados). Se algum ativo de `templates/vendor/` faltar, o gerador **para com erro claro** em vez de emitir página quebrada.

**Só este projeto:** o gerador nunca lê fora da raiz escaneada — `.claude/`, `.venv/`, `node_modules/`, `tests/`, `backup/`, `certs/` são podados. Mesma fronteira "um projeto por janela" (regra crítica 8).

Quando rodar: ao documentar um processo pro time, ao entrar num projeto que já existe (junto do `/mss-spec:analise`) e no fecho de feature que mexeu no fluxo.
