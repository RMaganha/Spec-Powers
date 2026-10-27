# Mapa de contexto — mss-spec

## Onde estamos
`chore/captura-limpeza-worktree` (saiu da `main` em `1d93d66`, 0.45.0, igual ao remoto) — **captura pronta na branch; merge é do owner**: das 2 capturas da `feature/partida-em-dois-niveis` entrou só o útil (memória "explicar com item real, antes e depois", 2 acréscimos em memórias, reincidência do F-033). Ficaram fora o F-042 (a decisão de 23/10 foi lida às 10:31 e desrespeitada às 10:36: a regra de "procurar o nome do arquivo" não resolveria) e o F-043. O worktree e a branch dele foram apagados: o owner não usa worktree.

<!-- histórico do estado anterior -->
`feature/bug-e-duvida-045` (saiu da `main` em `a394191`, 0.44.0) — **0.45.0 pronta na branch; merge é do owner**: a 0.43.0 (`b2491bb`, `feature/bug-e-duvida`) ficou fora da `main` quando a 0.44.0 foi integrada e foi reaplicada por cima dela — `/mss-spec:bug` e `/mss-spec:duvida` novos, `/mss-spec:diagnostico` destravado e chamado pelo `bug`, regra 11 aponta pro `bug`, regra "memória contestada → mostre a memória". Spec `docs/specs/bug-e-duvida.md`.

## Próximo passo
**Owner:** merge da `chore/captura-limpeza-worktree` na `main` e `git push origin main`. Depois, uma feature por conversa, na pasta principal e sem worktree: (1) nunca trabalhar em worktree; (2) "Fora de escopo" quer dizer "não agora, nesta conversa", não "nunca", e o `FORA-DE-ESCOPO.md` do kit legível pela busca. **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

<!-- histórico do próximo passo anterior -->
**Owner:** merge da `feature/bug-e-duvida` (0.43.0) e depois da `feature/partida-em-dois-niveis` (0.44.0) na `main`, e `git push origin main`. **No Whats (janela de lá):** qualquer gravação no MAPA ou no INDEX já aplica a forma; pra aplicar de uma vez, `/mss-spec:mapa`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-27 (partida em dois níveis, 0.44.0) · regenerável com /mss-spec:mapa -->
