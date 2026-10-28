# Mapa de contexto — mss-spec

## Onde estamos
`feature/upgrade-converte-to-dolist` (saiu da `main` em `41830b5`, 0.47.0) — **feature "upgrade converte o fora de escopo e o to-dolist"** em andamento, mesma conversa da 0.47.0; desenho aprovado em 2026-10-28 (recado vira 1 linha com o título da seção, texto do fora de escopo inteiro, riscado/FEITO vai pra lista do fim; to-dolist salvo no git como está antes de converter).

<!-- histórico do estado anterior -->
`main` — **0.47.0 mesclada (`44fb347`) e no remoto**; a captura da feature (diário, INDEX, MAPA) está num commit local na `main`, push é do owner: "fora de escopo" = "não agora", uma linha `#fora-de-escopo` no `to-dolist.md` (no git); a busca automática não lê mais; 61 itens do kit convertidos; formato antigo dos outros projetos aceito como provisório até o upgrade. Spec `docs/specs/fora-de-escopo-no-to-dolist.md`.

## Próximo passo
1. ⬜ **Feature "upgrade converte o fora de escopo e o to-dolist"** — em andamento na `feature/upgrade-converte-to-dolist`.
2. ⬜ **Depois de publicada: `/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: push da captura da 0.47.0** — `git push origin main`.
2. ⬜ **Padronizar os projetos com o desenho do kit** — o doctor aponta o que diverge, o upgrade converte (INDEX item 3).
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-28 (0.47.0, fora de escopo no to-dolist) · regenerável com /mss-spec:mapa -->
