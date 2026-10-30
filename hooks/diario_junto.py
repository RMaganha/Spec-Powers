"""Hook do mss-spec: DIÁRIO JUNTO DA MEMÓRIA — memória gravada sem o diário da sessão não sai.

Por que existe (caso F-048, `docs/EVALS.md`): a conversa "Validar mensagens WhatsApp em produção" (Whats,
2026-10-30, tarde) gravou `docs/EVALS.md` (F-093, F-094) e duas specs, e encerrou sem `memory/sessions/…`:
o problema que ficou aberto (resposta do especialista que não volta pro WhatsApp em produção) não ficou
escrito em lugar nenhum do projeto. O owner: *"o diário tem que ser junto com a memória, assim que gravar
ela"*. O `/mss-spec:memory capturar` já grava os dois; este hook cobra quando a memória foi gravada por
fora dele.

Contrato:
- evento `Stop`; lê no `transcript_path` o que o assistente gravou (Write/Edit/MultiEdit/NotebookEdit);
- **memória** = `memory/<arquivo>.md` (fora `MEMORY.md`, `DIARIO.md` e subpastas como `indice/`),
  `docs/EVALS.md` ou `docs/decisoes.md`; **diário** = `memory/sessions/<x>.md`;
- gravou memória e nenhum diário → **devolve a resposta** pelo contrato do `Stop` (JSON
  `{"decision": "block", "reason": …}`, exit 0) pedindo o diário; cobra **uma vez por arquivo de memória**
  (memória nova depois da cobrança → cobra de novo); com `stop_hook_active` verdadeiro, deixa sair;
- estado por sessão no temp do SO (`mss_diario_junto_<sessao>.json`);
- **falha ABERTA**: defeito → exit 0 calado; escape consciente, só do owner: `MSS_DIARIO_JUNTO_OFF=1`;
- registra `devolveu` no registro local (`hooks/_registro.py`).
"""
import json
import os
import re
import sys
import tempfile


try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None

from _transcricao import gravacoes


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("diario_junto", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_DIARIO_JUNTO_OFF"
TOPO = ("memory.md", "diario.md")

MOTIVO = (
    "[mss-spec] Memória gravada sem o diário da sessão (caso F-048). Nesta conversa você gravou {n} arquivo(s) de "
    "memória — {lista} — e nenhum `memory/sessions/<data>-<assunto>.md`. Memória sem diário perde o contexto: o "
    "que foi pedido, o que foi rejeitado, o que ficou aberto. Antes de encerrar, grave "
    "`memory/sessions/<data>-<assunto>.md` (Conversamos · Pivôs · Rejeitado · Fizemos · Próximo) e a linha no "
    "`memory/DIARIO.md`, como no passo 2 do /mss-spec:memory capturar. Escape consciente, só do owner: "
    "MSS_DIARIO_JUNTO_OFF=1."
)


def _texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else ""


def classificar(caminho):
    """'memoria', 'diario' ou None, pelo caminho (absoluto ou relativo, `\\` ou `/`)."""
    p = "/" + str(caminho).replace("\\", "/").strip().lower().lstrip("/")
    if not p.endswith(".md"):
        return None
    if "/memory/sessions/" in p:
        return "diario"
    if p.endswith("/docs/evals.md") or p.endswith("/docs/decisoes.md"):
        return "memoria"
    if "/memory/" in p:
        resto = p.rsplit("/memory/", 1)[1]
        if "/" in resto or resto in TOPO:
            return None
        return "memoria"
    return None


def _estado(sessao, ambiente):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    pasta = _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()
    return os.path.join(pasta, f"mss_diario_junto_{seguro}.json")


def cobradas(sessao, ambiente):
    try:
        with open(_estado(sessao, ambiente), encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:                                # noqa: BLE001
        return set()


def marcar(sessao, ambiente, caminhos):
    try:
        with open(_estado(sessao, ambiente), "w", encoding="utf-8") as f:
            json.dump(sorted(cobradas(sessao, ambiente) | set(caminhos)), f)
    except Exception:                                # noqa: BLE001
        pass


def _curto(caminho):
    p = str(caminho).replace("\\", "/")
    for marca in ("/memory/", "/docs/"):
        if marca in p:
            return marca.strip("/") + "/" + p.rsplit(marca, 1)[1]
    return p


def decidir(evento, ambiente=None):
    """Motivo da devolução (str) ou None = libera. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)):
            return None
        if not isinstance(evento, dict) or evento.get("hook_event_name") != "Stop":
            return None
        if evento.get("stop_hook_active"):
            return None
        gravs = gravacoes(evento.get("transcript_path"))
        if not gravs:
            return None
        memorias, diario = set(), False
        for _, _, caminho in gravs:
            tipo = classificar(caminho)
            if tipo == "diario":
                diario = True
            elif tipo == "memoria":
                memorias.add(caminho.replace("\\", "/"))
        if diario or not memorias:
            return None
        sessao = evento.get("session_id")
        novas = memorias - cobradas(sessao, ambiente)
        if not novas:
            return None
        marcar(sessao, ambiente, memorias)
        _anotar("devolveu", f"memoria_sem_diario={len(novas)}", evento)
        lista = ", ".join(f"`{_curto(c)}`" for c in sorted(novas)[:5])
        if len(novas) > 5:
            lista += f" (+{len(novas) - 5})"
        return MOTIVO.format(n=len(novas), lista=lista)
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    motivo = decidir(evento)
    if motivo is None:
        sys.exit(0)
    print(json.dumps({"decision": "block", "reason": motivo}))
    sys.exit(0)


if __name__ == "__main__":
    main()
