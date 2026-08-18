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
junto do número. Parente de [[feedback-pesquisar-fonte-primaria-antes-de-desenhar]] e de
[[feedback-item-de-backlog-nao-e-design]].
