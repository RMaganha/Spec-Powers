"""Duas conversas na mesma pasta não trocam a branch uma da outra — 6ª cerca do `git_publicacao.py` (0.59.0).

Por que existe (caso F-059, `docs/EVALS.md`): em 2026-11-11 a pasta estava na branch de OUTRA conversa, com
mudança por commitar; esta rodou `git status -sb && git switch -c feature/…` num comando só. A branch nasceu ali,
o commit da outra conversa caiu nela e, ao "devolver" a pasta, as duas conversas a moveram ao mesmo tempo. A regra
existia em prosa (`memory/feedback_feature_a_partir_da_master.md`, passo 0 do `nova-feature`) e, desde a 0.57.0,
num aviso de uma vez por conversa — só para criar branch, e que passa na repetição. O owner pediu trava
(item CRÍTICO do `to-dolist.md`): cobrado por hook, não por anotação.

O hook não sabe se outra conversa está viva; sabe quais branches ESTA conversa abriu. Contrato:
- pasta na principal (`main`/`master`), ou numa branch que esta conversa abriu → criar e trocar passam calados
  (a branch criada fica lembrada como desta conversa);
- **criar** branch com a pasta fora da principal e sem dizer que ela sai da principal → **nega** (a branch nasceria
  em cima do trabalho de outra conversa); dizendo (`git switch -c x main`) → vale como troca;
- **trocar** de branch numa branch que esta conversa não abriu: mudança por commitar → **nega**; pasta limpa, ou
  sem dar pra saber → **pede a aprovação do owner** (decisão dele, 2026-11-11: "fica o clique");
- `git checkout <arquivo>`, `git checkout -- <arquivo>` e `git checkout <branch> -- <arquivo>` não são troca;
- a branch atual é lida do arquivo `.git/HEAD`, sem rodar o git; "há mudança por commitar?" roda
  `git status --porcelain --untracked-files=no` (arquivo que o git não acompanha não conta);
- o que a conversa abriu fica no temp do SO (`mss_pasta_branch_<conversa>.json`), como o `kit_primeiro.py`;
- sem número de conversa não age (não há "desta conversa" sem ele); **falha ABERTA**: `.git` ilegível, HEAD
  destacado, defeito aqui → libera;
- escape consciente, só do owner: `MSS_PASTA_BRANCH_OFF=1`.
"""
import json
import os
import re
import shlex
import subprocess
import tempfile

ENV_DESLIGA = "MSS_PASTA_BRANCH_OFF"
NEGA, PERGUNTA = "deny", "ask"
PRINCIPAIS = ("main", "master")

_INICIO = r"(?:^|[;&|\n(]|\$\()\s*"
_ENV = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
_OPCOES_GIT = r"(?:\s+-[cC]\s+(?:\"[^\"]+\"|'[^']+'|\S+)|\s+--[\w-]+(?:=\S+)?)*"
RE_TROCA = re.compile(_INICIO + _ENV + r"git(?P<opcoes>" + _OPCOES_GIT + r")\s+(?P<verbo>switch|checkout)(?![\w-])"
                      + r"(?P<resto>[^;&|\n)]*)")
RE_CD = re.compile(r"(?:^|[;&|\n(])\s*cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|]+)")
RE_C = re.compile(r"-C\s+(\"[^\"]+\"|'[^']+'|\S+)")
# opções que consomem o argumento seguinte (o valor não é o nome da branch)
_COM_VALOR = ("--conflict", "--recurse-submodules", "--pathspec-from-file")
_CRIA = ("-c", "-C", "--create", "--force-create", "-b", "-B", "--orphan")

_SAIDA = ("O hook não sabe se a outra conversa ainda está aberta — o owner sabe. PARE e pergunte ao owner; não "
          "contorne (nem worktree, nem `git stash`, nem \"devolver\" a pasta por conta própria: cada troca a mais "
          "corre contra a da outra conversa — caso F-059). Escape consciente (só o owner decide): {env}=1.")
MOTIVO_CRIA = (
    "[mss-spec] BLOQUEADO — a pasta está na branch `{atual}`, que esta conversa não abriu, e a branch nova nasceria "
    "em cima dela, não da principal:\n  {comando}\n\n"
    "Toda branch nasce da principal atualizada (`git status -sb` tem de dizer `## main...origin/main`). " + _SAIDA
)
MOTIVO_SUJA = (
    "[mss-spec] BLOQUEADO — a pasta está na branch `{atual}`, que esta conversa não abriu, e há mudança por "
    "commitar:\n  {comando}\n\n"
    "Trocar de branch agora levaria junto (ou prenderia) trabalho que pode ser de outra conversa. " + _SAIDA
)
MOTIVO_PERGUNTA = (
    "[mss-spec] Aprovação do owner — a pasta está na branch `{atual}`, que esta conversa não abriu:\n  {comando}\n\n"
    "Se outra conversa está trabalhando nesta pasta, a troca tira a branch de baixo dela (caso F-059). Aprove se "
    "nenhuma outra conversa está usando `{atual}`; recuse se está."
)


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def _caminho(bruto, base):
    p = os.path.expanduser(bruto.strip().strip("\"'"))
    m = re.match(r"^/([a-zA-Z])(/|$)", p)
    if os.name == "nt" and m:
        p = f"{m.group(1).upper()}:/" + p[3:]
    return p if os.path.isabs(p) else os.path.join(base, p)


def _pasta_do_comando(comando, m, cwd):
    """Onde o git vai rodar: último `cd` antes do comando, depois o `-C <dir>` relativo a ele."""
    cds = RE_CD.findall(comando[:m.start() + 1])
    base = _caminho(cds[-1], cwd) if cds else cwd
    c = RE_C.search(m.group("opcoes") or "")
    return _caminho(c.group(1), base) if c else base


def _git_dir(pasta):
    """A pasta `.git` do repositório que contém `pasta` (sobe os pais), ou None."""
    d = os.path.abspath(pasta)
    while True:
        ponto = os.path.join(d, ".git")
        if os.path.isdir(ponto):
            return ponto
        if os.path.isfile(ponto):                     # worktree ou submódulo: `gitdir: <caminho>`
            with open(ponto, encoding="utf-8") as f:
                linha = f.read().strip()
            if linha.startswith("gitdir:"):
                alvo = linha[len("gitdir:"):].strip()
                return alvo if os.path.isabs(alvo) else os.path.normpath(os.path.join(d, alvo))
            return None
        pai = os.path.dirname(d)
        if pai == d:
            return None
        d = pai


def branch_atual(git_dir):
    """Nome da branch em `HEAD`, ou None (HEAD destacado ou ilegível)."""
    with open(os.path.join(git_dir, "HEAD"), encoding="utf-8") as f:
        linha = f.read().strip()
    prefixo = "ref: refs/heads/"
    return linha[len(prefixo):] if linha.startswith(prefixo) else None


def _e_branch(git_dir, nome):
    """`nome` é uma branch local (solta ou em `packed-refs`) ou de um remoto (o git cria a local sozinho)."""
    if os.path.isfile(os.path.join(git_dir, "refs", "heads", *nome.split("/"))):
        return True
    remotos = os.path.join(git_dir, "refs", "remotes")
    if os.path.isdir(remotos):
        for remoto in os.listdir(remotos):
            if os.path.isfile(os.path.join(remotos, remoto, *nome.split("/"))):
                return True
    try:
        with open(os.path.join(git_dir, "packed-refs"), encoding="utf-8") as f:
            for linha in f:
                ref = linha.strip().rpartition(" ")[2]
                if ref == f"refs/heads/{nome}" or (ref.startswith("refs/remotes/")
                                                   and ref.split("/", 3)[-1] == nome):
                    return True
    except OSError:
        pass
    return False


def _sai_da_principal(ponto):
    """O ponto de partida dito no comando é a principal (`main`, `origin/main`…)."""
    return bool(ponto) and ponto.rsplit("/", 1)[-1] in PRINCIPAIS


def mudanca(verbo, resto, pasta, git_dir):
    """("cria", nome, ponto de partida ou None) · ("troca", alvo, None) · None = não mexe na branch da pasta."""
    try:
        tokens = shlex.split(resto, posix=True)
    except ValueError:
        tokens = resto.split()
    if "--" in tokens or "-p" in tokens or "--patch" in tokens:
        return None                                   # restaura arquivo, não troca de branch
    posicionais, cria, i = [], False, 0
    while i < len(tokens):
        t = tokens[i]
        if t in _CRIA:
            cria = True
        elif t in _COM_VALOR:
            i += 1
        elif t == "-" or not t.startswith("-"):
            posicionais.append(t)
        i += 1
    if cria:
        return ("cria", posicionais[0], posicionais[1] if len(posicionais) > 1 else None) if posicionais else None
    if not posicionais:
        return None
    alvo = posicionais[0]
    if verbo == "checkout":
        if len(posicionais) > 1:
            return None                               # `git checkout <branch> <arquivo>`: arquivo de outra branch
        if alvo != "-" and not _e_branch(git_dir, alvo) and os.path.exists(os.path.join(pasta, alvo)):
            return None                               # `git checkout <arquivo>`
    return ("troca", alvo, None)


def _estado(sessao, ambiente):
    seguro = re.sub(r"[^\w-]", "_", str(sessao))[:80]
    pasta = _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()
    return os.path.join(pasta, f"mss_pasta_branch_{seguro}.json")


def desta_conversa(sessao, ambiente, repo):
    """Branches que esta conversa abriu neste repositório."""
    try:
        with open(_estado(sessao, ambiente), encoding="utf-8") as f:
            return set(json.load(f).get(repo) or [])
    except Exception:                                # noqa: BLE001
        return set()


def lembrar(sessao, ambiente, repo, branch):
    try:
        caminho = _estado(sessao, ambiente)
        try:
            with open(caminho, encoding="utf-8") as f:
                estado = json.load(f)
        except Exception:                            # noqa: BLE001
            estado = {}
        estado[repo] = sorted(set(estado.get(repo) or []) | {branch})
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estado, f)
    except Exception:                                # noqa: BLE001
        pass


def ha_mudanca(pasta):
    """True se há arquivo acompanhado pelo git com mudança por commitar. Levanta se o git não responder."""
    proc = subprocess.run(["git", "-C", pasta, "status", "--porcelain", "--untracked-files=no"],
                          capture_output=True, timeout=10)
    if proc.returncode != 0:
        raise OSError("git status falhou")
    return bool(proc.stdout.strip())


def _uma(comando, m, cwd, sessao, ambiente, sujo):
    pasta = _pasta_do_comando(comando, m, cwd)
    git_dir = _git_dir(pasta)
    if git_dir is None:
        return None
    atual = branch_atual(git_dir)
    if atual is None:
        return None
    achado = mudanca(m.group("verbo"), m.group("resto") or "", pasta, git_dir)
    if achado is None:
        return None
    tipo, alvo, ponto = achado
    if tipo == "troca" and alvo == atual:
        return None
    repo = os.path.normcase(os.path.realpath(git_dir))
    livre = atual in PRINCIPAIS or atual in desta_conversa(sessao, ambiente, repo)
    trecho = comando[m.start():m.end()].strip(" ;&|\n(")[:200]
    if tipo == "cria":
        if livre:
            lembrar(sessao, ambiente, repo, alvo)
            return None
        if not _sai_da_principal(ponto):
            return NEGA, MOTIVO_CRIA.format(atual=atual, comando=trecho, env=ENV_DESLIGA), \
                f"criar branch fora da principal ({atual})"
    elif livre:
        return None
    try:
        pendente = sujo(pasta)
    except Exception:                                # noqa: BLE001 — sem saber, quem decide é o owner
        pendente = False
    if pendente:
        return NEGA, MOTIVO_SUJA.format(atual=atual, comando=trecho, env=ENV_DESLIGA), \
            f"trocar de branch com mudança pendente ({atual})"
    return PERGUNTA, MOTIVO_PERGUNTA.format(atual=atual, comando=trecho), f"trocar de branch ({atual})"


def avaliar(comando, cwd, sessao, ambiente, sujo=None):
    """(tipo, motivo, detalhe) da ação mais grave — negar > perguntar — ou (None, None, None). Falha ABERTA."""
    try:
        if _texto(ambiente.get(ENV_DESLIGA)) or not _texto(comando) or not sessao:
            return None, None, None
        sujo = ha_mudanca if sujo is None else sujo
        achados = []
        for m in RE_TROCA.finditer(comando):
            achado = _uma(comando, m, cwd, sessao, ambiente, sujo)
            if achado:
                achados.append(achado)
        if not achados:
            return None, None, None
        negados = [a for a in achados if a[0] == NEGA]
        return negados[0] if negados else achados[0]
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None, None, None
