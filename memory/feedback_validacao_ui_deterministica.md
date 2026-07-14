---
name: feedback-validacao-ui-deterministica
description: Nunca validar UI dirigindo o browser ao vivo (clicar/screenshot em loop); tela = teste determinístico e smoke visual = humano
metadata:
  type: feedback
---

Validação de tela (UI) é **só determinística**: rota via `TestClient` (HTML 200 com os
elementos esperados) e, se indispensável, teste **Playwright roteirizado com asserts** (alvo por
`data-*`/nome acessível, dentro da suíte). O assistente **NUNCA** valida UI dirigindo o browser ao
vivo — nada de clicar/tirar screenshot em loop. Qualquer "smoke manual" é roteiro para **👤 humano**,
não tarefa do assistente.

**Why:** num piloto (MSS-SSC, 2026-07-14) o agente pegou o "smoke manual" do `PLANO-TESTE.md` e foi
clicar na tela: sem seletor estável clicava errado; em fluxo destrutivo (criar→excluir→recriar)
desfazia e refazia; e sem critério observável **julgava como falha algo que já tinha passado** →
~30 min em loop, com o owner assistindo até parar na mão. Cliques ao vivo do agente não são
repetíveis nem confiáveis como verificação.

**How to apply:** verificação anti-regressão = rodar o `pytest` do `PLANO-TESTE.md` **direto** e colar
a saída (100% verde). Cobertura de tela nasce como teste de rota; e2e real vira Playwright roteirizado.
Se alguém pedir "valida a tela", escreva/rode um teste — não abra o browser pra clicar. Ver também
[[feedback-nivel-cerimonia-velocidade]] e o comando `plano-teste` (é `disable-model-invocation`: o
modelo roda o pytest direto; o slash-command quem dispara é o humano, pra regravar o baseline).
