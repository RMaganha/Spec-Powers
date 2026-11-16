# 2026-09-14 — sessão perdida e travas de publicação (diário retroativo)

conversa: 68ed196a-88fc-46e5-8b7b-cd17bfadc74e

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta).

## Conversamos
A conversa de outro projeto em que o assistente fez push e o deploy quebrou a homologação.

## Pivôs
- Prosa não segura: a trava precisa ser mecânica (fala 006); o owner pediu "regra extremamente dura" (fala 005).

## Rejeitado
Só endurecer a prosa; tirar a credencial do assistente.

## Fizemos
0.26.0: `hooks/git_publicacao.py`, `hooks/um_item_por_janela.py`, casos F-022 e F-023; merge a pedido do owner.
Decisão em `docs/decisoes.md:32`.

## Próximo
Rollback e bissecção da homologação numa janela própria; canário dos hooks.
