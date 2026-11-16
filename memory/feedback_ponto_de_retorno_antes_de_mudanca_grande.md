---
name: feedback_ponto_de_retorno_antes_de_mudanca_grande
description: Branch do git não protege arquivo nunca commitado — antes de mudança grande, commit (e tag) do estado verde; senão voltar atrás vira reescrever
gatilho: quando for começar uma mudança grande num projeto com código ainda não commitado
sem_gatilho_de_acao: depende de julgamento (o que é mudança grande); o comando em si não tem sinal que distinga
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-07-08-review-do-kit-banco-e-front-mantine.md:25
metadata:
  type: feedback
---

Branch do git só protege o que já foi commitado. Antes de uma mudança grande, faça o commit (e, se ajudar, uma tag)
do estado verde; depois, commite cada estado verde. Assim voltar atrás é um `git checkout`, não reescrever.

**Why:** no MSS-SSC (2026-07-13) o piloto do front — a grade com `mantine-datatable` e depois a troca pela MRT beta —
foi feito sem commit nenhum. Quando o owner barrou a dependência beta, a volta para a `mantine-datatable` teve de ser
reescrita à mão (memory/sessions/2026-07-08-review-do-kit-banco-e-front-mantine.md:25).

**How to apply:** em projeto com código *untracked* ou sem commit recente, antes de mexer em algo grande, diga isso
ao owner e proponha o commit nominal do estado atual (stage pelo nome, nunca `git add .`). Parente de
[[feedback_feature_a_partir_da_master]] (a branch nasce da principal) e de [[feedback_so_dependencia_estavel]].
