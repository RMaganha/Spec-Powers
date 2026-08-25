# Mapa de contexto — mss-spec

## Onde estamos
`feature/anatomia` (da `main`@0.21.0) — **`/mss-spec:anatomia`**: gerador determinístico (`templates/anatomia.py`, irmão do `mapa_neural.py`) que regenera o painel "anatomia de runtime" do kit — disparo por regime (partida/evento/demanda/fecho) · matriz lê×escreve · riscos · fila — com números **medidos** (manifestos, frontmatter dos comandos, `hooks.json`, rules, orçamento em bytes, EVALS) e metadado curado travado por teste de wiring. Saída `docs/anatomia.html` fora do git. Protótipo validado em sessão (2026-08-25). Spec: `docs/specs/anatomia.md`.

<!-- histórico do estado anterior -->
`main` — **v0.21.0 publicada no GitHub** (`c56e452..9587413`, em sincronia com o `origin`; merge `--no-ff` de `feature/divergir`; suíte **149 verde**). **Anti-ancoragem no design**, ideia do repo `adhd` em prosa (stack npm rejeitado — 3º ideia-vs-stack): piso sempre-ativo no brainstorm do `nova-feature` (frames distintos + armadilha sedutora) · `/mss-spec:divergir` (subagentes isolados, **auto-proposto** quando a decisão é aberta E cara de reverter; caso **F-014**, corpus **14/14 fechados**) · memória com `gatilho:`. Spec: `docs/specs/divergir.md`.

## Próximo passo
**Podar os comandos** (item 5 do to-dolist): **100.356 bytes em 21 comandos** (o `divergir` somou ~3,4 KB na 0.21.0 — a poda ficou mais urgente, não menos) — é a maior superfície de context engineering que sobrou, e o mesmo tratamento do `CLAUDE.md` se aplica (teto por bytes travado por teste, mover nunca apagar). Depois, na ordem: fecho com os 3 artefatos garantidos + `git push` de fato · consolidar os 68 KB dos arquivos de memória · validar o kit com o modelo Fable. Antes disso, **sentir a 0.20.x em sessão nova**: o índice do repo tem que entrar sozinho e as regras de `.claude/rules/` acender ao tocar `.html`/`.sql`/`routes/`.

<!-- histórico do próximo passo anterior -->
**Sentir a 0.19.0 em uso, em sessão nova** — é o único teste que importa aqui: numa janela recarregada, o índice do repo tem que entrar sozinho (pelo ponteiro da nativa) e as regras de `.claude/rules/` têm que acender quando eu tocar um `.html`/`.sql`/`routes/`. Se o owner ainda precisar lembrar de algo que está na memória, isso vira caso novo em `docs/EVALS.md`. Depois: **1 caso aberto** (F-010, jargão inventado ao explicar desenho) e o **item 5 do to-dolist** (garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho), em janela própria. `git push` só quando o owner pedir.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
