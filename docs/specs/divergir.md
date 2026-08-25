# divergir — anti-ancoragem no design

## Estado atual
O kit combate a convergência prematura (a 1ª resposta ancora o resto) em 3 camadas: **piso sempre-ativo** no brainstorm do `nova-feature` — as 2-3 abordagens vêm de **frames deliberadamente distintos** e cada uma tem a **armadilha sedutora** marcada; **`/mss-spec:divergir`** (`commands/divergir.md`) — 3-5 subagentes paralelos **isolados** (1 frame cada, não se veem) geram abordagens e a janela faz o crítico (agrupa, pontua, marca armadilhas, aprofunda top-2), **auto-proposto** pelo `nova-feature` quando a decisão é **aberta** (2+ arquiteturas viáveis, sem precedente) **e cara de reverter**, sempre anunciando o custo (~10 chamadas) e esperando o sim; e **memória com `gatilho:`** (`memory/feedback_divergir_antes_de_convergir.md`) pras janelas fora do ritual. Ordem de precedência: precedente MSIG decide → sem precedente e fechada, o piso basta → aberta e cara, propõe o `divergir`. Ideia do repositório [adhd](https://github.com/uditakhourii/adhd); o stack npm (`adhd-agent`) foi rejeitado (`docs/decisoes.md` 2026-08-25). Wiring: `test_divergir_wiring`.

Fora de escopo: integrar o pacote npm/CLI `adhd-agent` · frames como configuração (a lista vive em prosa no comando) · disparo automático sem anúncio de custo.

## Histórico
- 2026-08-25 — criado: avaliação do repo `adhd` virou reimplementação em prosa (3 camadas), após o owner apontar o furo do opt-in puro ("pode ser que eu esqueça de chamar").
