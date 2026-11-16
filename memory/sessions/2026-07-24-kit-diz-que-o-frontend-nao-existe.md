# 2026-07-24 — o kit disse que o frontend "não existe" (diário retroativo)

conversa: 732c6614-8812-4e5a-a1fd-8773a9e328a8

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta). Período: 2026-07-24 a 2026-07-25.

## Conversamos
No Energy o kit disse "frontend não existe", depois "Falha ao executar a habilidade" e depois "não instalado".

## Pivôs
- A causa: `disable-model-invocation` mais o `nova-feature` sem ponte para o `/mss-spec:frontend`; o stack foi
  chutado a partir da anotação do Tailwind, que só fala do Nível 1 (fala 004).
- A troca da junção pelo marketplace caiu porque o `claude plugin list` mostrou `mss-spec@skills-dir` carregado.
- No app Desktop o painel do `/plugin` não aparece: "o autocomplete do `/plu` nem oferece" (fala 014).

## Rejeitado
Converter para marketplace (naquela data).

## Fizemos
0.13.0, 0.13.1 e 0.13.2; a anotação da intermitência; o upgrade no Energy.

## Próximo
Capturar o estado quebrado na próxima falha.
