# Mapa de contexto — mss-spec

## Onde estamos
`feature/context-engineering-orcamento` (da `main`@0.19.0) — **0.20.0: o kit para de inchar a própria janela** (suíte **146 verde**). A partida caiu de **12.976 → 6.374 tokens (−51%)**: `CLAUDE.md` 17.920 → 7.989 bytes (poda por **mover, nunca apagar**), `MAPA.md` 14.621 → 3.603 (histórico foi pro `MAPA-historico.md`), `INDEX.md` 11.256 → 3.031 (fechadas foram pro `INDEX-historico.md`). Novo: check 9 do `doctor` medindo o orçamento em bytes · diretiva de `/compact` (preserva branch e **premissas**) · higiene de janela (`/clear` + subagente). A poda derrubou 9 testes de wiring — cada um restaurado ou reapontado na mão. Spec (2ª metade): `docs/superpowers/specs/2026-08-18-evals-e-context-engineering-design.md`.

<!-- histórico do estado anterior -->
`feature/evals-e-context-engineering` (da `main`@0.18.0) — **0.19.0: evals e context engineering, pronta pra integrar** (suíte **136 verde**, era 116). O laço **falha → caso → guardrail → teste** existe: premissa **com fonte** antes do OK no `nova-feature` · `docs/EVALS.md` com os **12 casos reais** deste repo (sem guardrail = `aberto`) · `gatilho:` nas **34** memórias e índice agrupado por gatilho (teto 200 linhas/25 KB) · 3 regras **path-scoped** em `.claude/rules/` que o Code carrega sozinho · a memória nativa vira **ponteiro** pro índice do repo (ela auto-carregava 6 de 33 entradas — a causa-raiz do repeteco) · `capturar` colhendo **o que deu certo** e podando, `doctor` com o check 8 e `release` com o check 7. O ponteiro na pasta nativa desta máquina **já foi aplicado** (a nativa tinha 6 das 33 entradas). Spec: `docs/superpowers/specs/2026-08-18-evals-e-context-engineering-design.md`.

## Próximo passo
**Sentir a 0.19.0 em uso, em sessão nova** — é o único teste que importa aqui: numa janela recarregada, o índice do repo tem que entrar sozinho (pelo ponteiro da nativa) e as regras de `.claude/rules/` têm que acender quando eu tocar um `.html`/`.sql`/`routes/`. Se o owner ainda precisar lembrar de algo que está na memória, isso vira caso novo em `docs/EVALS.md`. Depois: **1 caso aberto** (F-010, jargão inventado ao explicar desenho) e o **item 5 do to-dolist** (garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho), em janela própria. `git push` só quando o owner pedir.

<!-- histórico do próximo passo anterior -->
Nos **2 projetos que não são MSS**, rodar o `/mss-spec:upgrade` pra a linha `**Infra:**` chegar lá — ele vai **perguntar**; respondendo "própria", o `doctor` para de cobrar proxy/CA/rede e o upgrade para de reintroduzir CA e compose office. **Ciclo do mapa neural fechado** e validado em campo (24 rotas, 0 fantasmas, 36/36 memórias, 8 camadas reais). Na fila: **canário da cerca da âncora em sessão nova** (escrita fora da âncora → `[mss-spec] BLOQUEADO`; se não bloquear, registrar o hook no `settings.json` pelo `hooks/README.md`) e o **1º uso real do `/mss-spec:analise`** no projeto de RAG/pgvector.


## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
