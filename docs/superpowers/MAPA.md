# Mapa de contexto — mss-spec

## Onde estamos
`feature/alerta-de-contexto` — **v0.29.0 pronta na branch; merge/push são do owner.** Suíte **469 verde**. Entregue: `hooks/alerta_contexto.py` (UserPromptSubmit + PostToolUse, avisa em 75/85/95% pela `usage` do transcript, não bloqueia) + prosa "bola de neve" (entender = subagente, mexer = to-dolist) no `CLAUDE.md`/`to-dolist`/`nova-feature`. **Não validado numa sessão nova** (recarregar e ver o aviso chegar). Spec: `docs/specs/alerta-de-contexto.md`.

<!-- histórico do estado anterior -->
`feature/inventario-do-banco-vivo` — **v0.28.0 pronta na branch; merge/push são do owner.** Suíte **452 verde** (era 336). Entregue: `templates/inventario_banco.py` (4º gerador: somente-leitura, só catálogo, par Fernet reaproveitado lido por `ast` + `--base`/`--par`, cruzamento citado/só-no-banco/sem citação, corpos versionados com segredo mascarado no corpo inteiro, marca de autoria) · `/mss-spec:inventario-banco` · passo automático na `analise` · `COMO-FUNCIONA.html` com 25 cards e contagem travada. **Não validado contra banco real.** Spec: `docs/specs/inventario-banco.md`; plano em `plans/2026-09-22-inventario-banco.md`.

## Próximo passo
**Dogfood no projeto C# (janela própria, aberta no projeto — não aqui):** `/mss-spec:analise` tem que disparar o inventário sozinho pela `<connectionStrings>`; conferir o regex do par e valor montado com `+`/`.encode()` no `get_connection.py` real usado como `--fonte`; cursor do pyodbc usável depois de falta de permissão no `msdb`; rodar duas vezes e ver o `git diff` dos `docs/banco/*.sql` vazio. Depois: item 7 do INDEX (C#/.NET), e o item 6 vira `fechada` no `INDEX-historico.md`.

<!-- histórico do próximo passo anterior -->
**Fila de conteúdo do Whats, uma janela por item, sem prazo** (é o que ainda estoura lá: 108 KB de partida contra ~33 KB de teto): 77 memórias sem `gatilho:` (`memoria_indice.py fila`, por família, com rascunho pro OK) · `CLAUDE.md` de 27 KB → 8 KB (mover procedimento pra comando/`.claude/rules/`) · 39 itens abertos no INDEX (decidir o que é `pausada:`) · bloco atual do MAPA (24 KB). **No kit:** observar o recall em uso por algumas sessões (F-025 fica aberto até reincidência zero ou cerca) · podar os 5 comandos grandes (~45 KB) com teto por bytes e teste · item 5 do INDEX (`upgrade — em andamento`) ainda conta como aberto pro hook `um_item_por_janela`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-22 · regenerável com /mss-spec:mapa -->
