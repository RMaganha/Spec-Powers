"""Hook do mss-spec: REGRA POR TIPO DE ARQUIVO, lida ANTES de gravar.

Por que existe: as regras de caminho do projeto (`.claude/rules/*.md`, frontmatter `paths:`) carregam
quando o assistente LÊ um arquivo que casa. Quando ele CRIA um arquivo novo — ou edita sem ler antes —
a regra não carrega: no Whats, `banco.md` faltou em 5 conversas que criaram arquivos em `sql/`.

Contrato:
- evento `PreToolUse`, matcher `Write|Edit|MultiEdit`;
- o caminho a gravar (relativo à raiz do projeto, `\\` → `/`, sem diferenciar maiúsculas) casa o
  `paths:` de alguma regra → **nega UMA vez por sessão e por regra**, com o texto da regra (sem o
  frontmatter) no motivo; a 2ª gravação passa. Várias regras no mesmo arquivo → uma negação só, com
  todos os textos, e todas ficam marcadas como mostradas;
- caminho fora da raiz (`CLAUDE_PROJECT_DIR` › `cwd`) nunca casa; regra sem `paths:` é ignorada;
- estado "já mostrada" no temp do SO (`mss_regra_antes_<sessao>.json`), como `_memoria_de_acao.py`;
- **falha ABERTA** e exit 0 sempre: frontmatter quebrado, arquivo ilegível ou qualquer bug daqui →
  silêncio. Este hook nunca trava o trabalho por defeito próprio.

Escape consciente, só do owner: `MSS_REGRA_OFF=1`.
"""
import json
import os
import posixpath
import re
import sys
import tempfile


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
            _registrar("regra_antes_de_gravar", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_REGRA_OFF"
ENV_RAIZ = "CLAUDE_PROJECT_DIR"
TOOLS_DE_ESCRITA = ("Write", "Edit", "MultiEdit")
PASTA_REGRAS = (".claude", "rules")


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


# --- glob -------------------------------------------------------------------------------------

def _regex_do_padrao(padrao):
    saida, i = [], 0
    while i < len(padrao):
        if padrao.startswith("**/", i):
            saida.append("(?:.*/)?")
            i += 3
        elif padrao.startswith("**", i):
            saida.append(".*")
            i += 2
        elif padrao[i] == "*":
            saida.append("[^/]*")
            i += 1
        elif padrao[i] == "?":
            saida.append("[^/]")
            i += 1
        else:
            saida.append(re.escape(padrao[i]))
            i += 1
    return re.compile("^" + "".join(saida) + "$")


def casa_glob(rel, padrao):
    """True se o caminho relativo `rel` casa o glob `padrao` (`**`, `*`, `?`); sem diferenciar
    maiúsculas e com `\\` tratado como `/` (Windows)."""
    rel = rel.replace("\\", "/").lower()
    padrao = padrao.replace("\\", "/").lower()
    return _regex_do_padrao(padrao).match(rel) is not None


# --- regras do projeto ------------------------------------------------------------------------

def _aspas(item):
    item = item.strip()
    if len(item) >= 2 and item[0] == item[-1] and item[0] in "\"'":
        item = item[1:-1]
    return item.strip()


def _separar(conteudo):
    """(paths, texto sem frontmatter). Sem frontmatter → ([], texto). Frontmatter aberto e não
    fechado → ValueError (a regra é pulada)."""
    conteudo = conteudo.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    linhas = conteudo.split("\n")
    if not linhas or linhas[0].strip() != "---":
        return [], conteudo
    fim = next((i for i in range(1, len(linhas)) if linhas[i].strip() == "---"), None)
    if fim is None:
        raise ValueError("frontmatter sem fechamento")
    paths, em_paths = [], False
    for linha in linhas[1:fim]:
        chave = re.match(r"^paths:\s*(.*)$", linha)
        if chave:
            resto = chave.group(1).strip()
            em_paths = not resto
            if resto.startswith("[") and resto.endswith("]"):
                paths += [_aspas(p) for p in resto[1:-1].split(",") if _aspas(p)]
            elif resto:
                paths.append(_aspas(resto))
        elif em_paths and re.match(r"^\s*-\s", linha):
            item = _aspas(linha.strip()[1:])
            if item:
                paths.append(item)
        elif linha.strip() and not linha.startswith((" ", "\t")):
            em_paths = False
    return paths, "\n".join(linhas[fim + 1:]).strip("\n")


def regras_do_projeto(raiz):
    """[(nome do arquivo, padrões do `paths:`, texto sem frontmatter)] — só regras COM `paths:`.
    Arquivo ilegível ou com frontmatter quebrado é pulado (falha aberta)."""
    pasta = os.path.join(raiz, *PASTA_REGRAS)
    try:
        nomes = sorted(n for n in os.listdir(pasta) if n.lower().endswith(".md"))
    except OSError:
        return []
    regras = []
    for nome in nomes:
        try:
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                paths, texto = _separar(f.read())
        except Exception:                            # noqa: BLE001
            continue
        if paths:
            regras.append((nome, paths, texto))
    return regras


# --- estado: regras já mostradas nesta sessão -------------------------------------------------

def _estado(sessao):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    return os.path.join(tempfile.gettempdir(), f"mss_regra_antes_{seguro}.json")


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


# --- decisão ----------------------------------------------------------------------------------

def _normalizar(caminho):
    return posixpath.normpath(caminho.replace("\\", "/"))


def _absoluto(caminho):
    return caminho.startswith("/") or re.match(r"^[A-Za-z]:/", caminho) is not None


def relativo_a_raiz(alvo, raiz, cwd):
    """Caminho do alvo relativo à raiz (com `/`, maiúsculas originais); None se o alvo está fora
    da raiz. Alvo relativo resolve contra o `cwd` do evento, como o tool resolveria."""
    alvo = _normalizar(alvo)
    raiz = _normalizar(raiz).rstrip("/")
    if not _absoluto(alvo):
        alvo = _normalizar((_normalizar(cwd).rstrip("/") if cwd else raiz) + "/" + alvo)
    if alvo.lower() == raiz.lower() or not alvo.lower().startswith(raiz.lower() + "/"):
        return None
    return alvo[len(raiz) + 1:]


def _motivo(rel, casadas):
    if len(casadas) == 1:
        nome, _, texto = casadas[0]
        return (f"[mss-spec] antes de gravar {rel}, leia a regra deste tipo de arquivo "
                f"(.claude/rules/{nome}):\n\n{texto}\n\nDepois repita a gravação.")
    nomes = ", ".join(f".claude/rules/{n}" for n, _, _ in casadas)
    blocos = "\n\n".join(f"[.claude/rules/{n}]\n{t}" for n, _, t in casadas)
    return (f"[mss-spec] antes de gravar {rel}, leia as regras deste tipo de arquivo "
            f"({nomes}):\n\n{blocos}\n\nDepois repita a gravação.")


def responder(evento, ambiente=None):
    """Saída de deny do PreToolUse, ou None (libera calado)."""
    ambiente = os.environ if ambiente is None else ambiente
    if _texto(ambiente.get(ENV_DESLIGA)):
        return None
    if not isinstance(evento, dict) or evento.get("tool_name") not in TOOLS_DE_ESCRITA:
        return None
    entrada = evento.get("tool_input")
    alvo = _texto(entrada.get("file_path")) if isinstance(entrada, dict) else None
    cwd = _texto(evento.get("cwd"))
    raiz = _texto(ambiente.get(ENV_RAIZ)) or cwd
    if not alvo or not raiz:
        return None

    rel = relativo_a_raiz(alvo, raiz, cwd)
    if rel is None:
        return None
    casadas = [r for r in regras_do_projeto(raiz) if any(casa_glob(rel, p) for p in r[1])]
    if not casadas:
        return None
    sessao = evento.get("session_id")
    feitas = ja_mostradas(sessao)
    casadas = [r for r in casadas if r[0] not in feitas]
    if not casadas:
        return None

    marcar(sessao, [r[0] for r in casadas])
    _anotar("negou", ", ".join(r[0] for r in casadas), evento)    # nomes das regras, nunca o caminho
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": _motivo(rel, casadas),
    }}


def main():
    try:
        evento = json.load(sys.stdin)
        saida = responder(evento)
        if saida is not None:
            # O motivo é pt-BR: força UTF-8 (no Windows o default é cp1252).
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except (AttributeError, OSError):
                pass
            json.dump(saida, sys.stdout, ensure_ascii=False)
    except Exception:                                # noqa: BLE001
        pass                                         # bug/entrada inválida NUNCA trava
    sys.exit(0)                                      # SEMPRE 0


if __name__ == "__main__":
    main()
