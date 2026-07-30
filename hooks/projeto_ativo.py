"""Hook do mss-spec: trava o alvo de escrita no PROJETO ATIVO (a âncora).

Nasceu de um acidente real: o owner trabalhava no projeto A, pediu "olha como o projeto B
resolveu isso" e o assistente passou a tratar o B como *o* projeto — editou lá e quebrou o B.
O `precedentes` manda, corretamente, abrir o código do outro projeto; o que faltava era dizer
que aquilo é **somente leitura**.

Contrato:
- evento `PreToolUse`, matcher `Write|Edit|NotebookEdit` (ler outro projeto é o OBJETIVO do
  precedentes — leitura nunca é barrada; Bash/PowerShell está fora de escopo por decisão do
  owner: heurística de shell dá falso positivo e ainda assim é furada);
- **nega** escrita fora da âncora, dizendo pra abrir uma janela na raiz do outro projeto;
- **libera** temp do SO, `~/.claude` e worktree do MESMO repo (o kit manda usar worktree, e
  worktree fica fora da pasta do projeto);
- **falha ABERTA** onde importa: entrada malformada, âncora indeterminável ou bug daqui → libera
  e sai 0. Cerca com defeito não pode parar o trabalho legítimo dentro do próprio projeto.
  **Exceção**: a sonda de worktree falha FECHADA (sem git não existe worktree a liberar — ver
  `mesmo_repo`), senão bastaria o git faltar no PATH pra cerca sumir sozinha.

Escape consciente: `MSS_ANCORA_OFF=1`.
"""
import json
import os
import subprocess
import sys

ENV_DESLIGA = "MSS_ANCORA_OFF"
ENV_ANCORA = "CLAUDE_PROJECT_DIR"
TOOLS_DE_ESCRITA = ("Write", "Edit", "NotebookEdit")
CAMPOS_DE_CAMINHO = ("file_path", "notebook_path")
ENVS_DE_TEMP = ("TEMP", "TMP", "TMPDIR")
ENVS_DE_CASA = ("USERPROFILE", "HOME")
TIMEOUT_GIT_S = 5

MOTIVO = (
    "[mss-spec] BLOQUEADO — escrita fora do projeto ativo.\n"
    "Projeto ativo (âncora desta janela): {ancora}\n"
    "Alvo recusado: {alvo}\n\n"
    "Outro projeto é REFERÊNCIA SOMENTE-LEITURA: você pode ler o código dele (Read/Grep/Glob) "
    "e trazer o padrão pro projeto ativo — nunca editar, consertar ou rodar nada lá. "
    "Se a mudança é mesmo naquele projeto, pare: diga ao owner pra fechar esta janela e abrir "
    "uma nova na raiz dele (um assunto E um projeto por janela). "
    "Se enxergou um bug lá, reporte — não conserte.\n"
    "Escape consciente (só o owner decide): {env}=1."
)


def _texto(valor):
    """Env/campo vazio ou em branco conta como ausente (não como caminho '')."""
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def normalizar(caminho):
    """Caminho comparável: absoluto, links/junctions resolvidos e case normalizado.

    No Windows `C:\\X\\a` e `c:/x/a` são o MESMO caminho — comparar cru daria falso
    positivo, barrando escrita dentro do próprio projeto.
    """
    return os.path.normcase(os.path.realpath(os.path.abspath(caminho)))


def ancora_de(evento, ambiente):
    """A raiz do projeto ativo: CLAUDE_PROJECT_DIR e, na falta dele, o cwd do evento."""
    return _texto(ambiente.get(ENV_ANCORA)) or _texto(evento.get("cwd"))


def caminho_alvo(evento):
    """O caminho que o tool quer escrever (`file_path` ou, no NotebookEdit, `notebook_path`)."""
    entrada = evento.get("tool_input") or {}
    for campo in CAMPOS_DE_CAMINHO:
        alvo = _texto(entrada.get(campo))
        if alvo:
            return alvo
    return None


def dentro(alvo, base):
    """True se `alvo` está na árvore de `base` (ou é a própria base)."""
    try:
        return os.path.commonpath([alvo, base]) == base
    except ValueError:      # drives diferentes no Windows
        return False


def bases_liberadas(ambiente):
    """Temp do SO e `~/.claude` — não são "outro projeto".

    Derivadas SÓ do `ambiente` recebido (nunca de `tempfile.gettempdir()`), pra decisão
    ser testável e não depender do ambiente real da máquina.
    """
    bases = []
    for env in ENVS_DE_TEMP:
        temp = _texto(ambiente.get(env))
        if temp:
            bases.append(normalizar(temp))
    for env in ENVS_DE_CASA:
        casa = _texto(ambiente.get(env))
        if casa:
            bases.append(normalizar(os.path.join(casa, ".claude")))
    return bases


def _git_common_dir(diretorio):
    """Diretório .git COMUM (compartilhado entre worktrees), ou None se não for repo."""
    proc = subprocess.run(
        ["git", "-C", diretorio, "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, timeout=TIMEOUT_GIT_S)
    if proc.returncode != 0:
        return None
    saida = _texto(proc.stdout)
    return normalizar(saida) if saida else None


def mesmo_repo(alvo, ancora, git_common_dir):
    """True só se alvo e âncora compartilham o .git comum — ou seja, o alvo é um
    worktree do MESMO repositório.

    Esta sonda falha FECHADA (git ausente/antigo/travado → False), ao contrário do resto
    do hook: worktree só existe se git existe, então "não deu pra perguntar ao git" nunca
    é um caso legítimo a liberar — seria só um jeito de a cerca sumir sozinha.
    """
    try:
        comum_alvo = git_common_dir(os.path.dirname(alvo) or alvo)
        comum_ancora = git_common_dir(ancora)
    except Exception:
        return False
    return bool(comum_alvo) and comum_alvo == comum_ancora


def decidir(evento, ambiente=None, git_common_dir=None):
    """None = libera; string = motivo do bloqueio (mostrado ao assistente)."""
    ambiente = os.environ if ambiente is None else ambiente
    git_common_dir = _git_common_dir if git_common_dir is None else git_common_dir

    if _texto(ambiente.get(ENV_DESLIGA)):
        return None
    if evento.get("tool_name") not in TOOLS_DE_ESCRITA:
        return None

    bruto = caminho_alvo(evento)
    ancora_bruta = ancora_de(evento, ambiente)
    if not bruto or not ancora_bruta:
        return None                                   # indeterminado → libera

    ancora = normalizar(ancora_bruta)
    # Os tools de escrita exigem caminho absoluto; se vier relativo, resolve como o tool
    # resolveria — contra o cwd do evento (a âncora é o fallback).
    base_relativa = _texto(evento.get("cwd")) or ancora_bruta
    alvo = normalizar(bruto if os.path.isabs(bruto) else os.path.join(base_relativa, bruto))

    if dentro(alvo, ancora):
        return None
    if any(dentro(alvo, base) for base in bases_liberadas(ambiente)):
        return None
    if mesmo_repo(alvo, ancora, git_common_dir):
        return None

    return MOTIVO.format(ancora=ancora_bruta, alvo=bruto, env=ENV_DESLIGA)


def main():
    try:
        evento = json.load(sys.stdin)
        motivo = decidir(evento if isinstance(evento, dict) else {})
    except Exception:
        sys.exit(0)                                   # bug/entrada inválida NUNCA trava
    if motivo is None:
        sys.exit(0)                                   # libera, calado
    # A mensagem é em pt-BR e vai pro contexto do assistente: força UTF-8 nas duas saídas
    # (no Windows o default é cp1252 e o acento sairia ilegível/quebrado).
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    # Deny pelos dois protocolos: JSON no stdout e exit 2 com o motivo no stderr.
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": motivo,
    }}, sys.stdout, ensure_ascii=False)
    print(motivo, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
