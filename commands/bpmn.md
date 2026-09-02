---
description: Desenha os processos do projeto em BPMN a partir do código (leitura estática por ast) — um processo por porta de entrada, raias por módulo, HTML self-contained + índice de texto, fora do git
argument-hint: "(sem argumento — usa o diretório atual)"
---

**Responda sempre em português (pt-BR).**

Gera o **desenho BPMN dos processos deste projeto lendo o código**. Um processo por **porta de entrada** — rota Flask/FastAPI (`POST /cotacao`) ou, se o projeto não expõe rota, os `main()` dos arquivos da raiz. **Duas saídas do mesmo modelo**, ambas em `docs/` e **fora do git**:

- **`docs/bpmn.md`** — os processos em texto (passos ordenados, tipo de elemento, raia, desfechos). É o que o **assistente** consulta;
- **`docs/bpmn.html`** — o desenho em SVG com raias e piscinas, seletor de processo, arrastar e zoom. É o que o **humano** vê.

1. **Rode o gerador** (script testável do plugin):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/templates/bpmn.py" --proj .
   ```

   Opcionais: `--out <dir>` · `--profundidade N` (níveis de subprocesso expandidos, default 2) · `--limite N` (teto de nós por processo, default 60) · `--ignorar pasta1,pasta2` · `--entrada <funcao>` (repetível — aponta uma função como porta de entrada quando ela não é rota nem `main`, ex.: um job de cron). Se `${CLAUDE_PLUGIN_ROOT}` não resolver, ache o script nos locais padrão (`~/.claude/plugins/cache/.../mss-spec/templates/bpmn.py` ou o clone do junction/skills-dir) — mesmo fallback do `doctor`. Não achou → **PARE com erro claro**; nunca invente caminho.

2. **Reporte os dois caminhos** (absolutos) e, se quiser o quadro agora, **leia o `bpmn.md`** e resuma os processos pro owner — quantas portas de entrada, onde o fluxo decide, o que fala com banco e com serviço externo.

3. **O que o gerador vira em cada elemento** (numeração do infográfico do Bizagi): rota/`main` → **início (1)** · chamada a função do projeto → **tarefa (4)**, com o rótulo saindo da 1ª linha do **docstring** (senão o nome) · função com decisão/chamadas por dentro → **subprocesso (5)**, expandido num painel próprio · `if/elif/else` → **gateway exclusivo (6)**, ramo rotulado pela condição como está escrita · `asyncio.gather`/pool → **gateway paralelo (7)** · `return` → **fim (3)** e `raise` → **fim de erro** · `try/except` → **evento de borda (19)** · `cursor.execute`/SQLAlchemy/pyodbc → **armazenamento de dados (16)** · `requests`/`httpx` → **fluxo de mensagem (11)** pra **piscina externa (13)** · módulo/pasta da função → **raia (14)** · docstring → **anotação (17)** · função usada por 2+ fluxos → **chamada de atividade (20)**.

4. **Heurística, não mágica — e ela se declara.** É leitura estática por `ast`, só **Python**: rota montada dinamicamente (`add_url_rule`, prefixo de Blueprint resolvido no registro), framework fora de Flask/FastAPI e linguagem fora do Python **não aparecem** — é limitação esperada, não invenção. Gateway inclusivo (8), por evento (9), objeto de dados (15) e grupo (18) **não são deriváveis do código** e saem **declarados** nas duas saídas. `.py` que não parseia vai pra seção **não lido** e a geração segue (falha aberta). Corte no teto deixa rastro `… (+N)` — nunca corta calado.

5. **Poda antes de fidelidade.** Só vira caixa chamada a função do próprio projeto ou decisão que muda o desfecho; `if` que não faz nem um nem outro não aparece. Control-flow completo daria 80 caixas numa rota e o desenho não seria aberto duas vezes. Se faltou detalhe, suba `--profundidade`; se sobrou ruído, desça.

6. **O desenho é pro humano** — o assistente segue lendo `MAPA.md`/`INDEX.md`/`memory/MEMORY.md` como fonte de decisão; a camada de texto dele aqui é o `bpmn.md`. Não use o HTML como insumo de raciocínio.

**Só este projeto:** o gerador nunca lê fora da raiz escaneada — `.claude/` (onde podem viver *worktrees* de **outro** projeto), `.venv/`, `node_modules/`, `tests/`, `backup/` e `certs/` são podados na descida. Mesma fronteira "um projeto por janela" (regra crítica 8) aplicada à leitura automática.

Quando rodar: ao documentar um processo pro time, ao entrar num projeto que já existe (junto do `/mss-spec:analise`) e no fecho de uma feature que mexeu no fluxo — o desenho é derivado e regenerável, então vale regenerar em vez de manter à mão.
