---
name: feedback_visual_pro_humano_dados_pro_assistente
description: visualização (grafo/HTML/dashboard) é pro humano; o ganho de performance/entendimento do assistente vem de dados agregados em TEXTO consultável
metadata:
  type: feedback
---

Ao propor uma "visualização" que supostamente ajuda o assistente (mapa neural, grafo, dashboard,
"conexões entre tudo"), separe duas coisas que se confundem: **um desenho é pro humano** (bate o olho e
entende o conjunto); **o assistente não "olha" figura pra raciocinar — ele lê texto**. Um `.html`/SVG
lindo não melhora em nada a performance do Claude. O que melhora "entendimento entre projetos/memórias"
é ter os **dados agregados e consultáveis em texto** (um índice `.md`, um resumo estruturado) num lugar
só, sem reler N fontes.

**Why:** no design da F2 do mapa de contexto, o owner perguntou se o mapa neural "agrega algo em
performance/entendimento ou é só saída visual". A resposta honesta destravou o design certo: o gerador
produz **duas saídas do mesmo modelo** — (a) `mapa-neural.md` (índice de texto, é o que o assistente
consulta) + (b) `mapa-neural.html` (grafo, é o que o humano vê). O valor funcional está em (a).

**How to apply:** quando pedirem uma visualização "pra IA entender melhor", entregue **também** (ou
primeiro) a camada de dados em texto — é dela que vem o ganho. Ofereça o visual como comunicação humana,
não como se deixasse o assistente mais esperto. E cheque o escopo: "ligar as memórias de tudo" resvala em
**knowledge-graph**, que o kit marcou como "não fazer" no `INDEX.md`. Relacionado:
[[feedback_validacao_ui_deterministica]] (visual se valida por dado, não dirigindo browser),
[[feedback_nao_inventar_fatos_concretos]] (o agregador só junta o declarado; nunca inventa conexão).
