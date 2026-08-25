# Mapa de contexto — mss-spec

## Onde estamos
`feature/divergir` (da `main`@0.20.1) — **anti-ancoragem no design**: a ideia do repositório `adhd` (divergir antes de convergir) reimplementada em prosa, com o stack npm rejeitado. Três camadas: piso sempre-ativo no brainstorm do `nova-feature` (abordagens sob frames distintos + armadilha sedutora marcada) · comando opt-in `/mss-spec:divergir` (subagentes isolados, 1 frame cada; auto-proposto quando a decisão é **aberta e cara de reverter**) · memória com `gatilho:` pras janelas fora do ritual. Spec: `docs/specs/divergir.md`.

<!-- histórico do estado anterior -->
`main` — **v0.20.1** (suíte **148 verde**). O ciclo de evals + context engineering fechou em 3 releases: **0.19.0** o recall (premissa com fonte · `docs/EVALS.md` · `gatilho:` nas memórias · `.claude/rules/`), **0.20.0** o orçamento (partida 12.976 → 6.374 tokens, teto virando teste), **0.20.1** o último caso aberto — **`docs/EVALS.md` 13/13 fechados**. Publicado no GitHub (`886764a..09712d1`), em sincronia com o `origin`.

## Próximo passo
**Podar os comandos** (item 5 do to-dolist): 95.593 bytes nos 20 comandos, que *cresceram* +8.691 na 0.20.0 — é a maior superfície de context engineering que sobrou, e o mesmo tratamento do `CLAUDE.md` se aplica (teto por bytes travado por teste, mover nunca apagar). Depois, na ordem: fecho com os 3 artefatos garantidos + `git push` de fato · consolidar os 68 KB dos arquivos de memória · validar o kit com o modelo Fable. Antes disso, **sentir a 0.20.x em sessão nova**: o índice do repo tem que entrar sozinho e as regras de `.claude/rules/` acender ao tocar `.html`/`.sql`/`routes/`.

<!-- histórico do próximo passo anterior -->
**Sentir a 0.19.0 em uso, em sessão nova** — é o único teste que importa aqui: numa janela recarregada, o índice do repo tem que entrar sozinho (pelo ponteiro da nativa) e as regras de `.claude/rules/` têm que acender quando eu tocar um `.html`/`.sql`/`routes/`. Se o owner ainda precisar lembrar de algo que está na memória, isso vira caso novo em `docs/EVALS.md`. Depois: **1 caso aberto** (F-010, jargão inventado ao explicar desenho) e o **item 5 do to-dolist** (garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho), em janela própria. `git push` só quando o owner pedir.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
