# Mapa de contexto — mss-spec

## Onde estamos
`main` — **0.47.0 mesclada (`44fb347`) e no remoto**; a captura da feature (diário, INDEX, MAPA) está num commit local na `main`, push é do owner: "fora de escopo" = "não agora", uma linha `#fora-de-escopo` no `to-dolist.md` (no git); a busca automática não lê mais; 61 itens do kit convertidos; formato antigo dos outros projetos aceito como provisório até o upgrade. Spec `docs/specs/fora-de-escopo-no-to-dolist.md`.

<!-- histórico do estado anterior -->
`feature/fora-de-escopo-no-to-dolist` (saiu da `main` em `244d144`, 0.46.0, com a captura já mesclada) — **feature "fora de escopo vira item do to-dolist"** em andamento, spec `docs/specs/fora-de-escopo-no-to-dolist.md`. Desenho aprovado em 2026-10-28; formato antigo aceito como provisório até o upgrade.

## Próximo passo
1. ⬜ **Owner: push da captura da 0.47.0** — `git push origin main`.
2. ⬜ **Padronizar os projetos com o desenho do kit** — o doctor aponta o que diverge, o upgrade converte (INDEX item 3).
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Feature "fora de escopo vira item do to-dolist"** — em andamento na `feature/fora-de-escopo-no-to-dolist`.
2. ⬜ **Padronizar os projetos com o desenho do kit** — o doctor aponta o que diverge, o upgrade converte; depois do item 1 (INDEX item 3).
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-28 (0.47.0, fora de escopo no to-dolist) · regenerável com /mss-spec:mapa -->
