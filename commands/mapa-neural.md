---
description: Gera o mapa mental do projeto atual — árvore radial com o projeto no centro e 4 dimensões (arquitetura · APIs & integrações · memórias · conexões entre projetos), em HTML self-contained + índice de texto
argument-hint: "(sem argumento — usa o diretório atual)"
---

**Responda sempre em português (pt-BR).**

Você vai gerar o **mapa mental do projeto atual** — a árvore com o projeto no centro e **4 dimensões**, cada uma **extraída do repo** (o gerador só lê o que existe; **nunca inventa**):
- **Arquitetura interna** — camadas/módulos presentes (`main.py`, `routers/`, `services/`, ...);
- **APIs & integrações** — endpoints expostos (rotas FastAPI) + integrações detectadas por *import* (banco, HTTP, fila);
- **Memórias & conhecimento** — specs, índice `memory/MEMORY.md`, `docs/decisoes.md`;
- **Conexões entre projetos** — a seção **Conexões** do `docs/superpowers/MAPA.md` (o nome do vizinho é o que estiver declarado lá — declare o **nome completo** do projeto).

Duas saídas do mesmo modelo:
- **`mapa-neural.md`** — índice em texto (é o que o **assistente** consulta pra ter o todo sem reler o repo);
- **`mapa-neural.html`** — mapa radial **full-screen**, expansível (clique no `＋`) e arrastável, 100% self-contained.

1. **Ache o gerador:** `${CLAUDE_PLUGIN_ROOT}/templates/mapa_neural.py`. Se a variável não resolveu, procure em `~/.claude/plugins/cache/*/mss-spec/*/templates/mapa_neural.py`. Não achou → PARE com erro claro; nunca invente caminho.
2. **Rode no projeto atual:** `python "${CLAUDE_PLUGIN_ROOT}/templates/mapa_neural.py"` (opcional: `--proj <dir> --out <dir>`). As saídas caem em **`docs/`** por padrão (toda pasta do superpowers tem `docs/`, fica isolado da raiz; ambas gitignoradas — derivadas/regeneráveis).
3. **Reporte os dois caminhos** (absolutos). Se quiser o quadro agora, **leia o `mapa-neural.md`** e resuma as dimensões pro owner.

**Heurística, não mágica:** os endpoints saem de decorators de rota; as integrações, de linhas de `import`; a arquitetura, das pastas de camada. É uma leitura estática — se algo do projeto não aparecer (rota montada dinamicamente, integração exótica), é limitação esperada, não invenção: complete declarando na seção **Conexões** do `MAPA.md` ou ajuste o código. A dimensão **Conexões** fica rica à medida que o `MAPA.md` é preenchido (via `/mss-spec:mapa`).
