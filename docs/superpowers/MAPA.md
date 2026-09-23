# Mapa de contexto — mss-spec

## Onde estamos
`feature/hooks-cerca-pipe-e-registro` — **v0.30.0 pronta na branch; merge/push são do owner.** Suíte **530 verde** (era 472). Entregue: cerca do pipe no `hooks/git_publicacao.py` (pytest em pipe antes do `git commit` → nega; F-025 fechado) + `hooks/_registro.py` (os 6 hooks anotam em `~/.claude/mss-spec/registro-hooks.jsonl` quando agem; `python hooks/_registro.py resumo`). As duas cercas negaram ao vivo nesta sessão e o registro gravou a linha. A branch `docs/catalogo-do-kit` (`8b935a2`, CATALOGO.html) segue fora da `main` — o CATALOGO precisa citar a cerca do pipe e o registro depois que as duas entrarem. Specs: `docs/specs/travas-um-item-por-janela.md` (4) e `docs/specs/registro-dos-hooks.md`.

<!-- histórico do estado anterior -->
`fix/alerta-contexto-janela-1m` — **v0.29.1 pronta na branch; merge/push são do owner** (0.29.0 já integrada). Fix: família 5 = janela de 1M (F-027). Suíte **472 verde**. Entregue: `hooks/alerta_contexto.py` (UserPromptSubmit + PostToolUse, avisa em 75/85/95% pela `usage` do transcript, não bloqueia) + prosa "bola de neve" (entender = subagente, mexer = to-dolist) no `CLAUDE.md`/`to-dolist`/`nova-feature`. **Não validado numa sessão nova** (recarregar e ver o aviso chegar). Spec: `docs/specs/alerta-de-contexto.md`.

## Próximo passo
**Dogfood no projeto C# (janela própria, aberta no projeto — não aqui):** `/mss-spec:analise` tem que disparar o inventário sozinho pela `<connectionStrings>`; conferir o regex do par e valor montado com `+`/`.encode()` no `get_connection.py` real usado como `--fonte`; cursor do pyodbc usável depois de falta de permissão no `msdb`; rodar duas vezes e ver o `git diff` dos `docs/banco/*.sql` vazio. Depois: item 7 do INDEX (C#/.NET), e o item 6 vira `fechada` no `INDEX-historico.md`. **No kit, depois do merge da 0.30.0:** `python hooks/_registro.py resumo` após algumas sessões (o recall acerta? alguma cerca deu falso bloqueio?) e atualizar o CATALOGO quando `docs/catalogo-do-kit` entrar.

<!-- histórico do próximo passo anterior -->
**Fila de conteúdo do Whats, uma janela por item, sem prazo** (é o que ainda estoura lá: 108 KB de partida contra ~33 KB de teto): 77 memórias sem `gatilho:` (`memoria_indice.py fila`, por família, com rascunho pro OK) · `CLAUDE.md` de 27 KB → 8 KB (mover procedimento pra comando/`.claude/rules/`) · 39 itens abertos no INDEX (decidir o que é `pausada:`) · bloco atual do MAPA (24 KB). **No kit:** observar o recall em uso por algumas sessões (F-025 fica aberto até reincidência zero ou cerca) · podar os 5 comandos grandes (~45 KB) com teto por bytes e teste · item 5 do INDEX (`upgrade — em andamento`) ainda conta como aberto pro hook `um_item_por_janela`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-22 · regenerável com /mss-spec:mapa -->
