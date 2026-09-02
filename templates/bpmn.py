"""Gera o desenho BPMN dos processos do projeto a partir do CÓDIGO (leitura estática por `ast`).

Irmão do `mapa_neural.py` (mapa mental) e do `anatomia.py` (painel de runtime): script
determinístico, testável, com duas saídas do mesmo modelo — `docs/bpmn.md` (texto: é o que o
ASSISTENTE lê) e `docs/bpmn.html` (desenho: é o que o HUMANO vê). Ambas derivadas e fora do git.

Um processo por **porta de entrada**: rota Flask/FastAPI (`POST /cotacao`) ou, quando o projeto não
expõe rota, os `main()`/`if __name__` da raiz. Regra dura: **nunca inventa caixa que não está no
código**; o que não é derivável (gateway inclusivo, por evento, objeto de dados, grupo) fica
declarado como não derivável na saída, e `.py` que não parseia vai pra "não lido" — falha ABERTA,
nunca derruba a geração.

Poda antes de fidelidade: só vira caixa chamada a função do próprio projeto ou decisão que muda o
desfecho. Control-flow completo daria 80 caixas por rota e ninguém abriria o arquivo duas vezes.
"""
from __future__ import annotations

import argparse
import ast
import html as _html
import re
import sys
from pathlib import Path

# ------------------------------------------------------------------------------------- constantes

_LIMITE_NOS = 60          # nós por processo; corte deixa rastro "… (+N)" (F-009: sem corte calado)
_PROFUNDIDADE = 2         # níveis de subprocesso expandidos
_MAX_ROTULO = 64          # bytes de rótulo antes do reticente

# pastas que nunca são processo do sistema (mesma fronteira do mapa_neural: um projeto por janela)
_FORA = frozenset({
    ".venv", "venv", "env", "node_modules", ".git", ".claude", ".pytest_cache", "__pycache__",
    ".mypy_cache", ".ruff_cache", "htmlcov", "build", "dist", ".idea", ".vscode",
    "tests", "test", "backup", "certs",
})

_METODOS_ROTA = frozenset({"get", "post", "put", "delete", "patch", "head", "options"})

# banco (elemento 16 — armazenamento de dados)
_DB_METODOS = frozenset({"execute", "executemany", "fetchall", "fetchone", "fetchmany"})
_DB_FUNCOES = frozenset({"connect", "create_engine", "read_sql", "read_sql_query", "to_sql"})
_DB_LIBS = frozenset({"pyodbc", "psycopg2", "psycopg", "sqlite3", "sqlalchemy", "pymssql", "asyncpg"})

# HTTP / serviço externo (elementos 11 e 13 — fluxo de mensagem e piscina)
_HTTP_LIBS = frozenset({"requests", "httpx", "aiohttp", "urllib", "urllib3"})
_HTTP_METODOS = frozenset({"get", "post", "put", "delete", "patch", "request", "send"})

# SDK de LLM: o serviço externo que NÃO se detecta por nome de lib na chamada, porque a chamada
# de verdade é método de instância (`self.model.generate_content(...)`). O sinal honesto é o
# **import do SDK no arquivo** — mesmo tardio, dentro do método, como no MSS-SSC. Sem import, o
# gerador não inventa piscina.
_LLM_SDKS = {
    "google.generativeai": "Gemini", "google.genai": "Gemini", "vertexai": "Vertex AI",
    "openai": "OpenAI", "anthropic": "Anthropic", "cohere": "Cohere",
    "langchain_openai": "OpenAI", "langchain_google_genai": "Gemini",
}
_LLM_CONSTRUTORES = frozenset({"GenerativeModel", "configure", "Client", "OpenAI", "AsyncOpenAI",
                               "AzureOpenAI", "AsyncAzureOpenAI", "Anthropic", "AsyncAnthropic",
                               "ChatOpenAI", "ChatGoogleGenerativeAI"})
_LLM_METODOS = frozenset({"generate_content", "generate_content_async", "send_message",
                          "start_chat", "count_tokens", "invoke", "ainvoke"})
_LLM_CADEIAS = (".completions.create", ".messages.create", ".responses.create")

# paralelismo (elemento 7 — gateway paralelo)
_PARALELO = frozenset({"gather", "ThreadPoolExecutor", "ProcessPoolExecutor", "as_completed"})

# o que a leitura estática NÃO consegue derivar — vai declarado na saída, não some em silêncio
NAO_DERIVAVEIS = [
    ("8. gateway inclusivo", "exige saber que dois caminhos podem valer ao mesmo tempo — o código "
                             "não declara isso"),
    ("9. gateway por evento", "depende de espera por evento externo (fila, timer), não de `if`"),
    ("15. objeto de dados", "o dado que entra/sai de cada tarefa exigiria análise de tipos"),
    ("18. grupo", "agrupamento é intenção de quem modela, não fato do código"),
]


# ------------------------------------------------------------------------------------- utilidades

def _rel(p: Path, proj: Path) -> str:
    try:
        return p.relative_to(proj).as_posix()
    except ValueError:
        return p.name


def _raia_de(rel: str) -> str:
    """Raia (elemento 14) = pasta de 1º nível do módulo; arquivo da raiz fica em 'raiz'."""
    partes = rel.split("/")
    return partes[0] if len(partes) > 1 else "raiz"


def _curto(t: str, n: int = _MAX_ROTULO) -> str:
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def _fonte(no) -> str:
    """Trecho de código como está escrito — nunca parafraseado."""
    if no is None:
        return ""
    try:
        return _curto(ast.unparse(no))
    except Exception:
        return ""


def _doc(fdef) -> str:
    try:
        return (ast.get_docstring(fdef) or "").strip()
    except Exception:
        return ""


def _rotulo_de(fdef, nome: str) -> str:
    """Rótulo da tarefa: 1ª linha do docstring (a frase de negócio que o dev escreveu) ou o nome."""
    doc = _doc(fdef)
    if doc:
        return _curto(doc.split("\n")[0].strip())
    return nome


def _no(tipo: str, rotulo: str, **extra) -> dict:
    base = {
        "tipo": tipo, "rotulo": rotulo, "raia": extra.pop("raia", "raiz"),
        "arquivo": extra.pop("arquivo", ""), "fn": extra.pop("fn", ""),
        "dados": extra.pop("dados", []), "mensagens": extra.pop("mensagens", []),
        "borda": extra.pop("borda", ""), "anotacao": extra.pop("anotacao", ""),
        "ramos": extra.pop("ramos", []), "filhos": extra.pop("filhos", []),
        "reuso": extra.pop("reuso", False),
    }
    base.update(extra)
    return base


def achatar(nos: list) -> list:
    """Todos os nós, descendo em ramos de gateway e filhos de subprocesso."""
    saida = []
    for n in nos:
        saida.append(n)
        for r in n.get("ramos") or []:
            saida.extend(achatar(r["nos"]))
        saida.extend(achatar(n.get("filhos") or []))
    return saida


# ------------------------------------------------------------------------------------ arquivos .py

def _arquivos_py(proj: Path, ignorar=()) -> list[Path]:
    fora = set(_FORA) | {x.strip().strip("/") for x in ignorar if x and x.strip()}
    achados = []

    def desce(d: Path):
        try:
            itens = sorted(d.iterdir(), key=lambda x: (x.is_dir(), x.name.lower()))
        except OSError:
            return
        for item in itens:
            if item.is_dir():
                if item.name in fora or item.name.startswith("."):
                    continue
                desce(item)
            elif item.suffix == ".py":
                achados.append(item)

    desce(proj)
    return achados


# ---------------------------------------------------------------------------- índice de funções

def _rotas_do_decorator(dec) -> list[str]:
    """`@app.route("/x", methods=["POST"])` → ['POST /x'] · `@router.get("/x")` → ['GET /x'].

    Só decorator de verdade: nome citado em comentário/docstring não chega aqui (é AST, não texto).
    """
    if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
        return []
    attr = dec.func.attr
    if attr not in _METODOS_ROTA and attr != "route":
        return []
    if not dec.args or not isinstance(dec.args[0], ast.Constant) or \
            not isinstance(dec.args[0].value, str):
        return []
    caminho = dec.args[0].value
    if attr in _METODOS_ROTA:
        return [f"{attr.upper()} {caminho}"]
    metodos = ["GET"]
    for kw in dec.keywords:
        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
            achados = [e.value.upper() for e in kw.value.elts
                       if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if achados:
                metodos = achados
    return [f"{m} {caminho}" for m in metodos]


def _modulo_para_arquivo(modulo: str, nivel: int, arquivo_caller: str, conhecidos: set) -> str:
    """`from servicos.regras import x` em `web.py` -> `servicos/regras.py`, se existir.

    Trata import relativo (`from .regras import x`) subindo `nivel` pastas a partir do chamador.
    Devolve "" quando o módulo não é do projeto (lib externa) — aí não há o que resolver.
    """
    partes = [x for x in (modulo or "").split(".") if x]
    if nivel:
        base = arquivo_caller.split("/")[:-1]
        base = base[: len(base) - (nivel - 1)] if nivel > 1 else base
        partes = base + partes
    if not partes:
        return ""
    for cand in ("/".join(partes) + ".py", "/".join(partes) + "/__init__.py"):
        if cand in conhecidos:
            return cand
    return ""


def indexar(proj: Path, ignorar=()) -> dict:
    """Varre o projeto e indexa as funções. Devolve o índice usado pela montagem do fluxo.

    Chaves: `por_nome` (fallback heurístico), `por_arquivo` (o par que resolve homônimo),
    `todas` (toda definição — a descoberta de porta de entrada precisa de todos os `main()`),
    `importado` (o que cada arquivo importa de quem, o sinal honesto de dono) e `nao_lidos`.
    """
    defs: dict[str, dict] = {}
    por_arquivo: dict[tuple, dict] = {}
    nao_lidos: list[dict] = []
    todas: list[dict] = []
    imports_crus: dict[str, list] = {}      # arquivo -> [(nome, modulo, nivel)]
    sdk: dict[str, dict] = {}               # arquivo -> {nome local do import: piscina}
    conhecidos: set[str] = set()

    arquivos = _arquivos_py(proj, ignorar)
    conhecidos = {_rel(a, proj) for a in arquivos}

    for arq in arquivos:
        rel = _rel(arq, proj)
        try:
            arvore = ast.parse(arq.read_text(encoding="utf-8"), filename=str(arq))
        except (SyntaxError, ValueError, UnicodeDecodeError, OSError) as e:
            nao_lidos.append({"arquivo": rel, "erro": f"{type(e).__name__}: {e}"})
            continue

        def registra(no, dentro_de=""):
            nome = no.name
            rotas = []
            for dec in no.decorator_list:
                rotas.extend(_rotas_do_decorator(dec))
            entrada = {
                "nome": nome, "no": no, "arquivo": rel, "raia": _raia_de(rel),
                "rotulo": _rotulo_de(no, nome), "doc": _doc(no), "rotas": rotas,
                "classe": dentro_de,
            }
            todas.append(entrada)
            por_arquivo[(rel, nome)] = entrada
            defs.setdefault(nome, entrada)
            if rotas:                      # rota sempre vence a colisão de nome
                defs[nome] = entrada

        for no in ast.walk(arvore):
            if isinstance(no, ast.ImportFrom):
                for a in no.names:
                    imports_crus.setdefault(rel, []).append(
                        (a.asname or a.name, no.module or "", no.level or 0))
                    # `from google import genai` / `from openai import OpenAI`
                    for chave in (f"{no.module}.{a.name}" if no.module else a.name, no.module):
                        if chave in _LLM_SDKS:
                            sdk.setdefault(rel, {})[a.asname or a.name] = _LLM_SDKS[chave]
                            break
            elif isinstance(no, ast.Import):
                # `import google.generativeai as genai` — inclusive TARDIO, dentro do método
                for a in no.names:
                    if a.name in _LLM_SDKS:
                        local = a.asname or a.name.split(".")[0]
                        sdk.setdefault(rel, {})[local] = _LLM_SDKS[a.name]

        for no in arvore.body:
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                registra(no)
            elif isinstance(no, ast.ClassDef):
                for m in no.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        registra(m, no.name)

    importado: dict[str, dict] = {}
    for arquivo, itens in imports_crus.items():
        for nome, modulo, nivel in itens:
            destino = _modulo_para_arquivo(modulo, nivel, arquivo, conhecidos)
            if destino:
                importado.setdefault(arquivo, {})[nome] = destino

    return {"por_nome": defs, "por_arquivo": por_arquivo, "todas": todas, "sdk": sdk,
            "importado": importado, "nao_lidos": nao_lidos, "arquivos": len(arquivos)}


# ------------------------------------------------------------------- classificação de uma chamada

def _nome_chamado(call: ast.Call) -> tuple[str, str]:
    """Devolve (raiz, atributo) da chamada: `requests.post(...)` → ('requests','post')."""
    f = call.func
    if isinstance(f, ast.Name):
        return f.id, ""
    if isinstance(f, ast.Attribute):
        base = f.value
        raiz = base.id if isinstance(base, ast.Name) else (
            base.attr if isinstance(base, ast.Attribute) else "")
        return raiz, f.attr
    return "", ""


def _primeiro_texto(call: ast.Call) -> str:
    for a in call.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            return a.value
    return ""


def _host(url: str) -> str:
    m = re.match(r"https?://([^/\s]+)", url or "")
    return m.group(1) if m else ""


def _e_banco(call: ast.Call) -> str:
    """Rótulo do armazenamento de dados, ou '' se a chamada não fala com banco."""
    raiz, attr = _nome_chamado(call)
    if attr in _DB_METODOS or (raiz in _DB_LIBS and (attr in _DB_FUNCOES or not attr)) \
            or (not attr and raiz in _DB_FUNCOES):
        texto = _primeiro_texto(call)
        if texto:
            return _curto(texto)
        return _curto(f"{raiz}.{attr}" if attr else raiz)
    return ""


def _e_http(call: ast.Call) -> str:
    """Rótulo do fluxo de mensagem (host/serviço), ou '' se não é chamada a serviço externo."""
    raiz, attr = _nome_chamado(call)
    if raiz in _HTTP_LIBS and (attr in _HTTP_METODOS or attr in ("Client", "urlopen", "create")
                               or not attr):
        return _host(_primeiro_texto(call)) or raiz
    return ""


def _e_llm(call: ast.Call, sdks: dict) -> str:
    """Rótulo da piscina de LLM, ou '' — só quando o arquivo importa um SDK de LLM.

    `sdks` mapeia o nome LOCAL do import para a piscina (`genai` → Gemini, `OpenAI` → OpenAI).
    Sem import no arquivo não há piscina: integração se declara no código, não se adivinha.
    """
    if not sdks:
        return ""
    raiz, attr = _nome_chamado(call)
    if raiz in sdks:                                    # genai.GenerativeModel / genai.configure
        return sdks[raiz]
    if attr in sdks:                                    # google.genai.Client após `from google …`
        return sdks[attr]
    padrao = next(iter(sdks.values()))                  # o SDK declarado neste arquivo
    if attr in _LLM_CONSTRUTORES or attr in _LLM_METODOS or (not attr and raiz in _LLM_CONSTRUTORES):
        return padrao
    fonte = _fonte(call.func)                           # cliente.chat.completions.create(...)
    if any(fonte.endswith(c) for c in _LLM_CADEIAS):
        return padrao
    return ""


def _e_externo(call: ast.Call, sdks: dict) -> str:
    return _e_http(call) or _e_llm(call, sdks)


def _calls(no) -> list[ast.Call]:
    """Chamadas de um statement, em ordem de leitura do código."""
    achadas = [x for x in ast.walk(no) if isinstance(x, ast.Call)]
    return sorted(achadas, key=lambda c: (getattr(c, "lineno", 0), getattr(c, "col_offset", 0)))


def _paralelo_em(stmt) -> list[ast.Call]:
    """Chamadas dentro de `asyncio.gather(...)`/pool — os ramos do gateway paralelo."""
    for c in _calls(stmt):
        _, attr = _nome_chamado(c)
        raiz_nome = c.func.id if isinstance(c.func, ast.Name) else attr
        if raiz_nome in _PARALELO or attr in _PARALELO:
            return [x for x in _calls(c) if x is not c]
    return []


# ------------------------------------------------------------------------------ perfil de uma função

def _perfil(fdef, sdks: dict | None = None) -> dict:
    """O que o corpo da função faz, sem descer em outras funções do projeto.

    Serve pra dois fins: anexar banco/mensagem/borda à TAREFA que chama a função (é ela que toca o
    dado, na leitura BPMN) e decidir se a função é tarefa simples ou subprocesso.
    """
    dados, msgs, bordas = [], [], []
    sdks = sdks or {}
    tem_decisao = False

    for no in ast.walk(fdef):
        if isinstance(no, ast.If) and no is not fdef:
            tem_decisao = True
        elif isinstance(no, ast.Try):
            tipos = []
            for h in no.handlers:
                tipos.append(_fonte(h.type) if h.type else "Exception")
                for interno in h.body:
                    if any(isinstance(x, ast.Raise) for x in ast.walk(interno)):
                        tipos[-1] += " → erro"
            if tipos:
                bordas.append(" · ".join(dict.fromkeys(tipos)))
        elif isinstance(no, ast.Call):
            d = _e_banco(no)
            if d:
                dados.append(d)
            h = _e_externo(no, sdks)
            if h:
                msgs.append(h)

    return {
        "dados": list(dict.fromkeys(dados)),
        "mensagens": list(dict.fromkeys(msgs)),
        "borda": " · ".join(dict.fromkeys(bordas)),
        "tem_decisao": tem_decisao,
    }


# --------------------------------------------------------------------------------- montagem do fluxo

class _Montador:
    def __init__(self, indice: dict, profundidade: int, limite: int):
        self.ix = indice
        self.defs = indice["por_nome"]
        self.profundidade = profundidade
        self.limite = limite
        self.piscinas: list[str] = []

    # -- resolução de chamada: mesmo arquivo -> import declarado -> qualquer arquivo ----------
    def resolver(self, nome: str, arquivo_caller: str):
        """Qual definição do projeto esta chamada aponta.

        Ordem importa: dois módulos com `gerar` faziam o processo de um desenhar as caixas
        internas do outro (achado do dogfood no próprio kit). O último degrau é heurístico e
        declarado — não é análise de tipos.
        """
        if not nome:
            return None
        d = self.ix["por_arquivo"].get((arquivo_caller, nome))
        if d:
            return d
        destino = self.ix["importado"].get(arquivo_caller, {}).get(nome)
        if destino:
            d = self.ix["por_arquivo"].get((destino, nome))
            if d:
                return d
        return self.defs.get(nome)

    # -- tarefa/subprocesso a partir de uma chamada a função do projeto -----------------------
    def _no_de_chamada(self, nome: str, prof: int, pilha: tuple, borda="",
                       arquivo_caller: str = "") -> dict | None:
        d = self.resolver(nome, arquivo_caller)
        if not d:
            return None
        perfil = _perfil(d["no"], self.ix["sdk"].get(d["arquivo"], {}))
        tem_chamada_projeto = any(
            self.resolver(_nome_chamado(c)[1] or (c.func.id if isinstance(c.func, ast.Name) else ""),
                          d["arquivo"])
            for c in _calls(d["no"]))
        subproc = perfil["tem_decisao"] or tem_chamada_projeto
        for m in perfil["mensagens"]:
            if m not in self.piscinas:
                self.piscinas.append(m)

        no = _no(
            "subprocesso" if subproc else "tarefa", d["rotulo"],
            raia=d["raia"], arquivo=d["arquivo"], fn=nome,
            dados=perfil["dados"], mensagens=perfil["mensagens"],
            borda=borda or perfil["borda"], anotacao=d["doc"],
        )
        chave = (d["arquivo"], nome)
        if subproc and prof < self.profundidade and chave not in pilha:
            no["filhos"] = self.nos_do_corpo(d["no"].body, d, prof + 1, pilha + (chave,))
            # quem fala com o serviço externo, na leitura BPMN, é a caixa VISÍVEL no nível de
            # cima: sem subir a mensagem do filho, a piscina era desenhada sem seta nenhuma
            # apontando pra ela (visto no MSS-SSC, com o Gemini dois níveis fundo).
            dentro = [x for f in achatar(no["filhos"]) for x in f["mensagens"]]
            no["mensagens"] = list(dict.fromkeys(no["mensagens"] + dentro))
        return no

    # -- statements de um corpo ---------------------------------------------------------------
    def nos_do_corpo(self, corpo, dono: dict, prof: int, pilha: tuple, borda="") -> list:
        nos: list[dict] = []
        for stmt in corpo:
            nos.extend(self._statement(stmt, dono, prof, pilha, borda))
        return nos

    def _statement(self, stmt, dono, prof, pilha, borda="") -> list:
        if isinstance(stmt, ast.If):
            return self._gateway(stmt, dono, prof, pilha, borda)

        if isinstance(stmt, ast.Try):
            tipos = []
            for h in stmt.handlers:
                t = _fonte(h.type) if h.type else "Exception"
                if any(isinstance(x, ast.Raise) for interno in h.body for x in ast.walk(interno)):
                    t += " → erro"
                tipos.append(t)
            nova = " · ".join(dict.fromkeys(tipos)) or borda
            nos = self.nos_do_corpo(stmt.body, dono, prof, pilha, nova)
            if nos:
                for n in nos:
                    n["borda"] = n["borda"] or nova
            else:                       # o try envolvia só chamada a lib: a borda vira o nó
                nos = self._chamadas_soltas(stmt.body, dono, nova)
            nos.extend(self.nos_do_corpo(stmt.orelse, dono, prof, pilha, borda))
            nos.extend(self.nos_do_corpo(stmt.finalbody, dono, prof, pilha, borda))
            return nos

        if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
            nos = self.nos_do_corpo(stmt.body, dono, prof, pilha, borda)
            if nos and isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
                nos[0]["anotacao"] = (nos[0]["anotacao"] + "\n" if nos[0]["anotacao"] else "") + \
                    f"em laço: {_fonte(stmt.target) if hasattr(stmt, 'target') else _fonte(stmt.test)}"
            nos.extend(self.nos_do_corpo(getattr(stmt, "orelse", []), dono, prof, pilha, borda))
            return nos

        if isinstance(stmt, ast.Return):
            # `return servico(x)` é o padrão do router fino: a chamada TEM de virar tarefa antes
            # do evento de fim, senão o processo inteiro sai como início → fim.
            nos = self._chamadas_do_statement(stmt, dono, prof, pilha, borda) if stmt.value else []
            alvo = _fonte(stmt.value) or "fim"
            nos.append(_no("fim", alvo, raia=dono["raia"], arquivo=dono["arquivo"]))
            return nos

        if isinstance(stmt, ast.Raise):
            return [_no("fim_erro", _fonte(stmt.exc) or "raise",
                        raia=dono["raia"], arquivo=dono["arquivo"])]

        # gateway paralelo (elemento 7)
        ramos_par = _paralelo_em(stmt)
        if ramos_par:
            ramos = []
            for c in ramos_par:
                raiz, attr = _nome_chamado(c)
                nome = attr or raiz
                filho = self._no_de_chamada(nome, prof, pilha, borda, dono["arquivo"])
                if filho:
                    ramos.append({"rotulo": filho["rotulo"], "nos": [filho]})
            if ramos:
                return [_no("gateway_paralelo", "em paralelo", raia=dono["raia"],
                            arquivo=dono["arquivo"], ramos=ramos)]

        return self._chamadas_do_statement(stmt, dono, prof, pilha, borda)

    def _chamadas_do_statement(self, stmt, dono, prof, pilha, borda) -> list:
        nos: list[dict] = []
        sdks = self.ix["sdk"].get(dono["arquivo"], {})
        for c in _calls(stmt):
            raiz, attr = _nome_chamado(c)
            nome = attr or raiz
            if self.resolver(nome, dono["arquivo"]):
                filho = self._no_de_chamada(nome, prof, pilha, borda, dono["arquivo"])
                if filho:
                    nos.append(filho)
                    continue
            d = _e_banco(c)
            if d:
                if nos:
                    nos[-1]["dados"] = list(dict.fromkeys(nos[-1]["dados"] + [d]))
                else:
                    nos.append(_no("tarefa", _curto(f"{raiz}.{attr}" if attr else raiz),
                                   raia=dono["raia"], arquivo=dono["arquivo"], dados=[d],
                                   borda=borda))
                continue
            h = _e_externo(c, sdks)
            if h:
                if h not in self.piscinas:
                    self.piscinas.append(h)
                if nos:
                    nos[-1]["mensagens"] = list(dict.fromkeys(nos[-1]["mensagens"] + [h]))
                else:
                    nos.append(_no("tarefa", _curto(f"{raiz}.{attr}" if attr else raiz),
                                   raia=dono["raia"], arquivo=dono["arquivo"], mensagens=[h],
                                   borda=borda))
        return nos

    def _chamadas_soltas(self, corpo, dono, borda) -> list:
        """Corpo que só chama lib externa: vira uma tarefa com os dados/mensagens dele."""
        dados, msgs, rotulo = [], [], ""
        sdks = self.ix["sdk"].get(dono["arquivo"], {})
        for stmt in corpo:
            for c in _calls(stmt):
                raiz, attr = _nome_chamado(c)
                d, h = _e_banco(c), _e_externo(c, sdks)
                if d:
                    dados.append(d)
                if h:
                    msgs.append(h)
                    if h not in self.piscinas:
                        self.piscinas.append(h)
                if (d or h) and not rotulo:
                    rotulo = _curto(f"{raiz}.{attr}" if attr else raiz)
        if not (dados or msgs):
            return []
        return [_no("tarefa", rotulo or "chamada externa", raia=dono["raia"],
                    arquivo=dono["arquivo"], dados=list(dict.fromkeys(dados)),
                    mensagens=list(dict.fromkeys(msgs)), borda=borda)]

    def _gateway(self, stmt: ast.If, dono, prof, pilha, borda) -> list:
        cond = _fonte(stmt.test)
        nos_sim = self.nos_do_corpo(stmt.body, dono, prof, pilha, borda)
        nos_nao = self.nos_do_corpo(stmt.orelse, dono, prof, pilha, borda)
        if not nos_sim and not nos_nao:
            return []                     # `if` que não muda desfecho nem chama nada: poda

        ramos = [{"rotulo": cond or "sim", "nos": nos_sim or
                  [_no("segue", "segue o fluxo", raia=dono["raia"])]}]
        ramos.append({"rotulo": "senão", "nos": nos_nao or
                      [_no("segue", "segue o fluxo", raia=dono["raia"])]})
        return [_no("gateway", self._pergunta(stmt.test, cond), raia=dono["raia"],
                    arquivo=dono["arquivo"], ramos=ramos, borda=borda,
                    pergunta=pergunta_ptbr(stmt.test))]

    @staticmethod
    def _pergunta(teste, cond: str) -> str:
        """O sujeito da decisão (o rótulo verbatim do modelo; os ramos levam a condição inteira)."""
        if isinstance(teste, ast.Compare):
            return _fonte(teste.left) or cond
        if isinstance(teste, ast.UnaryOp):
            return _fonte(teste.operand) or cond
        return cond


# ------------------------------------------------------------------------------------- corte (F-009)

def _cortar(nos: list, limite: int) -> tuple[list, int]:
    """Corta o processo no teto e deixa rastro `… (+N)` — índice que corta calado mente."""
    total = len(achatar(nos))
    if total <= limite:
        return nos, 0
    mantidos, contados = [], 0
    for n in nos:
        peso = len(achatar([n]))
        if contados + peso > limite:
            break
        mantidos.append(n)
        contados += peso
    faltam = total - contados
    mantidos.append(_no("corte", f"… (+{faltam}) — teto de {limite} nós por processo"))
    return mantidos, faltam


# ------------------------------------------------------------------------------------- extração

def _entradas(indice: dict, entradas_extra=()) -> list[dict]:
    """Portas de entrada, em cascata: rota → `main()` na raiz → `main()` em qualquer módulo.

    O 3º degrau nasceu do dogfood no próprio kit, cujos scripts vivem em `templates/` e não na
    raiz: sem ele o projeto saía com ZERO processo (fixture não vê isso; projeto real vê).
    """
    todas = indice["todas"]
    entradas = []
    for d in todas:
        for rota in d["rotas"]:
            entradas.append({"nome": rota, "def": d})
    if not entradas:
        mains = [d for d in todas if d["nome"] == "main"]
        na_raiz = [d for d in mains if "/" not in d["arquivo"]]
        for d in (na_raiz or mains):
            entradas.append({"nome": f"main() · {d['arquivo']}", "def": d})
    for nome in entradas_extra:
        d = indice["por_nome"].get(nome)
        if d and not any(e["def"] is d for e in entradas):
            entradas.append({"nome": f"{d['nome']}() · {d['arquivo']}", "def": d})
    entradas.sort(key=lambda e: e["nome"])
    return entradas


def extrair(proj, profundidade: int = _PROFUNDIDADE, limite: int = _LIMITE_NOS,
            ignorar=(), entradas_extra=()) -> dict:
    """Lê o projeto e devolve o modelo dos processos. Não escreve nada."""
    proj = Path(proj).resolve()      # `--proj .` é como o comando roda: sem resolver, o nome do
                                     # projeto sai vazio (Path(".").name == "")
    indice = indexar(proj, ignorar)
    nao_lidos = indice["nao_lidos"]
    processos = []

    for entrada in _entradas(indice, entradas_extra):
        d = entrada["def"]
        m = _Montador(indice, profundidade, limite)
        inicio = _no("inicio", entrada["nome"], raia=d["raia"], arquivo=d["arquivo"],
                     fn=d["nome"], anotacao=d["doc"])
        corpo = m.nos_do_corpo(d["no"].body, d, 1, ((d["arquivo"], d["nome"]),))
        nos = [inicio] + corpo
        if not any(n["tipo"] in ("fim", "fim_erro") for n in achatar(nos)):
            nos.append(_no("fim", "fim do processo", raia=d["raia"]))
        nos, cortados = _cortar(nos, limite)
        processos.append({
            "nome": entrada["nome"], "arquivo": d["arquivo"], "raia": d["raia"],
            "funcao": d["nome"], "anotacao": d["doc"], "nos": nos,
            "piscinas": list(m.piscinas), "cortados": cortados,
            "raias": list(dict.fromkeys(n["raia"] for n in achatar(nos) if n["raia"])),
        })

    # elemento 20 — chamada de atividade: o que é chamado por 2+ fluxos é reuso de verdade
    uso: dict[str, int] = {}
    for p in processos:
        for n in achatar(p["nos"]):
            if n["fn"] and n["tipo"] in ("tarefa", "subprocesso"):
                uso[n["fn"]] = uso.get(n["fn"], 0) + 1
    for p in processos:
        for n in achatar(p["nos"]):
            if n["fn"] and uso.get(n["fn"], 0) >= 2:
                n["reuso"] = True

    # ordem: do mais rico pro mais pobre (nome desempata). A alfabética abria a página em
    # `GET /` com 2 nós — dois circulinhos — enquanto o processo de 41 nós ficava enterrado, e
    # isso lia como "a ferramenta não achou nada".
    processos.sort(key=lambda p: (-len(achatar(p["nos"])), p["nome"]))

    piscinas = list(dict.fromkeys(x for p in processos for x in p["piscinas"]))
    return {
        "projeto": proj.name, "processos": processos, "nao_lidos": nao_lidos,
        "piscinas": piscinas, "profundidade": profundidade, "limite": limite,
        "arquivos_lidos": indice["arquivos"],
    }


# ----------------------------------------------- rótulo de DESENHO (pt-BR; modelo fica verbatim)
#
# Regra do owner: "trazer o conteúdo em pt-br, inglês só no que for texto de programação".
# Então o MODELO (e o `bpmn.md`) guardam o código como está escrito, e é aqui que nasce o texto
# que vai DENTRO da caixa desenhada: verbo e pergunta em português, identificador do código intacto.

_OPS_PTBR = [
    (ast.Gt, "maior que"), (ast.GtE, "maior ou igual a"),
    (ast.Lt, "menor que"), (ast.LtE, "menor ou igual a"),
    (ast.Eq, "é igual a"), (ast.NotEq, "é diferente de"),
    (ast.In, "está em"), (ast.NotIn, "não está em"),
]

_SQL_PTBR = {"SELECT": "Consulta o banco", "INSERT": "Grava no banco",
             "UPDATE": "Atualiza o banco", "DELETE": "Exclui do banco",
             "MERGE": "Grava no banco", "EXEC": "Executa no banco"}

_TETO_CAIXA = 40          # a caixa de tarefa do bpmn-js cabe ~3 linhas curtas


def _curtinho(texto: str, teto: int) -> str:
    """Corta em fronteira de palavra — rótulo que estoura a caixa é o que fez o desenho falhar."""
    texto = " ".join(str(texto).split())
    if len(texto) <= teto:
        return texto
    corte = texto[:teto].rsplit(" ", 1)[0]
    return (corte or texto[:teto]).rstrip(" ,;:.") + "…"


def pergunta_ptbr(teste) -> str:
    """A condição do `if` como PERGUNTA em pt-BR, com o identificador do código dentro.

    `not dados` → "Falta dados?" · `linha is None` → "linha está vazio?" ·
    `valor > 100000` → "valor maior que 100000?" · `anexos` → "Tem anexos?".
    Sem isto o losango saía rotulado `anexos` ou `row`, que não dizem nada a quem lê o processo.
    """
    if isinstance(teste, ast.UnaryOp) and isinstance(teste.op, ast.Not):
        return f"Falta {_fonte(teste.operand)}?"
    if isinstance(teste, ast.Compare) and len(teste.ops) == 1:
        esq, op = _fonte(teste.left), teste.ops[0]
        dire = _fonte(teste.comparators[0])
        if isinstance(op, ast.Is) and dire == "None":
            return f"{esq} está vazio?"
        if isinstance(op, ast.IsNot) and dire == "None":
            return f"{esq} existe?"
        for tipo, txt in _OPS_PTBR:
            if isinstance(op, tipo):
                return f"{esq} {txt} {dire}?"
    if isinstance(teste, (ast.Name, ast.Attribute, ast.Subscript)):
        return f"Tem {_fonte(teste)}?"
    if isinstance(teste, ast.Call):
        return f"{_fonte(teste)} confirma?"
    return f"{_fonte(teste)}?"


def _so_o_nome(chamada: str) -> str:
    """`JSONResponse({...})` → JSONResponse · `mssc.ValidacaoError('x')` → ValidacaoError."""
    m = re.match(r"^([A-Za-z_][\w.]*)\s*\(", " ".join(str(chamada).split()))
    return m.group(1).split(".")[-1] if m else str(chamada)


def _verbo_sql(sql: str) -> str:
    """O verbo sai do próprio SQL — derivado do código, não inventado."""
    primeira = re.sub(r"^[\s(]+", "", str(sql)).split(" ", 1)[0].upper()
    return _SQL_PTBR.get(primeira, "Acessa o banco")


def _frase(texto: str) -> str:
    """1ª frase do docstring: nome de atividade BPMN é frase curta, não parágrafo."""
    texto = " ".join(str(texto).split())
    for sep in (". ", " — ", " (", "(", ", ", ": ", ";"):
        if sep in texto:
            cabeca = texto.split(sep)[0].strip()
            if len(cabeca) >= 12:
                texto = cabeca
                break
    return texto


def rotulo_desenho(no: dict) -> str:
    """O texto que vai DENTRO da caixa: pt-BR, curto, sem estourar a forma."""
    tipo = no["tipo"]
    if tipo == "gateway":
        return _curtinho(no.get("pergunta") or no["rotulo"], _TETO_CAIXA)
    if tipo == "gateway_paralelo":
        return "Em paralelo"
    if tipo == "fim_erro":
        return _curtinho("Erro: " + _so_o_nome(no["rotulo"]), _TETO_CAIXA)
    if tipo == "fim":
        if no["rotulo"] in ("fim", "fim do processo"):
            return "Fim do processo"
        return _curtinho("Retorna " + _so_o_nome(no["rotulo"]), _TETO_CAIXA)
    if tipo == "segue":
        return "Segue o fluxo"
    if tipo in ("inicio", "corte"):
        return _curtinho(no["rotulo"], _TETO_CAIXA)
    if not no["fn"]:                      # tarefa que nasceu de chamada a lib, não a função nossa
        if no["dados"]:
            return _verbo_sql(no["dados"][0])
        if no["mensagens"]:
            return _curtinho("Chama " + no["mensagens"][0], _TETO_CAIXA)
    return _curtinho(_frase(no["rotulo"]), _TETO_CAIXA - 2)


def rotulo_ramo(no: dict, indice: int) -> str:
    """No desenho o ramo é sim/não; a condição inteira fica no `bpmn.md`."""
    if no["tipo"] != "gateway":
        return ""
    return "sim" if indice == 0 else "não"



# --------------------------------------------- BPMN 2.0 XML (o que o bpmn-js e o Bizagi entendem)
#
# O gerador NAO calcula coordenadas: emite o XML semantico e o `bpmn-auto-layout` (do bpmn.io,
# vendorizado) posiciona no navegador. Desenhar layout a mao foi o erro da 0.24.x -- tira de
# 4.000 px, rotulo truncado, seta cruzando caixa.

_NS_BPMN = ('xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
            'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
            'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
            'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')

_TAG_BPMN = {"inicio": "startEvent", "fim": "endEvent", "fim_erro": "endEvent",
             "tarefa": "task", "subprocesso": "subProcess", "corte": "task",
             "gateway": "exclusiveGateway", "gateway_paralelo": "parallelGateway"}


def _atr(texto) -> str:
    return _html.escape(str(texto), quote=True)


def _slug(texto: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", " ".join(str(texto).split())).strip("-").lower()
    return (s or "processo")[:60]


def grafo(nos_raiz: list) -> tuple[dict, list]:
    """Topologia (nós + arestas) do fluxo. Reusa o percurso do posicionador, ignora coordenada.

    Contrai o placeholder `segue`: em BPMN o ramo do guarda liga direto no próximo elemento,
    não numa caixa "segue o fluxo".
    """
    caixas, setas, _ = _posicionar(nos_raiz)
    nos = {c["id"]: c["no"] for c in caixas}
    arestas = [(s["de"], s["para"], s["rotulo"]) for s in setas]
    for cid, no in list(nos.items()):
        if no["tipo"] != "segue":
            continue
        entram = [(a, b, r) for a, b, r in arestas if b == cid]
        saem = [(a, b, r) for a, b, r in arestas if a == cid]
        arestas = [e for e in arestas if e[0] != cid and e[1] != cid]
        for de, _b, rot in entram:
            for _a2, para, _r in saem:
                arestas.append((de, para, rot))
        nos.pop(cid)
    return nos, arestas


def _rotulo_da_aresta(nos: dict, de: int, rotulo_cru: str) -> str:
    """O ramo do gateway vira sim/não; fluxo comum não leva rótulo."""
    pai = nos.get(de)
    if not pai or pai["tipo"] != "gateway" or not rotulo_cru:
        return ""
    ramos = pai.get("ramos") or []
    for i, r in enumerate(ramos):
        if r["rotulo"] == rotulo_cru:
            return rotulo_ramo(pai, i)
    return rotulo_ramo(pai, 0)


def diagramas(processo: dict) -> list[dict]:
    """Os NÍVEIS do processo: a rota (subprocessos colapsados) + um por subprocesso expandido.

    Drill-down com menos de 2 elementos não vira diagrama — saía um círculo solto na tela.
    """
    saida = []
    for nome, arquivo, nos in [(processo["nome"], processo["arquivo"], processo["nos"])] + [
            (rotulo_desenho(n), n["arquivo"], n["filhos"])
            for n in achatar(processo["nos"]) if n["filhos"]]:
        pontos, arestas = grafo(nos)
        if not pontos or (saida and len(pontos) < 2):
            continue
        saida.append({"nome": nome, "arquivo": arquivo, "nos": nos, "elementos": len(pontos),
                      "fluxos": len([1 for a, b, _r in arestas if a in pontos and b in pontos]),
                      "slug": _slug(nome) if not saida else f"{len(saida)}-{_slug(nome)}"})
    return saida


def render_bpmn(diagrama: dict) -> str:
    """XML BPMN 2.0 de UM diagrama — semântico, sem coordenadas (quem posiciona é o auto-layout)."""
    nos, arestas = grafo(diagrama["nos"])
    validas = [(i, de, para, rot) for i, (de, para, rot) in enumerate(arestas)
               if de in nos and para in nos]
    # o auto-layout monta o grafo pelos <incoming>/<outgoing> do NÓ: sem eles, o DI sai com
    # shapes e ZERO edges e as setas não aparecem (achado no spike).
    entra: dict = {}
    sai: dict = {}
    for i, de, para, _r in validas:
        sai.setdefault(de, []).append(f"f{i}")
        entra.setdefault(para, []).append(f"f{i}")

    corpo = []
    for cid, no in nos.items():
        eid = f"n{cid}"
        nome = _atr(rotulo_desenho(no))
        liga = "".join(f"<bpmn:incoming>{x}</bpmn:incoming>" for x in entra.get(cid, [])) + \
               "".join(f"<bpmn:outgoing>{x}</bpmn:outgoing>" for x in sai.get(cid, []))
        if no["tipo"] == "fim_erro":
            corpo.append(f'    <bpmn:endEvent id="{eid}" name="{nome}">{liga}'
                         f'<bpmn:errorEventDefinition id="{eid}_d"/></bpmn:endEvent>')
        else:
            tag = _TAG_BPMN[no["tipo"]]
            if tag == "subProcess" and len(grafo(no["filhos"])[0]) < 2:
                tag = "task"          # o "+" prometia drill-down que não existe
            corpo.append(f'    <bpmn:{tag} id="{eid}" name="{nome}">{liga}</bpmn:{tag}>')
        if no["borda"] and no["tipo"] in ("tarefa", "subprocesso"):
            bid = f"{eid}_b"
            # só a exceção: `mssc_service.ValidacaoError` estourava a marca do evento
            primeira = _so_o_nome(no["borda"]).split(" ")[0].split("·")[0].strip()
            erro = _atr(_curtinho(primeira.split(".")[-1], 24))
            corpo.append(f'    <bpmn:boundaryEvent id="{bid}" name="{erro}" '
                         f'attachedToRef="{eid}">'
                         f'<bpmn:errorEventDefinition id="{bid}_d"/></bpmn:boundaryEvent>')
    for i, de, para, rot in validas:
        rotulo = _rotulo_da_aresta(nos, de, rot)
        atr = f' name="{_atr(rotulo)}"' if rotulo else ""
        corpo.append(f'    <bpmn:sequenceFlow id="f{i}"{atr} sourceRef="n{de}" '
                     f'targetRef="n{para}"/>')

    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<bpmn:definitions {_NS_BPMN} id="Definitions_1" '
            'targetNamespace="http://bpmn.io/schema/bpmn">\n'
            f'  <bpmn:process id="Process_1" isExecutable="false" '
            f'name="{_atr(diagrama["nome"])}">\n'
            + "\n".join(corpo) + "\n  </bpmn:process>\n</bpmn:definitions>\n")


# ------------------------------------------------------------ render de TEXTO (o assistente lê esta)

# nome do elemento + o número do infográfico do Bizagi que o owner usou como modelo de notação
ELEMENTOS = {
    "inicio": ("início", 1),
    "fim": ("fim", 3),
    "fim_erro": ("fim de erro", 3),
    "tarefa": ("tarefa", 4),
    "subprocesso": ("subprocesso", 5),
    "gateway": ("gateway exclusivo", 6),
    "gateway_paralelo": ("gateway paralelo", 7),
    "segue": ("segue o fluxo", 10),
    "corte": ("corte", 0),
}


def _nome_elemento(tipo: str) -> str:
    nome, num = ELEMENTOS.get(tipo, (tipo, 0))
    return f"{nome} ({num})" if num else nome


def _detalhes(n: dict) -> str:
    partes = []
    if n["raia"] and n["tipo"] not in ("corte", "segue"):
        partes.append(f"raia `{n['raia']}`")
    for d in n["dados"]:
        partes.append(f"armazenamento de dados (16): `{d}`")
    for msg in n["mensagens"]:
        partes.append(f"fluxo de mensagem (11) → piscina `{msg}`")
    if n["borda"]:
        partes.append(f"evento de borda (19): {n['borda']}")
    if n["reuso"]:
        partes.append("chamada de atividade (20) — usada por 2+ fluxos")
    return " · ".join(partes)


def _passos(nos: list, nivel: int = 0) -> list[str]:
    linhas = []
    for i, n in enumerate(nos, 1):
        ind = "  " * nivel
        det = _detalhes(n)
        linhas.append(f"{ind}{i}. **{_nome_elemento(n['tipo'])}** {n['rotulo']}"
                      + (f" — {det}" if det else ""))
        if n["anotacao"]:
            primeira = n["anotacao"].split("\n")[0].strip()
            if primeira and primeira != n["rotulo"]:
                linhas.append(f"{ind}   > anotação (17): {_curto(primeira, 120)}")
        for r in n["ramos"]:
            linhas.append(f"{ind}   - ramo `{r['rotulo']}`:")
            linhas.extend(_passos(r["nos"], nivel + 2))
        if n["filhos"]:
            linhas.append(f"{ind}   - expansão do subprocesso:")
            linhas.extend(_passos(n["filhos"], nivel + 2))
    return linhas


def render_texto(modelo: dict) -> str:
    """Índice em texto dos processos — é o que o ASSISTENTE consulta (figura ele não lê)."""
    p_ = modelo["processos"]
    out = [
        f"# Processos de `{modelo['projeto']}` — desenho BPMN a partir do código",
        "",
        "<!-- GERADO por templates/bpmn.py (/mss-spec:bpmn). Saída derivada e regenerável, fora do",
        "     git. Leitura estática por `ast`: nada aqui é inferido além do que o código escreve. -->",
        "",
        f"{len(p_)} processo(s) · {modelo['arquivos_lidos']} arquivo(s) `.py` lido(s) · "
        f"profundidade {modelo['profundidade']} · teto de {modelo['limite']} nós por processo.",
        "",
    ]
    if modelo["piscinas"]:
        out += [f"**Piscinas externas (13)** detectadas no projeto: "
                + ", ".join(f"`{x}`" for x in modelo["piscinas"]), ""]

    if not p_:
        out += ["Nenhuma porta de entrada encontrada: o projeto não expõe rota Flask/FastAPI nem tem",
                "`main()` em arquivo da raiz. Aponte a função de entrada com `--entrada <nome>`.", ""]

    for pr in p_:
        out.append(f"## {pr['nome']}")
        meta = [f"`{pr['arquivo']}`", f"função `{pr['funcao']}`",
                "raias: " + ", ".join(f"`{r}`" for r in pr["raias"])]
        if pr["piscinas"]:
            meta.append("piscinas: " + ", ".join(f"`{x}`" for x in pr["piscinas"]))
        out += [" · ".join(meta), ""]
        if pr["anotacao"]:
            out += [f"> {_curto(pr['anotacao'].split(chr(10))[0], 160)}", ""]
        out += _passos(pr["nos"]) + [""]
        if pr["cortados"]:
            out += [f"*Processo cortado no teto: {pr['cortados']} nó(s) a mais não desenhados.*", ""]

    if modelo["nao_lidos"]:
        out += ["## Não lido", "",
                "Arquivo `.py` que não parseou. A geração segue (falha ABERTA) e declara o que ficou",
                "de fora — desenho que parece completo sem ser é pior que desenho com buraco visível.",
                ""]
        out += [f"- `{x['arquivo']}` — {x['erro']}" for x in modelo["nao_lidos"]] + [""]

    out += ["## O que não é derivável do código", "",
            "A leitura é estática. Estes elementos do BPMN **não** saem daqui e ficam declarados em",
            "vez de sumir em silêncio — se o processo precisa deles, é modelagem manual:", ""]
    out += [f"- **{nome}** — {porque}" for nome, porque in NAO_DERIVAVEIS]
    out += ["", "Também fora: rota montada dinamicamente (`add_url_rule`, prefixo de Blueprint "
            "resolvido no registro), framework fora de Flask/FastAPI, linguagem fora do Python.", ""]
    return "\n".join(out)


def _posicionar(nos: list):
    """Coloca cada nó numa (coluna, linha): coluna = ordem do fluxo, linha = ramo do gateway.

    Devolve (caixas, setas, colunas). A raia decide o Y final; a linha só desempata dentro dela.
    """
    caixas = []
    setas = []
    # a linha é alocada GLOBALMENTE por processo: `linha + i` fazia o ramo de um gateway aninhado
    # cair sobre a linha de um ramo irmão do gateway de fora — duas caixas empilhadas no SVG.
    estado = {"max": 0}

    def coloca(seq, col, linha, entradas):
        c = col
        estado["max"] = max(estado["max"], linha)
        for n in seq:
            cid = len(caixas)
            caixas.append({"id": cid, "no": n, "col": c, "linha": linha})
            for origem, rot in entradas:
                setas.append({"de": origem, "para": cid, "rotulo": rot})
            entradas = []
            if n["ramos"]:
                saidas, maior = [], c + 1
                for i, r in enumerate(n["ramos"]):
                    linha_ramo = linha if i == 0 else estado["max"] + 1
                    estado["max"] = max(estado["max"], linha_ramo)
                    cf, sai = coloca(r["nos"], c + 1, linha_ramo, [(cid, r["rotulo"])])
                    maior = max(maior, cf)
                    saidas.extend(sai)
                c = maior
                entradas = saidas
            elif n["tipo"] in ("fim", "fim_erro", "corte"):
                c += 1
            else:
                entradas = [(cid, "")]
                c += 1
        return c, entradas

    colunas, _ = coloca(nos, 0, 0, [])
    return caixas, setas, max(colunas, 1)

# ------------------------------- render do DESENHO (bpmn.io vendorizado — o humano olha este)
#
# Quem desenha NAO e este arquivo: e o `bpmn-js` (o motor do bpmn.io/Camunda) sobre coordenadas
# calculadas pelo `bpmn-auto-layout`, os dois vendorizados em templates/vendor/ igual ao
# vis-network do mapa-neural. A 0.24.x tentou layout SVG a mao e entregou tira de 4.000 px com
# rotulo truncado: layout de processo e problema resolvido, nao problema pra resolver aqui.

_VENDOR = Path(__file__).resolve().parent / "vendor"
_ATIVOS = ("bpmn-navigated-viewer.min.js", "bpmn-auto-layout.min.js", "bpmn-js.css")

# o auto-layout do bpmn.io declara o que NAO posiciona — vai escrito na pagina, nunca implicito
NAO_POSICIONADOS = [
    ("14. raia e 13. piscina", "o auto-layout posiciona só o primeiro participante e não desenha "
                               "raia; elas ficam no `bpmn.md` e na ficha de cada diagrama"),
    ("11. fluxo de mensagem", "a chamada a serviço externo (banco, Gemini, HTTP) aparece na ficha "
                              "do diagrama e no `bpmn.md`, não como seta"),
    ("17. anotação e 12. associação", "o docstring completo e o dado tocado ficam no `bpmn.md`"),
]


def _ativos_vendor() -> dict:
    """Lê as libs vendorizadas. Falta de arquivo é erro claro, não página quebrada em silêncio."""
    faltando = [n for n in _ATIVOS if not (_VENDOR / n).exists()]
    if faltando:
        raise FileNotFoundError(
            "faltam ativos vendorizados em templates/vendor/: " + ", ".join(faltando))
    return {n: (_VENDOR / n).read_text(encoding="utf-8") for n in _ATIVOS}


_CSS_PAGINA = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b2430;--mut:#5b6674;--line:#e3e7ec;--aviso:#f4d9a6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 "Segoe UI",system-ui,sans-serif;padding-bottom:40px}
header{background:var(--card);border-bottom:1px solid var(--line);padding:24px 4vw 18px}
h1{margin:0 0 4px;font-size:21px}
h1 small{color:var(--mut);font-weight:400;font-size:14px}
.sub{color:var(--mut);margin:6px 0 0;max-width:92ch;font-size:14px}
main{padding:0 4vw}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 4px}
nav a{font-size:13px;background:var(--card);color:var(--ink);border:1px solid var(--line);
border-radius:999px;padding:7px 14px;text-decoration:none}
nav a.filho{background:var(--bg);font-size:12.5px}
.diagrama{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:14px 16px 18px;margin:0 0 20px}
.diagrama h2{margin:0 0 2px;font-size:17px}
.meta{color:var(--mut);font-size:13px;margin:0 0 10px}
.meta code{background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:1px 5px}
.tela{height:58vh;border:1px solid var(--line);border-radius:10px;background:#fff;overflow:hidden}
.espera{padding:16px;color:var(--mut);font-size:13.5px;margin:0}
.espera.erro{color:#b91c1c}
.aviso{background:#fffaf0;border:1px solid var(--aviso);border-radius:12px;padding:14px 18px;
margin:16px 0;font-size:14px}
.aviso h3{margin:0 0 6px;font-size:15px} .aviso ul{margin:6px 0 0;padding-left:20px}
.fonte{color:var(--mut);font-size:12.5px;margin:24px 0 0;max-width:96ch}
"""

_JS_PAGINA = """
// o XML embutido vem SEM coordenadas: o auto-layout calcula aqui e o bpmn-js desenha.
document.querySelectorAll('.tela').forEach(function(el){
  var dados = document.getElementById('xml-' + el.getAttribute('data-slug'));
  if(!dados) return;
  BpmnAutoLayout.layoutProcess(dados.textContent).then(function(comDI){
    el.innerHTML = '';
    var visor = new BpmnJS({ container: el });
    return visor.importXML(comDI).then(function(){
      var tela = visor.get('canvas');
      tela.zoom('fit-viewport');
      // altura pelo CONTEUDO: moldura fixa deixava meia pagina em branco num diagrama de 4 caixas
      var vb = tela.viewbox();
      el.style.height = Math.min(Math.round(window.innerHeight * 0.74),
        Math.max(240, Math.round(vb.inner.height * vb.scale) + 90)) + 'px';
      tela.resized();
      tela.zoom('fit-viewport');
    });
  }).catch(function(e){
    el.innerHTML = '<p class="espera erro">Nao foi possivel montar este desenho (' +
      (e && e.message ? e.message : e) + '). Use o arquivo .bpmn ao lado (abre no Bizagi) ' +
      'ou o bpmn.md.</p>';
  });
});
"""


def render_html(modelo: dict, gerado_em: str = "") -> str:
    """Página self-contained: XML embutido + auto-layout + bpmn-js, tudo vendorizado (zero CDN)."""
    ativos = _ativos_vendor()
    abas, secoes, total = [], [], 0

    for proc in modelo["processos"]:
        for k, d in enumerate(diagramas(proc)):
            total += 1
            if not k:      # índice com 36 pílulas comia a 1ª tela antes de qualquer desenho
                abas.append('<a href="#%s">%s</a>' % (d["slug"], _atr(d["nome"])))
            ficha = [f'<code>{_atr(d["arquivo"])}</code>',
                     f'{d["elementos"]} elementos', f'{d["fluxos"]} fluxos']
            if not k:
                if proc["raias"]:
                    ficha.append("raias: " + ", ".join(f"<code>{_atr(r)}</code>"
                                                       for r in proc["raias"]))
                if proc["piscinas"]:
                    ficha.append("fala com: " + ", ".join(f"<code>{_atr(x)}</code>"
                                                          for x in proc["piscinas"]))
                if proc["cortados"]:
                    ficha.append(f'<b>cortado no teto: +{proc["cortados"]}</b>')
            xml = render_bpmn(d).replace("</script", "<\\/script")
            secoes.append(
                '<section class="diagrama" id="%s"><h2>%s</h2><p class="meta">%s</p>'
                '<div class="tela" data-slug="%s"><p class="espera">Montando o desenho… se este '
                'texto ficar, o visualizador não rodou: abra o <code>.bpmn</code> ao lado no '
                'Bizagi, ou leia o <code>bpmn.md</code>.</p></div>'
                '<script type="application/xml" id="xml-%s">%s</script></section>'
                % (d["slug"], _atr(d["nome"]), " · ".join(ficha), d["slug"], d["slug"], xml))

    avisos = ['<div class="aviso"><h3>O que este desenho não mostra</h3>'
              '<p>Dois tipos de buraco, os dois declarados — desenho que parece completo sem ser '
              'é pior que buraco visível.</p><p><b>Não derivável do código</b> (leitura estática):'
              '</p><ul>']
    for nome, porque in NAO_DERIVAVEIS:
        avisos.append(f"<li><b>{_atr(nome)}</b> — {_atr(porque)}</li>")
    avisos.append("</ul><p><b>Não posicionado pelo auto-layout do bpmn.io</b> "
                  "(limitação declarada pela própria lib):</p><ul>")
    for nome, porque in NAO_POSICIONADOS:
        avisos.append(f"<li><b>{_atr(nome)}</b> — {porque}</li>")
    avisos.append("</ul>")
    if modelo["nao_lidos"]:
        avisos.append("<p><b>Não lido</b> (a geração seguiu, falha aberta):</p><ul>")
        for x in modelo["nao_lidos"]:
            avisos.append(f'<li><code>{_atr(x["arquivo"])}</code> — {_atr(x["erro"])}</li>')
        avisos.append("</ul>")
    avisos.append("</div>")

    quando = (" · gerado em " + _atr(gerado_em)) if gerado_em else ""
    return (
        '<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>Processos em BPMN — {_atr(modelo["projeto"])}</title>\n'
        f'<style>{ativos["bpmn-js.css"]}</style>\n<style>{_CSS_PAGINA}</style>\n'
        "</head>\n<body>\n<header>\n"
        f'  <h1>Processos em BPMN — {_atr(modelo["projeto"])} <small>'
        f'{len(modelo["processos"])} porta(s) de entrada · {total} diagrama(s) · '
        f'{modelo["arquivos_lidos"]} arquivo(s) .py lidos{quando}</small></h1>\n'
        '  <p class="sub">Lido do <b>código</b> por <code>ast</code> e desenhado pelo '
        '<b>bpmn-js</b> sobre coordenadas do <b>bpmn-auto-layout</b> (bpmn.io, embutidos aqui — '
        'zero CDN). Um diagrama por porta de entrada, mais um por subprocesso: clique no índice. '
        'Arraste para mover, scroll para zoom. Nenhuma caixa foi inventada. Este desenho é '
        '<b>pro humano</b>; o assistente lê o <code>bpmn.md</code> gerado ao lado, e os '
        '<code>.bpmn</code> abrem no Bizagi.</p>\n</header>\n'
        '<noscript><p class="aviso">Esta página monta os desenhos por script. Sem JavaScript '
        'ficam só as fichas — abra os arquivos <code>.bpmn</code> no Bizagi ou leia o '
        '<code>bpmn.md</code>.</p></noscript>\n<main>\n'
        f'<nav>{"".join(abas)}</nav>\n{"".join(secoes)}\n{"".join(avisos)}\n'
        '<p class="fonte">Gerado por <code>templates/bpmn.py</code> '
        '(<code>/mss-spec:bpmn</code>): decorators de rota, chamadas a funções do próprio projeto, '
        '<code>if/else</code>, <code>try/except</code>, banco e serviço externo. Desenho por '
        'bpmn-js + bpmn-auto-layout (bpmn.io), vendorizados em <code>templates/vendor/</code>. '
        'Saída derivada e regenerável: fora do git de propósito.</p>\n'
        f'</main>\n<script>{ativos["bpmn-navigated-viewer.min.js"]}</script>\n'
        f'<script>{ativos["bpmn-auto-layout.min.js"]}</script>\n'
        f'<script>{_JS_PAGINA}</script>\n</body>\n</html>\n'
    )


# ------------------------------------------------------------------------------------------- CLI

def _gerar(proj_dir=None, out_dir=None, profundidade: int = _PROFUNDIDADE,
           limite: int = _LIMITE_NOS, ignorar=(), entradas_extra=()):
    """Como `gerar`, mas devolve também o modelo — o CLI reporta sem reler o projeto inteiro."""
    from datetime import datetime
    proj = (Path(proj_dir) if proj_dir else Path.cwd()).resolve()
    out = Path(out_dir) if out_dir else proj / "docs"
    out.mkdir(parents=True, exist_ok=True)

    modelo = extrair(proj, profundidade=profundidade, limite=limite, ignorar=ignorar,
                     entradas_extra=entradas_extra)
    md = out / "bpmn.md"
    html = out / "bpmn.html"

    # um .bpmn por diagrama: é o arquivo que abre no Bizagi, onde raia e piscina ganham a
    # posição que o auto-layout do bpmn.io não dá.
    pasta = out / "bpmn"
    pasta.mkdir(parents=True, exist_ok=True)
    for antigo in pasta.glob("*.bpmn"):
        antigo.unlink()
    for proc in modelo["processos"]:
        for d in diagramas(proc):
            (pasta / f"{d['slug']}.bpmn").write_text(render_bpmn(d), encoding="utf-8",
                                                     newline="\n")

    md.write_text(render_texto(modelo), encoding="utf-8", newline="\n")
    html.write_text(render_html(modelo, datetime.now().strftime("%Y-%m-%d %H:%M")),
                    encoding="utf-8", newline="\n")
    return md, html, modelo


def gerar(proj_dir=None, out_dir=None, profundidade: int = _PROFUNDIDADE,
          limite: int = _LIMITE_NOS, ignorar=(), entradas_extra=()):
    """Escreve as DUAS saídas: bpmn.md (texto, o assistente lê) e bpmn.html (desenho, o humano vê)."""
    md, html, _ = _gerar(proj_dir, out_dir, profundidade, limite, ignorar, entradas_extra)
    return md, html


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Desenha os processos do projeto em BPMN a partir do código (estático, por ast).")
    ap.add_argument("--proj", default=None, help="raiz do projeto (default: diretório atual)")
    ap.add_argument("--out", default=None, help="pasta de saída (default: <proj>/docs)")
    ap.add_argument("--profundidade", type=int, default=_PROFUNDIDADE,
                    help="níveis de subprocesso expandidos (default %d)" % _PROFUNDIDADE)
    ap.add_argument("--limite", type=int, default=_LIMITE_NOS,
                    help="teto de nós por processo (default %d)" % _LIMITE_NOS)
    ap.add_argument("--ignorar", default="", help="pastas a ignorar, separadas por vírgula")
    ap.add_argument("--entrada", action="append", default=[],
                    help="nome de função a tratar como porta de entrada (repetível)")
    a = ap.parse_args(argv)

    md, html, modelo = _gerar(a.proj, a.out, a.profundidade, a.limite,
                              [x for x in a.ignorar.split(",") if x.strip()], a.entrada)
    print("texto:   %s" % md.resolve())
    print("desenho: %s" % html.resolve())
    print("%d processo(s) desenhado(s) · %d arquivo(s) .py lido(s) · %d não lido(s)."
          % (len(modelo["processos"]), modelo["arquivos_lidos"], len(modelo["nao_lidos"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
