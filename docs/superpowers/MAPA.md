# Mapa de contexto — mss-spec

## Onde estamos
`feature/memoria-na-hora-da-proposta` (saiu da `main` em `8588bca`) — 0.49.0 pronta, sem commit: F-047 fechado (a resposta que propõe mudança em build, peça nova, variável ou proxy volta uma vez com as memórias do tema que não cita; "não se perdeu" contra o relato do owner volta). Suíte 1.031 verde.

<!-- histórico do estado anterior -->
`feature/memoria-na-hora-da-proposta` (saiu da `main` em `8588bca`) — F-047 aberto: testes → conferência no `confere_citacoes.py` → medir em respostas reais antes de ligar.

## Próximo passo
1. ⬜ **Owner: commit, merge e push da 0.49.0** — o assistente commita com o OK; `git switch main` · `git merge --no-ff feature/memoria-na-hora-da-proposta` · `git push origin main`.
2. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior -->
1. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
2. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-29 (0.49.0 pronta na branch; fecho do nova-feature) · regenerável com /mss-spec:mapa -->
