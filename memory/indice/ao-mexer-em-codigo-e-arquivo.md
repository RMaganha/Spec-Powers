# Ao mexer em código e arquivo

- **quando criar ou editar HTML, CSS ou JS de aplicação** → [Front-end: Tailwind + arquivos separados](../feedback_frontend_tailwind_arquivos_separados.md) — nada inline (exceto doc standalone)
- **quando gerar HTML com JS inline** → [Testar o JS gerado com `node --check`](../feedback_testar_js_gerado_node_check.md) — substring verde não pega erro de parse (a tela branca)
- **quando chamar processo externo por subprocess no Windows** → [`text=True` quebra a chamada ao git](../project_subprocess_texto_windows_quebra_git.md) — use bytes + `-z`
- **quando escrever código que parseia `.md` do kit** → [Descartar comentário; placeholder só em campo curto](../project_parse_md_do_kit_descartar_comentario.md) — filtro `<…>` na linha inteira engole texto real
- **quando gravar conteúdo levantado do projeto num arquivo de doc** → [Categoria 1 do upgrade sobrescreve](../project_upgrade_categoria1_sobrescreve.md) — o levantado vai pro `ARQUITETURA.md`
