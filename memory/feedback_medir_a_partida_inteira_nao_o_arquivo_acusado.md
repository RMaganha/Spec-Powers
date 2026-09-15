---
name: feedback_medir_a_partida_inteira_nao_o_arquivo_acusado
description: quando um hook/teto acusa UM arquivo, meça o conjunto inteiro contra os tetos antes de consertar o acusado — o que grita raramente é o que mais custa
gatilho: quando uma ferramenta, hook ou teto acusar UM arquivo (tamanho, lint, limite) e a reação natural for consertar só ele
metadata:
  type: feedback
---

Em 2026-09-14 o kit acusou o `memory/MEMORY.md` do Whats (25.421 bytes, teto 25.600) e mandou podar. Medida
a partida inteira do projeto (o que o `CLAUDE.md` do kit manda ler em toda janela): **214 KB ≈ 53 mil
tokens** — o índice acusado era **12%**; o MAPA estava 15× acima do teto e o INDEX 9×, sem ninguém reclamar,
porque o `doctor` só reporta e ninguém lê o reporte quando nada bloqueia.

**Why:** o alerta aponta onde há um sensor, não onde está o custo. Consertar o arquivo acusado teria
gasto a sessão e deixado 88% do problema no lugar.

**How to apply:** ao receber alerta de teto/tamanho, liste TODOS os arquivos do mesmo ritual e meça cada um
contra o seu teto (bytes, não impressão) antes de propor conserto; ordene pelo excesso, não pelo alerta.
Relacionado: [[feedback_medir_antes_de_afirmar_ganho]] (mede o ganho), [[feedback_simular_a_seco_com_dados_reais]].
