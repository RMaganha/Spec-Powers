---
name: feedback_regra_unica_em_vez_de_config
description: Owner prefere UMA regra explicável a mecanismo declarativo — proposta com seção de config foi cortada por confundir; exceções valem se cada uma cabe em 1 linha
gatilho: quando propor mecanismo de configuração, flag ou seção declarativa
metadata:
  type: feedback
---

Quando a detecção automática não acerta um caso, minha tendência é criar **mecanismo de
configuração** (uma seção declarativa no `MAPA.md`, um arquivo de opções). O owner cortou:
*"não entendi muito bem"* — e o que ele pediu foi **uma regra só**, que ele conseguisse repetir de
cabeça. Virou *"se está no repo, está no mapa"* + 4 exceções, cada uma explicável em **uma linha**
(ferramenta · já tem ramo próprio · o `.gitignore` do projeto · `--ignorar`).

**Why:** config nova é superfície nova — precisa ser documentada, distribuída por `upgrade`,
lembrada na hora certa e mantida em todo projeto. Regra única funciona **sem ninguém configurar
nada**, e quando precisa de exceção ela se apoia em algo que o projeto **já declara** (o
`.gitignore`), não num formato que o kit inventou.

**How to apply:** antes de propor seção/arquivo/flag de configuração, pergunte: dá pra resolver com
uma regra que dispense configuração? Existe declaração que o projeto **já** faz e que eu possa ler
em vez de pedir uma nova? Se a proposta precisar de parágrafo pra explicar, ela vai ser cortada —
e com razão. Corolário do mesmo diálogo: **não ensine a ferramenta a ler intenção em prosa**
(o `CLAUDE.md` dizer "esta pasta é descartável" não é contrato); declaração vale onde é executável.

Relacionado: [[feedback_nivel_cerimonia_velocidade]] (mesma preferência por leveza) e
[[feedback_avaliar_tool_externa_ideia_vs_stack]] (não inchar o kit).
