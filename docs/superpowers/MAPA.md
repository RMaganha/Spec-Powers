# Mapa de contexto — mss-spec

## Onde estamos
`feature/inventario-do-banco-vivo` — **v0.28.0 pronta na branch; merge/push são do owner.** Suíte **452 verde** (era 336). Entregue: `templates/inventario_banco.py` (4º gerador: somente-leitura, só catálogo, par Fernet reaproveitado lido por `ast` + `--base`/`--par`, cruzamento citado/só-no-banco/sem citação, corpos versionados com segredo mascarado no corpo inteiro, marca de autoria) · `/mss-spec:inventario-banco` · passo automático na `analise` · `COMO-FUNCIONA.html` com 25 cards e contagem travada. **Não validado contra banco real.** Spec: `docs/specs/inventario-banco.md`; plano em `plans/2026-09-22-inventario-banco.md`.

<!-- histórico do estado anterior -->
`main` — **v0.27.0 integrada e publicada pelo owner** (merge `8589085` de `feature/orcamento-de-partida-e-recall`; `doctor` confirma local = `origin/main`). Suíte **336 verde** (era 289). **Aplicada no Whats** em janela própria (3 commits por script, nada editado à mão): partida 190 → 108 KB; hooks confirmados carregando pela junction. Nasceu de uma sessão cara no projeto Whats: o kit mandou **podar** um índice de memória de 25 KB alegando "acima disso o excedente não carrega" — premissa da pasta **nativa**, falsa pro índice do repo (caso **F-024**); e o índice era 12% da partida (~214 KB ≈ 53 mil tokens por janela). Entregue: **índice em dois níveis** (`templates/memoria_indice.py` dividir/verificar/fila/buscar; topo 6 KB travado por teste; o kit já dividido: 8.694 → 2.976 B) · **`hooks/recall_memoria.py`** (UserPromptSubmit, injeta ≤ 600 B de ponteiros que casam com o prompt; não bloqueia; falha aberta) · **`templates/rodizio_partida.py`** mapa/index (move pro histórico, dry-run, conservação) · texto corrigido no molde, `memory`, `doctor` (aponta o comando exato), `upgrade`. Spec: `docs/superpowers/specs/2026-09-15-orcamento-de-partida-e-recall-deterministico-design.md`; plano ao lado em `plans/`.

## Próximo passo
**Dogfood no projeto C# (janela própria, aberta no projeto — não aqui):** `/mss-spec:analise` tem que disparar o inventário sozinho pela `<connectionStrings>`; conferir o regex do par e valor montado com `+`/`.encode()` no `get_connection.py` real usado como `--fonte`; cursor do pyodbc usável depois de falta de permissão no `msdb`; rodar duas vezes e ver o `git diff` dos `docs/banco/*.sql` vazio. Depois: item 7 do INDEX (C#/.NET), e o item 6 vira `fechada` no `INDEX-historico.md`.

<!-- histórico do próximo passo anterior -->
**Fila de conteúdo do Whats, uma janela por item, sem prazo** (é o que ainda estoura lá: 108 KB de partida contra ~33 KB de teto): 77 memórias sem `gatilho:` (`memoria_indice.py fila`, por família, com rascunho pro OK) · `CLAUDE.md` de 27 KB → 8 KB (mover procedimento pra comando/`.claude/rules/`) · 39 itens abertos no INDEX (decidir o que é `pausada:`) · bloco atual do MAPA (24 KB). **No kit:** observar o recall em uso por algumas sessões (F-025 fica aberto até reincidência zero ou cerca) · podar os 5 comandos grandes (~45 KB) com teto por bytes e teste · item 5 do INDEX (`upgrade — em andamento`) ainda conta como aberto pro hook `um_item_por_janela`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-22 · regenerável com /mss-spec:mapa -->
