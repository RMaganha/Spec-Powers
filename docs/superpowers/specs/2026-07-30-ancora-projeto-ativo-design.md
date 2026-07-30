# Âncora do projeto ativo (um projeto por janela) — spec viva

<!-- Spec viva por assunto: "Estado atual" reflete como o comportamento está HOJE; o Histórico é a narrativa. -->

## Estado atual

O **projeto ativo é a âncora** da janela: a raiz onde ela abriu (`CLAUDE_PROJECT_DIR`, com o `cwd` do
evento como fallback). É o **único destino de escrita** da sessão, e **não migra** porque o assistente
foi ler outro repositório. Todo outro projeto é **referência somente-leitura**: `Read`/`Grep`/`Glob`
sim; `Write`/`Edit`, `git`, `pytest`, build, `npm install` ou "consertar de passagem", **nunca**. O
padrão encontrado lá é **trazido pra cá** (cópia pra dentro da âncora, com OK do owner); se a mudança
é mesmo no outro projeto, o assistente **para** e manda fechar a janela e abrir outra na raiz dele
(um assunto **e um projeto** por janela); se enxergou um bug lá, **reporta** (`/mss-spec:to-dolist`),
não conserta — não conhece o estado daquele repo nem tem os testes dele verdes na frente.

A fronteira tem **duas faces**. A de **escrita** é a âncora (acima). A de **leitura** é: pra chegar ao
outro projeto, **pergunte o caminho** — nunca varra o disco (`find`/`ls`/`Glob` de repositório em
repositório, `grep` em `C:\`). O owner sabe onde está na hora; procurar é lento, queima tokens e termina
em chute. Idem pro nome exato de um container, de uma variável de ambiente ou de qual arquivo é o compose
de lá. Busca no disco só **depois** que ele não souber, ou pra confirmar algo que ele já apontou. Essa
face é **só prosa** — e de propósito: bloquear busca por heurística barraria a leitura legítima que o
`precedentes` exige (mesmo argumento que deixou Bash/PowerShell fora da cerca). Ela mora no
`templates/CLAUDE.md` (bullet "PERGUNTE, não vasculhe" + emenda na regra 8), na skill de precedentes e
no `commands/precedentes.md`.

Isso vive em **três camadas**:

1. **Prosa sempre-ativa** — regra crítica **8** do `templates/CLAUDE.md` (+ a regra "um assunto por
   janela" virou "um assunto **e um projeto** por janela"). Chega nos projetos que já existem pelo
   `/mss-spec:upgrade` (categoria 2, mescla — que agora manda **renumerar** ao inserir regra nova do
   molde, em vez de sobrescrever a regra específica do projeto, que é sempre a última).
2. **Antídoto no ponto de contágio** — a seção read-only está escrita onde o kit *manda* abrir outro
   projeto: `skills/precedentes-msig/SKILL.md`, `commands/precedentes.md` e o passo de precedentes do
   `commands/nova-feature.md`. Onde o kit diz "abra o código real de lá", diz junto "e só leia".
3. **Cerca determinística** — `hooks/projeto_ativo.py`, hook `PreToolUse` com matcher
   `Write|Edit|NotebookEdit`, **ligado por padrão** (registrado em `hooks/hooks.json`, referenciado
   pelo `plugin.json`). Nega escrita fora da âncora com uma mensagem que manda abrir janela na raiz do
   outro projeto. Filosofia **oposta** à do `capturar_nudge.py` (opt-in, não-bloqueante), de propósito:
   hook que falha em silêncio é ruim pra *lembrete*, mas **cerca não instalada não cerca nada**.

A cerca libera, pra não virar tranca: dentro da âncora (inclusive caminho **relativo**, que resolve
contra ela); **temp do SO** (`TEMP`/`TMP`/`TMPDIR`) e **`~/.claude`**; **worktree do MESMO repo**
(compara `git rev-parse --path-format=absolute --git-common-dir` — sem isso quebraria o fluxo
`superpowers:using-git-worktrees` que o próprio kit recomenda); e o escape consciente
`MSS_ANCORA_OFF=1`. **Falha ABERTA** onde importa: entrada malformada, âncora indeterminável ou
exceção do próprio hook → libera e sai **0** — cerca com defeito não pode parar o trabalho legítimo
dentro do projeto. **Uma exceção deliberada:** a *sonda de worktree* falha **FECHADA** (git
ausente/antigo/travado → nega), porque sem git não existe worktree a liberar e "indeterminado libera"
ali seria um jeito trivial de a cerca sumir sozinha (bastaria o git faltar no PATH).
O deny sai pelos **dois** protocolos aceitos pelo runtime (`hookSpecificOutput.permissionDecision:
"deny"` no stdout **e** exit code 2 com o motivo no stderr), em UTF-8 forçado (no Windows o default
cp1252 quebraria os acentos da mensagem).

Comparação de caminho é sempre **normalizada** (`realpath` + `abspath` + `normcase`): no Windows
`C:\X\a` e `c:/x/a` são o mesmo caminho, e comparar cru daria falso positivo barrando escrita dentro
do próprio projeto. Junctions/symlinks resolvem — o que importa pro kit, instalado por junction.

**Ressalva honesta:** com o kit instalado como **skills-dir plugin** (junction em
`~/.claude/skills/mss-spec`), o carregamento de hooks pelo `plugin.json` **não foi verificado ao vivo**
(hooks são lidos na partida da sessão, e o hook nasceu no meio dela). O `hooks/README.md` traz o teste
de canário e o fallback de registro no `settings.json`. Segunda ressalva: por `~/.claude` estar na
allow-list, a cerca **não protege o próprio kit** quando alcançado pelo caminho da junction — ele é
versionado, então o git é o rollback.

**Fora de escopo:** vigiar **Bash/PowerShell** (decisão do owner — parsear shell é heurística, dá
falso positivo e ainda assim é furada; shell fica coberto só pela prosa) · vigiar **leitura** (ler
outro projeto é o *objetivo* do `precedentes`) · desfazer o dano já causado no projeto B (isso é
`git` na janela **do B**) · check no `/mss-spec:doctor` ("a cerca está ativa?").

## Histórico

- 2026-07-30 — criado: âncora do projeto ativo em 3 camadas (regra crítica 8 · read-only no
  `precedentes` · hook `PreToolUse` ligado por padrão). Motivo: acidente real — o owner trabalhava no
  projeto A, pediu *"olha como o projeto B resolveu isso, faça igual"*, e o assistente adotou o B como
  projeto de trabalho, alterou arquivos lá e **quebrou o projeto B**. Decisões do owner no design:
  cerca **ligada por padrão e bloqueante** (não opt-in, não "pede confirmação" — um "sim" distraído
  reabriria o buraco) e cobertura **só nos tools de escrita** (Bash fora). Fail-open foi decisão de
  engenharia: a cerca é 2ª linha, e travar o trabalho legítimo por bug dela custaria mais que o risco
  que ela cobre.
- 2026-07-30 — acrescentada a **face de leitura**: "PERGUNTE, não vasculhe" no molde do `CLAUDE.md`
  (bullet próprio + emenda na regra 8), na skill de precedentes e no `commands/precedentes.md` (motivo:
  segundo relato do mesmo dia — o assistente passou **5 minutos varrendo o disco** atrás do projeto
  `evolution-go` e do compose dele, "gastando tokens à toa", quando o owner teria dito o caminho na hora;
  já havia sido reclamado em 24/07 no caso do projeto `Energy`). Causa raiz do **repeteco**: o
  aprendizado existia só na pasta **volátil** `~/.claude/projects/<proj>/memory/`, que não viaja entre
  projetos — resgatado pro repo (`memory/feedback_perguntar_em_vez_de_vasculhar.md`) e, principalmente,
  cravado no molde que o kit copia pra todo projeto. Ficou **só prosa** por decisão de design: cerca
  determinística contra busca barraria a leitura legítima do `precedentes`.
