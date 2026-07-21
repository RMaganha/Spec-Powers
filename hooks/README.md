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
