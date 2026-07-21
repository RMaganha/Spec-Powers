---
name: feedback_feature_a_partir_da_master
description: Fluxo de branch do kit — main é a linha principal atualizada; toda feature nova sai da main
metadata:
  type: feedback
---

O owner definiu (2026-07-17): a **linha principal é única e fica sempre atualizada** — todo
trabalho concluído é integrado nela (fast-forward quando possível). **Toda tarefa/feature nova nasce
de uma branch criada a partir da principal** (`git checkout main && git checkout -b <tipo>/<nome>`),
nunca direto na principal. **Nota (2026-07-21):** ao publicar no GitHub a principal foi renomeada
`master`→`main` (`git branch -M main`); agora a principal é a **`main`**.

**Why:** a `feature/doctor` tinha "inchado" e virado a linha principal de fato (39 commits, do front
moderno à 0.8.0), com nome de uma feature só — confuso. Consolidando tudo numa única principal, o ponto
de partida de qualquer trabalho fica único e previsível.

**How to apply:** no início de uma tarefa nova, garanta estar na `main` atualizada e abra a branch da
tarefa a partir dela. Ao terminar e integrar, volte pra `main` (não deixe o owner sentado numa branch
de feature já mesclada). Continua valendo a regra base: nunca codar direto na `main`, e stage nominal
(nunca `git add .`/`-A`). Agora que há remote, `git push` para publicar — sempre a pedido do owner.
Complementa [[feedback_nao_encerrar_com_pergunta]].
