"""Hook do mss-spec: BANCO DE PRODUÇÃO — leitura só com o OK do owner (um OK vale a tarefa), escrita nunca
pelo assistente.

Por que existe (benchmark MSIG_Agentes, 2026-11-06, item 5): o kit de agentes da equipe tem um hook que
classifica alias/host de produção, responde `ask` com o motivo, carimba a aprovação por tarefa (2 h) quando um
comando de produção executa, libera rotinas agendadas registradas e nega qualquer DML/DDL — e o MCP só aceita
SELECT. Aqui o `git_publicacao.py` cerca push e deploy, e o `docs/AMBIENTES.md` diz onde a produção mora, mas
nada cercava consulta ou escrita em banco de produção pelo shell ou por um MCP de SQL.

Fonte dos marcadores — o `docs/AMBIENTES.md` do projeto (`CLAUDE_PROJECT_DIR` › `cwd`), seção `## Produção`:
- linha "- **Hosts de produção (cerca):** `MS10PROSQL`, `BANCO_PRD`" → marcadores explícitos (vence);
- sem a linha: heurística — todo token em crase da seção que parece host/alias (sem espaço, sem `/`, sem
  extensão de arquivo, ≥ 5 caracteres, com dígito, maiúscula, hífen ou ponto);
- linha "- **Rotinas autorizadas em produção (só leitura):** `scripts/x.py`" → comando que invoca o
  caminho passa calado (rotina agendada não tem humano pra responder popup).
Sem seção, sem marcador → libera calado: não há produção declarada pra proteger.

Contrato:
- `PreToolUse`, matcher `Bash|PowerShell|mcp__.*`; lê `tool_input.command` (shell) ou `query`/`sql`/
  `statement` (MCP); num MCP, o nome do servidor (`mcp__<servidor>__…`) também conta como texto;
- cita um marcador (token inteiro, sem caixa) num segmento **executável** (não `echo`/`grep`/`cat`…), ou
  invoca um `.py` do projeto cujo conteúdo cita um marcador:
  - **escrita** (INSERT/UPDATE/DELETE/MERGE/ALTER/DROP/TRUNCATE/CREATE/GRANT/EXEC) numa consulta → **nega**:
    DML/DDL de produção vira `.sql` entregue ao owner;
  - **leitura** → **pede aprovação** (`ask`) **uma vez por tarefa**: o `--post` (`PostToolUse`) carimba quando
    um comando de produção EXECUTOU (executou = o owner aprovou); dentro da janela
    (`MSS_BANCO_PRD_MINUTOS`, padrão 120) os seguintes passam calados;
- **falha**: avaliação estourada com comando presente → `ask` (cerca com defeito não abre nem trava sozinha);
  evento sem comando → libera calado;
- escape consciente, só do owner: `MSS_BANCO_PRD_OFF=1`; registra `negou`/`perguntou`/`liberou-rotina`
  no registro local (`hooks/_registro.py`).

O rótulo 🟨 <ambiente> / 🟥 PRODUÇÃO em toda consulta é prosa (`.claude/rules/banco-e-segredo.md`): hook não
escreve resposta. Credencial nenhuma passa por aqui: o hook só lê nomes de host/alias do AMBIENTES.md.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import unicodedata


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
            _registrar("banco_producao", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_BANCO_PRD_OFF"
ENV_MINUTOS = "MSS_BANCO_PRD_MINUTOS"
MINUTOS_PADRAO = 120
NEGA, PERGUNTA = "deny", "ask"
TOOLS_DE_SHELL = ("Bash", "PowerShell")

RE_SECAO = re.compile(r"^## +(.+?)\s*$", re.M)
RE_HOSTS = re.compile(r"\*\*Hosts de produ[cç][aã]o \(cerca\):\*\*(.*)$", re.I | re.M)
RE_ROTINAS = re.compile(r"\*\*Rotinas autorizadas em produ[cç][aã]o[^*]*:\*\*(.*)$", re.I | re.M)
RE_CRASE = re.compile(r"`([^`\n]+)`")
EXTENSOES = (".md", ".py", ".json", ".yml", ".yaml", ".txt", ".sql", ".env", ".ps1", ".html", ".js", ".ts",
             ".csv", ".xlsx", ".bat", ".sh", ".toml", ".cfg", ".ini", ".git")
VERBOS_TEXTO = {"echo", "printf", "grep", "egrep", "rg", "sed", "awk", "cat", "head", "tail", "less", "more",
                "findstr", "select-string", "write-output", "write-host", "type", "diff", "wc", "sort", "uniq",
                "cut", "tr", "ls", "dir", "find", "get-content", "get-childitem", "test-path", "git", "code",
                "notepad", "explorer"}
SEPARADORES = re.compile(r"\n|;|&&|\|\||\||\(")
RE_SCRIPT_PY = re.compile(r"(?<![\w/\\.-])((?:[\w.\\/-]+[\\/])?[\w.-]+\.py)\b")
RE_ESCRITA_SQL = re.compile(r"(?<![\w.])(insert|update|delete|merge|alter|drop|truncate|create|grant|revoke|exec|"
                            r"execute|sp_executesql|bulk)\b", re.I)
RE_LEITURA_SQL = re.compile(r"^\s*(?:--[^\n]*\n|/\*.*?\*/\s*)*(select|with|show|explain|describe|desc)\b", re.I | re.S)
VERBOS_SQL_SHELL = ("sqlcmd", "psql", "mysql", "bcp", "osql", "invoke-sqlcmd", "sqlite3")
TAMANHO_MAX_SCRIPT = 2_000_000

MOTIVO_ESCRITA = (
    "[mss-spec] Escrita em banco de PRODUÇÃO ({marcador}) é ato do owner, nunca do assistente. DML/DDL de produção "
    "vira um `.sql` entregue pra ele executar (com o SELECT das linhas afetadas antes e o do estado final depois). "
    "Leitura (SELECT) em produção passa com o OK dele, uma vez por tarefa. Escape consciente, só do owner: {env}=1."
)
MOTIVO_LEITURA = (
    "[mss-spec] Este comando lê banco de PRODUÇÃO ({marcador} — `docs/AMBIENTES.md`, seção Produção). Regra do "
    "kit: produção só com o OK do owner. Ao aprovar, a aprovação vale pra esta tarefa ({minutos} min) — sem novo "
    "popup a cada consulta. Rotula o resultado como 🟥 CONSULTA PRODUÇÃO. Rotina agendada? Registre o script em "
    "`docs/AMBIENTES.md` → Produção → **Rotinas autorizadas em produção (só leitura)**. Escape, só do owner: {env}=1."
)
MOTIVO_DEFEITO = (
    "[mss-spec] A cerca de banco de produção (hooks/banco_producao.py) estourou ao avaliar este comando: {erro}. "
    "Ela pede a sua aprovação em vez de decidir sozinha. Escape consciente, só do owner: {env}=1."
)


def _texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else None


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


# ------------------------------------------------------------------ docs/AMBIENTES.md → marcadores

def secao_producao(texto):
    """O corpo da seção `## Produção` (ou `## Prod…`) do AMBIENTES.md; '' se não há."""
    partes = RE_SECAO.split(texto)
    for i in range(1, len(partes) - 1, 2):
        if _sem_acento(partes[i]).startswith("prod"):
            return partes[i + 1]
    return ""


def _parece_host(token):
    t = token.strip()
    if len(t) < 5 or " " in t or "/" in t or "\\" in t or t.startswith(("-", "<", "$", "*")):
        return False
    if any(t.lower().endswith(e) for e in EXTENSOES):
        return False
    return any(c.isdigit() or c.isupper() or c in "-." for c in t)


def marcadores(texto_ambientes):
    """(hosts/aliases de produção, rotinas autorizadas) lidos da seção Produção."""
    secao = secao_producao(texto_ambientes or "")
    if not secao:
        return [], []
    explicitos = RE_HOSTS.search(secao)
    if explicitos:
        hosts = [t.strip() for t in RE_CRASE.findall(explicitos.group(1)) if t.strip() and t.strip() != "*****"]
    else:
        hosts = sorted({t.strip() for t in RE_CRASE.findall(secao) if _parece_host(t)})
    rot = RE_ROTINAS.search(secao)
    rotinas = [t.strip().replace("\\", "/") for t in RE_CRASE.findall(rot.group(1))] if rot else []
    return hosts, rotinas


def _ler_ambientes(raiz):
    try:
        with open(os.path.join(raiz, "docs", "AMBIENTES.md"), encoding="utf-8-sig", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


# ------------------------------------------------------------------ comando → acesso a produção?

def _segmentos_executaveis(comando):
    out = []
    for seg in SEPARADORES.split(comando):
        toks = seg.strip().split()
        if not toks:
            continue
        verbo = toks[0].strip("&\"'").lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if verbo.endswith(".exe"):
            verbo = verbo[:-4]
        if verbo in VERBOS_TEXTO:
            continue
        out.append(seg)
    return out


def _cita(texto, marcador):
    return re.search(r"(?<![\w.-])" + re.escape(marcador) + r"(?![\w-])", texto, re.I) is not None


def _scripts_citados(segmentos, raiz):
    arquivos = []
    for seg in segmentos:
        for bruto in RE_SCRIPT_PY.findall(seg):
            caminho = bruto.replace("\\", "/")
            cand = caminho if os.path.isabs(caminho) else os.path.join(raiz, caminho)
            if os.path.isfile(cand):
                arquivos.append(cand)
    return arquivos


def _conteudo(caminho):
    try:
        if os.path.getsize(caminho) > TAMANHO_MAX_SCRIPT:
            return ""
        with open(caminho, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _escreve(texto_sql):
    """True se o SQL (ou a linha de comando com SQL) tem verbo de escrita e não é um SELECT puro."""
    if RE_LEITURA_SQL.match(texto_sql) and not RE_ESCRITA_SQL.search(texto_sql.split("\n", 1)[0]):
        # SELECT na 1ª linha: ainda pode haver DML depois de um `;`
        resto = texto_sql.split(";", 1)[1] if ";" in texto_sql else ""
        return RE_ESCRITA_SQL.search(resto) is not None
    return RE_ESCRITA_SQL.search(texto_sql) is not None


def classificar(evento, hosts, rotinas, raiz):
    """(acesso, marcador, texto) — acesso ∈ {None, 'rotina', 'leitura', 'escrita'}."""
    tool = evento.get("tool_name") or ""
    entrada = evento.get("tool_input") if isinstance(evento.get("tool_input"), dict) else {}
    if tool in TOOLS_DE_SHELL:
        comando = _texto(entrada.get("command"))
        if comando is None:
            return None, None, ""
        segmentos = _segmentos_executaveis(comando)
        texto = "\n".join(segmentos)
        if not texto.strip():
            return None, None, ""
        norm = comando.replace("\\", "/")
        for r in rotinas:
            if r and r in norm:
                return "rotina", r, texto
        achado = next((h for h in hosts if _cita(texto, h)), None)
        if achado is None:
            for arq in _scripts_citados(segmentos, raiz):
                corpo = _conteudo(arq)
                achado = next((h for h in hosts if _cita(corpo, h)), None)
                if achado:
                    break
            if achado is None:
                return None, None, ""
            return "leitura", achado, texto             # script: não dá pra saber o SQL → leitura (pede OK)
        tem_sql = any(v in texto.lower() for v in VERBOS_SQL_SHELL) or re.search(r"\s-[QqcCe]\s", texto)
        if tem_sql and _escreve(texto):
            return "escrita", achado, texto
        return "leitura", achado, texto
    if tool.startswith("mcp__"):
        sql = next((entrada.get(k) for k in ("query", "sql", "statement", "command") if _texto(entrada.get(k))), None)
        if sql is None:
            return None, None, ""
        servidor = tool.split("__")[1] if tool.count("__") >= 2 else ""
        texto = f"{servidor}\n{sql}"
        achado = next((h for h in hosts if _cita(texto, h)), None)
        if achado is None:
            return None, None, ""
        return ("escrita" if _escreve(sql) else "leitura"), achado, texto
    return None, None, ""


# ------------------------------------------------------------------ carimbo da aprovação (por projeto)

def _carimbo(raiz, ambiente):
    pasta = _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()
    chave = hashlib.sha1(os.path.normcase(os.path.abspath(raiz)).encode("utf-8")).hexdigest()[:12]
    return os.path.join(pasta, f"mss_banco_prd_{chave}.json")


def aprovacao_vigente(raiz, ambiente, agora=None):
    try:
        minutos = int(ambiente.get(ENV_MINUTOS) or MINUTOS_PADRAO)
    except (TypeError, ValueError):
        minutos = MINUTOS_PADRAO
    try:
        with open(_carimbo(raiz, ambiente), encoding="utf-8") as f:
            em = float(json.load(f).get("em", 0))
    except Exception:                                # noqa: BLE001
        return False
    agora = time.time() if agora is None else agora
    return 0 <= agora - em < minutos * 60


def carimbar(raiz, ambiente, agora=None):
    try:
        with open(_carimbo(raiz, ambiente), "w", encoding="utf-8") as f:
            json.dump({"em": time.time() if agora is None else agora}, f)
    except OSError:
        pass


# ------------------------------------------------------------------ decisão

def _raiz(evento, ambiente):
    return _texto(ambiente.get("CLAUDE_PROJECT_DIR")) or _texto(evento.get("cwd")) or os.getcwd()


def avaliar(evento, ambiente=None, agora=None):
    """(tipo, motivo): (None, None) libera · ('deny', …) · ('ask', …)."""
    ambiente = os.environ if ambiente is None else ambiente
    if not isinstance(evento, dict):
        return None, None
    if _texto(ambiente.get(ENV_DESLIGA)):
        return None, None
    tool = evento.get("tool_name") or ""
    if tool not in TOOLS_DE_SHELL and not tool.startswith("mcp__"):
        return None, None
    try:
        raiz = _raiz(evento, ambiente)
        hosts, rotinas = marcadores(_ler_ambientes(raiz))
        if not hosts and not rotinas:
            return None, None
        acesso, marcador, _ = classificar(evento, hosts, rotinas, raiz)
        if acesso is None:
            return None, None
        if acesso == "rotina":
            _anotar("liberou-rotina", marcador, evento)
            return None, None
        if acesso == "escrita":
            _anotar("negou", f"escrita em {marcador}", evento)
            return NEGA, MOTIVO_ESCRITA.format(marcador=marcador, env=ENV_DESLIGA)
        if aprovacao_vigente(raiz, ambiente, agora):
            return None, None
        _anotar("perguntou", f"leitura em {marcador}", evento)
        minutos = ambiente.get(ENV_MINUTOS) or MINUTOS_PADRAO
        return PERGUNTA, MOTIVO_LEITURA.format(marcador=marcador, minutos=minutos, env=ENV_DESLIGA)
    except Exception as erro:                        # noqa: BLE001 — cerca com defeito: pergunta, não decide
        return PERGUNTA, MOTIVO_DEFEITO.format(erro=erro, env=ENV_DESLIGA)


def pos(evento, ambiente=None, agora=None):
    """PostToolUse: um comando de leitura em produção EXECUTOU → o owner aprovou → carimba a tarefa."""
    ambiente = os.environ if ambiente is None else ambiente
    try:
        if not isinstance(evento, dict) or _texto(ambiente.get(ENV_DESLIGA)):
            return False
        raiz = _raiz(evento, ambiente)
        hosts, rotinas = marcadores(_ler_ambientes(raiz))
        if not hosts:
            return False
        acesso, _, _ = classificar(evento, hosts, rotinas, raiz)
        if acesso != "leitura":
            return False
        carimbar(raiz, ambiente, agora)
        return True
    except Exception:                                # noqa: BLE001
        return False


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    if "--post" in sys.argv[1:]:
        pos(evento)
        sys.exit(0)
    tipo, motivo = avaliar(evento)
    if tipo is None:
        sys.exit(0)
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
