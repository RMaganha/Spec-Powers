Dois hooks, com filosofias **opostas** — de propósito:

| Hook | Estado | Bloqueia? | Papel |
|---|---|---|---|
| `projeto_ativo.py` | **ligado por padrão** (registrado no `plugin.json`) | **sim** (nega) | cerca: escrita só no projeto ativo |
| `capturar_nudge.py` | opt-in, off | não | rede: lembra de capturar memória |

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
nesse modo o carregamento de hooks pelo `plugin.json` **precisa ser confirmado na prática**. Teste
depois de recarregar a sessão: peça uma escrita num caminho de outro projeto — tem que ser negada com
a mensagem `[mss-spec] BLOQUEADO`. Se passar (não bloqueou), registre à mão no seu `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit|NotebookEdit",
        "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/projeto_ativo.py\"" } ] }
    ]
  }
}
```

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
