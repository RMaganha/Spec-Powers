# 2026-07-20 — redes de segurança, upgrade --dry-run e distribuição por git (diário retroativo)

conversa: 525501d7-0f31-4a6c-9d89-08964da7a4d6
conversa: f647daf7-8c27-4f98-b83e-9ac15b6e71a0
conversa: c970cbaa-f0ac-4b84-91cb-5d3e2ec15cc4

> Escrito no sono da memória de 2026-11-16 a partir do texto de três conversas curtas do mesmo dia (só as falas do
> owner e do assistente; sem saída de ferramenta).

## Conversamos
- **Redes de segurança** (525501d7): as que já existem — auto-teste, git como rollback, CHANGELOG.
- **upgrade --dry-run** (f647daf7): uma opção que não muda o comportamento sem ela.
- **Distribuição por git** (c970cbaa): instalar o kit pela URL do repositório.

## Pivôs
- Em 525501d7 o INDEX foi editado na `master` e o assistente sugeriu `git commit -am` direto nela (fala 016); em
  f647daf7, uma edição solta no INDEX foi commitada "na `master` primeiro" (fala 004) — logo depois de a regra de
  branch por tarefa nascer (2026-07-17).
- Em c970cbaa a resposta fechou com oferta não pedida (fala 006).

## Rejeitado
Comando de rollback (YAGNI).

## Fizemos
- 0.8.2: HTML, `upgrade`, `kickoff` e LEIA-ME; item 11 fechado; `docs/analise` commitada (fala 005).
- 0.8.3: `--dry-run` mostrando o diff da categoria 1; teste de ligação; merge na `master`.
- 0.8.4: allowlist no marketplace, LEIA-ME com as duas vias, URL como marcador, `dependencies` fora.

## Próximo
Publicar quando houver remoto; item 12.
