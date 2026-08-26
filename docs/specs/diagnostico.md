# Diagnóstico disciplinado — trilho anti-loop de hipóteses

## Estado atual
Falha que não fecha tem trilho em 4 camadas, cada uma atuando num momento diferente:
**(1) regra crítica 11 do `templates/CLAUDE.md`** (sempre-ativa — o único mecanismo em contexto na
hora 2 de uma sessão longa): bug → `superpowers:systematic-debugging`; precedente que funciona →
**diff completo (código de boot incluso) ANTES de pedir evidência ao owner**; fato do owner não se
re-litiga; 2 rodadas sem causa = um teste que discrimina, na condição REAL do ambiente.
**(2) `commands/diagnostico.md`** (`/mss-spec:diagnostico`): o trilho completo, invocável pelo owner
quando ele vê o loop (o detector mais confiável) e auto-proposto pelo assistente ao bater a regra.
**(3) memória `feedback_diagnostico_disciplinado.md`** (gatilho: loop de diagnóstico) + caso
**F-015** em `docs/EVALS.md`. **(4) propagação**: a regra chega aos projetos existentes via
`/mss-spec:upgrade` (mescla do CLAUDE.md, renumerando — a regra do projeto vira 12).

Custo de contexto: o molde ficou em **7.938/8.000 bytes** — a regra coube via compressão de prosa
(mover/encurtar, nunca apagar: header, comando-citado-existe, partida, infra, regra 8, footer),
mantendo todo literal exigido pelos wirings.

Fora de escopo: hook determinístico detectando "loop de diagnóstico" (não há assinatura de tool pra
isso — heurística daria falso positivo, mesma razão do descarte no cerca-da-âncora); garantia de
não-recorrência (instrução mitiga, não elimina — a meta é encurtar o loop de 6 rodadas pra 1–2).

## Histórico
- 2026-08-26 — criado: nasce da sessão de deploy do MSS-SSC na Azure (~3h, PDF analisado nesta
  janela): 6 rodadas de owner num 503 cuja causa (caminho relativo no `main.py`) um diff contra o
  precedente achava de imediato, + 2 rodadas re-litigando App Setting correta (resposta: reiniciar).
  A `systematic-debugging` existia e nunca foi invocada — por isso a camada sempre-ativa + a
  alavanca humana, não só registro em EVALS (lido no kickoff, não na hora 2).
