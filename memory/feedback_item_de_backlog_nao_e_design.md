---
name: feedback-item-de-backlog-nao-e-design
description: Item curto de to-dolist/backlog é o sintoma, não o design — transcrever o item em bullets não é desenhar a feature
gatilho: quando a feature nascer de um item curto de to-dolist ou backlog
metadata:
  node_type: memory
  type: feedback
---

Item de to-dolist/backlog é **sintoma anotado com pressa**, não especificação. Pegar o item e virar
seus tópicos em "peças" da feature **não é desenhar** — é transcrever. O design exige diagnóstico
próprio: números do repo, causa-raiz, fonte primária, e o que o item **não** viu.

**Why:** 2026-08-18. O item 4 dizia "evals e context engineering… 3 peças… sem harness — só prosa nos
comandos". Entreguei exatamente essas 3 peças em bullets e o owner cortou: *"isso parece meio raso em
cobrir o eval e context engineering"*. Ao diagnosticar de verdade, o problema real apareceu e não
estava no item: **27 das 33 memórias duráveis nunca entravam na sessão sozinhas**, porque o índice
auto-carregado é o da pasta nativa (6 entradas) e o índice do repo dizia *o que a memória é* em vez de
*quando abri-la*. A feature entregue tem 6 peças, e 3 delas o item não imaginava. Caso **F-011** de
`docs/EVALS.md`.

**How to apply:** ao abrir a feature, trate o item como **entrada**, não como escopo: (1) meça o
estado atual no repo e traga números; (2) ache a causa-raiz do sintoma que o item descreve; (3)
consulte a fonte primária do mecanismo envolvido; (4) só então proponha as peças — e diga
explicitamente onde elas **divergem** do item. Restrição que o owner escreveu sobre o **meio** ("sem
harness", "sem lib nova") delimita o mecanismo, **não** a profundidade: ler assim é premissa, e ela é
`sem fonte`. Parente de [[feedback-pesquisar-fonte-primaria-antes-de-desenhar]] e de
[[feedback-consultar-destilado-antes-da-fonte]].
