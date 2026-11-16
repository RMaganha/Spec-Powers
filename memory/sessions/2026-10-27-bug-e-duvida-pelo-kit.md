# 2026-10-27 — bug e dúvida pelo kit (diário retroativo)

conversa: 584b3e53-ac37-4dda-9f19-de77fd1800f5

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta).

## Conversamos
As 4 últimas conversas do Whats: a memória foi lida e o assistente cedeu quando o owner contestou.

## Pivôs
- Comandos `/mss-spec:bug` e `/mss-spec:duvida` novos e o `diagnostico` destravado, com o kit chamando o superpowers
  (fala 009) — completado depois por `docs/decisoes.md:55` e `:59`.
- O "perdido" vinha da medida com o `\r` do Windows (fala 018).
- Com a junção, o plugin segue a branch aberta na pasta do kit: os comandos novos valeram no Whats antes do merge e
  sumiram quando a pasta voltou para a `main` (falas 014, 024).
- No PowerShell do owner o `git log` mostra o acento como `d<C3><BA>vida`; o owner leu como "perdido novamente!!"
  (falas 029-030).

## Rejeitado
Nada.

## Fizemos
0.43.0 (`b2491bb`), refeita como 0.45.0 (`d152857`, merge `1d93d66`, 962 testes).

## Próximo
Provar a entrada sem digitar o comando; as capturas que ficaram no worktree.
