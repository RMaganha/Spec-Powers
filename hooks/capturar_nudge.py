"""Hook do mss-spec: LEMBRETE DE CAPTURA — avisa o owner quando a conversa anda há tempo sem captura de memória.

Até a 0.49.0 era opt-in e desligado por padrão (decisão de 2026-07-30: "hook-lembrete continua opt-in").
0.50.0 (caso F-048): a conversa da tarde de 2026-10-30 no Whats gravou EVALS e specs e encerrou sem diário,
e a captura dependia de alguém lembrar de digitar `/mss-spec:memory capturar`. O owner: *"sempre chamar o
diário"*. Passa a vir **ligado** no `Stop`, **por sessão** e **sem bloquear**: o aviso vai pro owner
(`systemMessage`), que é quem digita o comando — a cobrança dura da memória sem diário é do `diario_junto.py`.

Contrato:
- evento `Stop`; estado por sessão no temp do SO (`mss_captura_<sessao>.json`): o 1º Stop da conversa só
  marca o começo; depois, passado `INTERVALO` (30 min, `MSS_CAPTURA_INTERVALO_S`) sem captura → aviso;
- captura = Write/Edit em `memory/sessions/` no transcript; captura dentro do intervalo → calado e rearma;
- `MSS_CAPTURA_INTERVALO_S=0` → avisa em todo Stop (uso em teste);
- **nunca bloqueia** (exit 0 sempre) e **não grava nada** — só lembra; **falha ABERTA**;
- escape consciente, só do owner: `MSS_CAPTURA_NUDGE_OFF=1`; registra `lembrou` no registro local.
"""
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone


try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None

try:
    from _transcricao import gravacoes as _gravacoes
except Exception:                                    # noqa: BLE001
    def _gravacoes(_):
        return []


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("capturar_nudge", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_CAPTURA_NUDGE_OFF"
ENV_INTERVALO = "MSS_CAPTURA_INTERVALO_S"
INTERVALO_PADRAO_S = 1800  # ~30 min de conversa
NUDGE = ("[mss-spec] Esta conversa anda há mais de {min} min sem captura de memória. Se fechou um raciocínio, uma "
         "decisão ou um diagnóstico, rode /mss-spec:memory capturar — grava a memória E o diário da sessão "
         "(memory/sessions/). Escape: MSS_CAPTURA_NUDGE_OFF=1.")


def deve_cutucar(ultimo_ts, agora, intervalo_s):
    """Decisão pura de throttle: cutuca se nunca cutucou ou se já passou o intervalo."""
    if ultimo_ts is None:
        return True
    return (agora - ultimo_ts) >= intervalo_s


def _texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else ""


def _estado(sessao, ambiente):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    pasta = _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()
    return os.path.join(pasta, f"mss_captura_{seguro}.json")


def _ler_marca(sessao, ambiente):
    try:
        with open(_estado(sessao, ambiente), encoding="utf-8") as f:
            return float(json.load(f).get("marca"))
    except Exception:                                # noqa: BLE001
        return None


def _gravar_marca(sessao, ambiente, marca):
    try:
        with open(_estado(sessao, ambiente), "w", encoding="utf-8") as f:
            json.dump({"marca": float(marca)}, f)
    except Exception:                                # noqa: BLE001
        pass


def _epoch(ts_iso):
    try:
        return datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except Exception:                                # noqa: BLE001
        return None


def ultima_captura(transcript_path):
    """Epoch do último Write/Edit em `memory/sessions/` no transcript, ou None."""
    ultimo = None
    for ts, _, caminho in _gravacoes(transcript_path):
        p = str(caminho).replace("\\", "/").lower()
        if "/memory/sessions/" in ("/" + p.lstrip("/")) and p.endswith(".md"):
            e = _epoch(ts) if ts else None
            if e is not None and (ultimo is None or e > ultimo):
                ultimo = e
    return ultimo


def decidir(evento, ambiente=None, agora=None):
    """Texto do aviso (str) ou None = calado. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)):
            return None
        if not isinstance(evento, dict) or evento.get("hook_event_name") != "Stop":
            return None
        agora = time.time() if agora is None else float(agora)
        try:
            intervalo = int(ambiente.get(ENV_INTERVALO, INTERVALO_PADRAO_S))
        except (TypeError, ValueError):
            intervalo = INTERVALO_PADRAO_S
        sessao = evento.get("session_id")
        if intervalo <= 0:
            _anotar("lembrou", "intervalo=0", evento)
            return NUDGE.format(min=0)
        captura = ultima_captura(evento.get("transcript_path"))
        if captura is not None and agora - captura < intervalo:
            _gravar_marca(sessao, ambiente, captura)       # capturou há pouco: rearma e cala
            return None
        marca = _ler_marca(sessao, ambiente)
        if marca is None:
            _gravar_marca(sessao, ambiente, agora)          # 1º Stop da conversa: só marca o começo
            return None
        if not deve_cutucar(marca, agora, intervalo):
            return None
        _gravar_marca(sessao, ambiente, agora)
        _anotar("lembrou", f"sem_captura_ha={int((agora - marca) // 60)}min", evento)
        return NUDGE.format(min=int((agora - marca) // 60))
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    aviso = decidir(evento)
    if aviso is None:
        sys.exit(0)
    print(json.dumps({"systemMessage": aviso}))      # aviso ao owner; stdout comum do Stop não chega a ninguém
    sys.exit(0)                                       # SEMPRE 0 — não-bloqueante


if __name__ == "__main__":
    main()
