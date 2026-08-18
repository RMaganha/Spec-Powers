# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.20.1** (suíte **148 verde**). O ciclo de evals + context engineering fechou em 3 releases: **0.19.0** o recall (premissa com fonte · `docs/EVALS.md` · `gatilho:` nas memórias · `.claude/rules/` · ponteiro na nativa), **0.20.0** o orçamento (partida de 12.976 → 6.374 tokens, teto virando teste) e **0.20.1** o último caso aberto. **`docs/EVALS.md` está 13/13 fechados.** Falta publicar (`git push` — o owner dispara).

<!-- histórico do estado anterior -->
`feature/context-engineering-orcamento` (da `main`@0.19.0) — **0.20.0: o kit para de inchar a própria janela** (suíte **146 verde**). A partida caiu de **12.976 → 6.374 tokens (−51%)**: `CLAUDE.md` 17.920 → 7.989 bytes (poda por **mover, nunca apagar**), `MAPA.md` 14.621 → 3.603 (histórico foi pro `MAPA-historico.md`), `INDEX.md` 11.256 → 3.031 (fechadas foram pro `INDEX-historico.md`). Novo: check 9 do `doctor` medindo o orçamento em bytes · diretiva de `/compact` (preserva branch e **premissas**) · higiene de janela (`/clear` + subagente). A poda derrubou 9 testes de wiring — cada um restaurado ou reapontado na mão. Spec (2ª metade): `docs/superpowers/specs/2026-08-18-evals-e-context-engineering-design.md`.

## Próximo passo
**Podar os comandos** (item 5 do to-dolist): 95.593 bytes nos 20 comandos, que *cresceram* +8.691 na 0.20.0 — é a maior superfície de context engineering que sobrou, e o mesmo tratamento do `CLAUDE.md` se aplica (teto por bytes travado por teste, mover nunca apagar). Depois, na ordem: fecho com os 3 artefatos garantidos + `git push` de fato · consolidar os 68 KB dos arquivos de memória · validar o kit com o modelo Fable. Antes disso, **sentir a 0.20.x em sessão nova**: o índice do repo tem que entrar sozinho e as regras de `.claude/rules/` acender ao tocar `.html`/`.sql`/`routes/`.

<!-- histórico do próximo passo anterior -->
**Sentir a 0.19.0 em uso, em sessão nova** — é o único teste que importa aqui: numa janela recarregada, o índice do repo tem que entrar sozinho (pelo ponteiro da nativa) e as regras de `.claude/rules/` têm que acender quando eu tocar um `.html`/`.sql`/`routes/`. Se o owner ainda precisar lembrar de algo que está na memória, isso vira caso novo em `docs/EVALS.md`. Depois: **1 caso aberto** (F-010, jargão inventado ao explicar desenho) e o **item 5 do to-dolist** (garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho), em janela própria. `git push` só quando o owner pedir.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
