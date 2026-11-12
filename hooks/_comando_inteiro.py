"""Comando guardado inteiro — a anotação ou o diário que cita um comando ou SQL guarda o comando COMPLETO.

Por que existe (decisão 23 de `docs/specs/memoria-em-tabela.md`; spec `docs/specs/comando-guardado-inteiro.md`):
no Whats uma anotação guardou o começo de um UPDATE, sem o WHERE, e o owner precisou reconstituir o comando
(`docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`, seção 4.7). Na mesma medição, 7 das 8 anotações com
reticências em SQL eram legítimas (exemplo de sintaxe, senha escondida) — por isso NEGA UMA VEZ por arquivo e por
conversa, com o trecho no motivo, e a repetição passa.

Roda dentro do `regra_antes_de_gravar.py` (mesmo evento, `PreToolUse` Write|Edit|MultiEdit, mesmo processo: um
hook separado custaria a partida do Python em toda gravação). Também é usado pelo `verificar` de
`templates/memoria_indice.py`, que só CONTA as anotações antigas.

O que conta como comando cortado: reticências (`...` ou `…`) dentro de
- bloco de código de SQL (todas as instruções) ou de terminal (a linha do comando e as de continuação);
- bloco de código sem língua declarada, na linha que começa como SQL ou como comando conhecido;
- trecho entre crases que começa como SQL ou como comando conhecido.
O que NÃO conta: `*****` (senha escondida), intervalo do git (`main...HEAD`), marcador entre `<` e `>` (exemplo de
sintaxe), bloco de outra língua (python, text, json…), saída de programa depois do comando e reticências em prosa.

Só o que a gravação traz de NOVO é cobrado: o corte que já estava no arquivo não volta pra quem edita outro trecho
(o comando original se perdeu; anotação antiga é assunto do `verificar` e do owner).

Sem número de conversa não age ("uma vez" não se garante). Falha ABERTA em tudo: quem chama embrulha em try/except.
Escape consciente, só do owner: `MSS_COMANDO_INTEIRO_OFF=1`.
"""
import json
import os
import re
import tempfile

ENV_DESLIGA = "MSS_COMANDO_INTEIRO_OFF"
INDICES = ("memory.md", "diario.md")
MAX_TRECHOS = 3
MAX_LETRAS = 300

LINGUAS_SQL = {"sql", "tsql", "t-sql", "plsql", "psql", "mssql", "postgres", "postgresql"}
LINGUAS_TERMINAL = {"bash", "sh", "shell", "zsh", "console", "terminal", "powershell", "ps1", "pwsh", "cmd", "bat",
                    "dos", "batch"}
COMANDOS = {
    "git", "gh", "python", "python3", "py", "pip", "pip3", "pytest", "uv", "poetry", "ruff", "docker",
    "docker-compose", "az", "kubectl", "helm", "terraform", "curl", "wget", "npm", "npx", "node", "yarn", "pnpm",
    "sqlcmd", "psql", "bcp", "mysql", "sqlite3", "ssh", "scp", "dotnet", "powershell", "pwsh", "cmd", "bash", "sh",
    "sudo", "make", "claude", "uvicorn", "gunicorn", "flask", "alembic", "n8n", "java", "mvn", "robocopy", "xcopy",
    "copy", "move", "del", "mkdir", "cd", "set", "setx", "export", "cat", "grep", "rg", "ls", "dir", "rm", "cp", "mv",
    "chmod", "tar", "unzip", "openssl", "nslookup", "ping", "netstat", "iisreset", "schtasks", "findstr",
}

RE_CERCA = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*([\w+#.-]*)")
RE_CRASES = re.compile(r"(`+)(.+?)\1")
RE_PROMPT = re.compile(r"^(?:\$|>|PS[^>\n]*>)\s+")
RE_SQL = re.compile(
    r"^(?:select\b|insert\s+into\b|update\s+\S|delete\s+from\b|merge\s+\S|exec(?:ute)?\s+\S|alter\s+\S|create\s+\S"
    r"|drop\s+\S|truncate\s+\S|with\s+\w+\s+as\b|declare\s+@)", re.I)
RE_VERBO_PS = re.compile(r"^[A-Z][a-z]+-[A-Z][A-Za-z]+\b")
RE_PRIMEIRA = re.compile(r"^(\S+)")
RE_RETICENCIAS = re.compile(r"(?<!\.)\.{3,}|…")
RE_MARCADOR = re.compile(r"<[^<>\n]*>")
RE_INTERVALO_GIT = re.compile(r"(?<=[\w/@~^}\]-])\.\.\.(?=[\w/@{])")
CONTINUA = ("\\", "`", "|", "^", "&&")


def _sem_prompt(linha):
    return RE_PROMPT.sub("", linha.strip(), count=1)


def _e_sql(linha):
    return RE_SQL.match(_sem_prompt(linha)) is not None


def _e_comando(linha):
    """True se a linha começa como comando conhecido de terminal (`git …`, `./script …`, `Get-Item …`)."""
    limpa = _sem_prompt(linha)
    m = RE_PRIMEIRA.match(limpa)
    if not m:
        return False
    palavra = m.group(1)
    if palavra.startswith(("./", ".\\")) and len(palavra) > 2:
        return True
    if RE_VERBO_PS.match(limpa):
        return True
    palavra = palavra.lower()
    if palavra.endswith(".exe"):
        palavra = palavra[:-4]
    return palavra in COMANDOS


def _parece_comando_de_terminal(linha):
    """Em bloco de terminal: comando conhecido, ou linha que começa por letra (comando que a lista não conhece).
    Linha de saída que começa por número ou pontuação (`24 passed`, `........ [100%]`) fica de fora."""
    limpa = _sem_prompt(linha)
    return _e_comando(linha) or (bool(limpa) and limpa[0].isalpha() and not limpa.startswith("#"))


def _tem_reticencias(texto):
    limpo = RE_INTERVALO_GIT.sub(" ", RE_MARCADOR.sub(" ", texto))
    return RE_RETICENCIAS.search(limpo) is not None


def _uma_linha(linhas):
    return " ⏎ ".join(l.strip() for l in linhas if l.strip())


def _do_bloco(linhas, lingua):
    """Trechos cortados de um bloco de código. `lingua` já em minúsculas ('' = sem língua declarada)."""
    sql, terminal = lingua in LINGUAS_SQL, lingua in LINGUAS_TERMINAL
    if lingua and not sql and not terminal:
        return []                                     # python, text, json, yaml…: não é comando nem SQL
    achados, i = [], 0
    while i < len(linhas):
        linha = linhas[i]
        if not linha.strip():
            i += 1
            continue
        if sql or _e_sql(linha):                      # instrução SQL: até a linha em branco ou o `;`
            fim = i
            while fim < len(linhas) and linhas[fim].strip():
                fim += 1
                if linhas[fim - 1].rstrip().endswith(";"):
                    break
            instrucao = linhas[i:fim]
            i = fim
        elif _e_comando(linha) or (terminal and _parece_comando_de_terminal(linha)):
            fim = i + 1                               # comando: a linha e as de continuação (`\`, crase, `|`, `^`)
            while fim < len(linhas) and linhas[fim].strip() and linhas[fim - 1].rstrip().endswith(CONTINUA):
                fim += 1
            instrucao = linhas[i:fim]
            i = fim
        else:
            i += 1
            continue
        if _tem_reticencias("\n".join(instrucao)):
            achados.append(_uma_linha(instrucao))
    return achados


def trechos_cortados(texto):
    """Lista (sem repetir, na ordem) dos comandos ou SQL com reticências achados em `texto`."""
    if not isinstance(texto, str) or not texto:
        return []
    achados, bloco, cerca, lingua = [], None, "", ""
    for linha in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = RE_CERCA.match(linha)
        if bloco is None:
            if m:
                bloco, cerca, lingua = [], m.group(1), m.group(2).lower()
                continue
            for crases in RE_CRASES.finditer(linha):
                trecho = crases.group(2).strip()
                if (_e_sql(trecho) or _e_comando(trecho)) and _tem_reticencias(trecho):
                    achados.append(trecho)
        elif m and m.group(1)[0] == cerca[0] and len(m.group(1)) >= len(cerca) and not m.group(2):
            achados += _do_bloco(bloco, lingua)
            bloco = None
        else:
            bloco.append(linha)
    if bloco is not None:                             # cerca sem fechar: o bloco vai até o fim
        achados += _do_bloco(bloco, lingua)
    vistos, saida = set(), []
    for a in achados:
        if a not in vistos:
            vistos.add(a)
            saida.append(a)
    return saida


def e_anotacao_ou_diario(rel):
    """True para `memory/<nome>.md` (fora os índices `MEMORY.md` e `DIARIO.md`) e `memory/sessions/<nome>.md`."""
    if not isinstance(rel, str):
        return False
    partes = rel.replace("\\", "/").lower().split("/")
    if not partes or partes[0] != "memory" or not partes[-1].endswith(".md"):
        return False
    if len(partes) == 2:
        return partes[1] not in INDICES
    return len(partes) == 3 and partes[1] == "sessions"


# --- o que a gravação traz de novo ------------------------------------------------------------------

def _ler(caminho):
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _str(valor):
    return valor if isinstance(valor, str) else ""


def antes_e_depois(tool, entrada, atual):
    """(texto de antes, texto como vai ficar). `atual` = conteúdo do arquivo hoje (None se não existe ou não deu
    pra ler). Edit/MultiEdit cujo trecho antigo não está no arquivo → só o texto novo, sem "antes"."""
    if tool == "Write":
        return atual or "", _str(entrada.get("content"))
    if tool == "Edit":
        trocas = [entrada]
    else:
        trocas = [t for t in (entrada.get("edits") or []) if isinstance(t, dict)]
    novos = "\n".join(_str(t.get("new_string")) for t in trocas)
    if atual is None:
        return "", novos
    depois = atual
    for t in trocas:
        velho = _str(t.get("old_string"))
        if not velho or velho not in depois:
            return "", novos
        depois = depois.replace(velho, _str(t.get("new_string")), -1 if t.get("replace_all") else 1)
    return atual, depois


# --- estado: arquivos já avisados nesta conversa ----------------------------------------------------

def _estado(sessao):
    seguro = re.sub(r"[^\w-]", "_", str(sessao))[:80]
    return os.path.join(tempfile.gettempdir(), f"mss_comando_inteiro_{seguro}.json")


def ja_avisados(sessao):
    try:
        with open(_estado(sessao), encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:                                # noqa: BLE001
        return set()


def marcar(sessao, rel):
    try:
        feitos = ja_avisados(sessao) | {rel}
        with open(_estado(sessao), "w", encoding="utf-8") as f:
            json.dump(sorted(feitos), f)
    except Exception:                                # noqa: BLE001
        pass


# --- decisão ----------------------------------------------------------------------------------------

def motivo(rel, trechos):
    lista = "\n".join(f"  - {t if len(t) <= MAX_LETRAS else t[:MAX_LETRAS] + ' [segue]'}" for t in trechos[:MAX_TRECHOS])
    resto = f"\n  (e mais {len(trechos) - MAX_TRECHOS})" if len(trechos) > MAX_TRECHOS else ""
    return (f"[mss-spec] antes de gravar {rel}: comando ou SQL com reticências —\n{lista}{resto}\n"
            f"Comando ou SQL que o owner vai rodar de novo é gravado INTEIRO na anotação e no diário (decisão 23 da "
            f"memória em tabela). Senha, token e credencial continuam escondidos: escreva ***** e onde o valor vive, "
            f"nunca o valor. Não tem o comando inteiro? Diga isso na anotação e de onde tirar — não invente o que "
            f"falta. É exemplo de sintaxe ou trecho que ninguém vai rodar? Repita a gravação: este aviso aparece uma "
            f"vez por arquivo nesta conversa. Escape consciente (só o owner): {ENV_DESLIGA}=1.")


def conferir(evento, rel, raiz, ambiente):
    """Motivo da negação (str) ou None. `rel` = caminho relativo à raiz do projeto, com `/`."""
    if (ambiente.get(ENV_DESLIGA) or "").strip():
        return None
    sessao = evento.get("session_id")
    if not sessao or not e_anotacao_ou_diario(rel):
        return None
    chave = rel.replace("\\", "/").lower()
    if chave in ja_avisados(sessao):
        return None
    entrada = evento.get("tool_input")
    if not isinstance(entrada, dict):
        return None
    antes, depois = antes_e_depois(evento.get("tool_name"), entrada, _ler(os.path.join(raiz, *rel.split("/"))))
    velhos = set(trechos_cortados(antes))
    novos = [t for t in trechos_cortados(depois) if t not in velhos]
    if not novos:
        return None
    marcar(sessao, chave)
    return motivo(rel, novos)
