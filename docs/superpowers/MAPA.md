# Mapa de contexto — mss-spec

## Onde estamos
`feature/um-item-por-chat` — **v0.34.0 pronta na branch** (3 commits à frente da `main` `b8267bd`, que está em dia com o `origin/main`; merge local com aprovação do owner, push da `main` é do owner). O `um_item_por_janela.py` conta **por chat**: chat novo sempre abre (outras abertas só geram aviso + worktree); o mesmo chat não abre 2ª feature enquanto a dele, achada só pelo nome, não está `fechada`/`pausada`. Três rodadas de revisão de código; suíte **676 verde** (baseline `c0eda5e`). Nasceu do bloqueio de 2026-09-24 no Whats (6 abertas travando o chat novo). Nenhuma feature aberta no INDEX.

<!-- histórico do estado anterior -->
`main` — **v0.31.1 integrada e publicada** (`edda6f3`, em dia com o `origin/main`). Nesta leva: 0.30.0 (cerca do pipe — F-025 fechado — e registro local dos hooks, `python hooks/_registro.py resumo`) · 0.31.0 (cerca de publicação **por destino**: push em main/master/dev/develop/production/homolog*/hml*/prod*/release/* e deploy negados; merge/rebase/push de feature pedem aprovação do owner) · 0.31.1 (teto do `CLAUDE.md` em 10 KB + frases-chave das regras travadas por teste). Suíte **572 verde**. Nenhuma feature aberta no INDEX.

## Próximo passo
**Integrar a 0.34.0:** `/mss-spec:release` verde → `/mss-spec:memory capturar` (OK do owner) → merge local na `main` (aprovação) → **push da `main` pelo owner**. **Canário ao vivo** (depois de o kit novo carregar): no mesmo chat `/mss-spec:nova-feature canario-a` e depois `canario-b` — o 2º bloqueia dizendo que o chat já é da `canario-a`; num chat novo o `canario-b` passa. **No Whats (janela de lá):** das 6 abertas do INDEX, as paradas viram `pausada: <motivo>` à mão (não bloqueiam mais, só poluem o aviso). Custos aceitos pra observar no `python hooks/_registro.py resumo`: bloqueio "não achei a linha dela pelo nome" quando o passo 3 grava título sem que um nome contenha o outro.

<!-- histórico do próximo passo anterior -->
**Dogfood no projeto C# (janela própria, aberta no projeto — não aqui):** `/mss-spec:analise` tem que disparar o inventário sozinho pela `<connectionStrings>`; conferir o regex do par e valor montado com `+`/`.encode()` no `get_connection.py` real usado como `--fonte`; cursor do pyodbc usável depois de falta de permissão no `msdb`; rodar duas vezes e ver o `git diff` dos `docs/banco/*.sql` vazio. Depois: item 7 do INDEX (C#/.NET), e o item 6 vira `fechada` no `INDEX-historico.md`. **No kit (janela nova):** a branch `docs/catalogo-do-kit` (`8b935a2`) nasceu antes da 0.30.0 — trazer a `main` pra ela (merge local, com aprovação) e fazer o `CATALOGO.html` citar a cerca do pipe, o registro, a cerca por destino e o teto de 10 KB, antes de integrar · `python hooks/_registro.py resumo` após algumas sessões (o recall acerta? a cerca por destino deu falso bloqueio — ex.: branch que começa com `prod`?) · F-028 aberto: reincidência zero em 3 sessões de avaliação/proposta.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-23 · regenerável com /mss-spec:mapa -->
