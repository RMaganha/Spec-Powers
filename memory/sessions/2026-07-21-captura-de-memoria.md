# 2026-07-21 — captura de memória (decisões + diário)

## Conversamos
Se valia agregar o [claude-mem](https://github.com/thedotmack/claude-mem) ao kit, ou capturar algo dele que evoluísse memória/mapa/precedentes. Virou o desenho da feature `captura-de-memoria`.

## Pivôs
- **Integrar o claude-mem → só capturar as ideias.** Cogitou-se integrar a ferramenta; repensou porque é serviço de runtime (worker Bun + SQLite + Chroma vetorial) que auto-captura o firehose — bate nos 3 pilares (não-serviço · memória curada · "texto consultável, não vetorial/knowledge-graph"). Ajustou pra aproveitar só as ideias, em markdown versionado.
- **Comando novo → 2º modo do `/mss-spec:memory`.** Cogitou-se `/mss-spec:capturar` + refresh do MAPA + hook. Owner apontou o risco de "2 comandos, mesmas funções" e plugin perdido; além disso o `/mss-spec:mapa` já é dono do MAPA e a escrita de memória já vivia no fecho. Ajustou pra `capturar` como 2º modo do `/mss-spec:memory` (com `resgatar` intacto); MAPA fica no `/mss-spec:mapa`.
- **Hook como gatilho → determinístico + hook só como rede.** Owner já tinha pegado hook falhando em silêncio. Ajustou pra: garantia = passo determinístico no fecho/finishing; hook `Stop`/`PreCompact` **opt-in, off por padrão**, só cutuca (se não disparar, nada se perde).
- **Só decisões → + diário de sessão, barato.** Centrou-se nas decisões (incl. negativas, anti-re-litígio "3 semanas depois"). Owner somou "gravar o que conversamos", com trava dura de custo (barato de gravar do contexto e de reler). Nasceu a **3ª camada**: diário de sessão, **1 arquivo por captura** + índice datado `DIARIO.md` (contra inchar o `MEMORY.md` de partida ou reler o histórico todo de um assunto).
- **Foco do resumo = a evolução, não o estado final.** Owner apontou ESTA conversa (quantas decisões foram repensadas) como o insumo que dá clareza e hoje se perde → o resumo prioriza os **pivôs** (`cogitou X → repensou por Y → ajustou pra Z`).

## Rejeitado
Integração do claude-mem (stack/serviço/vetorial) · comando novo separado · hook como fonte da verdade · tudo no `MEMORY.md` (incharia a partida) · 1 arquivo por assunto (relê o histórico inteiro).

## Fizemos
7 tasks em TDD de wiring, suíte **51 passed** (era 43): `capturar` no `/mss-spec:memory` · `templates/DIARIO.md` + dogfood · scaffolding no `kickoff` · `<private>` + índice-primeiro no `CLAUDE.md` · fecho do `nova-feature` delega · hook opt-in (`hooks/`) · docs + baseline. Decisão transversal em `docs/decisoes.md`.

## Próximo
Passo do owner: `/mss-spec:release` (versão/CHANGELOG/segurança) → `finishing` (merge → master).
