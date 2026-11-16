# 2026-07-14 — proxy novo, plano-teste em loop e segurança AppSec (diário retroativo)

conversa: 1af707be-d89f-4b8c-a5e2-1e7d2f2da5d8

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta). Período: 2026-07-14 a 2026-07-16.

## Conversamos
O proxy mudou de IP e o build quebrou com "issuer unknown"; o plano-teste entrou em loop clicando na tela; a
segurança das aplicações expostas.

## Pivôs
- A causa do build era a CA do FortiGate novo faltando no `corp-ca.pem`, não a rota; o `config.json` do Docker
  Desktop injeta o proxy em todo build (fala 004).
- Validação de tela passa a ser só determinística (fala 008) — origem de `memory/feedback_validacao_ui_deterministica.md`.
- O owner respondeu "?" duas vezes (falas 021-022), o assistente seguiu "Escrevendo a spec agora" (fala 023) e o
  owner parou: "Não finalizamos não é para escrever a spec … está ficando confuso" (fala 024).

## Rejeitado
Criptografar URL ou asset; um `TOKEN_API` para o login de usuário; teto de 8 h.

## Fizemos
`corp-ca` com 69 certificados; UI validada só de forma determinística; `/mss-spec:seguranca` com relatório em HTML;
pt-BR fixo; regra de branch por tarefa.

## Próximo
Rodar a auditoria no MSS-SSC; bump de versão só no release.
