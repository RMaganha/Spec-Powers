# Mapa de contexto — mss-spec

## Onde estamos
`feature/captura-de-memoria`, a partir da master — **assunto completo e verde** (7 tasks, suíte **51 passed**; commitado na branch, não integrado). Consolidado no `/mss-spec:memory` o modo **`capturar`** (2º modo, ao lado do `resgatar`): destila a sessão em **decisões** (incl. as negativas) + **diário de sessão** datado/indexado (`memory/sessions/<data>-<assunto>.md` + `memory/DIARIO.md`, foco nos **pivôs**), roteando pras 3 camadas de memória, com `<private>`, OK do owner e delegação do MAPA ao `/mss-spec:mapa`. Fecho do `nova-feature` passou a **delegar** ao `capturar`; hook `Stop`/`PreCompact` **opt-in** (off por padrão) só como rede. Integração do claude-mem **rejeitada** (serviço/firehose/vetorial bate nos pilares). Spec: `docs/superpowers/specs/2026-07-21-captura-de-memoria-design.md`.

## Próximo passo
Integrar (passo do owner): rodar a **1ª captura real** (dogfood desta sessão via `/mss-spec:memory capturar`) → `/mss-spec:release` (gate: versão/CHANGELOG/segurança) → `finishing` (merge → master). Baseline já regravado (51 verde). Nada mais pendente no assunto.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-20 · regenerável com /mss-spec:mapa -->
