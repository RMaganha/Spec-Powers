# Mapa de contexto — mss-spec

## Onde estamos
`chore/captura-upgrade-converte-to-dolist` (saiu da `main` em `6b8c34d`) — **0.48.0 mesclada e no remoto**: o `/mss-spec:upgrade` converte o to-dolist e o fora de escopo em dois tempos (original no git → prévia com a soma e 3 linhas reais → OK do owner → conversão) e o `/mss-spec:doctor` (check 10) aponta o que falta. Captura da conversa (F-045, F-046, diário) nesta branch; merge é do owner.

<!-- histórico do estado anterior -->
`feature/upgrade-converte-to-dolist` (saiu da `main` em `41830b5`, 0.47.0) — **feature "upgrade converte o fora de escopo e o to-dolist"** em andamento, mesma conversa da 0.47.0; desenho aprovado em 2026-10-28 (recado vira 1 linha com o título da seção, texto do fora de escopo inteiro, riscado/FEITO vai pra lista do fim; to-dolist salvo no git como está antes de converter).

## Próximo passo
1. ⬜ **Owner: merge e push da captura** — `git switch main` · `git merge --no-ff chore/captura-upgrade-converte-to-dolist` · `git push origin main`.
2. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Feature "upgrade converte o fora de escopo e o to-dolist"** — em andamento na `feature/upgrade-converte-to-dolist`.
2. ⬜ **Depois de publicada: `/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-28 (0.48.0, o upgrade converte o to-dolist) · regenerável com /mss-spec:mapa -->
