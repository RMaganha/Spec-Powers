# anotar decisões — log de decisões transversais (design)

Data: 2026-07-16 · feature do próprio kit mss-spec.

## Objetivo
Um lugar scannável pras decisões **transversais** (arquitetura, lib, padrão) — "decidimos X em vez de Y, porque Z" —, grandes e médias, sem duplicar o que já existe (Histórico da spec, memory, CHANGELOG).

## Problema
Decisões transversais (por que Mantine, por que pgvector, por que env-var) ficavam espalhadas ou se perdiam. Vira ouro no onboarding e evita rediscutir o que já foi decidido — mas não pode virar subsistema pesado (ADR) nem duplicar a spec/memory.

## Critérios de aceite
- DADO uma decisão transversal numa feature, QUANDO fecho o `/mss-spec:nova-feature`, ENTÃO acrescento 1 linha em `docs/decisoes.md`.
- DADO uma decisão de um assunto específico, ENTÃO ela fica no Histórico da spec dele (NÃO em `docs/decisoes.md` — sem duplicar).
- DADO um projeto novo, QUANDO rodo o `kickoff`, ENTÃO nasce um `docs/decisoes.md` (skeleton) e ele está no Mapa de arquivos do `CLAUDE.md`.

## Design
- **`docs/decisoes.md`** — arquivo único, versionado, 1 linha por decisão transversal. **Não** é `docs/adrs/` (sem subsistema).
- **Não se perde:** passo de fecho do `nova-feature` + item no Mapa de arquivos do `CLAUDE.md` + `kickoff` cria o skeleton (de `templates/DECISOES.md`).
- **Não duplica:** transversal → `decisoes.md`; por-assunto → Histórico da spec.

## Fora de escopo
Subsistema ADR (`docs/adrs/NNN`) · decisão por-assunto (fica na spec) · detecção automática de decisão.

## Arquivos tocados
- novo `templates/DECISOES.md` (skeleton) + `docs/decisoes.md` (deste repo, dogfood)
- `commands/kickoff.md` (copia o skeleton) · `commands/nova-feature.md` (passo de fecho) · `templates/CLAUDE.md` (Mapa de arquivos)

## Histórico
- 2026-07-16 — criado: log único `docs/decisoes.md` (só transversais), mantido pelo `nova-feature`; reusa doc, sem subsistema ADR.
