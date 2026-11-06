"""Hook do mss-spec: DECISÃO JUNTO DA MUDANÇA DE COMPORTAMENTO — mudou como o assistente age, registra por quê.

Por que existe (benchmark MSIG_Agentes, 2026-11-06): no kit de agentes da equipe, toda alteração de
comportamento (regra global, persona, hook, roteador) gera um registro de decisão no mesmo fechamento — quem
pediu, por quê, o que foi rejeitado, como reverter — e o sync avisa quando publica um desses arquivos sem decisão
do dia. Motivo deles: com várias pessoas alterando comportamento, "daqui a dois meses ninguém sabe por que o
kit age assim". Aqui o `docs/decisoes.md` já existe e o `capturar_nudge.py` cobra a captura por tempo; nada cobrava
a decisão quando a mudança é num arquivo de COMPORTAMENTO.

Contrato:
- evento `Stop`; lê no `transcript_path` o que o assistente gravou (Write/Edit/MultiEdit/NotebookEdit);
- **comportamento** = o que muda como o assistente age: `CLAUDE.md` da raiz, `.claude/rules/*.md`,
  `.claude/settings.json`, `.claude/hooks/*`, e, no próprio kit, `hooks/*.py`, `commands/*.md`,
  `templates/regras-do-kit/*`, `templates/rules/*`;
- **decisão** = `docs/decisoes.md`, ou o Histórico de uma spec (`docs/specs/*.md`, `docs/superpowers/specs/*.md`);
- gravou comportamento e nenhuma decisão → **devolve a resposta** pelo contrato do `Stop` (JSON
  `{"decision": "block", "reason": …}`, exit 0) pedindo a linha de decisão — proposta ao owner, que dá o OK;
  cobra **uma vez por arquivo de comportamento** (arquivo novo depois da cobrança → cobra de novo); com
  `stop_hook_active` verdadeiro, deixa sair (nunca laço);
- estado por sessão no temp do SO (`mss_decisao_junto_<sessao>.json`);
- **falha ABERTA**: defeito → exit 0 calado; escape consciente, só do owner: `MSS_DECISAO_JUNTO_OFF=1`;
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
            _registrar("decisao_junto", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_DECISAO_JUNTO_OFF"

# (padrão no caminho normalizado `/.../x`, descrição) — ordem não importa
RE_COMPORTAMENTO = (
    re.compile(r"/claude\.md$"),                                   # CLAUDE.md da raiz (regras do projeto)
    re.compile(r"/\.claude/rules/[^/]+\.md$"),
    re.compile(r"/\.claude/settings\.json$"),
    re.compile(r"/\.claude/hooks/[^/]+$"),
    re.compile(r"/hooks/[^/]+\.py$"),                              # o próprio kit
    re.compile(r"/commands/[^/]+\.md$"),
    re.compile(r"/templates/regras-do-kit/[^/]+$"),
    re.compile(r"/templates/rules/[^/]+\.md$"),
)
RE_DECISAO = (
    re.compile(r"/docs/decisoes\.md$"),
    re.compile(r"/docs/specs/[^/]+\.md$"),
    re.compile(r"/docs/superpowers/specs/[^/]+\.md$"),
)
# o que NÃO é comportamento mesmo casando acima: teste, README, cache
RE_FORA = re.compile(r"/(tests?|__pycache__|node_modules|\.venv)/|/readme\.md$|/_[^/]+\.py$|/templates/claude\.md$")

MOTIVO = (
    "[mss-spec] Comportamento mudou sem decisão registrada (benchmark MSIG_Agentes, 2026-11-06). Nesta conversa "
    "você gravou {n} arquivo(s) que mudam como o assistente age — {lista} — e nenhuma linha em `docs/decisoes.md` "
    "nem no Histórico de uma spec. Daqui a dois meses ninguém sabe por que a regra é assim. Antes de encerrar, "
    "proponha ao owner a decisão (1 linha: `- <data> — decidimos <X> em vez de <Y> — porque <Z>`; quem pediu, o "
    "que foi rejeitado e como reverter, se couber) em `docs/decisoes.md` — ou no Histórico da spec do assunto, se "
    "a decisão é de um assunto só — e grave com o OK dele. Escape consciente, só do owner: MSS_DECISAO_JUNTO_OFF=1."
)


def _texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else ""


def _norm(caminho):
    return "/" + str(caminho).replace("\\", "/").strip().lower().lstrip("/")


def classificar(caminho):
    """'comportamento', 'decisao' ou None, pelo caminho (absoluto ou relativo, `\\` ou `/`)."""
    p = _norm(caminho)
    if any(r.search(p) for r in RE_DECISAO):
        return "decisao"
    if RE_FORA.search(p):
        return None
    if any(r.search(p) for r in RE_COMPORTAMENTO):
        return "comportamento"
    return None


def _estado(sessao, ambiente):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    pasta = _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()
    return os.path.join(pasta, f"mss_decisao_junto_{seguro}.json")


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
    for marca in ("/.claude/", "/hooks/", "/commands/", "/templates/"):
        if marca in p:
            return marca.strip("/") + "/" + p.rsplit(marca, 1)[1]
    return p.rsplit("/", 1)[-1]


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
        comportamento, decisao = set(), False
        for _, _, caminho in gravs:
            tipo = classificar(caminho)
            if tipo == "decisao":
                decisao = True
            elif tipo == "comportamento":
                comportamento.add(caminho.replace("\\", "/"))
        if decisao or not comportamento:
            return None
        sessao = evento.get("session_id")
        novas = comportamento - cobradas(sessao, ambiente)
        if not novas:
            return None
        marcar(sessao, ambiente, comportamento)
        _anotar("devolveu", f"comportamento_sem_decisao={len(novas)}", evento)
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
