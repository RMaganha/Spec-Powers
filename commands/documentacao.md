---
description: Gera documentação em HTML no estilo editorial MSIG (arquivo único self-contained), a partir do template padrão
argument-hint: "[tema/assunto do documento]"
disable-model-invocation: true
---

Você vai gerar um documento **HTML** sobre **$ARGUMENTS**, seguindo **exatamente** o estilo editorial MSIG.

1. Use como base `${CLAUDE_PLUGIN_ROOT}/templates/doc/template.html` — **copie-o** e trabalhe em cima. O `<head>` e o bloco `<style>` são o padrão da casa: **não os altere** (mesmas fontes Instrument Serif/Newsreader/JetBrains Mono, mesma paleta cream/rust/forest/navy, mesmas classes). Exemplo completo no estilo: `${CLAUDE_PLUGIN_ROOT}/docs/COMO-FUNCIONA.html`.
2. **Substitua só o conteúdo**: `<title>`, sidebar (`sidebar-title`/`sidebar-sub`/`nav` com âncoras), `hero` (eyebrow, h1 com `<em>`, hero-sub, hero-meta), as `section` (section-num, h2 com `<em>`, lead, parágrafos), e `foot`. Use os blocos já definidos conforme o conteúdo pedir: `callout.{danger,warn,success,info,crit}`, `node` (card com `kv`/`label-row`/`pill`), `table`, `flow`, `scorebar`, `glossary`.
3. **Regras do estilo:** títulos em Instrument Serif com uma palavra em `<em>` (rust); `section-num` numerada; nav lateral com links `#ancora` batendo nos `id` das seções; código em `<code>`/`<pre>`. Mantenha coerência com o `COMO-FUNCIONA.html`.
4. **Arquivo único, self-contained** (é a exceção à regra de separar CSS/JS — doc portável que abre direto no navegador). Salve em `docs/<nome>.html` (ou onde eu indicar). Nada de arquivos `.css`/`.js` à parte. **Exceção conhecida:** as fontes vêm do Google Fonts (CDN) — offline ou atrás de proxy bloqueando, o doc cai nos fallbacks de sistema (`Georgia`/serif, monospace) e continua legível; é aceito, não corrija embutindo fontes.
5. Ao final, confirme o caminho gerado. Se $ARGUMENTS estiver vago, pergunte o tema e o público antes de gerar.
