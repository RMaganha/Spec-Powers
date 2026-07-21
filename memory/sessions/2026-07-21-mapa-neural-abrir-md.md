# 2026-07-21 — mapa neural: clique-para-abrir o .md (F2.1)

## Conversamos
Evolução do mapa neural: ao clicar num balão que tem um .md, abrir o arquivo no browser
(o owner sugeriu "abrir / pedir onde abrir / abrir via html"). Ajuste, não mapa novo.

## Pivôs
- **Como abrir → nova aba com markdown renderizado.** Três opções na mesa: painel embutido
  no próprio mapa · link file:// cru (navegador decide, texto cru/download) · nova aba com
  HTML renderizado. Owner escolheu **nova aba + markdown renderizado**.
- **Sem lib de markdown.** Pra manter self-contained sob file:// e sem tocar o proxy MSIG,
  o conteúdo dos .md é embutido inline na geração (coletar_docs) e renderizado por um
  renderizador markdown **vanilla inline** (~40 linhas) — nenhuma dependência/CDN nova.

## Rejeitado
Painel embutido no mapa · link file:// cru · texto cru em <pre> · vendorizar lib de markdown.

## Fizemos
TDD: coletar_docs + CA14 (render). Suíte **54 passed**. `templates/mapa_neural.py`
(coletar_docs, render_html com __DOCS__, mdToHtml/openDoc, handler de clique) + spec/INDEX/
MAPA/PLANO-TESTE atualizados. Observação do owner sobre resumos de 1 linha vazios ficou
fora de escopo (o clique abrindo o arquivo inteiro reduz a dependência deles).

## Próximo
Passo do owner: `/mss-spec:release` → `finishing` (merge → main).
