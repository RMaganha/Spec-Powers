Catorze hooks, em duas filosofias **opostas** — de propósito: **cerca** (bloqueia, vem ligada) × **rede** (cutuca, avisa).
Os catorze anotam no **registro local** cada vez que **agem** (seção no fim deste arquivo).

| Hook | Evento | Estado | Bloqueia? | Papel |
|---|---|---|---|---|
| `projeto_ativo.py` | `PreToolUse` Write/Edit/NotebookEdit | **ligado por padrão** | **sim** (nega) | cerca: escrita só no projeto ativo |
| `git_publicacao.py` | `PreToolUse` Bash/PowerShell | **ligado por padrão** | **sim** (nega · ou pede aprovação) | cerca: push em homologação/produção e deploy é ato do owner; merge/rebase/push de feature pedem aprovação · e pytest mascarado por pipe antes do `git commit` (F-025) · e **nega** gravar em OUTRO repositório pelo shell, com o comando pronto pra colar na janela dele (F-031) · e nega **uma vez por sessão** o comando que casa o `gatilho_comando:` de uma memória, com ela no motivo (F-034) |
| `um_item_por_janela.py` | `UserPromptSubmit` | **ligado por padrão** | **sim** (bloqueia o prompt) | cerca: o mesmo chat não abre 2ª feature enquanto a dele estiver aberta; outras abertas no INDEX só geram aviso (pasta em outra feature → parar e perguntar) |
| `capturar_nudge.py` | `Stop` | **ligado por padrão** (0.50.0) | não (avisa o owner) | rede: conversa há 30 min sem captura → `systemMessage` ao owner: rode `/mss-spec:memory capturar` (memória e diário juntos); por sessão (F-048) |
| `recall_memoria.py` | `UserPromptSubmit` | **ligado por padrão** | não (só injeta) | rede: aponta a memória/decisão que casou com o prompt (diário de sessão fica fora — F-030) |
| `alerta_contexto.py` | `UserPromptSubmit` + `PostToolUse` | **ligado por padrão** | não (só avisa) | rede: janela ≥ 75% → feche o assunto, to-dolist, `/clear` |
| `confere_citacoes.py` | `Stop` | **ligado por padrão** | devolve a resposta **uma vez** | rede: a resposta cita arquivo/`:linha`, `/mss-spec:<x>` ou `F-0NN` que não existe no disco → volta pra corrigir ou dizer "não sei" (F-035) · também rotas alternativas não pedidas (F-033) e o `gatilho_resposta:` de uma memória (F-034) |
| `teto_ao_gravar.py` | `PostToolUse` Write/Edit/MultiEdit/Bash/PowerShell | **ligado por padrão** | não (move e avisa) | rede: gravou MAPA/INDEX acima do teto → o excesso sai na hora pra arquivo próprio, com ponteiro (F-030) |
| `orcamento_partida.py` | `SessionStart` | **ligado por padrão** | não (só avisa) | rede: partida acima do teto → diz o que estourou, o que ler e que backlog não é fato (F-030) |
| `regras_do_kit.py` | `SessionStart` (2 entradas: `--bloco 1` e `--bloco 2`) | **ligado por padrão** | não (só injeta) | rede: projeto com a marca `<!-- mss-spec:regras-do-kit -->` no `CLAUDE.md` recebe as regras do kit (modo de trabalho · regras críticas) em toda janela; **falha visível** |
| `regra_antes_de_gravar.py` | `PreToolUse` Write/Edit/MultiEdit | **ligado por padrão** | **sim** (nega **uma vez** por sessão e por regra) | cerca: gravar arquivo que casa o `paths:` de uma regra de `.claude/rules/` (com subpastas; só em projeto com a marca) nega uma vez, com o texto da regra no motivo; a 2ª gravação passa; o `/compact` zera o estado |
| `sem_worktree.py` | `WorktreeCreate` + `PreToolUse` (EnterWorktree/Agent/Write/Edit/MultiEdit/NotebookEdit/abrir conversa) + `SessionStart` | **ligado por padrão** | **sim** (nega · criação falha) | cerca: nunca worktree, nunca conversa aberta a partir de outra (0.46.0) |
| `kit_primeiro.py` | `PreToolUse` Skill/Read + `UserPromptSubmit` | **ligado por padrão** | **sim** (nega) | cerca: skill do `superpowers:*` só por dentro de um comando do kit — sem `/mss-spec:<x>` digitado, invocado ou lido na conversa, a skill é negada com a porta certa (bug · nova-feature · duvida · analise) (0.50.0, F-048) |
| `diario_junto.py` | `Stop` | **ligado por padrão** | devolve a resposta (por memória nova) | cerca: gravou memória (`memory/*.md`, `docs/EVALS.md`, `docs/decisoes.md`) sem o diário da sessão (`memory/sessions/`) → a resposta volta pedindo o diário (0.50.0, F-048) |

---

# Hook ligado — o kit entra primeiro

`kit_primeiro.py` nega qualquer skill `superpowers:*` enquanto **nenhum comando do kit** tiver entrado na
conversa. Entrar pelo kit é: o owner digitar `/mss-spec:<x>` (`UserPromptSubmit`), o assistente invocar
`mss-spec:<x>` pela ferramenta `Skill`, ou ler `commands/<x>.md` do kit (`PreToolUse` em `Read` — é assim
que rodam os comandos `disable-model-invocation`, como o `nova-feature`). O estado é **por sessão**
(`mss_kit_primeiro_<sessao>.json` no temp do SO).

**Por que existe (caso F-048):** na conversa "Validar mensagens WhatsApp em produção" (Whats, 2026-10-30),
*"vamos tratar aqui mesmo o bug"* virou `superpowers:systematic-debugging` direto, sem o `/mss-spec:bug`; o
passo 1 do bug (memória, spec e diário antes da 1ª hipótese) não aconteceu e a hipótese errada
(`MITI_DEV_AUTH`) ocupou 23 minutos. A regra 11 e o `bug.md` (2026-10-27) já mandavam entrar pelo kit; o
`superpowers:using-superpowers` manda "bug → systematic-debugging primeiro". Prosa contra prosa, ganhou a
do superpowers — por isso cerca, não prosa. O superpowers continua sendo chamado, mas de dentro do comando
do kit, no passo certo.

**Formato da negativa:** o mesmo do `git_publicacao.py` (JSON `deny` no stdout + motivo no stderr + exit 2),
que já funciona ao vivo. Falha aberta; escape só do owner: `MSS_KIT_PRIMEIRO_OFF=1`; registra `negou`.

---

# Hook ligado — diário junto da memória

`diario_junto.py` (evento `Stop`) lê no transcript o que o assistente **gravou** nesta conversa. Gravou
memória — `memory/<arquivo>.md` (fora `MEMORY.md`, `DIARIO.md` e subpastas como `indice/`), `docs/EVALS.md`
ou `docs/decisoes.md` — e nenhum `memory/sessions/<data>-<assunto>.md`? A resposta **volta** pedindo o
diário (JSON `block`, exit 0), com a lista do que foi gravado. Cobra **uma vez por arquivo de memória**:
memória nova depois da cobrança cobra de novo; `stop_hook_active` deixa sair (nunca laço). Estado por sessão
no temp do SO.

**Por que existe (caso F-048):** a conversa da tarde de 2026-10-30 no Whats gravou `docs/EVALS.md` (F-093,
F-094) e duas specs e encerrou sem diário — o problema que ficou aberto (resposta do especialista que não
volta pro WhatsApp em produção) não ficou escrito em lugar nenhum. O owner: *"o diário tem que ser junto
com a memória, assim que gravar ela"*. O `/mss-spec:memory capturar` já grava os dois; o hook cobra quando a
memória foi gravada por fora dele. Falha aberta; escape só do owner: `MSS_DIARIO_JUNTO_OFF=1`; registra
`devolveu`.

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
- **worktree do MESMO repo** — comparando o `git rev-parse --git-common-dir` (não é "outro projeto");
  gravar dentro de worktree é negado por outra cerca, a `sem_worktree.py` (0.46.0);
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

Mesmo canário pras outras duas cercas: peça um `git push --dry-run origin main` (tem que vir `[mss-spec] BLOQUEADO`) e,
no **mesmo chat**, digite `/mss-spec:nova-feature canario-a` e depois `/mss-spec:nova-feature canario-b` (o 2º
prompt tem que ser bloqueado dizendo que o chat já é da `canario-a`; num chat novo, o `canario-b` passa).

---

# Hook ligado — push em homologação/produção é ato do owner (`git_publicacao.py`)

**Por que existe (acidente real, caso F-022, 2026-09):** numa janela aberta pra **uma** feature, o
assistente absorveu um 2º e um 3º assunto, mesclou branches e **disparou `git push`** — e o push é o
gatilho do deploy automático em homologação. Quando o owner viu, vários já tinham ido. A homologação
quebrou inteira e custou centenas de testes pra entender o quê. A frase *"`git push` só quando eu
pedir"* **já estava** no `CLAUDE.md` e foi ignorada: prosa não segura na hora 2 de uma sessão longa.

**Por que mudou (0.31.0):** a 1ª versão negava **todo** push/merge/rebase e travou o dia a dia —
merge local, push de branch de feature, até `git merge-base` (que só lê; o registro gravou a recusa).
O dano do F-022 veio do push que faz **deploy**: é isso que segue negado. O resto virou **pedido de
aprovação** — o owner vê o comando e aprova com um clique.

Evento `PreToolUse`, matcher `Bash|PowerShell`, lê `tool_input.command`:

| Comando | Decisão |
|---|---|
| `git push` pra branch **protegida** — `main`, `master`, `dev`, `develop`, `production`, `homolog*`, `hml*`, `prod*`, `release/*` — por refspec (`origin dev`, `HEAD:dev`, `x:main`, `--delete main`) | **nega** |
| `git push` sem refspec estando numa protegida, ou com o `@{push}` apontando pra uma (feature que rastreia `origin/dev`) | **nega** |
| `git push` de destino indeterminável: `--all`, `--mirror`, `--tags`, `:`, HEAD destacado, git que não responde | **nega** |
| deploy e integração remota: `gh pr merge`, `docker push`, `az acr build`, `az webapp <escrita>`, `az containerapp update\|create\|revision`, `az deployment … create\|delete\|cancel`, `az stack … create\|set\|delete` (receita Bicep do `/mss-spec:azure-ambiente` — `what-if`, `validate`, `show` passam) | **nega** |
| `git merge`, `git rebase` (menos `--abort`) e `git push` de feature/fix | **pede aprovação** (`"ask"`) |
| o resto: `merge-base`, `merge-tree`, `pull`, status, fetch, commit, checkout/branch, stash | passa calado |

Casa o **verbo no início de um comando simples** (e só o verbo inteiro — `merge` não casa
`merge-base`), não a palavra solta: `grep -rn 'git push' docs/` e `echo pushing` passam. Num comando
com várias ações, a mais grave vence (negar > pedir aprovação). Sem refspec, a cerca pergunta ao
**git da pasta do comando** (`-C <dir>` › último `cd <dir>` › `cwd`) a branch atual e o `@{push}`.

**Pedido de aprovação:** `permissionDecision: "ask"` com exit 0 — o app (Desktop incluso) mostra o
comando e o motivo, e o owner aprova ou recusa. Segundo a doc de permissões do Claude Code, o hook
não fura as regras de permissão (uma regra `ask` pede aprovação mesmo se o hook liberar).

**O que o assistente faz no push protegido:** roda `/mss-spec:release` (gate de pré-publicação),
cola o veredito e **pede** — o owner publica do terminal dele (hook não roda no terminal humano).

## Garantias

- **Falha FECHADA** onde importa: há comando e a avaliação estourou → **nega** com o motivo
  "cerca com defeito"; push sem destino explícito e git que não responde → **nega** ("não deu pra
  saber"). É o oposto da cerca da âncora, de propósito: uma escrita barrada por engano custa um
  `MSS_ANCORA_OFF=1`; um push que passa por engano custa um ambiente. Evento **sem comando**
  (malformado) libera calado — não existe push num evento vazio.
- **Calado quando libera**; ao negar, os dois protocolos (`permissionDecision: "deny"` no stdout +
  exit 2 com motivo no stderr); ao pedir aprovação, só o JSON e exit 0 (exit 2 ignoraria o `ask`).
- **Falso bloqueio conhecido:** feature cujo nome **começa** com `prod`/`hml`/`homolog` (ex.:
  `produto-x`) conta como protegida — use `feature/produto-x`.
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
- Não é "hook de pre-commit bloqueante" (`#fora-de-escopo` no `to-dolist.md`): não roda teste nem trava commit —
  só recusa o comando que **esconde** o resultado do teste.

---

# Hook ligado — um item por janela (`um_item_por_janela.py`)

**Por que existe:** mesmo acidente do F-022. A regra "um assunto por janela" existia como **alerta**
("é alerta, não trava") e ficou muda enquanto a janela de uma feature virava três assuntos. Agora é
trava mecânica no ponto onde dá: **abrir feature nova**.

Evento `UserPromptSubmit`: só age quando o prompt é `/mss-spec:nova-feature <nome>` (ou
`/nova-feature <nome>`) — qualquer outro texto passa calado. **Conta por chat** (desde a 0.34.0):
guarda qual feature cada chat abriu em `~/.claude/mss-spec/um-item-janelas.json`
(chave `session_id` + projeto → feature + quantas linhas estavam fechadas; um por máquina,
fora de qualquer repo; chat parado há mais de 30 dias sai — retomar renova; `MSS_UM_ITEM_ESTADO` troca
o caminho). No `<cwd>/docs/superpowers/INDEX.md`, **aberta** é a
linha com status `aberta` ou `em andamento` (`fechada` e `pausada: <motivo>` não contam; `## Backlog`
é ignorado, e a seção "Fora de escopo" do formato antigo também, só até o `upgrade` converter o projeto).

- **este chat já abriu a feature Y**, Y não está `fechada`/`pausada` (no INDEX ou no
  `INDEX-historico.md`; fora do INDEX Y segue valendo — a linha só nasce no passo 3) e o pedido é
  outra → **bloqueia o prompt** e manda abrir **um chat novo** (lá passa), ou continuar Y, ou o owner
  marcar Y `pausada: <motivo>` à mão, ou mandar o assunto novo pro `/mss-spec:to-dolist adicionar`;
- **chat novo** (ou Y encerrada) com feature aberta de **outro** chat no INDEX → **passa com aviso**
  listando as abertas e lembrando que duas features na mesma pasta trocam a branch uma da outra (pasta
  na branch de outra feature → **parar e perguntar ao owner**; nunca worktree nem outra conversa) — `systemMessage` pro terminal + `additionalContext` pro assistente repassar no Desktop;
- o **nome** é só o resto da linha do comando (as linhas de baixo são contexto; comando sozinho na
  linha = sem nome); a linha do chat é achada **só pelo nome**, por palavra inteira (`ui` não casa com `guia`; nome de 1 palavra só casa igual), e **encerrada** só se toda linha que casa estiver `fechada`/`pausada` (a `v1` fechada não encerra a `v2` nem a `busca vetorial hibrida` abertas). Linha nova em que nenhum nome contém o outro **não** é atribuída ao chat — o INDEX não diz qual chat a escreveu. Sem linha pelo nome, a feature do chat só conta como encerrada se nada está aberto no INDEX e alguma linha fechou desde a abertura; senão bloqueia dizendo que não achou a linha (custo aceito: título do passo 3 sem que um nome contenha o outro + outra feature aberta → o chat sai por chat novo);
- **a mesma** (por nome ou pelo slug da spec, sem acento/caixa), **sem nome**, **sem `session_id`**,
  **nenhuma aberta** ou projeto **sem INDEX** → passa calado.

Por que por chat e não por projeto: contando por projeto (0.26.0 a 0.33.0), com features abertas em
outros chats o chat **novo** também não abria nada — no Whats, 6 abertas travaram o comando e o owner
passou a tirar o `nova-feature` do prompt (o ritual deixou de rodar, como no F-030).

2ª camada: o **passo 0** do `commands/nova-feature.md` faz o mesmo check em prosa, pra quando o hook
não disparar.

## Garantias

- **Falha ABERTA**: entrada malformada ou bug → libera e sai 0. Apagar o prompt do owner por defeito
  do hook seria pior que a regra não disparar uma vez (e o passo 0 cobre).
- **Calado quando libera**; ao bloquear, `{"decision": "block", "reason": …}` no stdout + exit 2 com o
  motivo no stderr (é o que o owner vê no terminal); ao avisar, exit 0 com `systemMessage` +
  `hookSpecificOutput.additionalContext`. Estado ilegível → vazio; defeito ao gravar não muda a decisão.
- **Escape consciente só do owner:** `MSS_UM_ITEM_OFF=1`.

---

# Hook ligado — lembrete de captura (`capturar_nudge.py`)

`capturar_nudge.py` (evento `Stop`) avisa o **owner** quando a conversa anda há tempo sem captura de memória.
**Não bloqueia** e **nunca grava** nada: o aviso sai como `systemMessage` ("rode `/mss-spec:memory capturar`"),
porque é o owner quem digita o comando — e o comando grava a memória **e** o diário. A cobrança dura (memória
gravada sem diário) é do `diario_junto.py`.

**Como decide (por sessão):** o 1º `Stop` da conversa só marca o começo. Passados 30 min
(`MSS_CAPTURA_INTERVALO_S`, em segundos) sem nenhum Write em `memory/sessions/` no transcript → aviso, e
remarca. Captura dentro do intervalo → calado e rearma a partir dela. `MSS_CAPTURA_INTERVALO_S=0` avisa em
todo `Stop` (teste). Estado em `mss_captura_<sessao>.json` no temp do SO — duas conversas não se misturam.

## Por que passou a vir ligado (0.50.0, F-048)

Até a 0.49.0 era **opt-in e desligado** (decisão de 2026-07-30: "hooks podem falhar em silêncio; depender deles
seria frágil"). A conversa da tarde de 2026-10-30 no Whats gravou EVALS e specs e encerrou **sem diário** — a
captura dependia de alguém lembrar. O owner: *"sempre chamar o diário"*. Como o hook só avisa, falhar em
silêncio custa um lembrete, não um dado; e o diário tem a cerca própria.

## Como desligar ou ajustar

- `MSS_CAPTURA_NUDGE_OFF=1` — escape consciente, só do owner.
- `MSS_CAPTURA_INTERVALO_S=<segundos>` — intervalo (padrão 1800).

## Garantias

- **Não grava** memória/diário/decisão — só lembra.
- **Não bloqueia** — sai sempre com código 0; **falha ABERTA** (defeito → calado).
- Registra `lembrou` no registro local.

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

# Hook ligado — confere citações (`confere_citacoes.py`)

**Por que existe (F-035):** "não inventar fatos concretos" era só prosa. A doc da Anthropic sobre alucinação manda permitir o "não sei" e verificar cada afirmação contra a fonte; a parte que se verifica sem LLM é a citação. Evento `Stop`: lê `last_assistant_message` (ou a última resposta no transcript) e confere, fora de bloco de código, caminho em `crase` ou em link (com `:linha`, a linha tem de existir), `/mss-spec:<x>` e `F-0NN` (se o projeto tem `docs/EVALS.md`). Caminho vale no projeto ou no kit, inteiro ou como final de um caminho que existe; molde do kit (`docs/SEGURANCA.md` ← `templates/SEGURANCA.md`) conta. Não confere URL, glob, placeholder, texto com espaço, nem linha que **propõe** ("→", "criar", "novo", "vai para", "vira") ou **nega** ("não existe"). Achou o que não existe → **devolve a resposta uma vez** (exit 2, motivo no stderr em UTF-8); com `stop_hook_active` deixa sair. Medido em 121 respostas reais: 0 devolução nas sessões dentro do próprio projeto; as 7 que sobram são desta janela citando arquivos do Whats.

**0.36.0 — mesma devolução, mais duas conferências:** resposta com ≥ 2 rotas alternativas ("Rota 1", "Opção A"…) acima de 300 palavras sem o pedido falar em opção (F-033; medido: só a do caso em 201 respostas reais) e resposta que casa o `gatilho_resposta:` de uma memória do projeto ou do kit (F-034; uma vez por sessão por memória). O lado do comando mora no `git_publicacao.py`: `gatilho_comando:` casou → nega uma vez por sessão, repetir passa (medido: 6 de 957 comandos, um por sessão, todos heredoc de Python com acento). Escape `MSS_MEMORIA_ACAO_OFF=1`. O motivo vai por `print` comum no stderr, como nos outros hooks.

**0.50.0 — a devolução passa a sair pelo contrato do `Stop` (F-048):** JSON `{"decision": "block", "reason": …}`
no stdout com **exit 0**. Até a 0.49.0 era `exit 2` + motivo no stderr, e nesta máquina isso **nunca chegou**: o Git
Bash imprime `setlocale: LC_ALL: cannot change locale (enu): No such file or directory` no stderr de todo hook, e o
Claude Code lê "No such file or directory" com exit 2 como *"Hook script appears to be missing"* — a devolução virava
erro não-bloqueante. Medido nas transcrições (Whats e kit, 2026-09-25 a 2026-10-30): pelo menos 40 devoluções,
nenhuma entregue. Os hooks com exit 0 + JSON sempre chegaram, com o mesmo stderr. O `doctor` avisa quando `LC_ALL`
está assim.

## Garantias

- **Uma vez por turno**, nunca laço. **Falha ABERTA**. Sem citação inválida → calado, custo zero de token.
- **Escape consciente só do owner:** `MSS_CITACOES_OFF=1`.

---

# Hook ligado — teto ao gravar (`teto_ao_gravar.py`)

**Por que existe (F-030):** quem escreve no MAPA/INDEX (`/mss-spec:mapa`, `nova-feature`, `memory capturar`) só
acrescenta. O `doctor` media e o hook de abertura avisava, mas o conserto dependia de alguém rodar o rodízio — e o
Whats chegou a 160 KB de partida. Aqui o conserto roda na própria gravação.

Evento `PostToolUse` (Write/Edit/MultiEdit pelo `file_path`; Bash/PowerShell quando o comando cita o arquivo **e**
o arquivo mudou agora: mtime dentro de `JANELA_S` = 120 s e `(tamanho, mtime_ns)` diferente do último visto nesta
sessão, guardado no temp do SO — ler com `wc -c CLAUDE.md` ou `cat INDEX.md` cita o nome, mas não é gravação; comando cuja 1ª palavra é `git` — `git add CLAUDE.md`, `git commit` — nunca conta).
Gravou `docs/superpowers/MAPA.md` ou `INDEX.md` e passou do teto → `rodizio_partida.py enxugar --aplicar`, que
**move, nunca apaga**, confere a conservação e para assim que cabe: 1º o rodízio de sempre (blocos antigos e
fechadas pro histórico); depois, no INDEX, `## Backlog` → `BACKLOG.md` · `## Fora de escopo` → `FORA-DE-ESCOPO.md`
(formato antigo, só até o `upgrade` converter pro `to-dolist.md`; o recall não lê) · `## Assuntos existentes` → `ASSUNTOS-EXISTENTES.md` · linha longa de `## Em andamento`
→ `EM-ANDAMENTO.md` (fica nome/link — ponteiro — status verbatim, que a trava lê); no MAPA, `## Conexões` →
`CONEXOES.md` (fica a lista de nomes) e, se ainda não couber, só o bloco atual fica. Destino que já existe recebe
prepend datado. O `additionalContext` diz o que foi pra onde e manda **reler antes do próximo Edit**; o que sobra
acima do teto é conteúdo vivo e o hook pede o resumo pra spec. `CLAUDE.md` acima de 10,0 KB: **só avisa** (escolher o
destino de um bloco de regra é julgamento — F-029): com a marca das regras do kit manda mover um bloco inteiro com
ponteiro; **sem** a marca manda rodar `/mss-spec:upgrade`. Arquivo com conflito de merge não é tocado.

## Garantias

- **Nunca bloqueia** — sai sempre 0. **Falha ABERTA**. Dentro do teto → calado.
- **Escape consciente só do owner:** `MSS_TETO_OFF=1`.

---

# 3ª cerca no `git_publicacao.py` — outro projeto pelo shell (F-031)

A âncora (`projeto_ativo.py`) só vigia Write/Edit. Pelo shell, a janela do kit enxugou e commitou o Whats inteiro
(`cd <Whats> && git checkout -b … && git commit`, `--proj <Whats> --aplicar`). Agora, no mesmo processo da cerca de
publicação: **nega** o comando que **grava** num repositório git **diferente** do da âncora — git de escrita
(`add`, `commit`, `checkout`, `switch`, `branch <nome>`, `merge`, `rebase`, `reset`, `stash`, `tag <nome>`, `push`…)
na pasta de `-C` › último `cd` › cwd; `--proj <dir>` junto de `--aplicar`; `>`/`>>`/`tee` pra dentro dele (corpo de
heredoc não conta). "Outro projeto" é **identidade de repositório**, não heurística de caminho: pasta fora de repo
(Downloads, temp) e worktree do mesmo repo passam (worktree é negado pela 5ª cerca, abaixo); leitura (`status`, `log`, `diff`, `branch --show-current`,
`tag --list`) passa. A mensagem traz a raiz do outro projeto e o **comando verbatim** pra colar numa janela aberta
lá (decisão do owner: negar sempre e entregar o comando). Negar vence o "pedir aprovação" do merge. **Falha
ABERTA**; escape = o da âncora, `MSS_ANCORA_OFF=1`. **Brecha declarada:** script que grava com o caminho escrito
DENTRO dele não aparece no comando.

---

# Hook ligado — nunca worktree, nunca conversa a partir de outra (`sem_worktree.py`, 0.46.0)

**Por que existe:** em 2026-10-27 a conversa da 0.44.0 abriu sozinha `.claude/worktrees/partida-em-dois-niveis` —
o aviso do kit mandava ("abra esta num worktree") — e deixou 2 commits e memória fora da `main`; e duas conversas
abertas a partir de outra ficaram penduradas uma na outra na barra lateral. O owner não usa nenhum dos dois.

- `WorktreeCreate` → **falha sempre** (porta única de criação do Claude Code: `EnterWorktree`, subagente/workflow
  com `isolation: "worktree"`, sessão de fundo). O hook **substitui** a criação, então o escape não vale aqui;
- `PreToolUse` → **nega** `EnterWorktree` (entrar num que já existe), `Agent` com `isolation: "worktree"`, escrita
  com o alvo dentro de um worktree, e `mcp__ccd_session__start_session`/`hand_off_to_session` — a mensagem manda
  entregar o **texto pronto pra colar** e o owner abre a conversa pelo **+**;
- `SessionStart` → **avisa** quando a conversa já começa dentro de um worktree;
- **5ª cerca no `git_publicacao.py`** (shell): nega `git worktree add` e comando que grava dentro de um worktree.

## Garantias
- "Dentro de um worktree" é lido do arquivo `.git` (`gitdir:` em `…/worktrees/…`), sem rodar o git; submódulo não conta.
- Criar/entrar/abrir conversa nega sempre; "está dentro?" **falha ABERTA** (ilegível → libera).
- Escape consciente, só do owner: `MSS_WORKTREE_OFF=1` (menos no `WorktreeCreate`). Spec `docs/specs/nunca-trabalhar-em-worktree.md`.

---

# Hook ligado — orçamento da partida (`orcamento_partida.py`)

**Por que existe (F-030):** o Whats abria a janela com `CLAUDE.md` 28 KB + `MAPA.md` 60 KB + `INDEX.md`
71 KB — 73 mil → 139 mil tokens antes da 1ª resposta — e item velho de backlog entrou num plano de deploy
como se fosse o estado atual. O `doctor` (check 9) media isso, mas ninguém roda o doctor antes de cada janela.

Evento `SessionStart`. Mede em bytes, na raiz (`CLAUDE_PROJECT_DIR` › `cwd`): `CLAUDE.md` 10 KB ·
`docs/superpowers/MAPA.md` 6 KB · `docs/superpowers/INDEX.md` 7 KB · `memory/MEMORY.md` 6 KB (os tetos do
`tests/test_orcamento_contexto.py` e do `rodizio_partida.py`; um teste trava os três). Algum acima →
`additionalContext` (≤ 1.000 bytes) com o que estourou, o que ler de cada um (MAPA → `## Onde estamos`;
INDEX → `## Em andamento`; o resto por `grep`), "backlog, fora de escopo e diário não são o estado atual"
e "avise o owner" com o conserto: `CLAUDE.md` sem a marca → `/mss-spec:upgrade`; com a marca → mover bloco com
ponteiro; `/mss-spec:doctor` só quando estoura MAPA/INDEX/MEMORY. Tamanhos em KB com uma casa
(`10,1 KB (teto 10,0 KB)`). + `systemMessage` de 1 linha. **Não move nada**: mover é
decisão do owner (`rodizio_partida.py`, dry-run, janela própria no projeto).

## Garantias

- **Nunca bloqueia** — sai sempre 0. **Falha ABERTA**: defeito → calado. Tudo no teto → calado.
- **Escape consciente só do owner:** `MSS_ORCAMENTO_OFF=1`.

---

# Hook ligado — regras do kit pelo plugin (`regras_do_kit.py`)

**Por que existe:** as regras do kit (modo de trabalho · regras críticas) viviam coladas no `CLAUDE.md` de
cada projeto — cópia que envelhece e não acompanha o plugin. Agora moram em `templates/regras-do-kit/`
(`1-modo-de-trabalho.md` · `2-regras-criticas.md`) e este hook as injeta. O `CLAUDE.md` do projeto só carrega
a **marca**, numa linha sozinha: `<!-- mss-spec:regras-do-kit -->`.

Evento `SessionStart` (startup, resume, clear, compact), sem `matcher`. **Duas entradas** em `hooks.json`
(`regras_do_kit.py --bloco 1` e `--bloco 2`): o Claude Code corta cada `additionalContext` em 10.000
caracteres (acima disso o texto vira arquivo e só uma prévia de 2.000 chega ao modelo), então cada bloco é
uma string própria, com limite de **9.000 caracteres** (`LIMITE`). Na raiz (`CLAUDE_PROJECT_DIR` › `cwd`):
`CLAUDE.md` com a marca (vale com BOM e CRLF) → injeta o bloco; sem a marca → silêncio (projeto fora do kit
não recebe nada).

## Garantias

- **Nunca bloqueia** — sai sempre 0, inclusive com entrada ou `--bloco` malformados.
- **Falha visível (a exceção desta pasta):** os outros hooks falham ABERTO e calados; este não. Sem ele a
  janela abre sem as regras e ninguém percebe. Depois de confirmada a marca, bloco ilegível, acima de
  9.000 caracteres ou qualquer defeito → `systemMessage` de 1 linha (`regras do kit não carregaram — rode
  /mss-spec:doctor`), **nunca** bloco truncado. Antes da marca, defeito → calado.
- **Escape consciente só do owner:** `MSS_REGRAS_KIT_OFF=1`.

---

# Hook ligado — regra por tipo de arquivo antes de gravar (`regra_antes_de_gravar.py`)

**Por que existe:** as regras de caminho do projeto (`.claude/rules/*.md`, frontmatter `paths:`) carregam
quando o assistente **lê** um arquivo que casa. Quando ele **cria** um arquivo novo, ou edita sem ler antes,
a regra não carrega — no Whats, `banco.md` faltou em 5 conversas que criaram arquivos em `sql/`.

Evento `PreToolUse`, matcher `Write|Edit|MultiEdit`. O caminho a gravar, relativo à raiz do projeto
(`CLAUDE_PROJECT_DIR` › `cwd`), é comparado com o `paths:` de cada `.claude/rules/*.md` (`**`, `*`, `?`;
`\` vale `/`; maiúsculas não contam). Casou e a regra ainda não foi mostrada nesta sessão → **nega**, com o
texto da regra (sem o frontmatter) no motivo e "repita a gravação"; a 2ª tentativa passa. Várias regras no
mesmo arquivo → uma negação só, com todos os textos. O estado "já mostrada" fica no temp do SO
(`mss_regra_antes_<sessão>.json`).

Só age em projeto do kit: o `CLAUDE.md` da raiz precisa ter a marca `<!-- mss-spec:regras-do-kit -->`. As regras são lidas de `.claude/rules/` **com as subpastas** (como a migração faz); regra que ficou só com título e comentário HTML não nega. O `/compact` tira o texto da regra do contexto, então uma 2ª entrada `SessionStart` com `matcher: compact` roda `regra_antes_de_gravar.py --zerar`, que apaga o estado da sessão — a regra volta a ser mostrada.

## Garantias

- **Nunca trava por defeito próprio** — sai sempre 0. **Falha ABERTA**: frontmatter quebrado, regra ilegível
  ou bug → silêncio. Caminho fora da raiz do projeto nunca casa; regra sem `paths:` é ignorada.
- **Escape consciente só do owner:** `MSS_REGRA_OFF=1`.

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
| `git_publicacao` | `negou` · `perguntou` | `git push → dev`, `git push indeterminado`, `docker push`… · `git merge`, `git push → feature/x` · `pytest em pipe antes do git commit` · `defeito da cerca` |
| `projeto_ativo` | `negou` | o tool (`Write`/`Edit`) — **não** o caminho |
| `um_item_por_janela` | `bloqueou` · `avisou` | `abertas=N` |
| `recall_memoria` | `injetou` | os ponteiros (`docs/decisoes.md:25`, `memory/x.md`) |
| `alerta_contexto` | `avisou` | `faixa=85 pct=86 janela=1000000 modelo=claude-opus-5-5` |
| `capturar_nudge` | `lembrou` | — |
| `orcamento_partida` | `avisou` | `MAPA.md=60098 INDEX.md=70720` |
| `regra_antes_de_gravar` | `negou` | os nomes das regras (`banco.md`) — **não** o caminho |
| `regras_do_kit` | `entregou` · `falhou` | `bloco=1 caracteres=5604` · `bloco=2 FileNotFoundError` |
| `confere_citacoes` | `devolveu` | `citacoes=2` · `rotas` · `memoria=<nome>` — nunca o texto da resposta |
| `teto_ao_gravar` | `moveu` · `avisou` | `INDEX.md=70546->1892` · `CLAUDE.md=27933` |

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
