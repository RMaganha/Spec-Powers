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
_HTTP_LIBS = frozenset({"requests", "httpx", "aiohttp", "urllib", "urllib3", "openai", "anthropic"})
_HTTP_METODOS = frozenset({"get", "post", "put", "delete", "patch", "request", "send"})

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

    return {"por_nome": defs, "por_arquivo": por_arquivo, "todas": todas,
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

def _perfil(fdef) -> dict:
    """O que o corpo da função faz, sem descer em outras funções do projeto.

    Serve pra dois fins: anexar banco/mensagem/borda à TAREFA que chama a função (é ela que toca o
    dado, na leitura BPMN) e decidir se a função é tarefa simples ou subprocesso.
    """
    dados, msgs, bordas = [], [], []
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
            h = _e_http(no)
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
        perfil = _perfil(d["no"])
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
            alvo = _fonte(stmt.value) or "fim"
            return [_no("fim", alvo, raia=dono["raia"], arquivo=dono["arquivo"])]

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
            h = _e_http(c)
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
        for stmt in corpo:
            for c in _calls(stmt):
                raiz, attr = _nome_chamado(c)
                d, h = _e_banco(c), _e_http(c)
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
                    arquivo=dono["arquivo"], ramos=ramos, borda=borda)]

    @staticmethod
    def _pergunta(teste, cond: str) -> str:
        """A pergunta do losango: o sujeito da decisão (os ramos carregam a condição inteira)."""
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

    piscinas = list(dict.fromkeys(x for p in processos for x in p["piscinas"]))
    return {
        "projeto": proj.name, "processos": processos, "nao_lidos": nao_lidos,
        "piscinas": piscinas, "profundidade": profundidade, "limite": limite,
        "arquivos_lidos": indice["arquivos"],
    }


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


# --------------------------------------------------------------- render do DESENHO (o humano olha)

_W, _H = 178, 62          # tarefa / subprocesso
_GWL = 48                 # lado do losango do gateway
_EV = 19                  # raio do evento (início/fim)
_COL = 236                # passo horizontal de uma coluna
_ROW = 104                # altura de uma linha dentro da raia
_LBL = 132                # faixa do rótulo da raia
_PAD = 28
_PISCINA_H = 118

LEGENDA = [
    ("inicio", "1 · evento de início", "onde o processo começa (rota ou main)"),
    ("fim", "3 · evento de fim", "return — onde o processo termina"),
    ("fim_erro", "3 · fim de erro", "raise — termina em exceção"),
    ("tarefa", "4 · tarefa", "chamada a uma função do projeto"),
    ("subprocesso", "5 · subprocesso", "a função tem decisão/chamadas por dentro (+)"),
    ("gateway", "6 · gateway exclusivo", "if/elif/else — escolhe um caminho"),
    ("gateway_paralelo", "7 · gateway paralelo", "asyncio.gather / pool de threads"),
    ("dados", "16 · armazenamento de dados", "cursor.execute, SQLAlchemy, pyodbc"),
    ("borda", "19 · evento de borda", "try/except em volta da tarefa"),
    ("msg", "11 · fluxo de mensagem", "requests/httpx para piscina externa (13)"),
    ("reuso", "20 · chamada de atividade", "a mesma função usada por 2+ fluxos"),
]

_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b2430;--mut:#5b6674;--line:#e3e7ec;
--inicio:#0e9f6e;--fim:#1b2430;--erro:#b91c1c;--tarefa:#2563eb;--tarefa-bg:#f4f8ff;
--sub:#7c3aed;--sub-bg:#f7f2ff;--gw:#d97706;--gw-bg:#fffaf0;--dados:#0f766e;--msg:#0369a1;
--raia:#eef1f5;--piscina:#fdf4ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 "Segoe UI",system-ui,sans-serif;padding-bottom:50px}
header{background:var(--card);border-bottom:1px solid var(--line);padding:24px 4vw 18px}
h1{margin:0 0 4px;font-size:22px}
h1 small{color:var(--mut);font-weight:400;font-size:14px}
.sub{color:var(--mut);margin:6px 0 0;max-width:88ch;font-size:14px}
main{padding:0 4vw}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 6px}
nav button{font:inherit;font-size:13px;cursor:pointer;background:var(--card);color:var(--ink);
border:1px solid var(--line);border-radius:999px;padding:7px 14px}
nav button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.processo{display:none;background:var(--card);border:1px solid var(--line);
border-radius:12px;padding:16px 18px 20px;margin:10px 0 22px}
.processo.on{display:block}
.processo h2{margin:0 0 2px;font-size:18px}
.meta{color:var(--mut);font-size:13px;margin:0 0 12px}
.meta code{background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:1px 5px}
.tela{overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fcfdfe;
cursor:grab;max-height:78vh}
.tela.pegando{cursor:grabbing}
.zoom{display:flex;gap:6px;justify-content:flex-end;margin:8px 0 0}
.zoom button{font:inherit;font-size:12px;cursor:pointer;background:var(--card);
border:1px solid var(--line);border-radius:6px;padding:4px 10px}
.expansao{margin:18px 0 0;font-size:14px;color:var(--mut)}
.legenda{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:8px 18px;
background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
.legenda h3{grid-column:1/-1;margin:0 0 2px;font-size:15px}
.lg{display:flex;gap:9px;align-items:flex-start;font-size:13px}
.lg b{font-weight:600}.lg span{color:var(--mut)}
.lg i{flex:0 0 22px;height:22px;display:inline-block;margin-top:1px}
.aviso{background:#fffaf0;border:1px solid #f4d9a6;border-radius:12px;padding:14px 18px;
margin:16px 0;font-size:14px}
.aviso h3{margin:0 0 6px;font-size:15px}
.aviso ul{margin:6px 0 0;padding-left:20px}
.fonte{color:var(--mut);font-size:12.5px;margin:26px 0 0;max-width:96ch}
text{font:12px "Segoe UI",system-ui,sans-serif;fill:var(--ink)}
.rotulo-raia{font-size:12px;font-weight:600;fill:var(--mut);letter-spacing:.02em}
.faixa{fill:var(--raia)}.faixa-alt{fill:#f8fafc}
.e-tarefa rect{fill:var(--tarefa-bg);stroke:var(--tarefa);stroke-width:1.6}
.e-subprocesso rect{fill:var(--sub-bg);stroke:var(--sub);stroke-width:1.6}
.e-inicio circle{fill:#fff;stroke:var(--inicio);stroke-width:2}
.e-fim circle{fill:#fff;stroke:var(--fim);stroke-width:4}
.e-fim_erro circle{fill:#fff;stroke:var(--erro);stroke-width:4}
.e-gateway polygon,.e-gateway_paralelo polygon{fill:var(--gw-bg);stroke:var(--gw);stroke-width:1.6}
.e-corte rect{fill:none;stroke:var(--mut);stroke-width:1.4;stroke-dasharray:5 4}
.e-segue rect{fill:none;stroke:var(--line);stroke-width:1.4}
.e-dados path,.e-dados ellipse{fill:#effaf8;stroke:var(--dados);stroke-width:1.4}
.e-borda circle{fill:#fff;stroke:var(--gw);stroke-width:1.6}
.seta{fill:none;stroke:#8a95a3;stroke-width:1.5}
.msg{fill:none;stroke:var(--msg);stroke-width:1.4;stroke-dasharray:7 5}
.assoc{fill:none;stroke:var(--dados);stroke-width:1.2;stroke-dasharray:2 3}
.rot-seta{font-size:11px;fill:var(--mut)}
.caixa-piscina{fill:var(--piscina);stroke:#c084fc;stroke-width:1.4}
"""

_JS = """
function mostra(i){
  var secs=document.querySelectorAll('.processo'), bts=document.querySelectorAll('nav button');
  for(var k=0;k<secs.length;k++) secs[k].className='processo'+(k===i?' on':'');
  for(var k=0;k<bts.length;k++) bts[k].className=(k===i?'on':'');
}
document.addEventListener('click',function(ev){
  var b=ev.target.closest('nav button');
  if(b) mostra(parseInt(b.getAttribute('data-alvo'),10));
  var z=ev.target.closest('.zoom button');
  if(z){
    var tela=document.getElementById(z.getAttribute('data-tela'));
    var svg=tela.querySelector('svg');
    var atual=parseFloat(svg.getAttribute('data-escala')||'1');
    var passo=z.getAttribute('data-passo');
    var nova=passo==='0'?1:Math.min(2.2,Math.max(0.35,atual+parseFloat(passo)));
    svg.setAttribute('data-escala',nova);
    svg.style.width=(parseFloat(svg.getAttribute('data-w'))*nova)+'px';
    svg.style.height=(parseFloat(svg.getAttribute('data-h'))*nova)+'px';
  }
});
var telas=document.querySelectorAll('.tela');
for(var i=0;i<telas.length;i++){
  (function(el){
    var arrastando=false,x0=0,y0=0,l0=0,t0=0;
    el.addEventListener('mousedown',function(e){
      arrastando=true;x0=e.clientX;y0=e.clientY;l0=el.scrollLeft;t0=el.scrollTop;
      el.className='tela pegando';e.preventDefault();
    });
    window.addEventListener('mouseup',function(){arrastando=false;el.className='tela';});
    el.addEventListener('mousemove',function(e){
      if(!arrastando) return;
      el.scrollLeft=l0-(e.clientX-x0);el.scrollTop=t0-(e.clientY-y0);
    });
  })(telas[i]);
}
mostra(0);
"""


def _esc(t) -> str:
    return _html.escape(str(t), quote=True)


def _quebrar(t: str, largura: int = 24, maximo: int = 3) -> list:
    palavras = str(t).split()
    linhas, atual = [], ""
    for p in palavras:
        if atual and len(atual) + 1 + len(p) > largura:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
        if len(linhas) == maximo:
            break
    if atual and len(linhas) < maximo:
        linhas.append(atual)
    if not linhas:
        return [""]
    resto = len(palavras) - sum(len(x.split()) for x in linhas)
    if resto > 0:
        linhas[-1] = _curto(linhas[-1], largura - 1) + "…"
    return linhas


def _largura(tipo: str) -> int:
    if tipo in ("inicio", "fim", "fim_erro"):
        return _EV * 2
    if tipo in ("gateway", "gateway_paralelo"):
        return _GWL
    if tipo == "segue":
        return 96
    return _W


def _altura(tipo: str) -> int:
    if tipo in ("inicio", "fim", "fim_erro"):
        return _EV * 2
    if tipo in ("gateway", "gateway_paralelo"):
        return _GWL
    if tipo == "segue":
        return 30
    return _H


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


def _forma(n: dict, x: float, y: float) -> str:
    """SVG de um elemento, centrado em (x, y). Só formas — o BPMN do print, sem biblioteca."""
    tipo = n["tipo"]
    g = ['<g class="e-' + tipo + '">', "<title>" + _esc(n["anotacao"] or n["rotulo"]) + "</title>"]

    if tipo in ("inicio", "fim", "fim_erro"):
        g.append('<circle cx="%s" cy="%s" r="%s"/>' % (x, y, _EV))
        if tipo == "fim_erro":
            g.append('<path d="M%s %s L%s %s L%s %s L%s %s" fill="none" stroke="var(--erro)" '
                     'stroke-width="1.8"/>' % (x - 7, y + 5, x - 1, y - 5, x + 1, y + 2,
                                               x + 7, y - 6))
        for i, linha in enumerate(_quebrar(n["rotulo"], 26, 2)):
            g.append('<text x="%s" y="%s" text-anchor="middle">%s</text>'
                     % (x, y + _EV + 15 + i * 14, _esc(linha)))

    elif tipo in ("gateway", "gateway_paralelo"):
        m = _GWL / 2
        g.append('<polygon points="%s,%s %s,%s %s,%s %s,%s"/>'
                 % (x, y - m, x + m, y, x, y + m, x - m, y))
        marca = "+" if tipo == "gateway_paralelo" else "×"
        g.append('<text x="%s" y="%s" text-anchor="middle" font-size="17" fill="var(--gw)">%s</text>'
                 % (x, y + 5, marca))
        for i, linha in enumerate(_quebrar(n["rotulo"], 24, 2)):
            g.append('<text x="%s" y="%s" text-anchor="middle">%s</text>'
                     % (x, y + m + 15 + i * 14, _esc(linha)))

    elif tipo == "segue":
        w, h = _largura(tipo), _altura(tipo)
        g.append('<rect x="%s" y="%s" width="%s" height="%s" rx="6"/>'
                 % (x - w / 2, y - h / 2, w, h))
        g.append('<text x="%s" y="%s" text-anchor="middle" fill="var(--mut)">%s</text>'
                 % (x, y + 4, _esc(n["rotulo"])))

    else:                                   # tarefa · subprocesso · corte
        w, h = _largura(tipo), _altura(tipo)
        x0, y0 = x - w / 2, y - h / 2
        g.append('<rect x="%s" y="%s" width="%s" height="%s" rx="9"/>' % (x0, y0, w, h))
        linhas = _quebrar(n["rotulo"], 25, 3)
        base = y - (len(linhas) - 1) * 7 + 4
        for i, linha in enumerate(linhas):
            g.append('<text x="%s" y="%s" text-anchor="middle">%s</text>'
                     % (x, base + i * 14, _esc(linha)))
        if tipo == "subprocesso":           # marca do subprocesso colapsado (o "+" do elemento 5)
            g.append('<rect x="%s" y="%s" width="14" height="14" rx="2" fill="#fff" '
                     'stroke="var(--sub)" stroke-width="1.2"/>' % (x - 7, y0 + h - 15))
            g.append('<text x="%s" y="%s" text-anchor="middle" font-size="12" '
                     'fill="var(--sub)">+</text>' % (x, y0 + h - 4))
        if n["reuso"]:                      # elemento 20 — chamada de atividade
            g.append('<rect x="%s" y="%s" width="16" height="12" rx="2" fill="#fff" '
                     'stroke="var(--tarefa)" stroke-width="1.2"/>' % (x0 + 6, y0 + h - 15))
            g.append('<path d="M%s %s v8 M%s %s v8" stroke="var(--tarefa)" stroke-width="1.2"/>'
                     % (x0 + 11, y0 + h - 13, x0 + 17, y0 + h - 13))
        if n["borda"]:                      # elemento 19 — evento de borda na quina da tarefa
            g.append('<g class="e-borda"><title>%s</title>'
                     '<circle cx="%s" cy="%s" r="9"/><circle cx="%s" cy="%s" r="6"/></g>'
                     % (_esc(n["borda"]), x0 + w, y0 + h, x0 + w, y0 + h))
            g.append('<text x="%s" y="%s" font-size="11" fill="var(--gw)">%s</text>'
                     % (x0 + w + 12, y0 + h + 15, _esc(_curto(n["borda"], 26))))
        if n["dados"]:                      # elemento 16 — armazenamento + associação (12)
            dx, dy = x0 + w - 26, y0 - 34
            g.append('<g class="e-dados"><title>%s</title>'
                     '<path d="M%s %s v16 a11 5 0 0 0 22 0 v-16"/>'
                     '<ellipse cx="%s" cy="%s" rx="11" ry="5"/></g>'
                     % (_esc(" · ".join(n["dados"])), dx, dy + 6, dx + 11, dy + 6))
            g.append('<path class="assoc" d="M%s %s V%s"/>' % (dx + 11, dy + 28, y0))
            g.append('<text x="%s" y="%s" font-size="11" fill="var(--dados)">%s</text>'
                     % (dx + 26, dy + 16, _esc(_curto(n["dados"][0], 24))))
    g.append("</g>")
    return "".join(g)


def _seta(x1, y1, x2, y2, rotulo="", classe="seta") -> str:
    if abs(y1 - y2) < 1:
        d = "M%s %s H%s" % (x1, y1, x2)
        rx, ry = (x1 + x2) / 2, y1 - 6
    else:
        mx = (x1 + x2) / 2
        d = "M%s %s H%s V%s H%s" % (x1, y1, mx, y2, x2)
        rx, ry = mx + 6, (y1 + y2) / 2
    s = ['<path class="%s" d="%s" marker-end="url(#ponta)"/>' % (classe, d)]
    if rotulo:
        for i, linha in enumerate(_quebrar(rotulo, 22, 2)):
            s.append('<text class="rot-seta" x="%s" y="%s">%s</text>' % (rx, ry + i * 12,
                                                                        _esc(linha)))
    return "".join(s)


def _svg(nos: list, piscinas: list) -> str:
    caixas, setas, colunas = _posicionar(nos)
    if not caixas:
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="420" height="60" data-w="420" '
                'data-h="60" data-escala="1"><text x="16" y="34">processo sem nós desenháveis'
                '</text></svg>')

    # raias (elemento 14): ordem de aparição; cada raia compacta suas próprias linhas
    ordem, linhas_por_raia = [], {}
    for c in caixas:
        raia = c["no"]["raia"] or "raiz"
        if raia not in ordem:
            ordem.append(raia)
            linhas_por_raia[raia] = []
        if c["linha"] not in linhas_por_raia[raia]:
            linhas_por_raia[raia].append(c["linha"])
    topo, altura_raia = {}, {}
    y = _PAD
    for raia in ordem:
        linhas_por_raia[raia].sort()
        h = max(1, len(linhas_por_raia[raia])) * _ROW
        topo[raia], altura_raia[raia] = y, h
        y += h
    fim_raias = y
    largura = _LBL + _PAD + colunas * _COL + _PAD
    altura = fim_raias + (_PISCINA_H if piscinas else 0) + _PAD

    def centro(c):
        raia = c["no"]["raia"] or "raiz"
        local = linhas_por_raia[raia].index(c["linha"])
        return (_LBL + _PAD + c["col"] * _COL + _COL / 2,
                topo[raia] + local * _ROW + _ROW / 2)

    partes = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s" '
        'data-w="%s" data-h="%s" data-escala="1">' % (largura, altura, largura, altura,
                                                      largura, altura),
        '<defs><marker id="ponta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0 L10 5 L0 10 z" fill="#8a95a3"/></marker></defs>',
        # piscina do sistema (elemento 13), com as raias dentro
        '<rect x="%s" y="%s" width="%s" height="%s" rx="6" fill="none" stroke="#cfd6de"/>'
        % (_PAD / 2, _PAD / 2, largura - _PAD, fim_raias - _PAD / 2 + 6),
    ]
    for i, raia in enumerate(ordem):
        partes.append('<rect class="%s" x="%s" y="%s" width="%s" height="%s" opacity=".55"/>'
                      % ("faixa" if i % 2 == 0 else "faixa-alt", _PAD / 2, topo[raia],
                         largura - _PAD, altura_raia[raia]))
        partes.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#dde3ea"/>'
                      % (_PAD / 2 + _LBL, topo[raia], largura - _PAD / 2, topo[raia]))
        partes.append('<text class="rotulo-raia" transform="translate(%s,%s) rotate(-90)" '
                      'text-anchor="middle">raia %s</text>'
                      % (_PAD / 2 + 20, topo[raia] + altura_raia[raia] / 2, _esc(raia)))

    for s in setas:
        de, para = caixas[s["de"]], caixas[s["para"]]
        x1, y1 = centro(de)
        x2, y2 = centro(para)
        partes.append(_seta(x1 + _largura(de["no"]["tipo"]) / 2, y1,
                            x2 - _largura(para["no"]["tipo"]) / 2, y2, s["rotulo"]))

    for c in caixas:
        x, yy = centro(c)
        partes.append(_forma(c["no"], x, yy))

    if piscinas:                            # piscina externa (13) + fluxo de mensagem (11)
        py = fim_raias + 26
        partes.append('<rect x="%s" y="%s" width="%s" height="72" rx="6" fill="none" '
                      'stroke="#c084fc" stroke-dasharray="4 3"/>' % (_PAD / 2, py, largura - _PAD))
        partes.append('<text class="rotulo-raia" transform="translate(%s,%s) rotate(-90)" '
                      'text-anchor="middle">piscinas externas</text>' % (_PAD / 2 + 20, py + 36))
        pos = {}
        for i, nome in enumerate(piscinas):
            cx = _LBL + _PAD + i * (_W + 40) + _W / 2
            pos[nome] = (cx, py + 36)
            partes.append('<g class="e-piscina"><rect class="caixa-piscina" x="%s" y="%s" '
                          'width="%s" height="52" rx="9"/>' % (cx - _W / 2, py + 10, _W))
            for k, linha in enumerate(_quebrar(nome, 24, 2)):
                partes.append('<text x="%s" y="%s" text-anchor="middle">%s</text>'
                              % (cx, py + 34 + k * 14, _esc(linha)))
            partes.append("</g>")
        for c in caixas:
            for nome in c["no"]["mensagens"]:
                if nome in pos:
                    x, yy = centro(c)
                    partes.append(_seta(x, yy + _altura(c["no"]["tipo"]) / 2,
                                        pos[nome][0], pos[nome][1] - 26, "", "msg"))
    partes.append("</svg>")
    return "".join(partes)


_ICONES = {
    "inicio": '<circle cx="11" cy="11" r="9" fill="#fff" stroke="var(--inicio)" stroke-width="2"/>',
    "fim": '<circle cx="11" cy="11" r="8" fill="#fff" stroke="var(--fim)" stroke-width="3.5"/>',
    "fim_erro": '<circle cx="11" cy="11" r="8" fill="#fff" stroke="var(--erro)" '
                'stroke-width="3.5"/>',
    "tarefa": '<rect x="1" y="4" width="20" height="14" rx="3" fill="var(--tarefa-bg)" '
              'stroke="var(--tarefa)" stroke-width="1.5"/>',
    "subprocesso": '<rect x="1" y="4" width="20" height="14" rx="3" fill="var(--sub-bg)" '
                   'stroke="var(--sub)" stroke-width="1.5"/><text x="11" y="16" '
                   'text-anchor="middle" font-size="11" fill="var(--sub)">+</text>',
    "gateway": '<polygon points="11,1 21,11 11,21 1,11" fill="var(--gw-bg)" stroke="var(--gw)" '
               'stroke-width="1.5"/><text x="11" y="15" text-anchor="middle" font-size="10" '
               'fill="var(--gw)">×</text>',
    "gateway_paralelo": '<polygon points="11,1 21,11 11,21 1,11" fill="var(--gw-bg)" '
                        'stroke="var(--gw)" stroke-width="1.5"/><text x="11" y="15" '
                        'text-anchor="middle" font-size="10" fill="var(--gw)">+</text>',
    "dados": '<path d="M3 6 v10 a8 4 0 0 0 16 0 V6" fill="#effaf8" stroke="var(--dados)" '
             'stroke-width="1.4"/><ellipse cx="11" cy="6" rx="8" ry="4" fill="#effaf8" '
             'stroke="var(--dados)" stroke-width="1.4"/>',
    "borda": '<circle cx="11" cy="11" r="9" fill="#fff" stroke="var(--gw)" stroke-width="1.5"/>'
             '<circle cx="11" cy="11" r="6" fill="none" stroke="var(--gw)" stroke-width="1.5"/>',
    "msg": '<path d="M1 11 H21" stroke="var(--msg)" stroke-width="1.6" stroke-dasharray="5 3"/>'
           '<circle cx="19" cy="11" r="2.5" fill="none" stroke="var(--msg)"/>',
    "reuso": '<rect x="1" y="5" width="20" height="12" rx="2" fill="#fff" stroke="var(--tarefa)" '
             'stroke-width="1.4"/><path d="M8 7 v8 M14 7 v8" stroke="var(--tarefa)" '
             'stroke-width="1.3"/>',
}


def _icone_legenda(tipo: str) -> str:
    return ('<svg viewBox="0 0 22 22" width="22" height="22" xmlns="http://www.w3.org/2000/svg">'
            + _ICONES.get(tipo, "") + "</svg>")


def render_html(modelo: dict, gerado_em: str = "") -> str:
    """Desenho BPMN self-contained (SVG + JS vanilla, zero CDN — proxy MSIG derruba externo)."""
    processos = modelo["processos"]
    nav = "".join('<button data-alvo="%d">%s</button>' % (i, _esc(p["nome"]))
                  for i, p in enumerate(processos))

    secoes = []
    for i, p in enumerate(processos):
        meta = ["<code>" + _esc(p["arquivo"]) + "</code>",
                "função <code>" + _esc(p["funcao"]) + "</code>",
                "raias: " + ", ".join("<code>" + _esc(r) + "</code>" for r in p["raias"])]
        if p["piscinas"]:
            meta.append("piscinas: " + ", ".join("<code>" + _esc(x) + "</code>"
                                                 for x in p["piscinas"]))
        if p["cortados"]:
            meta.append("<b>cortado no teto: +%d nó(s)</b>" % p["cortados"])
        tela = "tela%d" % i
        corpo = ['<section class="processo"><h2>' + _esc(p["nome"]) + "</h2>",
                 '<p class="meta">' + " · ".join(meta) + "</p>",
                 '<div class="tela" id="%s">%s</div>' % (tela, _svg(p["nos"], p["piscinas"])),
                 '<div class="zoom"><button data-tela="%s" data-passo="-0.15">−</button>'
                 '<button data-tela="%s" data-passo="0">100%%</button>'
                 '<button data-tela="%s" data-passo="0.15">+</button></div>' % (tela, tela, tela)]
        for n in achatar(p["nos"]):
            if n["filhos"]:
                corpo.append('<p class="expansao"><b>Expansão do subprocesso</b> “%s” '
                             '— <code>%s</code></p>' % (_esc(n["rotulo"]), _esc(n["arquivo"])))
                corpo.append('<div class="tela">%s</div>' % _svg(n["filhos"], []))
        corpo.append("</section>")
        secoes.append("".join(corpo))

    legenda = ['<div class="legenda"><h3>Legenda — de onde cada elemento sai no código</h3>']
    for tipo, nome, de_onde in LEGENDA:
        legenda.append('<div class="lg"><i>%s</i><div><b>%s</b><br><span>%s</span></div></div>'
                       % (_icone_legenda(tipo), _esc(nome), _esc(de_onde)))
    legenda.append("</div>")

    avisos = ['<div class="aviso"><h3>O que a leitura estática NÃO deriva</h3>'
              "<p>Declarado em vez de sumir em silêncio — desenho que parece completo sem ser "
              "é pior que desenho com buraco visível. Estes elementos são modelagem manual:</p><ul>"]
    for nome, porque in NAO_DERIVAVEIS:
        avisos.append("<li><b>%s</b> — %s</li>" % (_esc(nome), _esc(porque)))
    avisos.append("</ul>")
    if modelo["nao_lidos"]:
        avisos.append("<p><b>Não lido</b> (a geração seguiu, falha aberta):</p><ul>")
        for x in modelo["nao_lidos"]:
            avisos.append("<li><code>%s</code> — %s</li>" % (_esc(x["arquivo"]),
                                                                  _esc(x["erro"])))
        avisos.append("</ul>")
    avisos.append("</div>")

    cabecalho_extra = (" · gerado em " + _esc(gerado_em)) if gerado_em else ""
    return (
        '<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>Processos em BPMN — " + _esc(modelo["projeto"]) + "</title>\n"
        "<style>" + _CSS + "</style>\n</head>\n<body>\n<header>\n"
        "  <h1>Processos em BPMN — " + _esc(modelo["projeto"]) + "\n"
        "    <small>" + str(len(processos)) + " porta(s) de entrada · "
        + str(modelo["arquivos_lidos"]) + " arquivo(s) .py lidos" + cabecalho_extra
        + "</small></h1>\n"
        '  <p class="sub">Desenhado a partir do <b>código</b> por leitura estática '
        "(<code>ast</code>): cada processo é uma porta de entrada do sistema, cada raia é um "
        "módulo/pasta. Nenhuma caixa aqui foi inventada — o que o código não diz fica "
        "declarado como não derivável. Este desenho é <b>pro humano</b>; o assistente lê o "
        "<code>bpmn.md</code> gerado ao lado.</p>\n</header>\n<main>\n"
        + "".join(legenda) + "\n<nav>" + nav + "</nav>\n" + "".join(secoes) + "\n"
        + "".join(avisos) + "\n"
        '<p class="fonte">Gerado por <code>templates/bpmn.py</code> '
        "(<code>/mss-spec:bpmn</code>) a partir dos arquivos <code>.py</code> do projeto — "
        "decorators de rota, chamadas a funções do próprio projeto, <code>if/else</code>, "
        "<code>try/except</code>, chamadas a banco e a serviço externo. Saída derivada e "
        "regenerável: fora do git de propósito. Arraste para navegar; use −/+ para o zoom.</p>\n"
        "</main>\n<script>" + _JS + "</script>\n</body>\n</html>\n"
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
