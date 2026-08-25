---
description: Gera o painel "anatomia de runtime" do kit — quando cada peça entra na janela (partida/evento/demanda/fecho) · matriz quem lê × quem escreve · riscos · fila — HTML self-contained com números medidos, fora do git
argument-hint: ""
---

**Responda sempre em português (pt-BR).**

Regenera o painel **anatomia de runtime** do kit neste projeto — a visão que o mapa-neural não dá: **quando** cada peça dispara na janela do assistente, **quem lê × quem escreve** cada artefato, onde mora o **risco** e o que está na **fila**. Números **medidos** na hora (manifestos, frontmatter dos comandos, `hooks.json`, rules, orçamento em bytes, `docs/EVALS.md`, MAPA/INDEX); a matriz e as classes de risco são metadado curado do kit, travado por teste de wiring.

1. **Rode o gerador** (script testável do plugin):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/templates/anatomia.py" --proj .
   ```

   Se `${CLAUDE_PLUGIN_ROOT}` não resolver, ache o script nos locais padrão (`~/.claude/plugins/cache/.../mss-spec/templates/anatomia.py` ou o clone apontado pelo junction/skills-dir) — mesmo fallback do `doctor`.

2. A saída é **`docs/anatomia.html`** — self-contained (zero CDN; proxy MSIG), **fora do git de propósito** (padrão ancorado `/docs/anatomia.html` no `.gitignore`): é retrato derivado e regenerável; retrato envelhece, o repo não. Abra no navegador e reporte o caminho + os destaques que a geração **mediu** (casos abertos do corpus, arquivo de partida acima do teto, se houver).

3. **O painel é pro humano** — o assistente continua lendo `MAPA.md`/`INDEX.md`/`memory/MEMORY.md` como fonte (regra "visual é pro humano; dados pro assistente"). Não use o HTML como insumo de decisão.

Quando rodar: sob demanda (avaliação do kit) e, se quiser o retrato sempre fresco, no fecho de release — é opcional, não faz parte do gate.
