Seis hooks, em duas filosofias **opostas** — de propósito: **cerca** (bloqueia, vem ligada) × **rede** (cutuca, opt-in).
Os seis anotam no **registro local** cada vez que **agem** (seção no fim deste arquivo).

| Hook | Evento | Estado | Bloqueia? | Papel |
|---|---|---|---|---|
| `projeto_ativo.py` | `PreToolUse` Write/Edit/NotebookEdit | **ligado por padrão** | **sim** (nega) | cerca: escrita só no projeto ativo |
| `git_publicacao.py` | `PreToolUse` Bash/PowerShell | **ligado por padrão** | **sim** (nega) | cerca: publicar/integrar/deploy é ato do owner · e pytest mascarado por pipe antes do `git commit` (F-025) |
| `um_item_por_janela.py` | `UserPromptSubmit` | **ligado por padrão** | **sim** (bloqueia o prompt) | cerca: feature nova só sem feature aberta |
| `capturar_nudge.py` | `Stop`/`PreCompact` | opt-in, off | não | rede: lembra de capturar memória |
| `recall_memoria.py` | `UserPromptSubmit` | **ligado por padrão** | não (só injeta) | rede: aponta a memória/decisão/diário que casou com o prompt |
| `alerta_contexto.py` | `UserPromptSubmit` + `PostToolUse` | **ligado por padrão** | não (só avisa) | rede: janela ≥ 75% → feche o assunto, to-dolist, `/clear` |

---

# Hook ligado — cerca do projeto ativo (âncora)

`projeto_ativo.py` é a **única camada que não depende de o assistente se comportar**. Evento
`PreToolUse`, matcher `Write|Edit|NotebookEdit`: **nega** escrita fora do **projeto ativo** (a âncora
= a raiz onde a janela abriu, de `CLAUDE_PROJECT_DIR`, com o `cwd` do evento como fallback).

**Por que existe (acidente real):** o owner trabalhava no projeto A, pediu *"olha como o projeto B
resolveu isso"* — e o assistente adotou o B como projeto de trabalho, editou arquivos lá e **quebrou
o B**. O `/mss-spec:precedentes` manda, corretamente, abrir o código do outro projeto; o que faltava
era dizer que aquilo é **somente leitura**. A regra em prosa (regra crítica 8 do `CLAUDE.md`) é a 1ª
linha; este hook é a 2ª — e é a que não esquece.

**Por que vem ligado** (ao contrário do nudge abaixo): hook que falha em silêncio é ruim pra *lembrete*,
mas cerca **não instalada** não cerca nada. O custo de o hook não disparar é voltar ao estado anterior
(só a prosa); o custo de não existir é o acidente se repetir.

## O que ele libera (pra não virar tranca)

- **dentro da âncora** — inclusive caminho relativo (resolve contra a âncora);
- **temp do SO** (`TEMP`/`TMP`/`TMPDIR`) e **`~/.claude`** — scratchpad e config global não são "outro
  projeto". *Ressalva honesta: com o kit instalado por junction em `~/.claude/skills/`, a cerca não
  protege o próprio kit — que é versionado, então o git é o rollback.*
- **worktree do MESMO repo** — comparando o `git rev-parse --git-common-dir`; sem isso, a cerca
  quebraria o fluxo `superpowers:using-git-worktrees` que o próprio kit recomenda;
- **`MSS_ANCORA_OFF=1`** — escape consciente, decisão do owner.

## Garantias

- **Falha ABERTA** onde importa: entrada malformada, âncora indeterminável ou exceção daqui → libera e
  sai **0**. Cerca com defeito não pode parar o trabalho legítimo dentro do próprio projeto.
  **Uma exceção deliberada:** a *sonda de worktree* falha **FECHADA** (git ausente/antigo/travado →
  nega) — sem git não existe worktree a liberar, e tratar isso como "indeterminado, libera" daria um
  jeito trivial de a cerca sumir (bastaria o git faltar no PATH).
- **Não vigia leitura** — ler outro projeto é o *objetivo* do `precedentes`.
- **Não vigia Bash/PowerShell** — decisão do owner: parsear shell é heurística, dá falso positivo e
  ainda assim é furada. Shell fica coberto só pela prosa.
- **Calado quando libera** (nada de poluir o contexto); ao negar, emite os **dois** protocolos de deny:
  `hookSpecificOutput.permissionDecision: "deny"` no stdout **e** exit code 2 com o motivo no stderr.

## Se não disparar (fallback)

O kit costuma estar instalado como **skills-dir plugin** (junction em `~/.claude/skills/mss-spec`), e
nesse modo o carregamento de hooks pelo `plugin.json` **precisa ser confirmado na prática** — **confirmado em 2026-09-15** no projeto Whats: o `recall_memoria.py` disparou numa janela nova sem nada em `settings.json`. Teste
depois de recarregar a sessão: peça uma escrita num caminho de outro projeto — tem que ser negada com
a mensagem `[mss-spec] BLOQUEADO`. Se passar (não bloqueou), registre à mão no seu `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit|NotebookEdit",
        "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/projeto_ativo.py\"" } ] },
      { "matcher": "Bash|PowerShell",
        "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/git_publicacao.py\"" } ] }
    ],
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/um_item_por_janela.py\"" } ] }
    ]
  }
}
```

Mesmo canário pras outras duas cercas: peça um `git push --dry-run` (tem que vir `[mss-spec] BLOQUEADO`) e,
com uma feature `aberta` no INDEX, digite `/mss-spec:nova-feature outra-coisa` (o prompt tem que ser
bloqueado com a lista das abertas).

---

# Hook ligado — publicar e integrar é ato do owner (`git_publicacao.py`)

**Por que existe (acidente real, caso F-022, 2026-09):** numa janela aberta pra **uma** feature, o
assistente absorveu um 2º e um 3º assunto, mesclou branches e **disparou `git push`** — e o push é o
gatilho do deploy automático em homologação. Quando o owner viu, vários já tinham ido. A homologação
quebrou inteira e custou centenas de testes pra entender o quê. A frase *"`git push` só quando eu
pedir"* **já estava** no `CLAUDE.md` e foi ignorada: prosa não segura na hora 2 de uma sessão longa.

Evento `PreToolUse`, matcher `Bash|PowerShell`, lê `tool_input.command` e **nega** o que:
- **publica**: `git push` (qualquer forma: `-u`, `--force*`, `-C <dir>`, encadeado com `;`/`&&`/`|`,
  prefixo `VAR=x`, PowerShell);
- **integra**: `git merge`, `git rebase` (menos `--abort`, que desfaz), `gh pr merge`;
- **faz deploy**: `docker push`, `az acr build`, `az webapp <escrita>` (`log`/`show`/`list` passam),
  `az containerapp update|create|revision`.

Casa o **verbo no início de um comando simples**, não a palavra solta — `grep -rn 'git push' docs/`
e `echo pushing` passam. **Libera o resto do git**: status, log, diff, fetch, add, commit,
checkout/switch/branch (abrir a branch da feature continua livre), stash.

**O que o assistente faz no lugar:** roda `/mss-spec:release` (gate de pré-publicação), cola o
veredito e **pede** — o owner publica/integra do terminal dele (hook não roda no terminal humano).

## Garantias

- **Falha FECHADA** onde importa: há comando e a avaliação estourou → **nega** com o motivo
  "cerca com defeito". É o oposto da cerca da âncora, de propósito: uma escrita barrada por engano
  custa um `MSS_ANCORA_OFF=1`; um push que passa por engano custa um ambiente. Evento **sem
  comando** (malformado) libera calado — não existe push num evento vazio.
- **Calado quando libera**; ao negar, os dois protocolos (`permissionDecision: "deny"` no stdout +
  exit 2 com motivo no stderr).
- **Escape consciente só do owner:** `MSS_PUBLICACAO_OFF=1` (no `settings.json`, bloco `env`). Não há
  escape por argumento do assistente.

## 2ª cerca no mesmo processo — pytest mascarado por pipe (caso F-025)

**Por que existe:** `python -m pytest -q 2>&1 | tail -1 && git commit …` **commitou com 2 testes
vermelhos** (`edc0ab9`, 2026-09-15). Num pipe, o código de saída é o do **último** comando (o `tail`),
e o `&&` só olha esse. A memória `feedback_pipe_mascara_o_exit_do_teste` foi escrita e **não bastou**:
reincidiu em `f9388e5` — prosa não chega no momento do atalho.

**Nega** quando o mesmo comando tem o **pytest como comando** (`pytest`, `py.test`, `<python> -m
pytest`) com a saída num `|` e um **`git commit` depois**, sem `pipefail`. Passam: `pytest && git
commit` (o commit depende do exit real), `pytest | tail` sem commit, `set -o pipefail; …`, `grep
pytest … | …` (a palavra como texto) e o teste **depois** do commit. PowerShell também é pego
(`| Select-Object -Last 1; git commit`).

- **Mora no `git_publicacao.py`** porque é o mesmo evento (`PreToolUse` Bash/PowerShell): um hook
  separado custaria ~190 ms a mais em **todo** comando de shell (medido: a partida do Python).
- **Modo de falha PRÓPRIO — ABERTA**: bug aqui → libera. Commit vermelho se reverte; push não — por
  isso a cerca de publicação segue FECHADA e é avaliada primeiro. Uma não liga nem desliga a outra.
- **Escape próprio, só do owner:** `MSS_PIPE_TESTE_OFF=1`.
- Não é "hook de pre-commit bloqueante" (fora de escopo no INDEX): não roda teste nem trava commit —
  só recusa o comando que **esconde** o resultado do teste.

---

# Hook ligado — um item por janela (`um_item_por_janela.py`)

**Por que existe:** mesmo acidente do F-022. A regra "um assunto por janela" existia como **alerta**
("é alerta, não trava") e ficou muda enquanto a janela de uma feature virava três assuntos. Agora é
trava mecânica no ponto onde dá: **abrir feature nova**.

Evento `UserPromptSubmit`: só age quando o prompt é `/mss-spec:nova-feature <nome>` (ou
`/nova-feature <nome>`) — qualquer outro texto passa calado. Lê `<cwd>/docs/superpowers/INDEX.md`
e considera **aberta** a linha de item com status `aberta` ou `em andamento` (`fechada` e
`pausada: <motivo>` não contam; a seção "Fora de escopo" é ignorada).

- **outra aberta** → **bloqueia o prompt** (apaga e mostra o motivo) listando as abertas e as três
  saídas honestas: terminar a aberta, o owner marcar `pausada: <motivo>` à mão, ou mandar o assunto
  novo pro `/mss-spec:to-dolist adicionar`;
- **a mesma** (por nome ou pelo slug da spec, sem acento/caixa) → passa — retomar não é misturar;
- **nenhuma aberta**, ou projeto **sem INDEX** → passa.

2ª camada: o **passo 0** do `commands/nova-feature.md` faz o mesmo check em prosa, pra quando o hook
não disparar.

## Garantias

- **Falha ABERTA**: entrada malformada ou bug → libera e sai 0. Apagar o prompt do owner por defeito
  do hook seria pior que a regra não disparar uma vez (e o passo 0 cobre).
- **Calado quando libera**; ao bloquear, `{"decision": "block", "reason": …}` no stdout + exit 2 com o
  motivo no stderr (é o que o owner vê no terminal).
- **Escape consciente só do owner:** `MSS_UM_ITEM_OFF=1`.

---

# Hook opt-in — nudge de captura de memória

`capturar_nudge.py` é um hook **opt-in**, **desligado por padrão** e **não-bloqueante**. Ele **só cutuca** — nunca grava nada sozinho — pra lembrar de rodar `/mss-spec:memory capturar` quando faz tempo desde a última captura.

**A fonte da verdade é o comando**, rodado no fecho da feature (o `nova-feature` já delega a ele). Este hook é só a **rede** pra quando o dev esquece de capturar no meio de uma conversa longa. **Se o hook não disparar, nada se perde** — o passo determinístico do fecho cobre.

## Por que não vem ligado

O kit **não registra** este hook no `plugin.json` de propósito: hooks podem **falhar em silêncio** (não disparar sem erro visível), então depender deles seria frágil. Você habilita conscientemente, sabendo que é best-effort.

## Como habilitar (no `settings.json` do seu projeto/usuário)

Não existe hook nativo "a cada X minutos" no Claude Code — os eventos são por-evento. Os que mais se aproximam:

- **`Stop`** — ao fim de cada resposta do assistente. Com o *throttle* embutido (arquivo de timestamp), o nudge só aparece a cada ~30 min de conversa (ajustável pela env `MSS_CAPTURA_INTERVALO_S`, em segundos).
- **`PreCompact`** — antes de a conversa ser compactada (o momento em que contexto está prestes a se perder — ótimo pra capturar antes).

Exemplo (registre o que quiser — só `Stop`, só `PreCompact`, ou os dois):

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/capturar_nudge.py\"" } ] }
    ],
    "PreCompact": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/capturar_nudge.py\"" } ] }
    ]
  }
}
```

## Garantias

- **Não grava** memória/diário/decisão — só imprime o lembrete (o `stdout` entra no contexto do assistente).
- **Não bloqueia** — sai sempre com código 0.
- **Throttle** — respeita `MSS_CAPTURA_INTERVALO_S` (padrão 1800s) via um timestamp em `%TEMP%`, pra não cutucar a cada mensagem.

---

# Hook ligado — recall determinístico

`recall_memoria.py` casa cada prompt do owner com os `gatilho:` das memórias, as linhas de
`memory/indice/*.md` (ou do `MEMORY.md` plano), o gist do `DIARIO.md`, as `docs/decisoes.md` e a coluna
gatilho do `docs/EVALS.md`, e injeta **só os 3 melhores ponteiros** (≤ 600 bytes) como
`additionalContext`. Nada casou → silêncio. Motor: `templates/memoria_indice.py` (o mesmo do
`/mss-spec:memory buscar`).

**Por que existe:** num projeto com 93 memórias o índice de 25 KB estava na janela e mesmo assim o owner
voltava às conversas antigas pra re-explicar onde o assunto tinha sido tratado. Recall que depende de o
modelo lembrar de abrir o arquivo não é recall.

**Por que vem ligado e não bloqueia:** custo de disparar = ~80 tokens quando casa, zero quando não; custo
de não existir = o owner virar índice humano. Ignora `/comando` e prompt com < 4 tokens úteis.

**Falha ABERTA:** exceção → exit 0 calado (`MSS_RECALL_DEBUG=1` mostra o traceback). Escape consciente,
só do owner: `MSS_RECALL_OFF=1`.

---

# Hook ligado — alerta de contexto (`alerta_contexto.py`)

**Por que existe:** a janela aberta pra UM assunto vira **bola de neve** — *"pra fechar A preciso
entender B"*, B puxa C — e o contexto enche sem ninguém ver, até a compactação automática (que só
dispara perto do limite e resume o que não devia). "Um assunto por janela" é prosa; a % da janela é
número, e número dá pra vigiar.

Eventos `UserPromptSubmit` (antes de cada prompt do owner) e `PostToolUse` (no meio de uma rodada
longa, quando não há prompt). **Hook não recebe a % da janela** — só a statusline recebe (doc do
Claude Code). A % sai do transcript: a **última** mensagem do assistente fora de subagente
(`isSidechain` falso) traz `message.usage`; contexto = `input_tokens` + `cache_read_input_tokens` +
`cache_creation_input_tokens`. Lê só a cauda do arquivo (512 KB).

- **limiar** 75% (`MSS_ALERTA_CONTEXTO_PCT`, 1–99). É **escolha do owner**: a documentação da
  Anthropic **não** fixa um número "saudável" — ela só compacta perto do limite. 75% deixa folga pra
  fechar o assunto antes disso;
- **janela** (nenhum hook a recebe; só o `SessionStart` às vezes recebe o `model`) =
  `MSS_JANELA_TOKENS` › `CLAUDE_CODE_AUTO_COMPACT_WINDOW` › `[1m]` no id ou uso acima de 200 mil →
  1.000.000 › **família 5** (`claude-opus-5-5`, `claude-sonnet-5`, `claude-fable-5-1` — o id no
  transcript vem **sem** `[1m]`) → 1.000.000 › 200.000 (4.x, Haiku). Modelo novo que fuja da regra:
  `MSS_JANELA_TOKENS`. Caso **F-027**: com 200 mil fixo, o hook dizia 92% onde o app mostrava
  184,8k / 1M (18%);
- **uma vez por faixa** (75 · 85 · 95) por sessão, somando os dois eventos; caiu abaixo do limiar
  (depois de `/compact`) → rearma. Estado em `%TEMP%/mss_alerta_contexto_<sessão>.txt`;
- **saída**: `additionalContext` manda o assistente abrir a próxima mensagem com o aviso e fechar a
  janela (estado no `MAPA.md`, sobra no `/mss-spec:to-dolist adicionar`, `/clear`) — porque o
  `systemMessage` **não aparece no app Desktop**; o `systemMessage` vai junto pra quem usa terminal;
- ignora evento de **subagente** (`agent_id`): a janela dele não é a do owner.

## Garantias

- **Nunca bloqueia** — sai sempre 0. **Falha ABERTA**: defeito → calado.
- **Calado** abaixo do limiar e na faixa já avisada.
- **Escape consciente só do owner:** `MSS_ALERTA_CONTEXTO_OFF=1`.

---

# Registro local — o que os hooks FIZERAM (`_registro.py`)

**Por que existe:** os hooks decidem calados, e ninguém consegue dizer quanto eles valem — quantas
vezes a cerca de publicação barrou um push, se o recall aponta a memória certa, se o alerta de
contexto calcula a janela certa. O caso **F-027** (o alerta dizia 92% onde o app mostrava 18%) só
apareceu porque o owner comparou com o print do app. Com o registro, isso vira número.

Cada hook, **só quando age**, anexa uma linha JSON em `~/.claude/mss-spec/registro-hooks.jsonl`
(um arquivo por máquina, fora de qualquer repo, com o nome da pasta do projeto em cada linha):

| hook | decisão | detalhe gravado |
|---|---|---|
| `git_publicacao` | `negou` | `git push`, `git merge`… · `pytest em pipe antes do git commit` · `defeito da cerca` |
| `projeto_ativo` | `negou` | o tool (`Write`/`Edit`) — **não** o caminho |
| `um_item_por_janela` | `bloqueou` | `abertas=N` |
| `recall_memoria` | `injetou` | os ponteiros (`docs/decisoes.md:25`, `memory/x.md`) |
| `alerta_contexto` | `avisou` | `faixa=85 pct=86 janela=1000000 modelo=claude-opus-5-5` |
| `capturar_nudge` | `lembrou` | — |

Ver o resumo (contagem por hook e decisão, os 3 detalhes mais comuns):

```
python hooks/_registro.py resumo            # tudo
python hooks/_registro.py resumo --dias 7   # só a última semana
```

## Garantias

- **Nunca grava o texto do prompt nem a linha de comando** — o detalhe é sempre um rótulo do
  próprio hook. Travado por teste com um segredo falso no comando, no prompt e no caminho.
- **Registro quebrado não muda decisão nenhuma** — disco cheio, pasta sem permissão, módulo
  ausente: o hook responde byte a byte igual (travado por teste nos seis). A cerca de publicação
  segue falhando FECHADA por conta dela, não do registro.
- **Passar calado não grava** (o `alerta_contexto` roda em todo `PostToolUse`; só a faixa nova vira linha).
- **Teto:** acima de 1 MB o arquivo vira `.1` (o `.1` anterior é descartado) — nunca cresce sem limite.
- **Custo:** anexar uma linha é < 1 ms, contra os ~190–260 ms que cada hook já gasta na partida do Python.
- **Escape consciente, só do owner:** `MSS_REGISTRO_OFF=1`. `MSS_REGISTRO_ARQUIVO` troca o caminho
  (a suíte usa, via `tests/conftest.py`, pra nunca sujar o registro real).
