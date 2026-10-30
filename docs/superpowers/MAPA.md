# Mapa de contexto — mss-spec

## Onde estamos
`feature/kit-entra-primeiro` (saiu da `main` em `755ba99`) — 0.50.0 pronta na branch, por mesclar (owner): hooks `kit_primeiro.py` (superpowers só por dentro do kit) e `diario_junto.py` (memória sem diário não sai), `confere_citacoes.py` devolvendo por JSON (a devolução do Stop nunca chegava nesta máquina), lembrete de captura ligado por sessão, `templates/AMBIENTES.md` + recall por seção, diário (7 dias) e ambiente no passo 1 de `bug`/`duvida`/`diagnostico`, `doctor` 12-13. Caso F-048 fechado; suíte inteira: 1.120 verdes (rodada completa com 4 vermelhos mecânicos — contagem de hooks, versão do marketplace, histórico das regras — consertados e reexecutados).

<!-- histórico do estado anterior -->
`chore/captura-memoria-na-hora-da-proposta` (saiu da `main` em `103345b`) — captura da 0.49.0: decisão, aprendizado do arquivo CRLF e diário da sessão. A 0.49.0 (F-047: memória na hora da proposta + sintoma do owner é fato) está mesclada e enviada.

<!-- histórico do estado anterior (2) -->
`feature/memoria-na-hora-da-proposta` (saiu da `main` em `8588bca`) — 0.49.0 pronta, sem commit: F-047 fechado. Suíte 1.031 verde.

## Próximo passo
1. ⬜ **Owner: merge e push da 0.50.0** — `git switch main` · `git merge --no-ff feature/kit-entra-primeiro` · `git push origin main`.
2. ⬜ **Owner: tirar `LC_ALL=enu` das variáveis de ambiente do Windows** (ou pôr `C.UTF-8`) e reabrir o app — o `doctor` (check 12) avisa enquanto estiver assim.
3. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; nasce o `docs/AMBIENTES.md` com os nomes que o projeto já tem e `falta preencher` no resto — os valores só o owner tem.
4. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** — a tarde de 30/10 (token sem `MITI_DEV_AUTH`, push do n8n em produção não resolvido) não tem diário.
5. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando: o hook deve negar o superpowers e apontar a porta.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: merge e push da captura** — `git switch main` · `git merge --no-ff chore/captura-memoria-na-hora-da-proposta` · `git push origin main`.
2. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

<!-- histórico do próximo passo anterior (2) -->
1. ⬜ **Owner: commit, merge e push da 0.49.0** — o assistente commita com o OK; `git switch main` · `git merge --no-ff feature/memoria-na-hora-da-proposta` · `git push origin main`.
2. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; no Whats, árvore limpa antes.
3. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-30 (0.50.0 na branch feature/kit-entra-primeiro, por mesclar) · regenerável com /mss-spec:mapa -->
