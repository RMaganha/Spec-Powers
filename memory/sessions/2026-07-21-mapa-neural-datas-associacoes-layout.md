# 2026-07-21 — mapa neural v0.11.0: datas · associações · layout tidy-tree

## Conversamos
Enriquecer o mapa neural (owner trouxe print de outro projeto + artigo de SOM): **datas nos balões**
e torná-lo "mais neural" (era organizacional). Depois, testando o real, o **layout embolava** (caixas
sobrepostas) → redesenho do layout.

## Pivôs
- **"Mais neural" → fatia leve, NÃO SOM.** Owner citou self-organizing map. Descartado SOM de verdade
  (vetor de features + treino, deps pesadas, não-determinístico, ganho duvidoso com ~50 itens); ficou
  **camada associativa heurística determinística** (memória↔memória por `[[links]]`; spec↔código por
  `Arquivos tocados`; nunca inventada).
- **Data = mtime, não commit-date.** Owner notou: durante a sessão o arquivo muda (hook/upgrade/geração)
  e o commit atrasa; o **mtime** reflete a verdade local (push/pull sincroniza).
- **Radial → tidy-tree horizontal.** O radial embolava/sobrepunha com muitos filhos. Owner aprovou (via
  **mockup**, antes de codar) árvore esquerda→direita (Knuth, zero-sobreposição) + curvas cubicBezier +
  balões modernos; **aceitou o reflow instantâneo** dos irmãos ao expandir (inverte "nada se mexe", mas
  sem física/tremor). Nós viraram **fixos** (não-arrastáveis).
- **Associações: sempre-visíveis → só no hover.** Sempre-visíveis viravam bagunça (linhas cinzas + setas
  dentro das caixas ao abrir). Passaram a `hidden` por padrão, **bojando à direita** (extremos ordenados
  por altura + curva horária), com **setas ‹ ›** nas 2 pontas e **realce da caixa conectada**.
- **Tela branca = erro de sintaxe (parse-time).** Um `})` a mais no `ASSOC.forEach` abortava o script
  antes do `vis.Network` — **sem log no console**, e a suíte seguia verde (só checava substrings). Bug
  **nascido na F2.2**, latente (o HTML não fora aberto). → guarda `node --check` no teste.
- **Release: 2 manifestos.** Bumpei só o `plugin.json` e mergeei sem re-rodar → `marketplace.json`
  defasado deixou a `main` vermelha (teste de coerência). Corrigido; virou memória.

## Rejeitado
SOM/ML de verdade · **ícone dentro do balão** (adiado — vis-network exige imagem-SVG por nó; ícones só
na legenda hoje) · nós arrastáveis (viraram fixos com o auto-layout) · associação por NLP/semântica ·
arestas sempre-visíveis.

## Fizemos
`extrair_associacoes` + `data`(mtime) por folha + layout **tidy-tree** (curvas cubicBezier + balões) +
hover só-no-hover/realce/setas + **fix tela branca** + guarda `test_html_js_tem_sintaxe_valida`
(`node --check`). Suíte **62 verde** (era 54). **v0.11.0** (plugin+marketplace+CHANGELOG). Spec viva
atualizada (F2.2/F2.3 + fix). `COMO-FUNCIONA.html`: card C19 em dia + seção "memória viva" ganhou
**mapa + precedentes** (+ menção ao diário). Merged `--no-ff` na `main` e **push**.

## Próximo
Aguardando próxima feature (`/mss-spec:nova-feature`). Polimento futuro possível: ícone dentro do balão.
