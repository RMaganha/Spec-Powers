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


def captura_mais_recente(gravs):
    """Epoch do último Write/Edit em `memory/sessions/` nas gravações `(ts, ferramenta, caminho)`, ou None."""
    ultimo = None
    for ts, _, caminho in gravs:
        p = str(caminho).replace("\\", "/").lower()
        if "/memory/sessions/" in ("/" + p.lstrip("/")) and p.endswith(".md"):
            e = _epoch(ts) if ts else None
            if e is not None and (ultimo is None or e > ultimo):
                ultimo = e
    return ultimo


def ultima_captura(transcript_path):
    """Epoch do último Write/Edit em `memory/sessions/` no transcript, ou None."""
    return captura_mais_recente(_gravacoes(transcript_path))


def regra(evento, ambiente, ler_gravacoes, ler_marca, agora):
    """A REGRA, sem disco: `ler_gravacoes()` devolve as gravações do assistente nesta conversa e `ler_marca(sessao)`
    a marca guardada (epoch ou None) — o disco, ou o de teste; só são chamadas quando a regra precisa. Devolve
    `(aviso, mudancas)`: o texto do aviso ou None = calado; mudancas tem `"anotacoes"` e, quando a marca muda,
    `"marca"` (o epoch a gravar). Qualquer defeito → None (falha aberta)."""
    mudancas = {"anotacoes": []}
    try:
        if _texto(ambiente.get(ENV_DESLIGA)):
            return None, mudancas
        if not isinstance(evento, dict) or evento.get("hook_event_name") != "Stop":
            return None, mudancas
        agora = float(agora)
        try:
            intervalo = int(ambiente.get(ENV_INTERVALO, INTERVALO_PADRAO_S))
        except (TypeError, ValueError):
            intervalo = INTERVALO_PADRAO_S
        if intervalo <= 0:
            mudancas["anotacoes"].append(("lembrou", "intervalo=0"))
            return NUDGE.format(min=0), mudancas
        captura = captura_mais_recente(ler_gravacoes())
        if captura is not None and agora - captura < intervalo:
            mudancas["marca"] = captura                     # capturou há pouco: rearma e cala
            return None, mudancas
        marca = ler_marca(evento.get("session_id"))
        if marca is None:
            mudancas["marca"] = agora                       # 1º Stop da conversa: só marca o começo
            return None, mudancas
        if not deve_cutucar(marca, agora, intervalo):
            return None, mudancas
        mudancas["marca"] = agora
        mudancas["anotacoes"].append(("lembrou", f"sem_captura_ha={int((agora - marca) // 60)}min"))
        return NUDGE.format(min=int((agora - marca) // 60)), mudancas
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None, {"anotacoes": []}


def decidir(evento, ambiente=None, agora=None):
    """A casca: a regra com o transcript e a marca do disco; grava a marca e o registro. Texto do aviso (str) ou
    None = calado. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        agora = time.time() if agora is None else float(agora)
        aviso, mudancas = regra(evento, ambiente, lambda: _gravacoes(evento.get("transcript_path")),
                                lambda sessao: _ler_marca(sessao, ambiente), agora)
        if "marca" in mudancas:
            _gravar_marca(evento.get("session_id"), ambiente, mudancas["marca"])
        for decisao, detalhe in mudancas["anotacoes"]:
            _anotar(decisao, detalhe, evento)
        return aviso
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def saida(aviso):
    """O que o processo imprime, ou None (calado): aviso ao owner — stdout comum do Stop não chega a ninguém."""
    return None if aviso is None else json.dumps({"systemMessage": aviso})


def main():
    try:
        from _entrada import ler_evento          # UTF-8, seja qual for a página de código do console
        evento = ler_evento()
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    impresso = saida(decidir(evento))
    if impresso is not None:
        print(impresso)
    sys.exit(0)                                       # SEMPRE 0 — não-bloqueante


if __name__ == "__main__":
    main()
