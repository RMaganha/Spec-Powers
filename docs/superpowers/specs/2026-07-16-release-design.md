# release — checklist de pré-publicação (design)

Data: 2026-07-16 · feature do kit mss-spec. **Implementada 2026-07-17.**

## Objetivo
Comando `/mss-spec:release` — um checklist inteligente antes de publicar: reúne num só passo o "antes de entregar" que hoje está espalhado.

## Problema
Publicar envolve várias etapas fáceis de esquecer (bump de versão, CHANGELOG, testes verdes, segurança, docs coerentes). Falta um gate único que confira tudo e reporte o que falta.

## Critérios de aceite (rascunho)
- DADO uma entrega, QUANDO rodo `/mss-spec:release`, ENTÃO ele reporta ✓/✗: versão bumpada (onde aplicável) · CHANGELOG atualizado · `plano-teste` 100% verde · `seguranca` revisada (se houve rota/endpoint) · specs/docs coerentes com o entregue.
- DADO algo ✗, ENTÃO **só reporta** o que falta (não publica, não conserta).

## Design (fechado 2026-07-17)
- Comando `/mss-spec:release` (`disable-model-invocation`) que **orquestra os checks que já existem** + veredito final. **Só reporta** (espírito do `doctor`): não bumpa versão, não edita CHANGELOG, não faz merge — aponta o que falta.
- **Escopo: ambos, condicional** — serve pro próprio plugin (versão `plugin.json`==`marketplace.json` + CHANGELOG) E pra projetos MSIG genéricos; cada check roda só se aplica (web app por branch, sem versão semântica, pula o check de versão).
- **Fronteira: gate ANTES do `finishing-a-development-branch`** — verde → você segue pro finishing (merge/PR). Sem sobreposição.
- Checks: (1) testes 100% verde (roda o pytest do PLANO-TESTE) · (2) versão coerente · (3) CHANGELOG atualizado · (4) segurança revisada se mexeu em rota/endpoint · (5) spec viva + INDEX coerentes com o entregue · (6) **convenções aderentes — aplica o checklist do `compliance`** (compliance segue disponível avulso) · (7) working tree sem perda e sem segredo no stage.
- Wiring: apontado no fecho do `nova-feature` (passo 6), antes do finishing.

## Fora de escopo
Fazer o deploy / pipeline de CI (o kit não gerencia deploy — ver roadmap). Bumpar versão / editar CHANGELOG / fazer merge (só reporta).

## Histórico
- 2026-07-16 — criado: spec inicial. Detalhar (brainstorming) e implementar em outro chat.
- 2026-07-17 — implementado: `commands/release.md` (6 checks, só reporta, gate antes do finishing), wiring no `nova-feature` passo 6, `test_release_wiring` no smoke. Decisões fechadas em brainstorming: escopo ambos-condicional · só reporta · gate antes do finishing. 22/22 verde.
- 2026-07-17 — o release passou a **rodar o checklist do `compliance`** como check nº 6 (convenções aderentes), a pedido do owner — a inspeção final agora cobre testes+versão+CHANGELOG+segurança(lembrete)+specs+**convenção** num veredito só; o `compliance` continua rodável avulso. `doctor` fica de fora (ambiente é pré-vôo de quem roda/builda, não de quem publica). 23/23 verde.
