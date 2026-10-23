Regras do kit — vem do plugin mss-spec em toda janela. Quando uma regra do CLAUDE.md do projeto conflitar com esta, a regra do CLAUDE.md do projeto vence.

## Regras críticas (nunca violar) — cada uma nasce de um bug ou decisão real
1. **Registro/memória/notas NUNCA num `CLAUDE.md`** (instrução sempre-ativa; polui o contexto). Memória = `memory/` **dentro do repo**; a pasta nativa guarda só um ponteiro pra ela.
2. Nunca commitar `.env` nem segredos; nunca hardcode de credencial.
3. **Front-end sempre Tailwind + `@tailwindcss/typography`, com JS/CSS em arquivos próprios** — detalhe em `.claude/rules/frontend.md` e `docs/FRONTEND.md`. Exceção: documento standalone (`/mss-spec:documentacao`).
4. **Estrutura de pastas em camadas, sempre** (`docs/ESTRUTURA.md`): nunca arquivos achatados numa pasta única. Router fino, regra no service, imports só "pra baixo".
5. **Segurança secure-by-default** — o app é alvo: autorização no **backend** por request, SQL parametrizado, entrada validada, segredo só por variável de ambiente, nada de PII/stack trace em log, obscuridade não é segurança. **Checklist em `docs/SEGURANCA.md`; auditoria com `/mss-spec:seguranca`.**
6. **Spec viva não pode mentir**: o "Estado atual" de `docs/specs/<assunto>.md` reflete o comportamento de HOJE — `feat` cria/atualiza, e `bugfix`/`refactor` que mude comportamento descrito também. Spec velha faz reintroduzir bug.
7. **Logging padronizado** (`config/logging.py`, via `/mss-spec:log`): `logging` da stdlib, **nunca `print`**; nunca logar PII nem segredo. Ao gerar arquivos novos, pergunte quais recebem `logger`.
8. **O projeto ativo é a ÂNCORA; outro projeto é SOMENTE-LEITURA.** A âncora é a raiz onde a janela abriu e **não migra**. Lá fora, ler sim; `Write`/`Edit`, `git`, `pytest` ou "consertar de passagem", **nunca** — traga o padrão pra cá. Mudança é lá? **pare e diga** (janela nova na raiz dele); bug visto lá, **reporte**. Cerca: hook `PreToolUse` (escape `MSS_ANCORA_OFF=1`).
9. **Antes de declarar pronto, rode o teste e cole a saída** (`docs/superpowers/PLANO-TESTE.md`): só afirme sucesso com **100% verde**. Regravar baseline é `/mss-spec:plano-teste`, disparado por mim. **Validação de tela é só determinística** — nunca dirigir o browser ao vivo.
10. **Pré-vôo de ambiente na 1ª tarefa de código**: rode os checks do `/mss-spec:doctor` que se aplicam e reporte ✓/✗. Não bloqueia, só avisa.
11. **Diagnóstico disciplinado**: bug/falha → `superpowers:systematic-debugging` antes de propor correção. Há precedente que funciona? **Diff completo contra ele (código de boot incluso) ANTES de me pedir evidência.** Fato que eu afirmei não se re-litiga. 2 rodadas sem causa = um teste que discrimina, na condição REAL. Trilho: `/mss-spec:diagnostico`.
