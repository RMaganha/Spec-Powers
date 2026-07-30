---
description: Consulta o catálogo de precedentes entre projetos MSIG (o que já foi resolvido em outro projeto)
argument-hint: "[assunto: ex. RAG, extração de PDF, conexão SQL]"
disable-model-invocation: true
---

Consulte o catálogo de precedentes em `${CLAUDE_PLUGIN_ROOT}/skills/precedentes-msig/SKILL.md` e responda: existe um projeto MSIG que já resolveu **$ARGUMENTS**? Se sim, aponte o projeto, o caminho e a abordagem, e lembre: **abra o código real de lá antes de replicar** — o catálogo é só um índice, o código pode ter evoluído.

Se nada no catálogo casar, diga isso claramente em vez de inventar um precedente.

**O projeto de referência é SOMENTE-LEITURA.** O projeto ativo (a raiz onde esta janela abriu) é a **âncora** — o único destino de escrita, e ela **não migra** porque você foi ler outro repositório. No projeto de referência: `Read`/`Grep`/`Glob` sim; `Write`/`Edit`, `git`, `pytest`, build ou "consertar de passagem", **nunca**. Se a mudança é lá, **pare** e diga ao owner pra fechar esta janela e abrir uma nova na raiz daquele projeto; se viu um bug lá, **reporte** (ofereça `/mss-spec:to-dolist`), não conserte.
