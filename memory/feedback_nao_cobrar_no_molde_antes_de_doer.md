---
name: feedback_nao_cobrar_no_molde_antes_de_doer
description: Não acrescentar ao molde do kit uma cobrança antes de ela doer — check que reclama do que não existe treina o owner a ignorar o relatório
gatilho: quando propor acrescentar um check, uma cobrança ou uma seção nova ao molde do kit (SEGURANCA, FRONTEND, doctor)
sem_gatilho_de_acao: depende de julgamento (se a cobrança já doeu); não tem frase nem comando fixo
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-08-14-cards-contra-o-kit.md:14
metadata:
  type: feedback
---

Cobrança nova no molde (check do `doctor`, item do `SEGURANCA.md`, regra do `FRONTEND.md`) só entra quando o
problema já apareceu num projeto real. Antes disso, ela vira ruído.

**Why:** em 2026-08-14, conferindo 10 cards de boas práticas contra o kit: *"check que reclama do que não existe
treina você a ignorar o relatório"*; o owner: *"ok então vamos deixar assim"* — RLS, matriz RBAC, WAF e o botão de
reportar erro ficaram de fora (memory/sessions/2026-08-14-cards-contra-o-kit.md:14). É o mesmo motivo da infra
própria: check que cobra infra inexistente faz o ✗ perder o sentido ([[project_kit_nao_assume_ambiente_de_origem]]).

**How to apply:** proposta de cobrança nova traz o caso real que a pede; sem caso, vai para o `to-dolist.md` como
`#fora-de-escopo` (não agora), com o motivo.
