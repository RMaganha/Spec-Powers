"""Memória com gatilho de AÇÃO — a memória que vale pro que o assistente vai FAZER, não pro prompt do owner.

Por que existe (caso F-034, `docs/EVALS.md`): o recall casa o prompt do owner (`UserPromptSubmit`). Duas
memórias existiam e não chegaram na hora: a do heredoc com acento (quebrou 3 vezes na mesma sessão) e a do kit
carregado por junction ("falta atualizar o plugin" dito sem abrir a memória). O gatilho delas é uma ação do
assistente — um comando, uma frase da resposta —, que nunca passa pelo prompt.

Uma memória declara, no frontmatter, opcionalmente:
- `gatilho_comando: <regex>` — casa o comando de Bash/PowerShell (lido pelo `git_publicacao.py`, que nega o
  comando UMA vez por sessão com a memória no motivo);
- `gatilho_resposta: <regex>` — casa a resposta final (lido pelo `confere_citacoes.py`, no `Stop`, que devolve
  a resposta UMA vez por sessão com a memória no motivo).
Lê `memory/*.md` do projeto e do kit (memória de máquina, como a do heredoc, mora no kit); `obsoleta:` fica de
fora; regex inválido é ignorado. Estado "já mostrei nesta sessão" no temp do SO. Falha ABERTA em tudo.
"""
import json
import os
import re
import tempfile

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE_FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
CAMPOS = {"comando": "gatilho_comando", "resposta": "gatilho_resposta"}


def _frontmatter(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            m = RE_FRONT.match(f.read())
    except (OSError, UnicodeDecodeError):
        return {}
    if not m:
        return {}
    campos = {}
    for linha in m.group(1).splitlines():
        mm = re.match(r"^([a-z_]+):\s*(.*)$", linha)
        if mm:
            campos[mm.group(1)] = mm.group(2).strip()
    return campos


def memorias(raiz, qual):
    """[(nome, caminho para mostrar, descrição, regex compilado)] das memórias com gatilho de `qual`."""
    campo, saida, vistos = CAMPOS[qual], [], set()
    for base, rotulo in ((raiz, ""), (KIT, "(kit) ")):
        pasta = os.path.join(base, "memory")
        if not base or not os.path.isdir(pasta):
            continue
        for nome in sorted(os.listdir(pasta)):
            if not nome.endswith(".md") or nome in ("MEMORY.md", "DIARIO.md") or nome in vistos:
                continue
            fm = _frontmatter(os.path.join(pasta, nome))
            if fm.get("obsoleta") or not fm.get(campo):
                continue
            try:
                rx = re.compile(fm[campo])
            except re.error:
                continue                              # regex quebrado numa memória não trava ninguém
            vistos.add(nome)
            saida.append((nome[:-3], f"{rotulo}memory/{nome}", fm.get("description", ""), rx))
    return saida


def _estado(sessao):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    return os.path.join(tempfile.gettempdir(), f"mss_memoria_acao_{seguro}.json")


def ja_mostradas(sessao):
    try:
        with open(_estado(sessao), encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:                                # noqa: BLE001
        return set()


def marcar(sessao, nomes):
    try:
        feitas = ja_mostradas(sessao) | set(nomes)
        with open(_estado(sessao), "w", encoding="utf-8") as f:
            json.dump(sorted(feitas), f)
    except Exception:                                # noqa: BLE001
        pass


def casar(texto, qual, raiz, sessao):
    """Memórias de `qual` cujo gatilho casa `texto` e que ainda não foram mostradas nesta sessão."""
    if not isinstance(texto, str) or not texto:
        return []
    feitas = ja_mostradas(sessao)
    return [m for m in memorias(raiz, qual) if m[0] not in feitas and m[3].search(texto)]
