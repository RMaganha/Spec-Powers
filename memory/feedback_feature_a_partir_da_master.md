---
name: feedback_feature_a_partir_da_master
description: Fluxo de branch do kit — master é a linha principal atualizada; toda feature nova sai da master
metadata:
  type: feedback
---

O owner definiu (2026-07-17): a **`master` é a linha principal e fica sempre atualizada** — todo
trabalho concluído é integrado nela (fast-forward quando possível). **Toda tarefa/feature nova nasce
de uma branch criada a partir da `master`** (`git checkout master && git checkout -b <tipo>/<nome>`),
nunca direto na `master`.

**Why:** a `feature/doctor` tinha "inchado" e virado a linha principal de fato (39 commits, do front
moderno à 0.8.0), com nome de uma feature só — confuso. Consolidando tudo na `master`, o ponto de
partida de qualquer trabalho fica único e previsível.

**How to apply:** no início de uma tarefa nova, garanta estar na `master` atualizada e abra a branch da
tarefa a partir dela. Ao terminar e integrar, volte pra `master` (não deixe o owner sentado numa branch
de feature já mesclada). Continua valendo a regra base: nunca codar direto na `master`, `git push` só a
pedido, e stage nominal (nunca `git add .`/`-A`). Complementa [[feedback_nao_encerrar_com_pergunta]].
