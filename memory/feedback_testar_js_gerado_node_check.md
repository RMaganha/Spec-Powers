---
name: feedback_testar_js_gerado_node_check
description: HTML/JS gerado — validar a SINTAXE do JS inline com `node --check` no teste; substring verde não pega erro de parse (a "tela branca")
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

Relacionado: [[feedback_validacao_ui_deterministica]] (validação de tela é determinística, não dirigindo
o browser ao vivo — o `node --check` é a versão determinística pro JS gerado) e
[[feedback_comandos_prosa_nao_unit_test]] (o que se testa e como).
