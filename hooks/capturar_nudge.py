"""Hook OPT-IN (experimental) do mss-spec: cutuca pra rodar /mss-spec:memory capturar.

NÃO grava nada e NÃO bloqueia — só emite um lembrete quando faz tempo desde a última
captura. A fonte da verdade é o comando (rodado no fecho da feature); este hook é só a
rede pra quando o dev esquece. Ver hooks/README.md.

Registrado (opt-in) nos eventos Stop e/ou PreCompact no settings.json do usuário.
Não existe hook nativo "a cada X min"; o throttle por timestamp aproxima isso.
"""
import os
import sys
import time


# Registro local do que este hook FEZ (`hooks/_registro.py`). Nunca muda a decisão: sem o módulo,
# ou com qualquer defeito dele, o hook segue exatamente igual.
try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("capturar_nudge", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass

NUDGE = ("[mss-spec] Faz um tempo desde a última captura de memória. "
         "Se fechou um raciocínio/decisão, rode /mss-spec:memory capturar "
         "pra não perder o diário desta sessão.")
INTERVALO_PADRAO_S = 1800  # ~30 min de conversa; ajustável por env MSS_CAPTURA_INTERVALO_S
STATE = os.path.join(os.environ.get("TEMP", "/tmp"), "mss_captura_ultimo.txt")


def deve_cutucar(ultimo_ts, agora, intervalo_s):
    """Decisão pura de throttle: cutuca se nunca cutucou ou se já passou o intervalo."""
    if ultimo_ts is None:
        return True
    return (agora - ultimo_ts) >= intervalo_s


def _ler_ultimo():
    try:
        with open(STATE, encoding="utf-8") as f:
            return float(f.read().strip())
    except (OSError, ValueError):
        return None


def _gravar_agora(agora):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            f.write(str(agora))
    except OSError:
        pass


def _evento_da_entrada():
    """O JSON do evento (só pro registro: projeto e sessão). Rodado à mão, sem stdin → {}."""
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        import json
        evento = json.load(sys.stdin)
        return evento if isinstance(evento, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def main():
    agora = time.time()
    try:
        intervalo = int(os.environ.get("MSS_CAPTURA_INTERVALO_S", INTERVALO_PADRAO_S))
    except ValueError:
        intervalo = INTERVALO_PADRAO_S
    if deve_cutucar(_ler_ultimo(), agora, intervalo):
        print(NUDGE)          # stdout do hook entra no contexto do assistente
        _gravar_agora(agora)
        _anotar("lembrou", "", _evento_da_entrada())
    sys.exit(0)               # SEMPRE 0 — não-bloqueante


if __name__ == "__main__":
    main()
