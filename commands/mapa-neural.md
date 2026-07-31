---
description: Gera o mapa mental do projeto atual — árvore radial com o projeto no centro e 4 dimensões (arquitetura · APIs & integrações · memórias · conexões entre projetos), em HTML self-contained + índice de texto
argument-hint: "(sem argumento — usa o diretório atual)"
---

**Responda sempre em português (pt-BR).**

Você vai gerar o **mapa mental do projeto atual** — a árvore com o projeto no centro e **4 dimensões**, cada uma **extraída do repo** (o gerador só lê o que existe; **nunca inventa**):
- **Arquitetura interna** — **se está no repo, está no mapa**: todo `.py` da raiz (entrypoints, tenham o nome que tiverem) + **toda pasta de 1º nível com conteúdo**, com o nome e a extensão que o projeto tiver (`apis/`, `persistencia/`, `web/` só com HTML, `prompts/` só com Markdown, `n8n/` só com JSON de fluxo), **descendo nas subpastas**. Ficam de fora só: pasta de ferramenta (`.venv`, `node_modules`, `.claude`…), pasta que já tem ramo próprio (`docs/`, `memory/`), **arquivo morto e insumo de build** (`backup/`, `certs/` — cópia arquivada aparecendo ao lado do arquivo vivo faz o mapa sugerir duas telas onde só existe uma), **o que o projeto manda o git ignorar** e o que vier em `--ignorar`. O mapa é **descritivo**; quem prescreve nome de pasta é o `docs/ESTRUTURA.md`;
- **APIs & integrações** — endpoints expostos (rotas **FastAPI** `@app.get("/x")` e **Flask** `@app.route("/x", methods=[...])` — sem `methods=`, GET) + integrações detectadas por *import* (banco, HTTP, fila);
- **Memórias & conhecimento** — specs, índice `memory/MEMORY.md`, `docs/decisoes.md`, `to-dolist` e o **diário de sessão** (índice `memory/DIARIO.md` → cada entrada aponta o `memory/sessions/<data>-<assunto>.md`);
- **Conexões entre projetos** — a seção **Conexões** do `docs/superpowers/MAPA.md` (o nome do vizinho é o que estiver declarado lá — declare o **nome completo** do projeto).

Duas saídas do mesmo modelo:
- **`mapa-neural.md`** — índice em texto (é o que o **assistente** consulta pra ter o todo sem reler o repo);
- **`mapa-neural.html`** — mapa radial **full-screen**, expansível (clique no `＋`) e arrastável, 100% self-contained.

1. **Ache o gerador:** `${CLAUDE_PLUGIN_ROOT}/templates/mapa_neural.py`. Se a variável não resolveu, procure em `~/.claude/plugins/cache/*/mss-spec/*/templates/mapa_neural.py`. Não achou → PARE com erro claro; nunca invente caminho.
2. **Antes de rodar, veja se o projeto declara alguma pasta como CÓPIA ARQUIVADA.** O critério de exclusão **não** é "não é runtime" — é **risco de confundir com o que está vivo**: pasta com versão obsoleta de tela/módulo que aparece no mapa como par da versão real (`backup/`, `_referencia/`, `v1_antigo/`…). O `CLAUDE.md`/`docs/ARQUITETURA.md` costumam dizer isso em prosa (*"a UI do sistema é uma só"*, *"reviver a v1 está fora de escopo"*). **O gerador não lê prosa de propósito** (adivinhar intenção é chute); quem lê é **você** — traduza **essa** declaração em `--ignorar`.
   **Não exclua pasta só por não ser runtime.** Script de investigação, notebook de análise, export de workflow (`n8n/`), fixture — não roda em produção e **ainda assim é peça do projeto**, útil de ver no mapa (decisão do owner sobre casos reais: `_investigacao/` e `n8n/` **ficam**). Na dúvida entre ruído e peça, **mantenha e pergunte** — esconder algo que existe é pior que listar algo de menos.
3. **Rode no projeto atual:** `python "${CLAUDE_PLUGIN_ROOT}/templates/mapa_neural.py"` (opcional: `--proj <dir> --out <dir>`; `--ignorar pasta1,pasta2` com o que você apurou no passo 2; `--limite N` muda o teto por ramo, default 200). As saídas caem em **`docs/`** por padrão (toda pasta do superpowers tem `docs/`, fica isolado da raiz; ambas gitignoradas — derivadas/regeneráveis).
4. **Reporte os dois caminhos** (absolutos). Se quiser o quadro agora, **leia o `mapa-neural.md`** e resuma as dimensões pro owner.

**Heurística, não mágica:** os endpoints saem de decorators de rota **no início da linha** (decorator citado em comentário/docstring não conta); as integrações, de linhas de `import`; a arquitetura, das pastas com código. É uma leitura estática — se algo do projeto não aparecer (rota montada dinamicamente ou por `add_url_rule`, prefixo de Blueprint resolvido no registro, framework fora de FastAPI/Flask, integração exótica), é limitação esperada, não invenção: complete declarando na seção **Conexões** do `MAPA.md` ou ajuste o código.

**Sem corte silencioso:** cada ramo mostra até **200** itens e, se cortar, deixa o rastro `… (+N)` — índice que corta calado faz você acreditar que viu tudo (aconteceu: 25 de 36 memórias, sem aviso, e as que sumiram eram as mais novas).

**Só este projeto:** o gerador nunca lê fora da raiz escaneada — `.claude/` (onde ficam os *worktrees*, que podem ser de **outro** projeto), `.venv/`, `node_modules/` e afins são podados na descida. É a mesma fronteira "um projeto por janela" (regra crítica 8), aplicada à leitura automática. A dimensão **Conexões** fica rica à medida que o `MAPA.md` é preenchido (via `/mss-spec:mapa`).
