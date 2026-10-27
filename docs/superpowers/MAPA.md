# Mapa de contexto — mss-spec

## Onde estamos
`feature/bug-e-duvida-045` (saiu da `main` em `a394191`, 0.44.0) — **0.45.0 pronta na branch; merge é do owner**: a 0.43.0 (`b2491bb`, `feature/bug-e-duvida`) ficou fora da `main` quando a 0.44.0 foi integrada e foi reaplicada por cima dela — `/mss-spec:bug` e `/mss-spec:duvida` novos, `/mss-spec:diagnostico` destravado e chamado pelo `bug`, regra 11 aponta pro `bug`, regra "memória contestada → mostre a memória". Spec `docs/specs/bug-e-duvida.md`.

<!-- histórico do estado anterior -->
`feature/partida-em-dois-niveis` (worktree `.claude/worktrees/partida-em-dois-niveis`, saiu da `main` em `7948da0`) — **0.44.0 pronta na branch; merge é do owner**: a forma do MAPA e do INDEX vale em toda gravação, mesmo abaixo do teto (`fechada` sai do INDEX; item longo do Próximo passo vai pro `PROXIMO-PASSO.md`; com `CONEXOES.md`, Conexões só com os nomes). Simulado numa cópia do Whats: MAPA 5.981 → 2.254 B, INDEX 5.635 → 2.424 B, nenhuma linha perdida. `CLAUDE.md` fora (decisão do owner). A `feature/bug-e-duvida` (0.43.0) segue não integrada.

## Próximo passo
**Owner:** merge da `feature/bug-e-duvida-045` (0.45.0) na `main` e `git push origin main`; depois apagar a `feature/bug-e-duvida` (o `b2491bb` já está reaplicado). Pendente da 0.44.0: as 2 capturas da `feature/partida-em-dois-niveis` (`aef098f`, `714f3a9`) e o worktree dela. **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

<!-- histórico do próximo passo anterior -->
**Owner:** merge da `feature/bug-e-duvida` (0.43.0) e depois da `feature/partida-em-dois-niveis` (0.44.0) na `main`, e `git push origin main`. **No Whats (janela de lá):** qualquer gravação no MAPA ou no INDEX já aplica a forma; pra aplicar de uma vez, `/mss-spec:mapa`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-27 (partida em dois níveis, 0.44.0) · regenerável com /mss-spec:mapa -->
