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
O motor de casamento é o de `templates/memoria_indice.py` (a reserva do `/mss-spec:memory buscar`, que desde a
0.56.0 busca primeiro na tabela de memória). Este aviso só troca pro motor da tabela depois de medido e com a
decisão do owner (`docs/specs/memoria-em-tabela.md`, decisão 21).
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


def regra(evento, ambiente, tem_memoria, motor):
    """A REGRA, sem disco: `tem_memoria(raiz)` diz se o projeto tem a pasta `memory/` e `motor()` devolve o
    `templates/memoria_indice.py` (ou o de teste) — quem lê a memória pra casar é o motor. Devolve
    `(resposta, mudancas)`: o dict pra imprimir ou None (silêncio); mudancas tem `"anotacoes"`. Qualquer defeito →
    None (falha aberta; `MSS_RECALL_DEBUG=1` mostra o traceback)."""
    mudancas = {"anotacoes": []}
    try:
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None, mudancas
        if not isinstance(evento, dict):
            return None, mudancas
        prompt = evento.get("prompt")
        if not isinstance(prompt, str) or prompt.lstrip().startswith("/"):
            return None, mudancas
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip():
            return None, mudancas
        proj = Path(raiz)
        if not tem_memoria(proj):
            return None, mudancas
        m = motor()
        toks, _ = m.tokens(prompt)
        if len(toks) < MIN_TOKENS_PROMPT:
            return None, mudancas
        texto = m.formatar_injecao(m.casar(proj, prompt, limite=LIMITE, diario=False))
        if not texto:
            return None, mudancas
        # só o ponteiro (arquivo:linha), nunca o prompt nem o resumo da memória
        ponteiros = [l[2:].split(" — ")[0] for l in texto.splitlines() if l.startswith("- ")]
        mudancas["anotacoes"].append(("injetou", ", ".join(ponteiros)))
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": texto}}, mudancas
    except Exception:                                # noqa: BLE001 — falha ABERTA
        if str((ambiente or os.environ).get(ENV_DEBUG, "")).strip():
            traceback.print_exc(file=sys.stderr)
        return None, {"anotacoes": []}


def responder(evento, ambiente=None):
    """A casca: a regra com o disco e o motor de verdade; grava o registro. dict pra imprimir, ou None = silêncio."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        resposta, mudancas = regra(evento, ambiente, lambda proj: (proj / "memory").is_dir(), _motor)
        for decisao, detalhe in mudancas["anotacoes"]:
            _anotar(decisao, detalhe, evento)
        return resposta
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def saida(resposta):
    """O que o processo imprime, ou None (calado)."""
    return None if resposta is None else json.dumps(resposta, ensure_ascii=False)


def main():
    try:
        from _entrada import ler_evento          # UTF-8, seja qual for a página de código do console
        evento = ler_evento()
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    impresso = saida(responder(evento))
    if impresso is None:
        sys.exit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print(impresso)
    sys.exit(0)


if __name__ == "__main__":
    main()
