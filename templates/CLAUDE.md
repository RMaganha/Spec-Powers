<!-- MODELO de CLAUDE.md — copie pra RAIZ do projeto e preencha os <...>. ENXUTO: entra em TODA sessão.
     Teste de cada linha: "removendo isto, ele erraria?". Procedimento longo vai pro comando/rules/spec. -->

# <Projeto> — <objetivo em 1 frase>

## Modo de trabalho (nunca violar)
- **Idioma**: responda **sempre em pt-BR**, inclusive em slash-command sem texto.
- **Base**: se existir `projeto.md` na raiz, leia antes de tudo.
- **Não codar antes do meu OK explícito**: diagnosticar → plano curto → OK → verificar no real.
- **Declare as premissas antes do OK**: o que você assume **sem eu ter dito**, cada uma com a **fonte** (arquivo, ou "você disse") ou marcada **`sem fonte`** — essas primeiro. Premissa derrubada vira caso em `docs/EVALS.md`.
- **Não inventar fatos concretos**: caminho, host, porta, nome de container — só o que está no repo ou o que eu confirmar. Na dúvida, `<a confirmar>` ou pergunte: caminho errado é pior que lacuna.
- **PERGUNTE, não vasculhe**: faltou um fato que **eu** tenho na cabeça (onde vive um projeto, nome exato de variável, qual é o compose)? Pergunte **curto, na hora**; nada de varrer o disco (`find`/`Glob` de repositório em repositório) — é lento e termina em chute. Busca só depois que eu não souber.
- **Comando `/mss-spec:<x>` citado EXISTE — leia o arquivo `commands/<x>.md`** (é `disable-model-invocation`: fora da lista de invocáveis; nunca conclua "não existe"). **"Rode `/mss-spec:X`" = execute os passos na mão** — invocar falha com *"Falha ao executar a habilidade"*. Kit parecendo ausente é diagnóstico do `/mss-spec:doctor`.
- **Siga as skills do superpowers à risca** (o harness lista quais são). Precisão acima de velocidade.
- **Assuma o papel de especialista sênior do domínio** (UI, banco, segurança, infra…): anuncie, trabalhe assim até o meu OK, volte a arquiteto/dev sênior.
- **Nível de cerimônia** (padrão **médio**; troque com `/mss-spec:modo`): varia só o peso do planejamento — TDD e verificação são inegociáveis em qualquer nível.
- **Git — branch da principal + local-only**: toda tarefa nova abre branch **a partir da principal atualizada** (`main`/`master`) — nunca na principal e **nunca a partir de outra branch**. Stage **nominal** (jamais `git add .`/`-A`). **`git push` só quando eu pedir.**

## Contexto de janela (o recurso mais caro)
- **Na partida, leia nesta ordem**: `docs/superpowers/MAPA.md` (onde estamos) → `memory/MEMORY.md` (índice por **gatilho**: *quando* abrir cada memória) → `docs/superpowers/INDEX.md` (tarefas abertas) → `docs/EVALS.md` (falhas que custaram caro). São **índices**: abra o arquivo só quando apontarem relevância, nunca a pasta inteira.
- **Ao reabrir um assunto**, abra antes a spec viva (`docs/specs/<assunto>.md`): "Estado atual" diz como está HOJE.
- **`.claude/rules/`**: regra com `paths:` que carrega sozinha quando você toca um arquivo que casa. É onde mora a regra por tipo de arquivo (front, banco, rota) — **não repita esse conteúdo aqui**.
- **Sob demanda, nunca na partida**: `memory/DIARIO.md` → `memory/sessions/<data>-<assunto>.md` · `docs/superpowers/MAPA-historico.md` e `INDEX-historico.md` (estado velho, tarefas fechadas).
- **Um assunto por janela — e um projeto por janela** (regra 8). Surgiu um 2º assunto? **Alerte**, ofereça `/mss-spec:to-dolist adicionar <assunto>` e sugira **`/clear` + janela nova**. É alerta, não trava.
- **Investigação ampla vai por subagente** (varrer muitos arquivos): ele lê em janela separada e devolve o resumo. Corrigiu duas vezes o mesmo ponto? `/clear` e recomece com prompt melhor.
- **Ao compactar (`/compact`), preserve**: a **branch** e o assunto · as **premissas** declaradas · os critérios de aceite abertos · o comando de teste e a última saída · os arquivos tocados.
- **`<private>`**: trecho marcado `<private>…</private>` nunca vira memória/diário/decisão versionada.

## Contexto
- **Infra:** <**MSIG** | **própria**> — MSIG = rede `mitiai_network`, proxy, CA do FortiGate, SQL corporativo (`docs/AMBIENTE.md`). Própria = nada disso (sem proxy no `.env`, sem `docker-compose.office.yml`, sem `get_connection.py`); o doctor pula esses checks. Definido no `/mss-spec:kickoff`; é esta linha que os comandos leem.
- **Stack/runtime:** <ex.: Python 3.x / Node> · **Como roda:** <CLI | serviço/porta | container | cron>
- **UI:** <não | web — ex.: FastAPI + Jinja; ver `.claude/rules/frontend.md`>
- **Integrações externas:** <sites / APIs / filas, ou "nenhuma">
- **Banco:** <não | qual> — ver `.claude/rules/banco-e-segredo.md`

## Mapa de arquivos (só o que não se infere lendo o repo)
- `projeto.md` — base/contexto fundamental (lido primeiro; pode não existir)
- `docs/ESTRUTURA.md` **prescreve** onde arquivo novo nasce; `docs/ARQUITETURA.md` **descreve** o projeto como é hoje e lista **o que não nasceu do kit** (intocável)
- `docs/decisoes.md` — decisões **transversais** ("X em vez de Y — porque Z")
- `<arquivo>` — <responsabilidade>

## Regras críticas (nunca violar) — cada uma nasce de um bug ou decisão real
1. **Registro/memória/notas NUNCA num `CLAUDE.md`** (é instrução sempre-ativa e polui o contexto). Memória = `memory/` **dentro do repo**; a pasta nativa guarda só um ponteiro pra ela.
2. Nunca commitar `.env` nem segredos; nunca hardcode de credencial.
3. **Front-end sempre Tailwind + `@tailwindcss/typography`, com JS/CSS em arquivos próprios** — detalhe em `.claude/rules/frontend.md` e `docs/FRONTEND.md`. Exceção: documento standalone (`/mss-spec:documentacao`).
4. **Estrutura de pastas em camadas, sempre** (`docs/ESTRUTURA.md`): nunca arquivos achatados numa pasta única. Router fino, regra no service, imports só "pra baixo".
5. **Segurança secure-by-default** — o app é alvo: autorização no **backend** por request, SQL parametrizado, entrada validada, segredo só por variável de ambiente, nada de PII/stack trace em log, obscuridade não é segurança. **Checklist em `docs/SEGURANCA.md`; auditoria com `/mss-spec:seguranca`.**
6. **Spec viva não pode mentir**: o "Estado atual" de `docs/specs/<assunto>.md` reflete o comportamento de HOJE — `feat` cria/atualiza, e `bugfix`/`refactor` que mude comportamento descrito também. Spec velha faz reintroduzir bug.
7. **Logging padronizado** (`config/logging.py`, via `/mss-spec:log`): `logging` da stdlib, **nunca `print`**; nunca logar PII nem segredo. Ao gerar arquivos novos, pergunte quais recebem `logger`.
8. **O projeto ativo é a ÂNCORA; outro projeto é SOMENTE-LEITURA.** A âncora é a raiz onde a janela abriu e **não migra**. Lá fora, ler sim; `Write`/`Edit`, `git`, `pytest` ou "consertar de passagem", **nunca** — traga o padrão pra cá. Mudança é lá? **pare e diga** (janela nova na raiz dele); bug visto lá, **reporte**. Cerca: hook `PreToolUse` (escape `MSS_ANCORA_OFF=1`) — cerca é 2ª linha, a regra é esta.
9. **Antes de declarar pronto, rode o teste e cole a saída** (`docs/superpowers/PLANO-TESTE.md`): só afirme sucesso com **100% verde**. Regravar baseline é `/mss-spec:plano-teste`, disparado por mim. **Validação de tela é só determinística** — nunca dirigir o browser ao vivo.
10. **Pré-vôo de ambiente na 1ª tarefa de código**: rode os checks do `/mss-spec:doctor` que se aplicam e reporte ✓/✗. Não bloqueia, só avisa.
11. **Diagnóstico disciplinado**: bug/falha → `superpowers:systematic-debugging` antes de propor correção. Há precedente que funciona? **Diff completo contra ele (código de boot incluso) ANTES de me pedir evidência.** Fato que eu afirmei não se re-litiga. 2 rodadas sem causa = um teste que discrimina, na condição REAL. Trilho: `/mss-spec:diagnostico`.
12. <regra específica do seu projeto…>

<!-- Cresceu? Mova o detalhe pro comando/rules/spec e deixe o ponteiro. Teto: 8 KB — o doctor mede e avisa. -->
