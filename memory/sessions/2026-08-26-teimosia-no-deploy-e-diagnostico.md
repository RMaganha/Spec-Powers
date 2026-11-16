# 2026-08-26 — teimosia no deploy e o comando diagnostico (diário retroativo)

conversa: dc9685cd-5fdd-46f2-9488-986ce7e83d52

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta).

## Conversamos
O PDF de uma conversa do MSS-SSC: 6 rodadas de erro 503 com o assistente teimando.

## Pivôs
- O "só registrar no EVALS" foi derrubado pelo owner (fala 003).
- A regra sempre ativa foi posta à prova e entrou o comando acionado pelo owner (fala 006).

## Rejeitado
Só registrar no EVALS.

## Fizemos
0.23.0: regra crítica 11, `/mss-spec:diagnostico`, a anotação `feedback_diagnostico_disciplinado` e o caso F-015;
merge e push a pedido do owner.

## Próximo
Rodar o upgrade no MSS-SSC numa janela própria (o assistente recusou fazer daqui, fala 014).
