---
name: feedback_mapa_se_corrige_depois_do_merge
description: MAPA gravado antes do merge fica dizendo "aguardando o merge" — depois que o owner mescla, uma branch curta corrige o "Onde estamos", senão a próxima conversa lê um estado falso
gatilho: quando gravar o MAPA antes de um merge que ainda vai acontecer, ou quando o owner disser que mesclou
sem_gatilho_de_acao: a ação é gravar arquivo (o MAPA), que o gatilho de comando e de resposta não enxerga
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-11-11-conversa-nova-nao-se-perde.md:54
metadata:
  type: feedback
---

O MAPA gravado na branch da feature diz "aguardando o merge". Depois que o owner mescla, ele mente: a próxima
conversa lê um estado que já passou. O conserto é uma branch curta a partir da `main` só para acertar o "Onde estamos"
(e o "Próximo passo").

**Why:** aconteceu três vezes seguidas — 2026-11-11, 2026-11-12 e 2026-11-16 (`docs/mapa-sono-mesclado`: *"senão a
próxima conversa leria um estado falso"*) (memory/sessions/2026-11-11-conversa-nova-nao-se-perde.md:54).

**How to apply:** o owner disse que mesclou → `git status -sb`, branch curta da `main`, MAPA em dia, commit, e peça o
merge dela. Ao editar o "Onde estamos", só um bloco de histórico (F-067).
