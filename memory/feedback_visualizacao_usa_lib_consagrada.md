---
name: feedback_visualizacao_usa_lib_consagrada
description: Desenho/diagrama/grafo/layout — use a biblioteca consagrada VENDORIZADA (o kit já faz isso); geometria escrita à mão sai ilegível
gatilho: quando a feature pedir desenho, diagrama, grafo ou layout visual
metadata:
  type: feedback
---

Feature que pede **desenho** (diagrama, grafo, fluxo, organograma, timeline): procure a **biblioteca
consagrada** do domínio e **vendorize** — não escreva geometria. "Self-contained, zero CDN" neste kit
**nunca** significou desenhar à mão: significa **lib embutida**. O precedente estava aqui desde a
0.11.0, `templates/vendor/vis-network.min.js` (673 KB), usado pelo `mapa-neural`.

**Why:** na 0.24.x eu escrevi um layout SVG próprio pro `/mss-spec:bpmn` — raias como faixas de Y,
colunas de 236 px, setas em cotovelo. Rodado num projeto real (MSS-SSC, 24 rotas), o maior diagrama
saiu com **3.964 × 576 px** e **222 rótulos truncados**: o owner abriu e disse *"não dá visibilidade
alguma... não agregou em nada"*. A rodada inteira foi refeita com `bpmn-js` + `bpmn-auto-layout`
(bpmn.io), que estavam a **um `npm view`** de distância — e o resultado ficou legível na primeira
tentativa. Layout de processo/grafo é problema resolvido há uma década; competir com isso é queimar
uma sessão inteira.

**How to apply:** antes de escrever a primeira coordenada, (1) veja o que o projeto **já vendoriza**
(`templates/vendor/`), (2) confira a lib na fonte primária (`npm view <lib> version`, e leia a seção
**Limitations** do pacote — foi ela que me avisou que raia e fluxo de mensagem não são posicionados),
(3) prefira o **formato padrão do domínio** como saída (BPMN 2.0 XML abre no Bizagi; o desenho é só
uma das visualizações dele). Se a lib for ESM e você quiser evitar dependência de runtime, **empacote
uma vez** (`esbuild --bundle --format=iife`) e vendorize o bundle: o gerador segue Python puro.

Relacionado: [[feedback_avaliar_tool_externa_ideia_vs_stack]] (aqui a decisão foi o oposto: a lib
**casa** com os pilares porque vendorizar não adiciona runtime), [[feedback_so_dependencia_estavel]]
(bpmn-js 18.27.0, sem beta), [[feedback_testar_js_gerado_node_check]] (o que ainda pode quebrar na
página gerada) e [[project_dogfood_gerador_diff_antes_depois]] (foi o projeto real que expôs tudo).
