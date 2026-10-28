# Mapa de contexto — mss-spec

## Onde estamos
`chore/captura-fora-de-escopo` (saiu da `main` em `4cbbdfb`, 0.46.0, igual ao remoto) — **captura pronta na branch; merge é do owner**: decidido que "fora de escopo" quer dizer "não agora" e vira item do `to-dolist.md` com a tag `#fora-de-escopo`, com o to-dolist no git; e que todo projeto segue o desenho do kit (o doctor aponta, o upgrade converte). Caso F-044 (texto de passagem leva premissa não conferida). Nenhum código mudou.

<!-- histórico do estado anterior -->
`feature/nunca-worktree` (saiu da `main` em `00998bc`, 0.45.0) — **0.46.0 pronta na branch; merge é do owner**: hook novo `sem_worktree.py` + 5ª cerca do `git_publicacao.py` — nunca worktree (criar, entrar, gravar dentro) e nunca conversa aberta a partir de outra (o assistente entrega o texto pronto e o owner abre pelo +). O aviso de "outra feature aberta" parou de mandar abrir worktree: pasta na branch de outra feature → parar e perguntar. Spec `docs/specs/nunca-trabalhar-em-worktree.md`.

## Próximo passo
**Owner:** merge da `chore/captura-fora-de-escopo` na `main` e `git push origin main`; depois, conversa nova pelo **+** com o texto entregue em 2026-10-28 pra feature "fora de escopo vira item do to-dolist" (INDEX item 2). Em seguida, a padronização dos projetos (INDEX item 3). **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

<!-- histórico do próximo passo anterior -->
**Owner:** merge da `feature/nunca-worktree` na `main` e `git push origin main`; depois, conversa nova pelo **+** (a trava só carrega em conversa nova) pra 2ª feature: "Fora de escopo" quer dizer "não agora, nesta conversa", não "nunca", e o `FORA-DE-ESCOPO.md` do kit legível pela busca. **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-27 (nunca trabalhar em worktree, 0.46.0) · regenerável com /mss-spec:mapa -->
