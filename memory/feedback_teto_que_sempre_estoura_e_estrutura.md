---
name: feedback-teto-que-sempre-estoura-e-estrutura
description: Teto que estoura em todo projeto é sinal de estrutura errada, não de número baixo — meça o que é comum a todos antes de propor subir o teto
gatilho: quando um teto ou orçamento estourar em vários projetos, ou quando for propor subir um teto
metadata:
  type: feedback
---

Subir o teto não é conserto quando o estouro se repete em todo projeto: procure a parte **comum** a todos e
pergunte se ela precisa estar ali.

**Why:** 2026-10-23, doctor no Whats acusou `CLAUDE.md` com 10.096 B (teto 10.000). Eu propus subir pra 12.000 B
e o owner respondeu: *"mas ainda 12k não é baixo qualquer alteração subiria ele, precisamos resolver em
definitivo"*. A medição mostrou a causa: o `kickoff` copiava o modelo do kit (9.757 B só de regra do kit) pra
dentro de cada projeto, sobrando 243 B pro projeto. A 0.31.1 já tinha subido o teto de 8 pra 10 KB e o problema
voltou. O conserto definitivo foi tirar a parte comum do arquivo (regras do kit pelo plugin, 0.42.0).

**How to apply:** antes de propor um número, meça quanto do arquivo é igual entre os projetos (ou vem de molde).
Se a parte comum come o teto, o desenho é separar, não subir. Parente de
[[feedback_medir_a_partida_inteira_nao_o_arquivo_acusado]] e de [[project-regra-por-tipo-carrega-ao-ler]].
