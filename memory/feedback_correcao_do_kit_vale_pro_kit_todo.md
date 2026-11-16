---
name: feedback_correcao_do_kit_vale_pro_kit_todo
description: Erro ou melhoria de um comando do kit achado na janela de um projeto se corrige no kit, para todos — nunca como exceção tratada só naquele projeto
gatilho: quando achar, na janela de um projeto, um erro ou uma melhoria de um comando, molde ou padrão do kit
sem_gatilho_de_acao: depende de julgamento (se o defeito é do kit ou do projeto); não tem frase nem comando fixo
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-10-21-azure-ambiente.md:67
metadata:
  type: feedback
---

Decisão do owner, dita duas vezes e recuperada no sono de 2026-11-16 (`docs/decisoes.md`, linha de 2026-11-16):
**correção e padrão do kit nascem no kit**, e os projetos consomem — erro de um comando do kit visto num projeto se
corrige no kit inteiro, nunca como exceção tratada só naquele projeto.

**Why:** 2026-07-14: *"sempre as correções vamos trazer aqui e as melhorias de layout… você faz ai o controle é
nosso!"* (memory/sessions/2026-07-08-review-do-kit-banco-e-front-mantine.md:27). 2026-10-15: *"tem que corrigir tudo,
não vou ficar tratando exceções em janelas de outros projetos"* (memory/sessions/2026-10-21-azure-ambiente.md:67).

**How to apply:** na janela do projeto, diga em 1 linha que o defeito é do kit e anote no `to-dolist.md` do kit; o
conserto acontece numa conversa do kit e chega ao projeto pelo `/mss-spec:upgrade` (`docs/decisoes.md:52`). Não
remende o arquivo do projeto para contornar. Parente de [[feedback_uma_tarefa_numa_conversa_so]].
