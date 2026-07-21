"""mapa_neural.py — o mapa MENTAL do projeto (F2 do mapa de contexto).

Monta, para o **projeto atual**, uma árvore com o projeto no centro e 4 dimensões, cada uma
preenchida por um extrator que lê o repo (nunca inventa):
  - **Arquitetura interna** — camadas/módulos presentes (main.py, routers/, services/, ...).
  - **APIs & integrações** — endpoints expostos (rotas FastAPI) + integrações (banco, HTTP, fila).
  - **Memórias & conhecimento** — specs, índice `memory/MEMORY.md`, `docs/decisoes.md`, `to-dolist`
    e o **diário de sessão** (índice `memory/DIARIO.md` → `memory/sessions/<data>-<assunto>.md`).
  - **Conexões entre projetos** — a seção `Conexões` do `docs/superpowers/MAPA.md`.

Cada folha ancorada num arquivo ganha a **data** (mtime `YYYY-MM-DD`), e o gerador extrai uma
**camada associativa leve** (`extrair_associacoes`) — arestas heurísticas memória↔memória (`[[links]]`)
e spec↔código (`## Arquivos tocados`), nunca inventadas.

Duas saídas do mesmo modelo:
  (a) `mapa-neural.md`   — índice em texto (o assistente consulta) + seção Relações;
  (b) `mapa-neural.html` — mapa radial **full-screen**, expansível (clique no ＋) e arrastável, com
      as arestas associativas pontilhadas que acendem no hover; 100% self-contained (vis-network
      embutido inline, fontes de sistema — zero CDN).

Uso:
    python mapa_neural.py                 # projeto = diretório atual; saída no mesmo lugar
    python mapa_neural.py --proj <dir> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

_TITULO_RE = re.compile(r"^#\s*Mapa de contexto\s*[—–-]\s*(.+?)\s*$", re.MULTILINE)
_COMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_ROTA_RE = re.compile(r"@\w+\.(get|post|put|delete|patch|head|options)\s*\(\s*[\"']([^\"']+)[\"']", re.I)
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([\w.]+)", re.M)
_H1_RE = re.compile(r"^#\s+(.*?)\s*$", re.MULTILINE)

_IGNORAR_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
                 ".mypy_cache", ".ruff_cache", "dist", "build", ".idea", ".vscode"}
_CAMADAS = ["main.py", "config", "models", "schemas", "services", "routers", "repositories",
            "utils", "commands", "templates", "pages", "static", "sql", "tests"]


def _no(id, dim=None, filhos=None, resumo=None, local=None, data=None):
    n = {"id": id}
    if dim:
        n["dim"] = dim
    if resumo:
        n["resumo"] = resumo  # 1 linha do que a peça faz — pro índice servir de consulta, não só nomes
    if local:
        n["local"] = local  # caminho relativo — o pop-up mostra "onde está"
    if data:
        n["data"] = data  # mtime YYYY-MM-DD — "quando foi mexido" (verdade LOCAL; o commit atrasa na sessão)
    n["filhos"] = filhos or []
    return n


def _data(path: Path) -> str:
    """Data do arquivo = mtime em `YYYY-MM-DD`. Escolha do mtime (não do commit-date): durante a
    sessão o arquivo pode mudar (hook/upgrade/geração) e o commit atrasaria; o mtime reflete a
    verdade LOCAL agora (após push/pull todos sincronizam). Vazio se o arquivo não existe."""
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    except OSError:
        return ""


def _resumo(path: Path) -> str:
    """1-linha do que a peça faz: docstring de módulo (.py) ou `description` do frontmatter (.md)."""
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix == ".py":
        m = re.search(r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', txt[:2000], re.S)
        if m:
            for linha in m.group(1).splitlines():
                if linha.strip():
                    return linha.strip()[:90]
    elif path.suffix == ".md":
        m = re.search(r"(?m)^description:\s*(.+?)\s*$", txt)
        if m:
            return m.group(1).strip().strip("\"'")[:110]
    return ""


def _py_files(proj: Path, limite=400):
    out = []
    for p in proj.rglob("*.py"):
        if any(part in _IGNORAR_DIRS for part in p.parts):
            continue
        out.append(p)
        if len(out) >= limite:
            break
    return out


def nome_projeto(proj: Path) -> str:
    mapa = proj / "docs" / "superpowers" / "MAPA.md"
    if mapa.exists():
        m = _TITULO_RE.search(_COMENT_RE.sub("", mapa.read_text(encoding="utf-8")))
        if m:
            return m.group(1).strip()
    return proj.resolve().name


# ---- extrator: conexões entre projetos ----------------------------------

def _secao_conexoes(texto: str) -> str:
    out, dentro = [], False
    for ln in texto.splitlines():
        if ln.strip().lower().startswith("## conex"):
            dentro = True
            continue
        if dentro and ln.strip().startswith("## "):
            break
        if dentro:
            out.append(ln)
    return "\n".join(out)


def parse_conexoes(texto: str) -> list:
    texto = _COMENT_RE.sub("", texto)
    saida = []
    for ln in _secao_conexoes(texto).splitlines():
        s = ln.strip()
        s = s[2:].strip() if s.startswith("- ") else (s[1:].strip() if s.startswith("-") else None)
        if s is None:
            continue
        direc = None
        for tok in ("→", "->"):
            if s.startswith(tok):
                direc, s = "out", s[len(tok):].strip(); break
        if direc is None:
            for tok in ("←", "<-"):
                if s.startswith(tok):
                    direc, s = "in", s[len(tok):].strip(); break
        if direc is None:
            continue
        alvo, resto = (s.split(":", 1) + [""])[:2] if ":" in s else (s, "")
        alvo = alvo.strip()
        if not alvo or "<" in alvo or alvo.lower().startswith("nenhuma"):
            continue
        mp = re.search(r"\(([^)]*)\)\s*$", resto)
        ponto = mp.group(1).strip() if mp else ""
        rotulo = (resto[: mp.start()] if mp else resto).strip()
        saida.append({"direcao": direc, "alvo": alvo, "rotulo": rotulo, "ponto": ponto})
    return saida


def extrair_conexoes(proj: Path) -> dict:
    mapa = proj / "docs" / "superpowers" / "MAPA.md"
    filhos = []
    if mapa.exists():
        for c in parse_conexoes(mapa.read_text(encoding="utf-8")):
            det = []
            if c["rotulo"]:
                det.append(_no(c["rotulo"]))
            if c["ponto"]:
                det.append(_no(c["ponto"]))
            filhos.append(_no(c["alvo"], filhos=det))
    return _no("Conexões entre projetos", "conn", filhos)


# ---- extrator: arquitetura interna ---------------------------------------

def extrair_arquitetura(proj: Path) -> dict:
    filhos = []
    for camada in _CAMADAS:
        alvo = proj / camada
        if not alvo.exists():
            continue
        if alvo.is_file():
            filhos.append(_no(camada, resumo=_resumo(alvo), local=camada, data=_data(alvo)))
            continue
        arqs = sorted([p for p in alvo.glob("*.py") if p.name != "__init__.py"] +
                      list(alvo.glob("*.md")), key=lambda p: p.name)
        sub = [_no(p.name, resumo=_resumo(p), local="%s/%s" % (camada, p.name), data=_data(p))
               for p in arqs[:25]]
        if len(arqs) > 25:
            sub.append(_no("… (+%d)" % (len(arqs) - 25)))
        filhos.append(_no(camada + "/", filhos=sub, local=camada + "/"))
    return _no("Arquitetura interna", "arq", filhos)


# ---- extrator: APIs & integrações ----------------------------------------

def extrair_apis(proj: Path) -> dict:
    endpoints, imports = [], set()
    for py in _py_files(proj):
        if any(seg in ("tests", "test") for seg in py.parts):
            continue  # rota/import em teste não é a API do projeto (evita fixtures como falso-positivo)
        txt = py.read_text(encoding="utf-8", errors="ignore")
        for metodo, path in _ROTA_RE.findall(txt):
            ep = "%s %s" % (metodo.upper(), path)
            if ep not in endpoints:
                endpoints.append(ep)
        for m in _IMPORT_RE.finditer(txt):  # só imports reais — menção em string/comentário não conta
            imports.add(m.group(1).split(".")[0])
    integr = []
    if imports & {"pyodbc", "psycopg2", "psycopg", "pymssql", "sqlalchemy"}:
        integr.append("banco (SQL)")
    if imports & {"httpx", "requests", "aiohttp"}:
        integr.append("cliente HTTP (requests/httpx)")
    if imports & {"pika", "kafka", "confluent_kafka", "celery", "redis"}:
        integr.append("fila / mensageria")
    filhos = []
    if endpoints:
        filhos.append(_no("endpoints expostos", filhos=[_no(e) for e in endpoints[:30]]))
    if integr:
        filhos.append(_no("integrações externas", filhos=[_no(i) for i in integr]))
    return _no("APIs & integrações", "api", filhos)


# ---- extrator: memórias & conhecimento -----------------------------------

def _titulo_md(p: Path) -> str:
    m = _H1_RE.search(p.read_text(encoding="utf-8", errors="ignore"))
    return m.group(1).strip() if m else p.stem


def _lead_md(p: Path) -> str:
    """1ª linha de conteúdo real de um .md (após o H1, pulando `Data:`/citações/subtítulos)."""
    linhas = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    vistos_h1 = False
    for ln in linhas:
        if ln.startswith("# "):
            vistos_h1 = True
            continue
        if not vistos_h1:
            continue
        s = ln.strip().lstrip(">").strip()
        if s and not s.startswith("#") and not s.lower().startswith("data:"):
            return s[:140]
    return ""


def _rel(p: Path, proj: Path) -> str:
    return str(p.relative_to(proj)).replace("\\", "/")


def extrair_memorias(proj: Path) -> dict:
    filhos = []
    # specs — título + caminho + lead como resumo
    specs = sorted({p for p in proj.glob("docs/**/specs/*.md")} |
                   {p for p in proj.glob("docs/specs/*.md")})
    if specs:
        filhos.append(_no("specs", filhos=[
            _no(_titulo_md(p), local=_rel(p, proj), resumo=_lead_md(p), data=_data(p)) for p in specs[:25]
        ]))
    # índice de memória (linha `- [Título](arquivo) — gancho`): título + caminho + gancho como resumo
    mem_idx = proj / "memory" / "MEMORY.md"
    if mem_idx.exists():
        itens = []
        for ln in mem_idx.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln.startswith("- "):
                continue
            m = re.match(r"-\s*\[([^\]]+)\]\(([^)]+)\)\s*(?:[—-]\s*(.*))?$", ln)
            if m:
                arq = m.group(2).strip()
                loc = (arq if "/" in arq else "memory/" + arq).replace("\\", "/")
                itens.append(_no(m.group(1).strip(), local=loc, resumo=(m.group(3) or "").strip(),
                                 data=_data(proj / loc)))
            else:
                corpo = ln[2:]
                itens.append(_no(corpo.split("—")[0].strip(),
                                 resumo=corpo.split("—", 1)[1].strip() if "—" in corpo else ""))
        if itens:
            filhos.append(_no("memórias", filhos=itens[:25]))
    # decisões transversais — cada uma vira um filho (texto = resumo; caminho = decisoes.md)
    dec = proj / "docs" / "decisoes.md"
    if dec.exists():
        decs = []
        for ln in dec.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("- "):
                txt = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[—-]\s*", "", ln[2:].strip())
                decs.append(_no(txt[:60], local="docs/decisoes.md", resumo=txt[:220], data=_data(dec)))
        if decs:
            filhos.append(_no("decisões (%d)" % len(decs), filhos=decs[:25]))
    # to-dolist pessoal (fora do git; só entra se existir) — captura rápida do owner
    todo = proj / "to-dolist.md"
    if todo.exists():
        itens = [ln.strip()[2:].strip() for ln in todo.read_text(encoding="utf-8").splitlines()
                 if ln.strip().startswith("- ")]
        if itens:
            filhos.append(_no("to-dolist (%d)" % len(itens),
                              filhos=[_no(t[:60], local="to-dolist.md", resumo=t, data=_data(todo))
                                      for t in itens[:25]]))
    # diário de sessão (memory/DIARIO.md → memory/sessions/<data>-<assunto>.md): "o que conversamos/decidimos"
    diario = proj / "memory" / "DIARIO.md"
    if diario.exists():
        data_atual, difilhos = "", []
        for ln in diario.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("## "):
                data_atual = ln[3:].strip()
            elif ln.startswith("- ["):
                # formato: - [<assunto>] <gist ...> → sessions/<arquivo>  (o gist pode conter setas; pega a ÚLTIMA)
                m = re.match(r"-\s*\[([^\]]+)\]\s*(.*?)(?:\s*→\s*(\S+))?$", ln)
                if not m:
                    continue
                assunto, gist, alvo = m.group(1).strip(), (m.group(2) or "").strip(), (m.group(3) or "").strip()
                loc = alvo if alvo.startswith("memory/") else ("memory/" + alvo if alvo else "memory/DIARIO.md")
                titulo = ("%s · %s" % (data_atual, assunto)) if data_atual else assunto
                loc = loc.replace("\\", "/")
                difilhos.append(_no(titulo[:60], local=loc, resumo=gist[:220], data=_data(proj / loc)))
        if difilhos:
            filhos.append(_no("diário (%d)" % len(difilhos), filhos=difilhos[:25]))
    return _no("Memórias & conhecimento", "mem", filhos)


# ---- camada associativa (arestas heurísticas, nunca inventadas) ----------

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_PREFIXOS_SLUG = ("feedback_", "project_", "reference_", "user_")
_COD_EXT = (".py", ".md", ".js", ".css", ".html", ".sql", ".txt", ".json", ".yml", ".yaml")


def _norm_slug(s: str) -> str:
    return s.strip().lower().replace("-", "_")


def _slug_pelado(s: str) -> str:
    for pre in _PREFIXOS_SLUG:
        if s.startswith(pre):
            return s[len(pre):]
    return s


def _secao_arquivos_tocados(texto: str) -> str:
    out, dentro = [], False
    for ln in texto.splitlines():
        if re.match(r"^##\s+Arquivos tocados", ln.strip(), re.I):
            dentro = True
            continue
        if dentro and ln.strip().startswith("## "):
            break
        if dentro:
            out.append(ln)
    return "\n".join(out)


def extrair_associacoes(proj: Path) -> list:
    """Arestas associativas heurísticas e DETERMINÍSTICAS, de duas fontes REAIS (nunca inventadas):
      - **memória↔memória**: os `[[links]]` no corpo das memórias, resolvidos a um arquivo real de
        `memory/` (slug normalizado: minúsculas, `-`↔`_`, tolerando prefixo `feedback_`/`project_`/…);
        link órfão (que não resolve a arquivo) é **descartado**;
      - **spec↔código**: os caminhos citados na seção `## Arquivos tocados` das specs, quando o
        arquivo **existe em disco**.
    Cada aresta = {"a": <local>, "b": <local>, "t": "mem"|"spec"}; pares deduplicados (não-ordenados).
    """
    proj = Path(proj)
    vistos, arestas = set(), []

    def _add(a, b, t):
        if not a or not b or a == b:
            return
        chave = (t, frozenset((a, b)))
        if chave not in vistos:
            vistos.add(chave)
            arestas.append({"a": a, "b": b, "t": t})

    # memória↔memória: [[links]] resolvíveis (normalização de slug; só arquivo real vira aresta)
    memdir = proj / "memory"
    if memdir.is_dir():
        arquivos = [p for p in memdir.glob("*.md") if p.name not in ("MEMORY.md", "DIARIO.md")]
        por_slug, por_pelado = {}, {}
        for p in arquivos:
            slug = _norm_slug(p.stem)
            por_slug.setdefault(slug, "memory/" + p.name)
            por_pelado.setdefault(_slug_pelado(slug), "memory/" + p.name)
        for p in arquivos:
            origem = "memory/" + p.name
            for bruto in _LINK_RE.findall(p.read_text(encoding="utf-8", errors="ignore")):
                s = _norm_slug(bruto)
                alvo = por_slug.get(s) or por_pelado.get(_slug_pelado(s))  # arquivo real, ou None
                if alvo:
                    _add(origem, alvo, "mem")

    # spec↔código: caminhos de `## Arquivos tocados` que existem em disco
    specs = sorted({p for p in proj.glob("docs/**/specs/*.md")} |
                   {p for p in proj.glob("docs/specs/*.md")})
    for p in specs:
        sec = _secao_arquivos_tocados(p.read_text(encoding="utf-8", errors="ignore"))
        for tok in re.findall(r"`([^`]+)`", sec):
            cam = tok.strip().replace("\\", "/")
            if "/" in cam and cam.lower().endswith(_COD_EXT) and (proj / cam).is_file():
                _add(_rel(p, proj), cam, "spec")
    return arestas


# ---- árvore + saídas -----------------------------------------------------

def construir_arvore(proj: Path) -> dict:
    proj = Path(proj)
    return _no(nome_projeto(proj), "projeto", [
        extrair_arquitetura(proj),
        extrair_apis(proj),
        extrair_memorias(proj),
        extrair_conexoes(proj),
    ])


def coletar_docs(proj: Path, arvore: dict) -> dict:
    """Lê o conteúdo dos `.md` referenciados por algum nó (campo `local`) pra embutir inline no HTML.

    Chave = caminho relativo (como está no `local`); valor = conteúdo do arquivo. Deduplica e
    ignora quem não existe em disco (ex.: item do índice de memória apontando pra arquivo ausente).
    """
    proj = Path(proj)
    docs: dict = {}

    def caminha(n):
        loc = n.get("local")
        if loc and loc.lower().endswith(".md") and loc not in docs:
            alvo = proj / loc
            if alvo.is_file():
                docs[loc] = alvo.read_text(encoding="utf-8", errors="ignore")
        for f in n.get("filhos", []):
            caminha(f)

    caminha(arvore)
    return docs


def render_texto(arvore: dict, assoc: list | None = None) -> str:
    L = ["# Mapa mental — %s" % arvore["id"], "",
         "> Índice **derivado** do projeto (arquitetura · APIs · memórias · conexões).",
         "> Regenere com `/mss-spec:mapa-neural`. Não editar à mão.", ""]

    def caminha(no, nivel):
        for f in no.get("filhos", []):
            resumo = (" — " + f["resumo"]) if f.get("resumo") else ""
            data = (" [%s]" % f["data"]) if f.get("data") else ""
            L.append("%s- %s%s%s" % ("  " * nivel, f["id"], data, resumo))
            caminha(f, nivel + 1)

    for dim in arvore["filhos"]:
        L.append("## %s" % dim["id"])
        if not dim.get("filhos"):
            L.append("_(nada detectado)_")
        caminha(dim, 0)
        L.append("")
    # Relações associativas (a camada "neural" leve: o que se liga a quê, atravessando a árvore)
    if assoc:
        L.append("## Relações (associativas)")
        L.append("> Arestas heurísticas do repo (memória↔memória por `[[links]]`; spec↔código por"
                 " `Arquivos tocados`). Nunca inventadas.")
        for e in assoc:
            L.append("- %s ↔ %s" % (e["a"], e["b"]))
        L.append("")
    return "\n".join(L) + "\n"


_HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa mental — __TITLE__</title>
<style>
  :root{ --canvas:#faf8f3; --ink:#1f2a44; --muted:#8a8477;
         --arq:#2d6a4f; --api:#b5451f; --mem:#6a4c93; --conn:#1d4e89; --center:#1f2a44; }
  *{box-sizing:border-box;} html,body{height:100%;}
  body{margin:0;height:100vh;width:100vw;display:flex;flex-direction:column;overflow:hidden;
       background:var(--canvas);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",sans-serif;}
  header{flex:0 0 auto;padding:12px 22px 8px;border-bottom:1px solid #ece6d8;}
  h1{font-family:Georgia,serif;font-size:20px;margin:0;font-weight:600;}
  h1 em{color:var(--api);font-style:italic;}
  .bar{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-top:5px;font-size:12px;color:var(--muted);}
  .bar b{color:var(--ink);} .leg{display:inline-flex;align-items:center;gap:5px;}
  .dot{width:11px;height:11px;border-radius:3px;display:inline-block;}
  #wrap{flex:1 1 auto;position:relative;} #net{position:absolute;inset:0;}
  #pop{position:fixed;z-index:20;max-width:340px;background:#fff;border:1px solid #e2dccb;
       border-left:4px solid var(--ink);border-radius:8px;box-shadow:0 8px 28px rgba(31,42,68,.18);
       padding:9px 12px;font-size:12.5px;display:none;pointer-events:none;}
  #pop .nome{font-weight:700;font-size:14px;color:var(--ink);}
  #pop .loc{font-family:ui-monospace,monospace;font-size:11px;color:var(--muted);margin:2px 0 6px;word-break:break-all;}
  #pop .dt{font-size:11px;color:var(--muted);margin:0 0 6px;} #pop .dt b{color:#33405c;font-weight:600;}
  #pop .res{color:#33405c;line-height:1.45;} #pop .muted{color:var(--muted);font-style:italic;}
</style></head>
<body>
<header>
  <h1>Mapa <em>mental</em> do projeto — __TITLE__</h1>
  <div class="bar">
    <span>clique no <b>＋</b> pra expandir · clique num item <b>.md</b> pra abrir o arquivo em nova aba · arraste a caixa · role/arraste o fundo pra navegar · passe o mouse pra ver detalhes (e <b>acender</b> as ligações pontilhadas)__GEN__</span>
    <span class="leg"><i class="dot" style="background:var(--arq)"></i>arquitetura</span>
    <span class="leg"><i class="dot" style="background:var(--api)"></i>APIs &amp; integrações</span>
    <span class="leg"><i class="dot" style="background:var(--mem)"></i>memórias</span>
    <span class="leg"><i class="dot" style="background:var(--conn)"></i>conexões entre projetos</span>
  </div>
</header>
<div id="wrap"><div id="net"></div></div>
<div id="pop"></div>
<script>__VISLIB__</script>
<script>
(function(){
  var COL={arq:'#2d6a4f',api:'#b5451f',mem:'#6a4c93',conn:'#1d4e89',projeto:'#1f2a44'};
  var TREE=__TREE__;
  var DOCS=__DOCS__;  // {caminho.md: conteúdo} — embutido na geração; abre em nova aba ao clicar
  var ASSOC=__ASSOC__;  // [{a,b,t}] arestas associativas (memória↔memória, spec↔código) — nunca inventadas
  var ACOL={mem:'#6a4c93', spec:'#b5451f'};  // cor da aresta associativa por tipo
  var uid=0, byUid={};

  // renderizador markdown vanilla inline (sem lib/CDN): títulos, listas, código, blockquote, links, ---
  function mdEsc(s){ return (''+s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function mdInline(s){ s=mdEsc(s);
    s=s.replace(/`([^`]+)`/g,'<code>$1</code>');
    s=s.replace(/\\*\\*([^*]+)\\*\\*/g,'<strong>$1</strong>');
    s=s.replace(/\\*([^*]+)\\*/g,'<em>$1</em>');
    s=s.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,'<a href="$2">$1</a>');
    return s; }
  function mdToHtml(src){
    var lines=(''+src).split(/\\r?\\n/), out=[], inCode=false, code=[], list=null;
    function closeList(){ if(list){ out.push('</'+list+'>'); list=null; } }
    for(var i=0;i<lines.length;i++){ var ln=lines[i];
      if(/^```/.test(ln)){ if(inCode){ out.push('<pre><code>'+mdEsc(code.join('\\n'))+'</code></pre>'); code=[]; inCode=false; } else { closeList(); inCode=true; } continue; }
      if(inCode){ code.push(ln); continue; }
      if(/^\\s*---+\\s*$/.test(ln)){ closeList(); out.push('<hr>'); continue; }
      var h=ln.match(/^(#{1,6})\\s+(.*)$/); if(h){ closeList(); var lv=h[1].length; out.push('<h'+lv+'>'+mdInline(h[2])+'</h'+lv+'>'); continue; }
      var q=ln.match(/^\\s*>\\s?(.*)$/); if(q){ closeList(); out.push('<blockquote>'+mdInline(q[1])+'</blockquote>'); continue; }
      var ul=ln.match(/^\\s*[-*]\\s+(.*)$/); if(ul){ if(list!=='ul'){ closeList(); out.push('<ul>'); list='ul'; } out.push('<li>'+mdInline(ul[1])+'</li>'); continue; }
      var ol=ln.match(/^\\s*\\d+\\.\\s+(.*)$/); if(ol){ if(list!=='ol'){ closeList(); out.push('<ol>'); list='ol'; } out.push('<li>'+mdInline(ol[1])+'</li>'); continue; }
      if(/^\\s*$/.test(ln)){ closeList(); continue; }
      closeList(); out.push('<p>'+mdInline(ln)+'</p>'); }
    if(inCode) out.push('<pre><code>'+mdEsc(code.join('\\n'))+'</code></pre>');
    closeList(); return out.join('\\n'); }

  function openDoc(n){ if(!n||!n.local) return false;
    var src=DOCS[n.local]; if(src===undefined) return false;
    var w=window.open('','_blank'); if(!w) return false;
    var css="body{max-width:820px;margin:0 auto;padding:32px 24px;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#1f2a44;line-height:1.6;}"
      +"h1,h2,h3,h4{font-family:Georgia,serif;line-height:1.25;}h1{font-size:26px;}"
      +"code{font-family:ui-monospace,monospace;background:#f2efe7;padding:1px 5px;border-radius:4px;font-size:.9em;}"
      +"pre{background:#f7f5ef;padding:14px;border-radius:8px;overflow:auto;}pre code{background:none;padding:0;}"
      +"blockquote{border-left:3px solid #d9d3c4;margin:0;padding:2px 14px;color:#5a5647;}"
      +"a{color:#1d4e89;}hr{border:none;border-top:1px solid #e2dccb;margin:22px 0;}"
      +".loc{font-family:ui-monospace,monospace;font-size:12px;color:#8a8477;margin-bottom:18px;word-break:break-all;}";
    w.document.write('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
      +'<meta name="viewport" content="width=device-width,initial-scale=1">'
      +'<title>'+mdEsc(n.local)+'</title><style>'+css+'</style></head><body>'
      +'<div class="loc">'+mdEsc(n.local)+'</div>'+mdToHtml(src)+'</body></html>');
    w.document.close(); return true; }
  (function init(n,p,dim){ n._uid=++uid; n._p=p; n.dim=n.dim||dim; if(n.exp===undefined)n.exp=(p===null);
    byUid[n._uid]=n; if(n.filhos)n.filhos.forEach(function(c){init(c,n,n.dim);}); })(TREE,null,'projeto');

  // índice local -> [uids]: liga as arestas associativas aos nós certos (um mesmo arquivo pode ter +1 nó)
  var byLocal={};
  Object.keys(byUid).forEach(function(u){ var n=byUid[u];
    if(n.local){ (byLocal[n.local]=byLocal[n.local]||[]).push(n._uid); } });

  var pop=document.getElementById('pop'), cont=document.getElementById('net');
  function esc(s){return (''+s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  // layout RADIAL determinístico — SEM física (nada de animação "se mexendo").
  // As posições são calculadas; expandir só ACRESCENTA os filhos, os demais nós não saem do lugar.
  function Ldist(l){ return l<=1 ? 240 : 175; }
  function layout(n,dir,level){
    if(!n._p){ n._bx=0; n._by=0; }
    else { n._bx=n._p._x+Ldist(level)*Math.cos(dir); n._by=n._p._y+Ldist(level)*Math.sin(dir); }
    n._x=n._bx+(n._dx||0); n._y=n._by+(n._dy||0);
    if(n.exp&&n.filhos){ var k=n.filhos.length;
      for(var i=0;i<k;i++){ var cd;
        if(level===0){ cd=2*Math.PI*i/k-Math.PI/2; }
        else { var sp=Math.min(2.6,0.7+k*0.32); cd=(k===1)?dir:(dir-sp/2+sp*i/(k-1)); }
        layout(n.filhos[i],cd,level+1); } }
  }
  function visiveis(n,a){ a.push(n); if(n.exp&&n.filhos)n.filhos.forEach(function(c){visiveis(c,a);}); return a; }

  var nodes=new vis.DataSet(), edges=new vis.DataSet();
  function rebuild(){
    layout(TREE,-Math.PI/2,0);
    var vivos=visiveis(TREE,[]), ok={}; vivos.forEach(function(n){ ok[n._uid]=1; });
    nodes.getIds().forEach(function(id){ if(!ok[id]) nodes.remove(id); });
    // limpa só as arestas de ÁRVORE ('e'+uid) que sumiram; as associativas ('a…') são refeitas abaixo
    edges.getIds().forEach(function(id){ id=String(id);
      if(id.charAt(0)==='e' && !ok[+id.slice(1)]) edges.remove(id);
      else if(id.charAt(0)==='a') edges.remove(id); });
    vivos.forEach(function(n){
      var center=(n.dim==='projeto'), kids=n.filhos&&n.filhos.length;
      var mark=kids?(n.exp?'  −':'  +'):'';
      nodes.update({ id:n._uid, label:(''+n.id)+mark, x:n._x, y:n._y, shape:'box', margin:9, borderWidth:2, shadow:false,
        color:{ background:center?'#1f2a44':'#ffffff', border:COL[n.dim]||'#1f2a44',
                highlight:{ background:center?'#26324f':'#f3efe6', border:COL[n.dim]||'#1f2a44' } },
        font:{ color:center?'#faf8f3':'#1f2a44', size:center?16:13, face:'system-ui', bold:!!center } });
      if(n._p) edges.update({ id:'e'+n._uid, from:n._p._uid, to:n._uid, width:2,
        color:{ color:COL[n.dim]||'#999', opacity:0.55, highlight:COL[n.dim]||'#999' }, smooth:{type:'continuous'} });
    });
    // arestas ASSOCIATIVAS: só entre nós VISÍVEIS (a "teia" cresce conforme se expande),
    // pontilhadas e fracas — acendem no hover (acenderAssoc). Nunca inventadas: vêm do dado ASSOC.
    ASSOC.forEach(function(e,i){ var A=byLocal[e.a]||[], B=byLocal[e.b]||[];
      A.forEach(function(ua){ B.forEach(function(ub){
        if(ua!==ub && ok[ua] && ok[ub]){
          edges.add({ id:'a'+i+'_'+ua+'_'+ub, from:ua, to:ub, dashes:true, width:1, _assoc:1, _base:ACOL[e.t]||'#999',
            color:{ color:ACOL[e.t]||'#999', opacity:0.16 }, smooth:{ type:'curvedCW', roundness:0.2 } });
        } })); });
  }
  function acenderAssoc(uid){ edges.forEach(function(e){ if(!e._assoc) return;
    var on=(e.from===uid||e.to===uid);
    edges.update({ id:e.id, width:on?2.5:1, shadow:!!on, color:{ color:e._base, opacity:on?0.95:0.16 } }); }); }
  function apagarAssoc(){ edges.forEach(function(e){ if(e._assoc)
    edges.update({ id:e.id, width:1, shadow:false, color:{ color:e._base, opacity:0.16 } }); }); }

  var net=new vis.Network(cont, {nodes:nodes,edges:edges}, {
    physics:false, layout:{ improvedLayout:false },
    interaction:{ hover:true, dragNodes:true, dragView:true, zoomView:true },
    nodes:{ shapeProperties:{ borderRadius:8 } }
  });

  net.on('click', function(p){ if(!p.nodes.length) return; var n=byUid[p.nodes[0]]; if(!n) return;
    if(n.filhos&&n.filhos.length){ n.exp=!n.exp; rebuild(); return; }   // nó com filhos: expande/recolhe
    if(n.local&&/\\.md$/i.test(n.local)) openDoc(n); });                 // folha .md: abre em nova aba
  net.on('hoverNode', function(p){ showPop(byUid[p.node]); acenderAssoc(p.node); });
  net.on('blurNode', function(){ hidePop(); apagarAssoc(); });
  net.on('dragStart', hidePop); net.on('zoom', hidePop);
  net.on('dragEnd', function(p){ if(p.nodes.length){ var id=p.nodes[0], n=byUid[id], pos=net.getPositions([id])[id];
    if(n&&pos){ n._dx=pos.x-n._bx; n._dy=pos.y-n._by; } } });  // guarda o arraste (fica onde soltou)

  function showPop(n){ if(!n) return;
    var pos=net.getPositions([n._uid])[n._uid]; if(!pos) return;
    var dom=net.canvasToDOM(pos), rect=cont.getBoundingClientRect();
    var loc=n.local?'<div class="loc">'+esc(n.local)+'</div>':'';
    var dt=n.data?'<div class="dt"><b>modificado:</b> '+esc(n.data)+'</div>':'';
    var res=n.resumo?'<div class="res">'+esc(n.resumo)+'</div>':'<div class="res muted">(sem descrição registrada)</div>';
    pop.innerHTML='<div class="nome">'+esc(n.id)+'</div>'+loc+dt+res;
    pop.style.borderLeftColor=COL[n.dim]||'#1f2a44'; pop.style.display='block';
    var pw=pop.offsetWidth, ph=pop.offsetHeight;
    var left=rect.left+dom.x-pw/2; left=Math.max(8,Math.min(left,window.innerWidth-pw-8));
    var top=rect.top+dom.y-ph-26; if(top<8) top=rect.top+dom.y+26;
    pop.style.left=left+'px'; pop.style.top=top+'px'; }
  function hidePop(){ pop.style.display='none'; }

  rebuild();
  net.fit({animation:false});
})();
</script>
</body></html>
"""


def render_html(arvore: dict, gerado_em: str = "", docs: dict | None = None,
                assoc: list | None = None) -> str:
    gen = " · gerado em %s" % gerado_em if gerado_em else ""
    vis = (Path(__file__).resolve().parent / "vendor" / "vis-network.min.js").read_text(encoding="utf-8")
    html = (_HTML.replace("__TITLE__", str(arvore["id"]))
                 .replace("__GEN__", gen)
                 .replace("__VISLIB__", vis))
    # __TREE__/__DOCS__/__ASSOC__ carregam JSON que pode conter o texto de OUTRO placeholder
    # (ex.: uma spec que menciona `__DOCS__`) — substituí num passo só pra não contaminar.
    subs = {"__TREE__": json.dumps(arvore, ensure_ascii=False),
            "__DOCS__": json.dumps(docs or {}, ensure_ascii=False),
            "__ASSOC__": json.dumps(assoc or [], ensure_ascii=False)}
    return re.sub(r"__TREE__|__DOCS__|__ASSOC__", lambda m: subs[m.group(0)], html)


def gerar(proj_dir=None, out_dir=None):
    proj = Path(proj_dir) if proj_dir else Path.cwd()
    if not proj.exists():
        raise ValueError("projeto não encontrado: %s" % proj)
    arv = construir_arvore(proj)
    assoc = extrair_associacoes(proj)
    # saída em docs/ (todo projeto tem, via superpowers; fica isolado e não polui a raiz)
    out = Path(out_dir) if out_dir else proj / "docs"
    out.mkdir(parents=True, exist_ok=True)
    md = out / "mapa-neural.md"
    html = out / "mapa-neural.html"
    docs = coletar_docs(proj, arv)
    md.write_text(render_texto(arv, assoc=assoc), encoding="utf-8")
    html.write_text(render_html(arv, datetime.now().strftime("%Y-%m-%d %H:%M"), docs=docs, assoc=assoc),
                    encoding="utf-8")
    return md, html


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gera o mapa mental do projeto (4 dimensões).")
    ap.add_argument("--proj", help="diretório do projeto (default: diretório atual)")
    ap.add_argument("--out", help="pasta de saída (default: o próprio projeto)")
    args = ap.parse_args(argv)
    try:
        md, html = gerar(proj_dir=args.proj, out_dir=args.out)
    except ValueError as e:
        raise SystemExit(str(e))
    print("mapa mental gerado:\n  texto: %s\n  html:  %s" % (Path(md).resolve(), Path(html).resolve()))


if __name__ == "__main__":
    main()
