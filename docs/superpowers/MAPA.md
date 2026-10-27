# Mapa de contexto — mss-spec

## Onde estamos
`feature/nunca-worktree` (saiu da `main` em `00998bc`, 0.45.0) — **0.46.0 pronta na branch; merge é do owner**: hook novo `sem_worktree.py` + 5ª cerca do `git_publicacao.py` — nunca worktree (criar, entrar, gravar dentro) e nunca conversa aberta a partir de outra (o assistente entrega o texto pronto e o owner abre pelo +). O aviso de "outra feature aberta" parou de mandar abrir worktree: pasta na branch de outra feature → parar e perguntar. Spec `docs/specs/nunca-trabalhar-em-worktree.md`.

<!-- histórico do estado anterior -->
`chore/captura-limpeza-worktree` (saiu da `main` em `1d93d66`, 0.45.0, igual ao remoto) — **captura pronta na branch; merge é do owner**: das 2 capturas da `feature/partida-em-dois-niveis` entrou só o útil (memória "explicar com item real, antes e depois", 2 acréscimos em memórias, reincidência do F-033). Ficaram fora o F-042 (a decisão de 23/10 foi lida às 10:31 e desrespeitada às 10:36: a regra de "procurar o nome do arquivo" não resolveria) e o F-043. O worktree e a branch dele foram apagados: o owner não usa worktree.

## Próximo passo
**Owner:** merge da `feature/nunca-worktree` na `main` e `git push origin main`; depois, conversa nova pelo **+** (a trava só carrega em conversa nova) pra 2ª feature: "Fora de escopo" quer dizer "não agora, nesta conversa", não "nunca", e o `FORA-DE-ESCOPO.md` do kit legível pela busca. **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

<!-- histórico do próximo passo anterior -->
**Owner:** merge da `chore/captura-limpeza-worktree` na `main` e `git push origin main`. Depois, uma feature por conversa, na pasta principal e sem worktree: (1) nunca trabalhar em worktree; (2) "Fora de escopo" quer dizer "não agora, nesta conversa", não "nunca", e o `FORA-DE-ESCOPO.md` do kit legível pela busca. **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-27 (nunca trabalhar em worktree, 0.46.0) · regenerável com /mss-spec:mapa -->
