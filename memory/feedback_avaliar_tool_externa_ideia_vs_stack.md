---
name: feedback-avaliar-tool-externa-ideia-vs-stack
description: Ao avaliar ferramenta externa, separar a IDEIA da IMPLEMENTAÇÃO — integrar o stack só se casar com os pilares; senão, capturar só a ideia
metadata:
  node_type: memory
  type: feedback
---

Ao avaliar uma ferramenta externa (biblioteca, plugin, serviço) pra "agregar ao projeto", separe a
**ideia** da **implementação**. Extraia as ideias boas; **integre o stack só se ele casar com os
pilares do projeto**. Se o stack bate nos pilares, reimplemente a ideia no idioma da casa em vez de
arrastar a dependência.

**Why:** na avaliação do [claude-mem](https://github.com/thedotmack/claude-mem) (2026-07-21), a
ferramenta trazia ideias ótimas (captura nos limites de sessão, progressive disclosure, tag
`<private>`), mas o **stack** era serviço de runtime (worker Bun + SQLite + Chroma vetorial) que
auto-captura o firehose e comprime com IA — batendo de frente com 3 pilares do kit: **não-serviço**
(é scaffolding de comandos-prosa, não daemon), **memória curada** (1 fato/arquivo revisado, não
firehose) e **texto consultável, não busca vetorial** (knowledge-graph é fora de escopo). Integrar
teria inchado o plugin e traído o grão. Resultado: pegamos as ideias em markdown versionado e nasceu a
feature `captura-de-memoria` (v0.10.0), com zero dependência nova.

**How to apply:** ao receber um "que acha de agregar X?", primeiro liste (a) as ideias que X traz e
(b) o stack/arquitetura que X exige; cruze (b) com os pilares do projeto e só integre se couber.
Quando não couber, proponha reimplementar a **ideia**, não o serviço. Registre a decisão — o que se
rejeitou e por quê — em `docs/decisoes.md` (insumo anti-re-litígio). Mesma linha de
[[feedback-visual-pro-humano-dados-pro-assistente]] ("o ganho é texto consultável, não máquina nova")
e de [[feedback-consultar-destilado-antes-da-fonte]].
