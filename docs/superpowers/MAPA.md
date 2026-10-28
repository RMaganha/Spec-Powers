# Mapa de contexto — mss-spec

## Onde estamos
`main` (`9884cf9`, igual ao remoto, 0.48.0) — nenhuma feature em andamento no INDEX. A 0.48.0 (o `/mss-spec:upgrade` converte o to-dolist e o fora de escopo; o `/mss-spec:doctor` aponta o que falta) e a captura dela estão mescladas e enviadas.

<!-- histórico do estado anterior -->
`chore/captura-upgrade-converte-to-dolist` (saiu da `main` em `6b8c34d`) — **0.48.0 mesclada e no remoto**: o `/mss-spec:upgrade` converte o to-dolist e o fora de escopo em dois tempos (original no git → prévia com a soma e 3 linhas reais → OK do owner → conversão) e o `/mss-spec:doctor` (check 10) aponta o que falta. Captura da conversa (F-045, F-046, diário) nesta branch; merge é do owner.

## Próximo passo
1. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
2. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: merge e push da captura** — `git switch main` · `git merge --no-ff chore/captura-upgrade-converte-to-dolist` · `git push origin main`.
2. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-28 (0.48.0 mesclada; /mss-spec:mapa) · regenerável com /mss-spec:mapa -->
