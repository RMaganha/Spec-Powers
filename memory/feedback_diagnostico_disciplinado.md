---
name: feedback-diagnostico-disciplinado
description: Falha que não fecha em 2 rodadas? Pare o loop de hipóteses — diff completo contra o precedente que funciona (código de boot incluso) ANTES de pedir evidência ao owner; fato do owner não se re-litiga
gatilho: quando entrar em loop de diagnóstico (falha que não fecha em 2 rodadas)
metadata:
  node_type: memory
  type: feedback
---

Diagnóstico de falha que não fecha é **loop disciplinado**, não lista de hipóteses. Na ordem:
invocar `superpowers:systematic-debugging` antes de propor correção; se existe **precedente que
funciona** (outro projeto, versão anterior), o **diff completo contra ele — incluindo o código de
boot/entrypoint, não só infra — vem ANTES de pedir qualquer evidência ao owner**; reproduzir a
**condição real** do ambiente (CWD, envs ausentes, comando de subida), não a do terminal local; e
**fato afirmado pelo owner não se re-litiga** — a explicação certa é compatível com ele.

**Why:** 2026-08-26, deploy do MSS-SSC na Azure: 6 rodadas de owner perdidas num 503 listando
hipóteses de plataforma (porta, Route All, ACR, sidecar), quando o diff contra o projeto de
referência — que o owner tinha apontado **desde o kickoff** e cobrou de novo no meio ("todos os
outros subiram de primeira") — achava a causa em minutos: caminho relativo no `main.py`, processo
morrendo no import. O "testei local e passou" ancorou tudo: o teste rodava de `/app` e nunca
reproduziu o CWD da nuvem. Depois, mais 2 rodadas re-litigando uma App Setting **correta** ("acabei
de afirmar que já estava lá certa, que inferno") quando a resposta era "reiniciar". Nas palavras do
owner: *"para de ser teimoso"*. A skill `systematic-debugging` existia e nunca foi invocada.

**How to apply:** o trilho completo vive em `commands/diagnostico.md` (o owner invoca
`/mss-spec:diagnostico` quando vê o loop; o assistente auto-propõe ao bater 2 rodadas sem causa —
regra crítica de diagnóstico do `CLAUDE.md`). Cada pedido de evidência ao owner custa uma rodada:
antes de pedir, liste o que você ainda não comparou sozinho, e o pedido carrega **um teste que
discrimina**, nunca uma lista. Caso F-015 em `docs/EVALS.md`. Parente de
[[feedback-perguntar-em-vez-de-vasculhar]] (a rodada do owner é cara) e de
[[feedback-nao-inventar-fatos-concretos]] (fato do owner é fato).
