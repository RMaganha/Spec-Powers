# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.23.0 publicada no GitHub** (`85c4428..cb3e678`, em sincronia com o `origin`; merge `--no-ff` de `feature/diagnostico`; suíte **160 verde**). **Trilho disciplinado de diagnóstico (F-015)**, nascido da análise do PDF da sessão de deploy do MSS-SSC (6 rodadas de owner num 503 + 2 re-litigando App Setting correta). 4 camadas: regra crítica 11 no molde (sempre-ativa; o CLAUDE.md ficou em 7.938/8.000 bytes via compressão mover-não-apagar) · `/mss-spec:diagnostico` (alavanca do owner) · memória `feedback_diagnostico_disciplinado` + F-015 no EVALS · propagação via `upgrade` (mescla + renumera). Spec: `docs/specs/diagnostico.md`.

<!-- histórico do estado anterior -->
`main` — **v0.22.0 publicada no GitHub** (`7374903..7a6f3ab`, em sincronia com o `origin`; merge `--no-ff` de `feature/anatomia`; suíte **159 verde**). **`/mss-spec:anatomia`**: gerador determinístico (`templates/anatomia.py`) do painel "anatomia de runtime" — disparo por regime · matriz lê×escreve · riscos · fila — com números **medidos** (manifestos em `utf-8-sig` — regressão do BOM virou teste) e metadado curado com `alvos` travados por teste. Saída `/docs/anatomia.html` fora do git (2 gitignores). Dogfood rodado: 103.815 B em 22 comandos, medido pelo próprio painel. Spec: `docs/specs/anatomia.md`.

## Próximo passo
**Podar os comandos**: **103.815 bytes em 22 comandos** (medido pelo `/mss-spec:anatomia` na 0.22.0). Leitura certa: a soma é tendência, **não** taxa por sessão (comando `disable-model-invocation` só custa quando invocado) — o alvo real são os **5 grandes** (`nova-feature` 12,1 KB · `analise` 9,6 · `kickoff` 8,5 · `upgrade` 8,1 · `memory` 7,9 ≈ 46 KB), onde instrução demais vira instrução ignorada. Mesmo tratamento do `CLAUDE.md`: teto por bytes travado por teste, mover nunca apagar. Depois, na ordem: fecho com os 3 artefatos garantidos + `git push` de fato · consolidar os 68 KB dos arquivos de memória · validar o kit com o modelo Fable. Antes disso, **sentir a 0.20.x em sessão nova**: o índice do repo tem que entrar sozinho e as regras de `.claude/rules/` acender ao tocar `.html`/`.sql`/`routes/`.

<!-- histórico do próximo passo anterior -->
**Sentir a 0.19.0 em uso, em sessão nova** — é o único teste que importa aqui: numa janela recarregada, o índice do repo tem que entrar sozinho (pelo ponteiro da nativa) e as regras de `.claude/rules/` têm que acender quando eu tocar um `.html`/`.sql`/`routes/`. Se o owner ainda precisar lembrar de algo que está na memória, isso vira caso novo em `docs/EVALS.md`. Depois: **1 caso aberto** (F-010, jargão inventado ao explicar desenho) e o **item 5 do to-dolist** (garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho), em janela própria. `git push` só quando o owner pedir.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
