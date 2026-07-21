# Mapa de contexto — mss-spec

## Onde estamos
`feature/mapa-de-contexto`, a partir da master — **assunto completo e verde** (F1 + F2, suíte 42 passed): F1 = o `MAPA.md` por projeto (onde estamos · próximo passo · conexões) integrado no fluxo + `/mss-spec:mapa`; F2 = `/mss-spec:mapa-neural` (gerador `templates/mapa_neural.py`) que monta o **mapa mental do projeto** (projeto no centro + 4 dimensões extraídas do repo) em HTML radial full-screen expansível/arrastável + índice de texto. Trabalho na working tree, **ainda não commitado**. Spec: `docs/superpowers/specs/2026-07-20-mapa-de-contexto-design.md`.

## Próximo passo
Integrar (passo do owner): `/mss-spec:plano-teste` (regrava o baseline) → `/mss-spec:release` (gate) → `finishing` (merge/commit). Nada mais pendente no assunto.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-20 · regenerável com /mss-spec:mapa -->
