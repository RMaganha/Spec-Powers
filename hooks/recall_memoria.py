"""Hook do mss-spec: RECALL DETERMINÍSTICO — aponta a memória que casou com o prompt.

Por que existe: num projeto grande o owner voltava às conversas antigas e re-explicava ao assistente
onde um assunto já tinha sido tratado. A memória estava no repo; o índice de 25 KB estava na janela;
ninguém abria a linha certa. Aqui o Python casa o prompt com `gatilho:`/índice/diário/decisões/EVALS
e injeta só os ponteiros (≤ 600 bytes). Zero tokens pra buscar; ~80 tokens quando acha.

Contrato:
- evento `UserPromptSubmit`; **nunca bloqueia** (rede, não cerca) — saída é `additionalContext`;
- silêncio (stdout vazio, exit 0) quando: nada casa · prompt começa com `/` (comando tem ritual
  próprio) · prompt com < 4 tokens úteis · projeto sem `memory/`;
- projeto = `CLAUDE_PROJECT_DIR` (âncora da janela), fallback `cwd` do evento;
- **falha ABERTA**: qualquer exceção → exit 0 calado (`MSS_RECALL_DEBUG=1` mostra o traceback);
- escape consciente, só do owner: `MSS_RECALL_OFF=1`.
O motor de casamento é o de `templates/memoria_indice.py` (o mesmo do `/mss-spec:memory buscar`).
"""
import json
import os
import sys
import traceback
from pathlib import Path


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
            _registrar("recall_memoria", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass

ENV_DESLIGA = "MSS_RECALL_OFF"
ENV_DEBUG = "MSS_RECALL_DEBUG"
MIN_TOKENS_PROMPT = 4
LIMITE = 3


def _motor():
    """Importa templates/memoria_indice.py pelo caminho do plugin (hooks/ e templates/ são irmãos)."""
    import importlib.util
    caminho = Path(__file__).resolve().parent.parent / "templates" / "memoria_indice.py"
    spec = importlib.util.spec_from_file_location("memoria_indice", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None
        if not isinstance(evento, dict):
            return None
        prompt = evento.get("prompt")
        if not isinstance(prompt, str) or prompt.lstrip().startswith("/"):
            return None
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip():
            return None
        proj = Path(raiz)
        if not (proj / "memory").is_dir():
            return None
        motor = _motor()
        toks, _ = motor.tokens(prompt)
        if len(toks) < MIN_TOKENS_PROMPT:
            return None
        texto = motor.formatar_injecao(motor.casar(proj, prompt, limite=LIMITE))
        if not texto:
            return None
        # só o ponteiro (arquivo:linha), nunca o prompt nem o resumo da memória
        ponteiros = [l[2:].split(" — ")[0] for l in texto.splitlines() if l.startswith("- ")]
        _anotar("injetou", ", ".join(ponteiros), evento)
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": texto}}
    except Exception:                                # noqa: BLE001 — falha ABERTA
        if str((ambiente or os.environ).get(ENV_DEBUG, "")).strip():
            traceback.print_exc(file=sys.stderr)
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    saida = responder(evento)
    if saida is None:
        sys.exit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print(json.dumps(saida, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
