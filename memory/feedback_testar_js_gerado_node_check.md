---
name: feedback_testar_js_gerado_node_check
description: HTML/JS gerado — validar a SINTAXE do JS inline com `node --check` no teste; substring verde não pega erro de parse (a "tela branca")
gatilho: quando gerar HTML com JS inline
metadata:
  type: feedback
---

Quando um gerador monta **HTML com JS inline** (ex.: `templates/mapa_neural.py`), inclua um teste que
roda **`node --check`** no bloco de script gerado (pula se não houver `node` no PATH). Motivo: asserções
de **substring** (`"cubicBezier" in html`, etc.) passam **verdes mesmo com um `SyntaxError` de
parse-time** que deixa a página **inteira branca** — o script nem executa, o `vis.Network` não sobe, e
**não há log no console** (erro de parse acontece antes de qualquer hook). Foi assim que um `})` a mais
no fecho de um `forEach` derrubou o mapa neural (bug nascido latente: o HTML da fase não fora aberto e a
suíte seguia verde).

Regra de bolso: **teste verde por substring ≠ JS válido**. Para qualquer saída que seja código executável
(JS/HTML), tenha uma checagem que de fato **parseia** o resultado.

**E o `node --check` não basta: o conteúdo não pode DEPENDER do JS pra existir na tela.** No `bpmn`
(0.24.1) o JS estava sintaticamente perfeito — o problema era o CSS: as 24 seções nasciam
`display:none` e só o script inline revelava uma. O owner abriu o HTML, o script não rodou (viewer
que sandboxa, CSP, extensão) e ele viu **só a legenda e os nomes das rotas**. Conserto: esconder é
**enriquecimento** (`body.js .processo{display:none}`, com o script ligando `body.className='js'`),
o índice virou **âncora** em vez de botão, e um teste garante que nenhuma regra de esconder existe
fora do escopo `body.js`. Compare sempre com o precedente que funciona: o `anatomia.html` tem
**zero** `display:none` — conteúdo estático é o padrão da família. Caso **F-017** do corpus.

Segunda armadilha da mesma rodada: a assertion `"msg" in html` passava porque casava com o **CSS**
(`.msg{...}`), enquanto **nenhuma seta** de fluxo de mensagem era desenhada. Asserção de substring
em HTML precisa mirar a marca do elemento (`class="msg"`), não o token solto.

Relacionado: [[feedback_validacao_ui_deterministica]] (validação de tela é determinística, não dirigindo
o browser ao vivo — o `node --check` é a versão determinística pro JS gerado) e
[[feedback_comandos_prosa_nao_unit_test]] (o que se testa e como).
