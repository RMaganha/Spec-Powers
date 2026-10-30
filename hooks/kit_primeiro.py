"""Hook do mss-spec: O KIT ENTRA PRIMEIRO — skill do superpowers só por dentro de um comando do kit.

Por que existe (caso F-048, `docs/EVALS.md`): na conversa "Validar mensagens WhatsApp em produção"
(Whats, 2026-10-30), o owner disse *"vamos tratar aqui mesmo o bug"* e o assistente invocou
`superpowers:systematic-debugging` direto, sem o `/mss-spec:bug`. O passo 1 do bug — memória, spec e
diário ANTES da 1ª hipótese — não aconteceu, e em 8 minutos a hipótese errada (`MITI_DEV_AUTH`) estava
na mesa; o owner: *"você nunca olha as memórias!!"*. A regra crítica 11 e o `bug.md` já mandavam entrar
pelo kit (2026-10-27, 1ª reincidência); o `superpowers:using-superpowers` manda "bug → systematic-debugging
primeiro". Prosa contra prosa, ganhou a do superpowers. Aqui a cerca é determinística: o superpowers
continua sendo chamado, mas de dentro do comando do kit, no passo certo.

Contrato:
- `UserPromptSubmit`: prompt que começa com `/mss-spec:` → marca "entrou pelo kit" nesta sessão; calado;
- `PreToolUse` em `Skill`: `mss-spec:*` → marca e libera; `superpowers:*` sem marca → **nega** dizendo a
  porta certa (bug · nova-feature · duvida · analise); qualquer outra skill → libera;
- `PreToolUse` em `Read`: `commands/<x>.md` do kit → marca (os comandos `disable-model-invocation` —
  `nova-feature`, `analise`, `memory`… — rodam por leitura do arquivo, não por `Skill`);
- estado por sessão no temp do SO (`mss_kit_primeiro_<sessao>.json`), como o `_memoria_de_acao.py`:
  duas conversas não se misturam;
- negativa no mesmo formato do `git_publicacao.py` (JSON `deny` no stdout + motivo no stderr + exit 2) —
  é o que já funciona ao vivo nesta máquina;
- **falha ABERTA**: qualquer defeito → libera calado; escape consciente, só do owner: `MSS_KIT_PRIMEIRO_OFF=1`;
- registra `negou` no registro local (`hooks/_registro.py`), nunca o texto do prompt.
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


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("kit_primeiro", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_KIT_PRIMEIRO_OFF"
KIT = os.path.normcase(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREFIXO_KIT = "mss-spec:"
PREFIXO_SUPERPOWERS = "superpowers:"

MOTIVO = (
    "[mss-spec] O kit entra primeiro: `{skill}` só roda por dentro de um comando do kit (regra crítica 11; "
    "caso F-048). Nesta conversa nenhum comando do kit rodou ainda. Entre pela porta certa — ela lê a memória, "
    "a spec e o diário antes da 1ª hipótese e chama o superpowers no passo certo:\n"
    "- erro, falha, algo que parou ou mudou de comportamento → /mss-spec:bug\n"
    "- mudança ou coisa nova → /mss-spec:nova-feature (leia commands/nova-feature.md e siga os passos)\n"
    "- pergunta sobre o projeto → /mss-spec:duvida\n"
    "- projeto que já existia e o kit ainda não conhece → /mss-spec:analise\n"
    "Escape consciente, só do owner: MSS_KIT_PRIMEIRO_OFF=1."
)


def _texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else ""


def _estado(sessao, ambiente):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    pasta = _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()
    return os.path.join(pasta, f"mss_kit_primeiro_{seguro}.json")


def entrou(sessao, ambiente):
    """True se, nesta sessão, algum comando do kit já entrou (digitado, invocado ou lido)."""
    try:
        with open(_estado(sessao, ambiente), encoding="utf-8") as f:
            return bool(json.load(f).get("entrou"))
    except Exception:                                # noqa: BLE001
        return False


def marcar(sessao, ambiente, por):
    try:
        with open(_estado(sessao, ambiente), "w", encoding="utf-8") as f:
            json.dump({"entrou": True, "por": str(por)[:120]}, f)
    except Exception:                                # noqa: BLE001
        pass


def _e_comando_do_kit(caminho):
    """`commands/<x>.md` do kit — no clone de desenvolvimento (raiz deste arquivo), na instalação em
    `~/.claude/skills/mss-spec/` ou no cache do marketplace (`.../mss-spec/<versão>/`)."""
    p = os.path.normcase(os.path.abspath(caminho)).replace("/", os.sep)
    if not p.endswith(".md"):
        return False
    pasta = os.path.basename(os.path.dirname(p))
    if pasta != "commands":
        return False
    return p.startswith(KIT) or "mss-spec" in p


def decidir(evento, ambiente=None):
    """Motivo da negativa (str) ou None = libera calado. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)):
            return None
        if not isinstance(evento, dict):
            return None
        sessao = evento.get("session_id")
        nome_evento = evento.get("hook_event_name")
        if nome_evento == "UserPromptSubmit":
            if _texto(evento.get("prompt")).lstrip().startswith("/" + PREFIXO_KIT):
                marcar(sessao, ambiente, "prompt")
            return None
        if nome_evento != "PreToolUse":
            return None
        ferramenta = evento.get("tool_name")
        entrada = evento.get("tool_input")
        if not isinstance(entrada, dict):
            return None
        if ferramenta == "Read":
            caminho = _texto(entrada.get("file_path"))
            if caminho and _e_comando_do_kit(caminho):
                marcar(sessao, ambiente, "read " + os.path.basename(caminho))
            return None
        if ferramenta != "Skill":
            return None
        skill = _texto(entrada.get("skill")).strip()
        if not skill:
            return None
        if skill.startswith(PREFIXO_KIT):
            marcar(sessao, ambiente, "skill " + skill)
            return None
        if not skill.startswith(PREFIXO_SUPERPOWERS):
            return None
        if entrou(sessao, ambiente):
            return None
        _anotar("negou", skill, evento)
        return MOTIVO.format(skill=skill)
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
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": motivo,
    }}))
    print(motivo, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
