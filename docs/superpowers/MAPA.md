# Mapa de contexto — mss-spec

## Onde estamos
`feature/fora-de-escopo-no-to-dolist` (saiu da `main` em `244d144`, 0.46.0, com a captura já mesclada) — **feature "fora de escopo vira item do to-dolist"** em andamento, spec `docs/specs/fora-de-escopo-no-to-dolist.md`. Desenho aprovado em 2026-10-28; formato antigo aceito como provisório até o upgrade.

<!-- histórico do estado anterior -->
`chore/captura-fora-de-escopo` (saiu da `main` em `4cbbdfb`, 0.46.0, igual ao remoto; nenhuma feature em andamento no INDEX) — **captura pronta na branch (`49317cf`); merge é do owner**: decidido que "fora de escopo" quer dizer "não agora" e vira item do `to-dolist.md` com a tag `#fora-de-escopo`, com o to-dolist no git; e que todo projeto segue o desenho do kit (o doctor aponta, o upgrade converte). Caso F-044 (texto de passagem leva premissa não conferida). Nenhum código mudou.


## Próximo passo
1. ⬜ **Feature "fora de escopo vira item do to-dolist"** — em andamento na `feature/fora-de-escopo-no-to-dolist`.
2. ⬜ **Padronizar os projetos com o desenho do kit** — o doctor aponta o que diverge, o upgrade converte; depois do item 1 (INDEX item 3).
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior -->
**Owner:** merge da `chore/captura-fora-de-escopo` na `main` e `git push origin main`; depois, conversa nova pelo **+** com o texto entregue em 2026-10-28 pra feature "fora de escopo vira item do to-dolist" (INDEX item 2). Em seguida, a padronização dos projetos (INDEX item 3). **No Whats:** janela nova pra testar o `/mss-spec:bug` sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-28 (captura do fora de escopo) · regenerável com /mss-spec:mapa -->
