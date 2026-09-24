# Mapa de contexto — mss-spec

## Onde estamos
`feature/um-item-por-chat` — **0.34.0 em construção**: o `um_item_por_janela.py` passa a contar por chat (`session_id`); chat novo abre e só avisa das outras abertas (worktree). Nasceu do bloqueio de 2026-09-24 no Whats (6 abertas travando o chat novo).

<!-- histórico do estado anterior -->
`main` — **v0.31.1 integrada e publicada** (`edda6f3`, em dia com o `origin/main`). Nesta leva: 0.30.0 (cerca do pipe — F-025 fechado — e registro local dos hooks, `python hooks/_registro.py resumo`) · 0.31.0 (cerca de publicação **por destino**: push em main/master/dev/develop/production/homolog*/hml*/prod*/release/* e deploy negados; merge/rebase/push de feature pedem aprovação do owner) · 0.31.1 (teto do `CLAUDE.md` em 10 KB + frases-chave das regras travadas por teste). Suíte **572 verde**. Nenhuma feature aberta no INDEX.

## Próximo passo
**Dogfood no projeto C# (janela própria, aberta no projeto — não aqui):** `/mss-spec:analise` tem que disparar o inventário sozinho pela `<connectionStrings>`; conferir o regex do par e valor montado com `+`/`.encode()` no `get_connection.py` real usado como `--fonte`; cursor do pyodbc usável depois de falta de permissão no `msdb`; rodar duas vezes e ver o `git diff` dos `docs/banco/*.sql` vazio. Depois: item 7 do INDEX (C#/.NET), e o item 6 vira `fechada` no `INDEX-historico.md`. **No kit (janela nova):** a branch `docs/catalogo-do-kit` (`8b935a2`) nasceu antes da 0.30.0 — trazer a `main` pra ela (merge local, com aprovação) e fazer o `CATALOGO.html` citar a cerca do pipe, o registro, a cerca por destino e o teto de 10 KB, antes de integrar · `python hooks/_registro.py resumo` após algumas sessões (o recall acerta? a cerca por destino deu falso bloqueio — ex.: branch que começa com `prod`?) · F-028 aberto: reincidência zero em 3 sessões de avaliação/proposta.

<!-- histórico do próximo passo anterior -->
**Fila de conteúdo do Whats, uma janela por item, sem prazo** (é o que ainda estoura lá: 108 KB de partida contra ~33 KB de teto): 77 memórias sem `gatilho:` (`memoria_indice.py fila`, por família, com rascunho pro OK) · `CLAUDE.md` de 27 KB → 8 KB (mover procedimento pra comando/`.claude/rules/`) · 39 itens abertos no INDEX (decidir o que é `pausada:`) · bloco atual do MAPA (24 KB). **No kit:** observar o recall em uso por algumas sessões (F-025 fica aberto até reincidência zero ou cerca) · podar os 5 comandos grandes (~45 KB) com teto por bytes e teste · item 5 do INDEX (`upgrade — em andamento`) ainda conta como aberto pro hook `um_item_por_janela`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-23 · regenerável com /mss-spec:mapa -->
