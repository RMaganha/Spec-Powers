---
name: project_ajudante_de_teste_sentinela_em_vez_de_none
description: ajudante de teste com parâmetro opcional usa sentinela (PADRAO = object()) quando None é um caso testado
gatilho: quando escrever ajudante de teste com parâmetro opcional que pode receber None de propósito
metadata:
  type: project
---

`def _rodar(..., evento=None)` com `evento if evento is not None else _evento()` faz o teste da entrada
malformada (`evento=None`) receber o evento válido — o teste passa a provar outra coisa. Use
`PADRAO = object()` e `evento is not PADRAO`. Custou 4 falhas na rodada única da suíte em camadas
(2026-11-18, `23a96e1`: capturar_nudge, decisao_junto, diario_junto, regras_do_kit).
