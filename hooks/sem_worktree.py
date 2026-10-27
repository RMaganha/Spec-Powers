"""Hook do mss-spec: nunca trabalhar em worktree, nunca abrir uma conversa a partir de outra.

Nasceu de 2026-10-27: a conversa da 0.44.0 abriu sozinha `.claude/worktrees/partida-em-dois-niveis` —
o aviso do próprio kit mandava ("abra esta num worktree") — e deixou 2 commits e memória fora da `main`.
No mesmo dia, duas conversas abertas a partir de outra ficaram penduradas uma na outra na barra lateral
e o owner se perdeu. Ele não usa nenhum dos dois: tudo na pasta principal, numa branch saída da `main`;
conversa nova ele abre pelo + e cola o texto que o assistente entrega.

Contrato (um processo, vários eventos — `hook_event_name` decide):
- `WorktreeCreate` → **falha sempre** (exit 2, nada no stdout). É a porta única de criação do Claude Code
  (EnterWorktree, subagente/workflow isolado, sessão de fundo) e o hook SUBSTITUI a criação: desligado,
  ele também não criaria — por isso o escape não vale aqui;
- `PreToolUse` → **nega** `EnterWorktree` (cobre entrar num worktree que já existe), `Agent` com
  `isolation: "worktree"`, escrita (`Write`/`Edit`/`MultiEdit`/`NotebookEdit`) com o alvo dentro de um
  worktree, e abrir/passar conversa (`start_session`/`hand_off_to_session`);
- `SessionStart` → **avisa** quando a conversa já começa dentro de um worktree.

"Dentro de um worktree" é lido do disco, sem rodar o git: subindo do caminho, o 1º `.git` é ARQUIVO com
`gitdir:` apontando pra `…/worktrees/…` (submódulo aponta pra `…/modules/…`). Modos de falha: criar,
entrar e abrir conversa negam sempre (não dependem de nada); "está dentro?" falha ABERTA (ilegível →
libera) — a criação já está fechada, e cerca com defeito não pode parar a gravação legítima.

Escape consciente, só do owner: `MSS_WORKTREE_OFF=1` (menos no `WorktreeCreate`, ver acima).
A 5ª cerca do `git_publicacao.py` cobre o shell (`git worktree add`, gravar dentro de um worktree).
"""
import json
import os
import sys


# Registro local do que este hook FEZ (`hooks/_registro.py`). Nunca muda a decisão.
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
            _registrar("sem_worktree", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_WORKTREE_OFF"
NEGA, AVISA = "deny", "avisa"
TOOLS_DE_ESCRITA = ("Write", "Edit", "MultiEdit", "NotebookEdit")
CAMPOS_DE_CAMINHO = ("file_path", "notebook_path")
TOOLS_DE_CONVERSA = ("mcp__ccd_session__start_session", "mcp__ccd_session__hand_off_to_session")

_ONDE = ("O owner não usa worktree: trabalhe na pasta principal do projeto, numa branch saída da `main`. "
         "A pasta principal está na branch de outra feature? PARE e pergunte ao owner — não contorne.")
_ESCAPE = " Escape consciente (só o owner decide): " + ENV_DESLIGA + "=1."

MOTIVO_CRIAR = "[mss-spec] BLOQUEADO — criar ou entrar em worktree ({como}).\n" + _ONDE + _ESCAPE
MOTIVO_GRAVAR = ("[mss-spec] BLOQUEADO — gravar dentro de um worktree:\n  {alvo}\n(worktree: {raiz})\n"
                 + _ONDE + _ESCAPE)
MOTIVO_CONVERSA = (
    "[mss-spec] BLOQUEADO — abrir, propor ou passar trabalho pra outra conversa a partir desta.\n"
    "O owner abre conversa nova ele mesmo, pelo + — conversa aberta por outra fica pendurada nela na barra "
    "lateral e ele se perde. Entregue o TEXTO PRONTO pra colar (num bloco, completo, com os valores reais: "
    "o comando do kit, a pasta, a branch e o que ler antes) e pare." + _ESCAPE
)
MOTIVO_CRIACAO_CLAUDE = (
    "[mss-spec] Criação de worktree recusada: o owner não usa worktree. Trabalhe na pasta principal do "
    "projeto, numa branch saída da `main`; se ela está na branch de outra feature, pare e pergunte ao owner."
)
AVISO_ABERTURA = (
    "[mss-spec] Esta conversa começou DENTRO de um worktree ({raiz}), e o owner não usa worktree. "
    "Não grave nem commite aqui (a trava nega). Diga isso ao owner na 1ª resposta e entregue o texto pronto "
    "pra ele abrir uma conversa nova pelo + na pasta principal do projeto."
)


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def dentro_de_worktree(caminho):
    """Raiz do worktree que contém `caminho` (que pode ainda não existir), ou None.

    Sobe até achar o 1º `.git`: pasta = repositório principal (None); arquivo com `gitdir:` em
    `…/worktrees/…` = worktree; outro arquivo (submódulo) = None. Sem `.git` até a raiz = None.
    """
    d = os.path.abspath(caminho)
    while True:
        marca = os.path.join(d, ".git")
        if os.path.isdir(marca):
            return None
        if os.path.isfile(marca):
            with open(marca, encoding="utf-8", errors="replace") as f:
                conteudo = f.read(4096)
            for linha in conteudo.splitlines():
                if linha.startswith("gitdir:"):
                    destino = linha[len("gitdir:"):].strip().replace("\\", "/")
                    return d if "/worktrees/" in destino else None
            return None
        pai = os.path.dirname(d)
        if pai == d:
            return None
        d = pai


def _alvo(evento):
    entrada = evento.get("tool_input") or {}
    for campo in CAMPOS_DE_CAMINHO:
        alvo = _texto(entrada.get(campo))
        if alvo:
            base = _texto(evento.get("cwd")) or os.getcwd()
            return alvo if os.path.isabs(alvo) else os.path.join(base, alvo)
    return None


def _pre_tool_use(evento):
    tool = evento.get("tool_name")
    entrada = evento.get("tool_input")
    entrada = entrada if isinstance(entrada, dict) else {}
    if tool == "EnterWorktree":
        return NEGA, MOTIVO_CRIAR.format(como="ferramenta EnterWorktree"), "EnterWorktree"
    if tool == "Agent" and entrada.get("isolation") == "worktree":
        return NEGA, MOTIVO_CRIAR.format(como='subagente com isolation: "worktree"'), "Agent isolado"
    if tool in TOOLS_DE_CONVERSA:
        return NEGA, MOTIVO_CONVERSA, tool.rsplit("__", 1)[-1]
    if tool in TOOLS_DE_ESCRITA:
        alvo = _alvo(evento)
        try:
            raiz = dentro_de_worktree(alvo) if alvo else None
        except Exception:                            # noqa: BLE001 — falha ABERTA
            raiz = None
        if raiz:
            return NEGA, MOTIVO_GRAVAR.format(alvo=alvo, raiz=raiz), f"{tool} em worktree"
    return None, None, None


def avaliar(evento, ambiente=None):
    """(tipo, texto): (None, None) libera · ("deny", motivo) nega · ("avisa", aviso) avisa na abertura."""
    ambiente = os.environ if ambiente is None else ambiente
    if not isinstance(evento, dict) or _texto(ambiente.get(ENV_DESLIGA)):
        return None, None
    nome = evento.get("hook_event_name")
    if nome == "SessionStart":
        try:
            raiz = dentro_de_worktree(_texto(evento.get("cwd")) or os.getcwd())
        except Exception:                            # noqa: BLE001 — falha ABERTA
            raiz = None
        if not raiz:
            return None, None
        _anotar("avisou", "abertura em worktree", evento)
        return AVISA, AVISO_ABERTURA.format(raiz=raiz)
    tipo, motivo, detalhe = _pre_tool_use(evento)
    if tipo is not None:
        _anotar("negou", detalhe, evento)
    return tipo, motivo


def _utf8():
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)                                  # entrada inválida → libera
    if isinstance(evento, dict) and evento.get("hook_event_name") == "WorktreeCreate":
        _anotar("negou", "WorktreeCreate", evento)
        _utf8()
        print(MOTIVO_CRIACAO_CLAUDE, file=sys.stderr)
        sys.exit(2)                                  # sem caminho no stdout → a criação falha
    try:
        tipo, texto = avaliar(evento)
    except Exception:                                # noqa: BLE001
        sys.exit(0)                                  # bug daqui NUNCA trava
    if tipo is None:
        sys.exit(0)
    _utf8()
    if tipo == AVISA:
        print(json.dumps({"systemMessage": texto, "hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": texto}}, ensure_ascii=False))
        sys.exit(0)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": texto,
    }}, ensure_ascii=False))
    print(texto, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
