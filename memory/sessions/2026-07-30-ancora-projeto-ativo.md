# 2026-07-30 — âncora do projeto ativo: um projeto por janela (v0.15.0)

## Conversamos
Relato de acidente, não pedido de feature: *"quando uso o `mss-spec:precedentes` ou algo do tipo, o kit
passa a trabalhar em outro projeto... eu estava no projeto A e falei 'olha o projeto B tem isso, veja como
está lá e faça igual', a partir daí ele assumiu o projeto B e mudou tudo lá **quebrando todo o projeto
B**"*. O que se pedia era o guardrail que faltava.

## Pivôs
- **Diagnóstico: deriva de contexto, não malícia.** Nada no kit fixava o **alvo de escrita**. O
  `precedentes` manda (corretamente) "abra o código real de lá" — e não dizia que aquilo é **somente
  leitura**; sem âncora declarada, o último caminho lido passa a parecer "o projeto". A regra que mais se
  aproximava, "um assunto por janela", falava de *assunto*, não de *projeto*. O buraco era exatamente esse.
- **O owner escolheu a cerca mais forte: bloquear.** Ofereci 4 níveis (ligada+bloqueia · ligada+pergunta ·
  opt-in · só prosa) e ele foi no primeiro. Isso **inverteu uma política escrita do kit** ("o kit não
  registra hook no `plugin.json` de propósito — hooks falham em silêncio"): a regra passou a valer só pra
  hook-**lembrete**; hook-**cerca** vem ligado, porque cerca não instalada não cerca nada.
- **Escopo cortado por ele: Bash/PowerShell fica fora.** Parsear shell é heurística — dá falso positivo e
  ainda assim é furada. Ficou só nos tools de escrita, onde o caminho é campo estruturado (decisão exata,
  zero falso positivo) — e foi o vetor real do acidente ("mudou tudo lá" = arquivos alterados).
- **Falso positivo que eu quase criei: worktree.** O próprio kit recomenda `using-git-worktrees`, e
  worktree fica **fora** da pasta do projeto — a cerca ingênua quebraria o fluxo da casa. Resolvido
  comparando `git rev-parse --git-common-dir` (mesmo repo = libera), não por heurística de nome de pasta.
- **Autocrítica na revisão (virou commit próprio):** eu tinha feito a sonda de worktree **falhar aberta** —
  ou seja, bastaria o `git` faltar no PATH pra cerca sumir sozinha. Corrigido: essa sonda **falha
  fechada** (sem git não existe worktree a liberar). O fail-open geral (entrada malformada, âncora
  indeterminável, bug do hook) ficou — cerca com defeito não pode travar trabalho legítimo dentro do
  projeto.
- **Limite declarado, não escondido:** o kit está instalado por **junction** (skills-dir plugin) e o
  carregamento de hooks pelo `plugin.json` nesse modo **não pôde ser verificado na sessão** (hooks carregam
  na partida, e o hook nasceu no meio dela). Virou canário no `hooks/README.md` + **Próximo passo** do MAPA,
  com fallback de registro no `settings.json`.
- **Achado de reboque:** o molde do `CLAUDE.md` ganhou uma regra crítica nova **antes** do placeholder da
  regra do projeto, então o `upgrade` (categoria 2) passou a avisar pra **renumerar** em vez de sobrescrever
  a regra do owner — e a referência velha "a regra 7" no `upgrade.md` já estava defasada.

## Rejeitado
- **Só prosa, sem hook** — foi justamente a prosa que faltou/falhou; regra sem cerca deixa o risco intacto.
- **Hook opt-in** (coerente com a filosofia antiga) — cerca que o dev precisa instalar não cerca nada.
- **Hook que pede confirmação** em vez de negar — um "sim" distraído reabre o buraco.
- **Vigiar Bash/PowerShell** por heurística de shell, e **vigiar leitura** (ler outro projeto é o
  *objetivo* do `precedentes`).
- **Check "a cerca está ativa?" no `/mss-spec:doctor`** — fora do escopo acordado; o canário manual cobre.
- **Desfazer o dano no projeto B** — isso é `git` na janela **do B**, não daqui.

## Fizemos
3 camadas: regra crítica **8** do `templates/CLAUDE.md` (+ "um assunto **e um projeto** por janela") ·
read-only no ponto de contágio (`precedentes-msig`, `commands/precedentes.md`, passo do `nova-feature`) ·
`hooks/projeto_ativo.py` (`PreToolUse` em `Write|Edit|NotebookEdit`, ligado no `plugin.json` via
`hooks/hooks.json`; libera dentro da âncora/temp/`~/.claude`/worktree do mesmo repo; escape
`MSS_ANCORA_OFF=1`; deny pelos 2 protocolos em UTF-8). Costuras: `hooks/README.md` (as duas filosofias de
hook lado a lado), `LEIA-ME` (4ª rede de segurança), `upgrade` (renumeração), PLANO-TESTE (baseline 91).
15 testes de comportamento + 4 de wiring → suíte **91 verde** (era 72); bump **0.15.0** nos 2 manifestos +
CHANGELOG. Branch `feature/ancora-projeto-ativo`, 5 commits.

## Próximo
**Canário em sessão nova**: pedir escrita num caminho de outro projeto e esperar `[mss-spec] BLOQUEADO`. Se
não bloquear, registrar o hook à mão no `settings.json` (snippet no `hooks/README.md`). Depois integrar e
**publicar** a 0.15.0 — sem push, nenhum outro projeto recebe a cerca nem a regra (que lá chega pelo
`/mss-spec:upgrade`). Em seguida, o primeiro uso real do `/mss-spec:analise` no projeto de RAG/pgvector,
que continua na fila.

## Emenda (mesma sessão, 0.15.1) — a face de leitura
Depois de integrar a 0.15.0, o owner trouxe um **segundo relato do mesmo assunto** (print de outra
janela): o assistente passou **5 minutos varrendo o disco** atrás do projeto `evolution-go` e do compose
dele — *"gastando tokens a toa para tentar achar!!"*, *"não é para investigar, me pergunte"*. A 0.15.0
cercou a face de **escrita**; faltava a de **leitura**: **como se chega** ao outro projeto.

- **Pivô:** a causa do **repeteco** não era falta de aprendizado — a regra existia (reclamada em 24/07,
  caso do projeto `Energy`), mas morava **só** em `~/.claude/projects/<proj>/memory/`, pasta **volátil e
  por-projeto**: não valia numa janela de outro projeto. Conserto de verdade = **cravar no
  `templates/CLAUDE.md`**, que o kit copia pra todo projeto; o resgate da memória pro repo é secundário.
  Confirma a regra da casa: **memória de um projeto não protege os outros**.
- **Decisão:** ficou **só prosa**, sem cerca determinística — bloquear busca por heurística barraria a
  leitura legítima que o próprio `precedentes` exige (o mesmo argumento que deixou Bash fora da cerca).
- **Não gravado aqui:** o caminho concreto do `evolution-go` que o owner passou. É fato do **outro**
  projeto — vai na memória dele, numa janela aberta lá; e o catálogo de precedentes é portável por regra
  (só caminho relativo). Coerente com "um projeto por janela".
- **Feito:** bullet "PERGUNTE, não vasculhe" no molde do `CLAUDE.md` + emenda na regra 8 · aviso na skill
  e no `commands/precedentes.md` · `memory/feedback_perguntar_em_vez_de_vasculhar.md` resgatado pro repo
  (+ ponteiro no `MEMORY.md`) · `test_perguntar_nao_vasculhar` → suíte **92 verde** · bump **0.15.1**.
