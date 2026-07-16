# to-dolist — caixa de captura rápida (design)

Data: 2026-07-16 · feature do próprio kit mss-spec (branch `feature/to-dolist`).

## Objetivo
Comando `/mss-spec:to-dolist` para capturar ideias/ajustes que surgem **fora do contexto** da tarefa atual, sem desviar da branch em andamento. A lista fica **visível em qualquer branch**.

## Problema
No meio de uma tarefa (ex.: lógica de negócio + banco), o dev percebe uma melhoria de OUTRO assunto (ex.: uma tela). Hoje ou faz na branch errada (polui o contexto) ou esquece. Falta uma caixa de captura leve, sempre à mão, independente de branch.

## Critérios de aceite
- DADO um projeto sem `to-dolist.md`, QUANDO rodo `/mss-spec:to-dolist adicionar comprar leite`, ENTÃO o arquivo é criado na raiz com a linha `- comprar leite (add: 2026-07-16)` e passa a estar ignorado pelo git.
- DADO itens na lista, QUANDO rodo `/mss-spec:to-dolist listar`, ENTÃO vejo os itens numerados 1..N na ordem do arquivo.
- DADO uma lista com 10 itens, QUANDO rodo `/mss-spec:to-dolist feito 7`, ENTÃO o 7º item sai do arquivo e os demais permanecem.
- DADO que estou em outra branch, QUANDO listo, ENTÃO vejo a mesma lista (o arquivo é não-rastreado e o git não o toca ao trocar de branch).
- DADO qualquer ação, ENTÃO `to-dolist.md` nunca é commitada.

## Design
- **Armazenamento:** `to-dolist.md` na raiz do PROJETO (não na pasta do plugin), listado no `.gitignore`. Por ser não-rastreado, sobrevive à troca de branch → visível em qualquer branch. Pessoal, local, não versionado.
- **Comando:** `commands/to-dolist.md`, `disable-model-invocation: true`. Ações via `$ARGUMENTS`: `adicionar <texto>` · `listar` · `feito <n>`.
- **Formato:** uma linha por item — `- <texto> (add: AAAA-MM-DD)`.

## Fora de escopo
Editar item, prazos, prioridade, arquivar concluídos, sincronizar com INDEX/nova-feature, escopo global entre projetos. É só captura rápida por-projeto.

## Arquivos tocados
- novo `commands/to-dolist.md`
- `templates/gitignore` e `.gitignore` (deste repo) ganham `to-dolist.md`
- `tests/test_smoke_kit.py` — checagem de que `to-dolist.md` está no `templates/gitignore`

## Histórico
- 2026-07-16 — criado: design da feature to-dolist (aprovado no chat).
