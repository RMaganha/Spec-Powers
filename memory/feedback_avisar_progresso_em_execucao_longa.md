---
name: feedback-avisar-progresso-em-execucao-longa
description: Em execução longa (subagentes, plano de várias tarefas), mantenha a lista de tarefas em dia e mande 1 linha de status a cada etapa dizendo o que falta e quanto tempo — o owner acompanha pela lista e pelas mensagens, não pelos commits
gatilho: quando a tarefa rodar por subagentes ou passar de ~10 minutos sem mensagem ao owner
metadata:
  type: feedback
---

Execução longa sem sinal parece travada, mesmo quando está andando.

**Why:** 2026-10-23, construção da 0.42.0 por subagentes com revisor por tarefa (~3 h). Três reclamações:
*"está fazendo algo está parado na tarefa 4 há varios minutos"* (a lista ficou em "Tarefa 4" enquanto a 6 rodava —
eu não avancei o passo ao fechar a 4 e a 5), *"está a quase 1hora sem responder"* (a onda de correção da revisão
final + a re-revisão rodaram sem nenhum aviso) e *"vai ficar o dia todo nisso?"*. Caso F-041.

**How to apply:** avance a lista no mesmo turno em que a tarefa fecha (não depois). A cada retorno de subagente,
1 linha: o que terminou, o que roda agora, o que falta e uma estimativa ("a suíte leva ~3 min"). Antes de uma
espera longa (revisão final, onda de correção), diga que vai demorar e quanto. Parente de
[[feedback-nivel-cerimonia-velocidade]].
