---
description: Trilho disciplinado de diagnóstico — corta o loop de hipóteses; diff contra o precedente que funciona ANTES de pedir evidência ao owner; fato do owner não se re-litiga
argument-hint: "[sintoma: ex. 503 na nuvem, conexão que não fecha, teste vermelho sem causa]"
disable-model-invocation: true
---

Trilho de diagnóstico pra falha que **não fecha** — o owner invoca quando vê o assistente em loop
("teimoso"), e o assistente **auto-propõe** ao bater a regra crítica de diagnóstico do `CLAUDE.md`
(2 rodadas sem causa). Sintoma em foco: **$ARGUMENTS**.

Origem (por que este comando existe): 2026-08-26, deploy do MSS-SSC na Azure — **6 rodadas de owner
perdidas num 503** listando hipóteses de plataforma, quando um diff contra o projeto de referência
(que o owner tinha apontado desde o início) achava a causa em minutos: caminho relativo no `main.py`
matava o processo no import. Mais 2 rodadas re-litigando uma App Setting **correta** quando a resposta
era "reiniciar" (o processo rodava com config velha). O detector de loop mais confiável foi o owner —
este comando é a alavanca dele; a regra crítica é a do assistente.

## O trilho (na ordem; não pule)

**0. Pare o loop.** Nada de nova hipótese nem novo pedido de evidência até cumprir os passos abaixo.
Invoque `superpowers:systematic-debugging` (skill invocável de verdade) e siga a disciplina dela.

**1. Tabela de fatos do owner.** Liste o que o owner **afirmou** nesta conversa (valor conferido,
"funciona em X", print colado). **Fato afirmado pelo owner não se re-litiga**: se a sua leitura da
evidência contradiz um fato dele, a sua tarefa é achar a explicação **compatível com os dois** (ex.:
valor certo no Portal + placeholder no log = processo com configuração velha → **reiniciar**), não
provar que ele está errado.

**2. Precedente primeiro.** Existe projeto/versão/ambiente onde isso **funciona**? (Não sabe qual?
Rode `/mss-spec:precedentes` ou pergunte.) Então o próximo passo é o **diff completo contra ele,
artefato por artefato — incluindo o código de boot/entrypoint (`main.py`, CMD, startup), não só
infra** (pipeline, Dockerfile, variáveis). O diff acha a causa **sem** precisar da hipótese certa.
O precedente é **SOMENTE-LEITURA** (a âncora não migra): bug visto lá, reporte, **não conserte**.

**3. Reproduza a condição REAL.** "Testei local e passou" só prova algo se o teste reproduz as
condições do ambiente que falha: **CWD** do processo, variáveis ausentes/vazias, usuário, rede,
comando de subida exato. Antes de declarar "o problema não está no código", **nomeie por escrito**
cada diferença entre o seu teste e o ambiente real — cada uma é uma hipótese viva.

**4. Economia de rodadas.** Cada "me manda o log/print" custa uma ida do owner ao Portal/terminal —
é o recurso mais caro do diagnóstico. Antes de pedir qualquer evidência: (a) liste o que você ainda
**não** comparou/testou sozinho (se a lista não está vazia, faça isso primeiro); (b) o pedido carrega
**um teste que discrimina** — separa metades do espaço de causas de uma vez — nunca uma lista de
hipóteses pro owner testar uma a uma.

**5. Fecho.** Causa fechada → registre a armadilha (sintoma → causa → correção) na doc/spec do
assunto. Se o assistente alongou o loop (hipótese repetida, fato do owner contestado, diff adiado),
isso é caso pro `docs/EVALS.md` — a falha do processo também se registra, não só a do sistema.
