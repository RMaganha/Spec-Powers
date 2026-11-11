---
name: feedback-medir-antes-de-afirmar-ganho
description: Proposta de melhoria de custo/desempenho/qualidade começa pela MEDIÇÃO do estado atual — número primeiro, peça depois
gatilho: quando propor melhoria de custo, desempenho ou qualidade
metadata:
  node_type: memory
  type: feedback
---

Antes de propor qualquer melhoria de **custo, desempenho ou qualidade**, **meça o estado atual e
mostre o número**. A medição não é enfeite do argumento: é o que decide **quais** peças existem.

**Why:** 2026-08-18. A queixa era vaga ("falta context engineering"). Medir levou 2 minutos e mudou
tudo: `templates/CLAUDE.md` custava **17.920 bytes (~4.343 tokens) em toda sessão de todo projeto** e
o ritual de partida somava **~13.000 tokens** — com **79% do `MAPA.md`** em blocos de histórico
relidos a cada vez. Sem esses três números eu teria escrito conselho genérico sobre "manter o contexto
enxuto"; com eles, saíram 5 peças concretas e um resultado verificável (**−51%** na partida). Vale a
mesma lição do achado anterior desta sessão: as **6 de 33 entradas** do índice nativo.

**How to apply:** meça **antes** de desenhar, com o comando mais bobo que der (`wc -c`, contar
ocorrências, somar tamanhos) e ponha o **antes × depois** numa tabela. Depois transforme o teto em
**teste** — número sem teste volta a subir na semana seguinte. E se o teto que você mesmo definiu
apertar, a pergunta certa é "o que aqui ainda é procedimento?" e não "quanto posso cortar": mexer no
teto pra caber é aceitável **só** quando o corte restante apagaria guardrail — e aí escreva o porquê
junto do número.

**Corolário (2026-09-23, F-028):** medir inclui **localizar**. Antes de dizer "o guardrail X teria
pegado o caso Y", abra o caso e veja *em que momento* ele falhou (commit? release? deploy?); antes de
citar o custo de um comando do kit, leia o `commands/<x>.md`. Os dois levam minutos — e sem eles eu
vendi "release em script" pra um problema que acontece na hora do commit.

Parente de [[feedback-pesquisar-fonte-primaria-antes-de-desenhar]] e de
[[feedback-item-de-backlog-nao-e-design]].

**Reincidiu (2026-11-10, F-054) — uma medição não é conclusão.** No teste de mesa da memória em tabela concluí
de **1 caso** (escolhido por mim, sabendo a resposta) que "resumir o pedido acha melhor"; com 310 casos piorou.
O owner: *"voce está assumindo esse 1 teste como verdade absoluta!"*. Passa a valer: conclusão só com **mais de
um caso de resposta conhecida**, com o **defeito do gabarito dito** e a **alternativa medida ao lado**; e a
medida se repete por projeto e por metade dos casos antes de virar afirmação. **O que deu certo na mesma
sessão:** quando o owner perguntou *"mas assim não seria melhor para dividir e buscar?"* e *"talvez … buscar 30
e depois … tirando 10 … o que acha?"*, a resposta foi **medir na mesma régua** em vez de opinar — várias tabelas
não ganharam; escolher 10 entre 30 melhorou. Régua: `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`.
