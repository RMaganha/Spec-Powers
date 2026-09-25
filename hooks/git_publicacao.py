"""Hook do mss-spec: push em HOMOLOGAÇÃO/PRODUÇÃO é ato do owner — o resto do git o assistente
roda, com a aprovação do owner.

Nasceu de um acidente real (2026-09, caso F-022 em `docs/EVALS.md`): numa janela aberta pra
UMA feature, o assistente absorveu um 2º e um 3º assunto, mesclou branches e disparou
`git push` — e o push é o gatilho do deploy automático em homologação. Quando o owner viu,
vários já tinham ido; o ambiente quebrou inteiro e custou centenas de testes pra entender o quê.

A 1ª versão (0.26.0) negava TODO push/merge/rebase e travou o dia a dia — merge local, push de
branch de feature, até `git merge-base`, que só lê. O dano do F-022 veio do push que faz DEPLOY:
é isso que segue negado. O resto vira pedido de aprovação — o owner vê o comando e aprova com um
clique (`permissionDecision: "ask"`, que aparece também no app Desktop).

Contrato:
- evento `PreToolUse`, matcher `Bash|PowerShell`; lê `tool_input.command`;
- **nega**:
  - `git push` cujo destino é branch **protegida** — `main`, `master`, `dev`, `develop`,
    `production`, `homolog*`, `hml*`, `prod*`, `release/*` — por refspec (`origin dev`,
    `HEAD:dev`, `x:main`, `--delete main`) ou, sem refspec, pela branch atual e pelo `@{push}`
    (a feature que rastreia `origin/dev` iria pra dev);
  - `git push` de destino **indeterminável**: `--all`, `--mirror`, `--tags`, `:`, HEAD destacado,
    git inconsultável;
  - deploy e integração remota: `gh pr merge`, `docker push`, `az acr build`, `az webapp <escrita>`,
    `az containerapp update|create|revision`;
- **pede aprovação**: `git merge`, `git rebase` (menos `--abort`) e `git push` de feature/fix;
- **libera calado** o resto do git (`merge-base`, `merge-tree`, `pull`, status, commit…);
- casa o VERBO no início de um comando simples (após `;`, `&&`, `|`, `(`, quebra de linha ou
  prefixo `VAR=x`), não a palavra solta — `grep 'git push'` e `echo pushing` passam; num comando
  com várias ações, a mais grave vence (negar > perguntar);
- **falha FECHADA**: há comando e a avaliação estourou → nega (cerca com defeito não pode abrir
  sozinha). Evento sem comando (malformado) → libera calado: não existe push num evento vazio.

Escape consciente, só do owner: `MSS_PUBLICACAO_OFF=1`.

2ª cerca no MESMO processo (mesmo evento, custo extra ~0 ms): **pytest mascarado por pipe antes
do `git commit`** (caso F-025). `pytest … | tail -1 && git commit` commitou com 2 testes vermelhos:
o código de saída de um pipe é o do último comando, e o `&&` só olha esse. Nega quando o mesmo
comando tem o pytest (como comando, não como texto) com a saída num `|` e um `git commit` depois,
sem `pipefail`. Modo de falha PRÓPRIO — **ABERTA** (commit vermelho se reverte; push não) — e
escape próprio: `MSS_PIPE_TESTE_OFF=1`. Uma cerca não liga nem desliga a outra.
"""
import json
import os
import re
import shlex
import subprocess
import sys


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
            _registrar("git_publicacao", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass

ENV_DESLIGA = "MSS_PUBLICACAO_OFF"
ENV_PIPE_DESLIGA = "MSS_PIPE_TESTE_OFF"
TOOLS_DE_SHELL = ("Bash", "PowerShell")
NEGA, PERGUNTA = "deny", "ask"

# Branches de homologação/produção: push nelas dispara deploy. Uma regra só, sem configuração.
PROTEGIDAS = ("main", "master", "dev", "develop", "production")
PROTEGIDAS_PREFIXO = ("homolog", "hml", "prod", "release/")
PROTEGIDAS_TEXTO = "main, master, dev, develop, production, homolog*, hml*, prod*, release/*"

# Início de um comando simples: começo do texto, separador de shell, abre-parêntese ou `$(`.
_INICIO = r"(?:^|[;&|\n(]|\$\()\s*"
# Prefixo `VAR=valor` (um ou mais) antes do executável.
_ENV = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
# `git` com opções globais antes do verbo: `-C <dir>`, `-c k=v`, `--no-pager`, `--git-dir=…`.
_OPCOES_GIT = r"(?:\s+-[cC]\s+(?:\"[^\"]+\"|'[^']+'|\S+)|\s+--[\w-]+(?:=\S+)?)*"
_GIT = r"git" + _OPCOES_GIT + r"\s+"
# Fim do verbo: nem letra nem hífen depois — `merge` não casa `merge-base`/`merge-tree`.
_FIM = r"(?![\w-])"

_PUSH = re.compile(_INICIO + _ENV + r"git(?P<opcoes>" + _OPCOES_GIT + r")\s+push" + _FIM
                   + r"(?P<args>[^;&|\n)]*)")
_CD = re.compile(r"(?:^|[;&|\n(])\s*cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|]+)")

INTEGRACAO = (
    (re.compile(_INICIO + _ENV + _GIT + r"merge" + _FIM + r"(?!\s+--abort\b)"), "git merge"),
    (re.compile(_INICIO + _ENV + _GIT + r"rebase" + _FIM + r"(?!\s+--abort\b)"), "git rebase"),
)

DEPLOY = (
    (re.compile(_INICIO + _ENV + r"gh\s+pr\s+merge\b"), "gh pr merge — integra o PR no remoto"),
    (re.compile(_INICIO + _ENV + r"docker\s+push\b"), "docker push — publica imagem"),
    (re.compile(_INICIO + _ENV + r"az\s+acr\s+build\b"), "az acr build — constrói e publica imagem"),
    (re.compile(_INICIO + _ENV + r"az\s+webapp\s+(?!(?:log|show|list)\b)\S"),
     "az webapp <escrita> — altera o Web App"),
    (re.compile(_INICIO + _ENV + r"az\s+containerapp\s+(?:update|create|revision)\b"),
     "az containerapp — altera o Container App"),
)

# opções do `git push` que consomem o argumento seguinte
_PUSH_COM_VALOR = ("-o", "--push-option", "--repo", "--receive-pack", "--exec")
_PUSH_ABRANGENTE = ("--all", "--mirror", "--tags", "--branches")

# pytest como COMANDO (não a palavra solta): `pytest`, `py.test`, `<python> -m pytest`.
_PYTEST = re.compile(_INICIO + _ENV + r"(?:\S*python[\d.]*(?:\.exe)?\s+(?:-\S+\s+)*-m\s+pytest|py\.?test)\b")
_COMMIT = re.compile(_INICIO + _ENV + _GIT + r"commit\b")
_PIPE_SIMPLES = re.compile(r"(?<!\|)\|(?!\|)")      # `|`, não `||`

_POR_QUE = ("Por quê: push nessas branches dispara o deploy automático — em 2026-09 vários pushes "
            "numa janela de feature quebraram a homologação inteira (caso F-022 do docs/EVALS.md). ")
_SAIDA = ("Pronto pra publicar: rode `/mss-spec:release` (gate de pré-publicação), cole o veredito e "
          "PEÇA — o owner faz o push do terminal dele. Escape consciente (só o owner decide): {env}=1.")

MOTIVO_PROTEGIDA = (
    "[mss-spec] BLOQUEADO — push para `{destino}` é ato do OWNER: é branch de homologação/produção.\n"
    "Comando recusado:\n  {comando}\n\n" + _POR_QUE +
    "Push de branch de feature/fix o assistente roda, com a aprovação do owner. "
    "Protegidas: " + PROTEGIDAS_TEXTO + ". " + _SAIDA
)

MOTIVO_INDETERMINADO = (
    "[mss-spec] BLOQUEADO — não deu pra saber pra qual branch este push vai ({porque}), e na dúvida a "
    "cerca nega: um push em homologação/produção é ato do OWNER.\nComando recusado:\n  {comando}\n\n"
    "Diga o destino explicitamente — `git push origin <sua-feature>` — e o push de feature/fix roda "
    "com a aprovação do owner. " + _SAIDA
)

MOTIVO_DEPLOY = (
    "[mss-spec] BLOQUEADO — deploy/integração remota é ato do OWNER, não do assistente.\n"
    "Comando recusado ({alvo}):\n  {comando}\n\n" + _POR_QUE + _SAIDA
)

MOTIVO_PERGUNTA = (
    "[mss-spec] Aprovação do owner — {alvo}:\n  {comando}\n\n"
    "Não atinge homologação/produção (push em " + PROTEGIDAS_TEXTO + " segue bloqueado). "
    "Aprove se isto é da feature desta janela; recuse se misturou assunto (caso F-022)."
)

MOTIVO_DEFEITO = (
    "[mss-spec] BLOQUEADO — a cerca de publicação está com DEFEITO ({erro!r}) e, por segurança, "
    "nega em vez de abrir. Publicar/integrar segue sendo ato do owner (rode `/mss-spec:release` "
    "e peça). Reporte o erro; escape consciente (só o owner): {env}=1."
)

MOTIVO_PIPE = (
    "[mss-spec] BLOQUEADO — o pipe esconde o resultado do pytest e o commit sairia mesmo com teste "
    "vermelho.\nComando recusado:\n  {comando}\n\n"
    "Por quê: num pipe, o código de saída é o do ÚLTIMO comando (`tail`, `grep`, `Select-Object`), "
    "não o do pytest — e o `&&` só olha esse. Foi assim que saiu commit com testes vermelhos, duas "
    "vezes (caso F-025 do docs/EVALS.md). Saídas: (1) rode o pytest num passo próprio, leia o "
    "resultado e só então commite; ou (2) comece o comando com `set -o pipefail;` (Bash). "
    "Escape consciente (só o owner decide): {env}=1."
)


def _texto(valor):
    """Env/campo vazio ou em branco conta como ausente."""
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def protegida(nome):
    """True se a branch é de homologação/produção (push = deploy)."""
    n = (nome or "").strip().lower()
    if n.startswith("refs/heads/"):
        n = n[len("refs/heads/"):]
    return n in PROTEGIDAS or n.startswith(PROTEGIDAS_PREFIXO)


def _git_destino(pasta):
    """(branch atual — `HEAD` se destacado —, destino do `git push` sem refspec ou None).

    Levanta se o git não responder: quem chama trata como destino indeterminado (nega)."""
    def rodar(*args):
        # bytes, não text=True: no Windows o text=True quebra a chamada ao git (memória do kit)
        proc = subprocess.run(["git", "-C", pasta, *args], capture_output=True, timeout=10)
        return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()
    codigo, atual = rodar("rev-parse", "--abbrev-ref", "HEAD")
    if codigo != 0 or not atual:
        raise OSError("git rev-parse falhou")
    codigo, destino = rodar("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{push}")
    destino = destino.split("/", 1)[1] if codigo == 0 and "/" in destino else None
    return atual, destino


def _pasta_do_push(comando, m, cwd):
    """Onde o git vai rodar: `-C <dir>` > último `cd <dir>` antes do push > cwd do evento."""
    c = re.search(r"-C\s+(\"[^\"]+\"|'[^']+'|\S+)", m.group("opcoes") or "")
    alvo = c.group(1) if c else None
    if alvo is None:
        cds = _CD.findall(comando[:m.start() + 1])
        alvo = cds[-1] if cds else None
    if alvo is None:
        return cwd
    alvo = alvo.strip("\"'")
    return alvo if os.path.isabs(alvo) or alvo.startswith("/") else os.path.join(cwd, alvo)


def _refspecs(args):
    """Destinos declarados no push: lista (vazia = implícito) ou str com o porquê de ser indeterminável."""
    try:
        tokens = shlex.split(args, posix=True)
    except ValueError:
        tokens = args.split()
    posicionais, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in _PUSH_ABRANGENTE:
            return f"`{t}` atinge várias branches"
        if t in _PUSH_COM_VALOR:
            i += 1
        elif not t.startswith("-"):
            posicionais.append(t)
        i += 1
    destinos = []
    for ref in posicionais[1:]:                      # o 1º posicional é o remoto
        ref = ref.lstrip("+")
        if ref == ":":
            return "refspec `:` empurra todas as branches casadas"
        destinos.append(ref.split(":", 1)[1] or ref.split(":", 1)[0] if ":" in ref else ref)
    return destinos


def _avaliar_push(comando, m, cwd, git_destino):
    """(tipo, motivo, detalhe) de UM `git push` do comando."""
    trecho = comando[m.start():m.end()].strip(" ;&|\n(")
    destinos = _refspecs(m.group("args"))
    if isinstance(destinos, str):
        return NEGA, MOTIVO_INDETERMINADO.format(porque=destinos, comando=trecho[:200], env=ENV_DESLIGA), \
            "git push indeterminado"
    precisa_git = not destinos or "HEAD" in destinos
    atual = empurra = None
    if precisa_git:
        try:
            atual, empurra = git_destino(_pasta_do_push(comando, m, cwd))
        except Exception:                            # noqa: BLE001 — sem git não há como provar o destino
            return NEGA, MOTIVO_INDETERMINADO.format(porque="o git não respondeu", comando=trecho[:200],
                                                     env=ENV_DESLIGA), "git push indeterminado"
        if not atual or atual == "HEAD":
            return NEGA, MOTIVO_INDETERMINADO.format(porque="HEAD destacado, sem branch atual",
                                                     comando=trecho[:200], env=ENV_DESLIGA), \
                "git push indeterminado"
    alvos = [atual if d == "HEAD" else d for d in destinos] if destinos else [atual] + ([empurra] if empurra else [])
    for alvo in alvos:
        if protegida(alvo):
            return NEGA, MOTIVO_PROTEGIDA.format(destino=alvo, comando=trecho[:200], env=ENV_DESLIGA), \
                f"git push → {alvo}"
    return PERGUNTA, MOTIVO_PERGUNTA.format(alvo=f"git push → {', '.join(alvos)}", comando=trecho[:200]), \
        f"git push → {alvos[0]}"


def publica_ou_integra(comando, cwd=".", git_destino=None):
    """(tipo, motivo, detalhe) da ação mais grave do comando — negar > perguntar — ou None."""
    git_destino = _git_destino if git_destino is None else git_destino
    achados = []
    for padrao, rotulo in DEPLOY:
        if padrao.search(comando):
            achados.append((NEGA, MOTIVO_DEPLOY.format(alvo=rotulo, comando=comando[:200], env=ENV_DESLIGA),
                            rotulo.split(" — ")[0]))
    for m in _PUSH.finditer(comando):
        achados.append(_avaliar_push(comando, m, cwd, git_destino))
    for padrao, rotulo in INTEGRACAO:
        if padrao.search(comando):
            achados.append((PERGUNTA, MOTIVO_PERGUNTA.format(alvo=rotulo, comando=comando[:200]), rotulo))
    if not achados:
        return None
    negados = [a for a in achados if a[0] == NEGA]
    return negados[0] if negados else achados[0]


def mascara_teste(comando):
    """True se um pipe esconde o exit do pytest antes de um `git commit` no mesmo comando."""
    if "pipefail" in comando:
        return False
    teste = _PYTEST.search(comando)
    if teste is None:
        return False
    commit = _COMMIT.search(comando, teste.end())
    if commit is None:
        return False
    # entre o pytest e o commit (inclui o separador que abre o commit: `pytest | git commit`)
    return _PIPE_SIMPLES.search(comando[teste.end():commit.start() + 1]) is not None


def _decidir_publicacao(comando, ambiente, cwd, git_destino):
    """(tipo, motivo, detalhe) ou (None, None, None). Falha FECHADA."""
    if _texto(ambiente.get(ENV_DESLIGA)):
        return None, None, None
    try:
        achado = publica_ou_integra(comando, cwd=cwd, git_destino=git_destino)
    except Exception as erro:                        # noqa: BLE001 — falha FECHADA
        return NEGA, MOTIVO_DEFEITO.format(erro=erro, env=ENV_DESLIGA), "defeito da cerca"
    return achado if achado else (None, None, None)


def _decidir_pipe(comando, ambiente):
    """(motivo, detalhe pro registro) ou (None, None). Falha ABERTA."""
    if _texto(ambiente.get(ENV_PIPE_DESLIGA)):
        return None, None
    try:
        if not mascara_teste(comando):
            return None, None
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None, None
    return MOTIVO_PIPE.format(comando=comando[:200], env=ENV_PIPE_DESLIGA), "pytest em pipe antes do git commit"


# ------------------------------------------------------------------ 3ª cerca: OUTRO projeto no shell (F-031)
# A âncora (`projeto_ativo.py`) só vigia Write/Edit; pelo shell, uma janela editou e commitou em outro
# projeto. "Outro projeto" = repositório git DIFERENTE do da âncora — pasta fora de repo e worktree do
# mesmo repo não contam. Falha ABERTA (heurística de shell); escape = o da âncora, `MSS_ANCORA_OFF`.

ENV_ANCORA_DESLIGA = "MSS_ANCORA_OFF"
_GIT_ESCRITA = ("add", "commit", "checkout", "switch", "merge", "rebase", "reset", "restore", "rm", "mv",
                "cherry-pick", "revert", "tag", "apply", "am", "clean", "pull", "push", "stash", "branch")
_GIT_VERBO = re.compile(_INICIO + _ENV + r"git(?P<opcoes>" + _OPCOES_GIT + r")\s+(?P<verbo>[\w-]+)"
                        + r"(?P<resto>[^;&|\n)]*)")
_BRANCH_LEITURA = re.compile(r"^\s*(?:(?:-[avlr]+|--(?:show-current|all|list|remotes|verbose|contains"
                             r"|merged|no-merged|sort=\S+|format=\S+|color\S*))\s*)*$")
_STASH_LEITURA = re.compile(r"^\s*(?:list|show)\b")
_TAG_LEITURA = re.compile(r"^\s*(?:(?:-l|--list|-n\d*|--contains\s+\S+|--sort=\S+)\s*)*(?:\S*\*\S*\s*)?$")
_PROJ = re.compile(r"--proj(?:=|\s+)(\"[^\"]+\"|'[^']+'|[^\s;&|]+)")
_REDIRECAO = re.compile(r"(?<![<>&\d])>>?\s*(\"[^\"]+\"|'[^']+'|[^\s;&|<>]+)")
_TEE = re.compile(r"(?:^|[|;&\n])\s*tee\s+(?:-a\s+)?(\"[^\"]+\"|'[^']+'|[^\s;&|]+)")
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\2[ \t]*(?=\n|$)", re.S)
_ALVOS_NULOS = ("/dev/null", "$null", "nul", "null")

MOTIVO_OUTRO_PROJETO = (
    "[mss-spec] BLOQUEADO — este comando grava em OUTRO projeto:\n  {raiz}\n"
    "e esta janela é do projeto:\n  {ancora}\n\n"
    "Um projeto por janela: pela linha de comando, uma janela editou e commitou em outro projeto (casos "
    "F-022 e F-031 do docs/EVALS.md). Não rode daqui. Diga ao owner pra abrir uma janela na pasta do outro "
    "projeto e colar lá, exatamente:\n\n"
    "Rode no terminal deste projeto e me mostre a saída:\n```\n{comando}\n```\n\n"
    "Escape consciente (só o owner decide): {env}=1."
)


def _sem_heredoc(comando):
    """Corpo de heredoc é dado, não comando: `>` dentro de uma mensagem de commit não é redirecionamento."""
    return _HEREDOC.sub("<<heredoc", comando)


def _caminho_do_shell(bruto, base):
    """Caminho como o shell o resolveria: sem aspas, `~` expandido, `/c/x` do Git Bash → `C:/x`, relativo à base."""
    p = bruto.strip().strip("\"'")
    p = os.path.expanduser(p)
    m = re.match(r"^/([a-zA-Z])(/|$)", p)
    if os.name == "nt" and m:
        p = f"{m.group(1).upper()}:/" + p[3:]
    return p if os.path.isabs(p) else os.path.join(base, p)


def _pasta_antes(comando, posicao, cwd):
    """A pasta em que o trecho em `posicao` roda: último `cd` antes dele, ou o cwd."""
    cds = _CD.findall(comando[:posicao + 1])
    return _caminho_do_shell(cds[-1], cwd) if cds else cwd


def _alvos_de_escrita(comando, cwd):
    """[(caminho, rótulo)] que o comando GRAVA — só as formas visíveis no texto do comando."""
    texto = _sem_heredoc(comando)
    alvos = []
    for m in _GIT_VERBO.finditer(texto):
        verbo, resto = m.group("verbo"), m.group("resto") or ""
        if verbo not in _GIT_ESCRITA:
            continue
        if verbo == "branch" and _BRANCH_LEITURA.match(resto):
            continue
        if verbo == "stash" and _STASH_LEITURA.match(resto):
            continue
        if verbo == "tag" and _TAG_LEITURA.match(resto):
            continue
        base = _pasta_antes(texto, m.start(), cwd)
        c = re.search(r"-C\s+(\"[^\"]+\"|'[^']+'|\S+)", m.group("opcoes") or "")
        alvos.append((_caminho_do_shell(c.group(1), base) if c else base, f"git {verbo}"))
    for trecho in re.split(r"[;&|\n]+", texto):
        if "--aplicar" in trecho:
            for p in _PROJ.findall(trecho):
                alvos.append((_caminho_do_shell(p, cwd), "--proj … --aplicar"))
    for rx, rotulo in ((_REDIRECAO, "redirecionamento"), (_TEE, "tee")):
        for m in rx.finditer(texto):
            alvo = m.group(1).strip("\"'")
            if alvo.lower() in _ALVOS_NULOS or alvo.startswith("&"):
                continue
            alvos.append((_caminho_do_shell(alvo, _pasta_antes(texto, m.start(), cwd)), rotulo))
    return alvos


def _repo_de(caminho):
    """(git common dir, toplevel) do repo que contém `caminho` (sobe até a pasta que existe), ou (None, None)."""
    d = caminho
    while d and not os.path.isdir(d):
        pai = os.path.dirname(d)
        if pai == d:
            return None, None
        d = pai
    def _rodar(*args):
        proc = subprocess.run(["git", "-C", d, "rev-parse", *args], capture_output=True, text=True, timeout=5)
        return proc.stdout.strip() if proc.returncode == 0 else None
    comum = _rodar("--path-format=absolute", "--git-common-dir")
    if not comum:
        return None, None
    return os.path.normcase(os.path.realpath(comum)), _rodar("--show-toplevel")


def _decidir_outro_projeto(evento, comando, ambiente, cwd):
    """(motivo, detalhe) ou (None, None). Falha ABERTA."""
    if _texto(ambiente.get(ENV_ANCORA_DESLIGA)):
        return None, None
    try:
        ancora = _texto(ambiente.get("CLAUDE_PROJECT_DIR")) or _texto(evento.get("cwd"))
        if ancora is None:
            return None, None
        ancora_n = os.path.normcase(os.path.realpath(ancora))
        comum_ancora = None
        for caminho, rotulo in _alvos_de_escrita(comando, cwd):
            alvo_n = os.path.normcase(os.path.realpath(os.path.abspath(caminho)))
            try:
                if os.path.commonpath([alvo_n, ancora_n]) == ancora_n:
                    continue                          # dentro da âncora
            except ValueError:
                pass                                  # drives diferentes: segue a checagem
            comum, raiz = _repo_de(alvo_n)
            if comum is None:
                continue                              # fora de qualquer repo: não é "outro projeto"
            if comum_ancora is None:
                comum_ancora = _repo_de(ancora_n)[0] or ""
            if comum == comum_ancora:
                continue                              # worktree do mesmo repositório
            return (MOTIVO_OUTRO_PROJETO.format(raiz=raiz or caminho, ancora=ancora, comando=comando.strip(),
                                                env=ENV_ANCORA_DESLIGA),
                    f"outro projeto ({rotulo})")
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None, None
    return None, None


# ------------------------------------------------------------------ 4ª verificação: memória do comando (F-034)
# Memória com `gatilho_comando:` (regex) vale pro que o assistente vai RODAR — o recall só casa o prompt do owner.
# Casou → nega UMA vez por sessão com a memória no motivo; repetir o comando passa. Falha ABERTA.

ENV_MEMORIA_DESLIGA = "MSS_MEMORIA_ACAO_OFF"
MOTIVO_MEMORIA = (
    "[mss-spec] Antes deste comando — a memória `{nome}` cobre isto (caso F-034):\n  {descricao}\n"
    "Detalhe em `{arquivo}`. Siga o que ela diz; se já considerou, repita o comando — este aviso aparece uma vez "
    "por sessão. Escape consciente (só o owner): {env}=1."
)


def _decidir_memoria_do_comando(evento, comando, ambiente):
    """(motivo, detalhe) ou (None, None)."""
    if _texto(ambiente.get(ENV_MEMORIA_DESLIGA)):
        return None, None
    try:
        import _memoria_de_acao as mem
        raiz = _texto(ambiente.get("CLAUDE_PROJECT_DIR")) or _texto(evento.get("cwd"))
        sessao = evento.get("session_id")
        achadas = mem.casar(comando, "comando", raiz, sessao)
        if not achadas:
            return None, None
        nome, arquivo, descricao, _ = achadas[0]
        mem.marcar(sessao, [nome])
        return (MOTIVO_MEMORIA.format(nome=nome, descricao=descricao, arquivo=arquivo, env=ENV_MEMORIA_DESLIGA),
                f"memória do comando ({nome})")
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None, None


def avaliar(evento, ambiente=None, git_destino=None):
    """(tipo, motivo): (None, None) libera · ("deny", …) nega · ("ask", …) pede aprovação do owner."""
    ambiente = os.environ if ambiente is None else ambiente
    if not isinstance(evento, dict) or evento.get("tool_name") not in TOOLS_DE_SHELL:
        return None, None
    entrada = evento.get("tool_input")
    comando = _texto(entrada.get("command") if isinstance(entrada, dict) else None)
    if comando is None:
        return None, None                            # nada a avaliar → nada a negar
    cwd = _texto(evento.get("cwd")) or os.getcwd()
    tipo, motivo, detalhe = _decidir_publicacao(comando, ambiente, cwd, git_destino)
    if tipo != NEGA:
        motivo_outro, detalhe_outro = _decidir_outro_projeto(evento, comando, ambiente, cwd)
        if motivo_outro is not None:                 # negar vence perguntar
            tipo, motivo, detalhe = NEGA, motivo_outro, detalhe_outro
    if tipo != NEGA:
        motivo_pipe, detalhe_pipe = _decidir_pipe(comando, ambiente)
        if motivo_pipe is not None:                  # negar vence perguntar
            tipo, motivo, detalhe = NEGA, motivo_pipe, detalhe_pipe
    if tipo is None:                                 # só quando nenhuma cerca agiu: é aviso, não trava
        motivo_mem, detalhe_mem = _decidir_memoria_do_comando(evento, comando, ambiente)
        if motivo_mem is not None:
            tipo, motivo, detalhe = NEGA, motivo_mem, detalhe_mem
    if tipo is not None:
        _anotar("negou" if tipo == NEGA else "perguntou", detalhe, evento)
    return tipo, motivo


def decidir(evento, ambiente=None, git_destino=None):
    """Compatibilidade: o motivo de qualquer ação (negar ou perguntar), ou None."""
    return avaliar(evento, ambiente, git_destino)[1]


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)                                  # entrada inválida: não há comando → libera
    tipo, motivo = avaliar(evento)
    if tipo is None:
        sys.exit(0)                                  # libera, calado
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": tipo,
        "permissionDecisionReason": motivo,
    }}))
    if tipo == PERGUNTA:
        sys.exit(0)                                  # `ask` só vale com exit 0 (exit 2 = bloqueio)
    print(motivo, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
