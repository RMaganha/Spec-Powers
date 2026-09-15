"""memoria_indice.py — índice de memória do projeto em DOIS níveis.

Topo (`memory/MEMORY.md`): 1 linha por FAMÍLIA de gatilho, teto 6 KB — é o que entra em toda janela.
Subíndice (`memory/indice/<familia>.md`): 1 linha por memória, aberto só quando a família bate.

Por que: o índice plano cresce 1 linha por memória; num projeto grande (93 memórias no Whats) passou de
25 KB (~6.400 tokens em TODA janela) e o kit mandou podar — contra a decisão "mover, nunca apagar".
Este script MOVE: `dividir` é dry-run por padrão, verifica conservação byte a byte e só grava com
`--aplicar`. `verificar` audita o par topo+subíndices; `fila` lista o que falta de conteúdo (memória
sem `gatilho:`); `buscar` acha ponteiros por termo — o mesmo motor `casar()` que o hook de recall usa.

Uso:  python memoria_indice.py dividir  [--proj DIR] [--aplicar]
      python memoria_indice.py verificar [--proj DIR] [--aplicar]   (--aplicar corrige o N do topo)
      python memoria_indice.py fila      [--proj DIR]
      python memoria_indice.py buscar    "<termo>" [--proj DIR] [--limite N]
"""
import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

TETO_TOPO = 6000          # bytes — entra em toda janela
TETO_LINHA = 600          # bytes — linha maior é procedimento disfarçado de índice
INDICES = {"MEMORY.md", "DIARIO.md"}
SUBDIR = "indice"
MAX_FRASES = 4
MAX_FRASE = 60

RE_SECAO = re.compile(r"^## +(.*\S)\s*$")
RE_ITEM = re.compile(r"^- (?P<prefixo>.*?)\[(?P<titulo>[^\]]+)\]\((?P<arquivo>[^)]+)\)(?P<resto>.*)$")
RE_LINK_LOCAL = re.compile(r"\]\((?!\.\./)(?![a-z]+://)([^)/]+\.md)\)")
RE_FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)


@dataclass
class Item:
    linha: str
    titulo: str
    arquivo: str          # relativo a memory/


@dataclass
class Familia:
    titulo: str
    itens: list = field(default_factory=list)

    @property
    def slug(self) -> str:
        return slug(self.titulo)


@dataclass
class Relatorio:
    familias: list = field(default_factory=list)
    topo: str = ""
    bytes_antes: int = 0
    bytes_topo: int = 0
    problemas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    gravou: bool = False

    @property
    def ok(self) -> bool:
        return not self.problemas


# ------------------------------------------------------------------ utilidades de texto

def _ler(p: Path):
    """(texto com \\n, eol original) — preserva CRLF de repo Windows."""
    bruto = p.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in bruto else "\n"
    return bruto.replace("\r\n", "\n"), eol


def _gravar(p: Path, texto: str, eol: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(texto.replace("\n", eol).encode("utf-8"))


def slug(titulo: str) -> str:
    s = re.sub(r"\(.*?\)", "", titulo)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def relink(linha: str) -> str:
    """`](arquivo.md)` → `](../arquivo.md)`; não toca em `../`, URL nem `[[wikilink]]`."""
    return RE_LINK_LOCAL.sub(r"](../\1)", linha)


def frontmatter(p: Path) -> dict:
    try:
        texto, _ = _ler(p)
    except (OSError, UnicodeDecodeError):
        return {}
    m = RE_FRONT.match(texto)
    if not m:
        return {}
    campos = {}
    for l in m.group(1).splitlines():
        mm = re.match(r"^([a-z_]+):\s*(.*)$", l)
        if mm:
            campos[mm.group(1)] = mm.group(2).strip()
    return campos


# ------------------------------------------------------------------ parse

def ler_indice_plano(texto: str, soltas=None) -> list:
    """Famílias com itens. `soltas` (se passado) recebe (família, linha) de toda linha não vazia dentro
    de uma seção que NÃO é item — o `dividir` recusa nesse caso, pra nada sumir em silêncio."""
    fams, atual = [], None
    for linha in texto.replace("\r\n", "\n").split("\n"):
        m = RE_SECAO.match(linha)
        if m:
            atual = Familia(m.group(1))
            fams.append(atual)
            continue
        mi = RE_ITEM.match(linha)
        if mi and atual is not None:
            atual.itens.append(Item(linha, mi.group("titulo"), mi.group("arquivo")))
        elif atual is not None and linha.strip() and soltas is not None:
            soltas.append((atual.titulo, linha))
    return [f for f in fams if f.itens]


def _frase(gatilho: str) -> str:
    g = re.sub(r"^(quando|ao|na|no|em)\s+", "", gatilho.strip(), flags=re.I)
    g = re.split(r"\s+[—–-]\s+|;|\(", g, maxsplit=1)[0].strip().rstrip(".:")
    return g if len(g) <= MAX_FRASE else g[:MAX_FRASE].rsplit(" ", 1)[0] + "…"


def frases_de_gatilho(fam: Familia, memdir: Path) -> list:
    frases = []
    for it in fam.itens:
        g = frontmatter(memdir / it.arquivo).get("gatilho")
        if g:
            f = _frase(g)
            if f and f not in frases:
                frases.append(f)
        if len(frases) >= MAX_FRASES:
            break
    return frases


def montar_topo(fams: list, memdir: Path) -> str:
    out = ["# Memória do projeto — índice por gatilho", "",
           "<!-- 1 linha por FAMÍLIA. Gatilho bateu? abra o subíndice da família ANTES de agir.",
           f"     Teto deste topo: {TETO_TOPO // 1000} KB (orçamento de partida). Memória nova entra no",
           "     subíndice; `python memoria_indice.py verificar` confere e corrige o N. -->", ""]
    for f in fams:
        frases = frases_de_gatilho(f, memdir)
        cauda = f" · quando: {' · '.join(frases)}" if frases else ""
        out.append(f"- **{f.titulo}** → [subíndice]({SUBDIR}/{f.slug}.md) — {len(f.itens)} memórias{cauda}")
    return "\n".join(out) + "\n"


def montar_subindice(f: Familia) -> str:
    return "\n".join([f"# {f.titulo}", ""] + [relink(it.linha) for it in f.itens]) + "\n"


# ------------------------------------------------------------------ dividir

def dividir(memdir: Path, aplicar: bool = False) -> Relatorio:
    memdir = Path(memdir)
    rel = Relatorio()
    idx = memdir / "MEMORY.md"
    if not idx.is_file():
        rel.problemas.append(f"não existe {idx}")
        return rel
    texto, eol = _ler(idx)
    rel.bytes_antes = len(texto.encode("utf-8"))
    if (memdir / SUBDIR).exists():
        rel.problemas.append(f"{memdir / SUBDIR} já existe — o índice já foi dividido? use `verificar`")
        return rel
    soltas = []
    fams = ler_indice_plano(texto, soltas)
    if not fams:
        rel.problemas.append("nenhuma seção `## ` com itens `- [Título](arquivo.md)` no índice")
        return rel
    for fam, linha in soltas:
        rel.problemas.append(f"linha solta (não é item) em '{fam}' — seria perdida: {linha[:80]!r}")
    # conservação 1: nenhum ponteiro quebrado
    for f in fams:
        for it in f.itens:
            if "/" not in it.arquivo and not (memdir / it.arquivo).is_file():
                rel.problemas.append(f"ponteiro quebrado em '{f.titulo}': {it.arquivo}")
    # conservação 2: slug único
    slugs = [f.slug for f in fams]
    for s in set(slugs):
        if slugs.count(s) > 1:
            rel.problemas.append(f"duas seções viram o mesmo subíndice: {s}")
    if rel.problemas:
        return rel
    rel.familias = fams
    rel.topo = montar_topo(fams, memdir)
    rel.bytes_topo = len(rel.topo.encode("utf-8"))
    if rel.bytes_topo > TETO_TOPO:
        rel.problemas.append(f"topo ficaria com {rel.bytes_topo} bytes (teto {TETO_TOPO}) — famílias demais?")
        return rel
    subs = {f.slug: montar_subindice(f) for f in fams}
    # conservação 3: cada linha original reaparece (relinkada) exatamente uma vez
    originais = sorted(relink(it.linha) for f in fams for it in f.itens)
    movidas = sorted(l for s in subs.values() for l in s.split("\n") if l.startswith("- "))
    if originais != movidas:
        rel.problemas.append("conservação falhou: linhas movidas ≠ linhas originais")
        return rel
    gordas = [l for l in movidas if len(l.encode("utf-8")) > TETO_LINHA]
    if gordas:
        rel.avisos.append(f"{len(gordas)} linha(s) acima de {TETO_LINHA} bytes (movidas assim mesmo; encurtar é conteúdo)")
    if texto.lstrip().startswith("<!--"):
        rel.avisos.append("o comentário-modelo do índice antigo não é memória: sai do topo")
    if aplicar:
        for s, corpo in subs.items():
            _gravar(memdir / SUBDIR / f"{s}.md", corpo, eol)
        _gravar(idx, rel.topo, eol)
        rel.gravou = True
    return rel


def _tabela(rel: Relatorio) -> str:
    out = ["| família | linhas | bytes | tokens ≈ | carrega |", "|---|---:|---:|---:|---|",
           f"| topo `memory/MEMORY.md` | {rel.topo.count(chr(10))} | {rel.bytes_topo} | {rel.bytes_topo // 4} | toda partida |"]
    for f in rel.familias:
        b = len(montar_subindice(f).encode("utf-8"))
        out.append(f"| `memory/{SUBDIR}/{f.slug}.md` | {len(f.itens)} | {b} | {b // 4} | só quando a família bate |")
    return "\n".join(out)


# ------------------------------------------------------------------ verificar / fila

def _memorias(memdir: Path) -> list:
    return sorted(p for p in memdir.glob("*.md") if p.name not in INDICES)


def _linhas_dos_subindices(memdir: Path) -> list:
    """[(subíndice Path, nº da linha, Item)] de todos os memory/indice/*.md."""
    out = []
    for sub in sorted((memdir / SUBDIR).glob("*.md")):
        texto, _ = _ler(sub)
        for n, linha in enumerate(texto.split("\n"), 1):
            m = RE_ITEM.match(linha)
            if m:
                out.append((sub, n, Item(linha, m.group("titulo"), m.group("arquivo"))))
    return out


def _n_do_topo(topo: str) -> dict:
    """{slug: (nº da linha, N declarado)} a partir das linhas `→ [subíndice](indice/<slug>.md) — N memórias`."""
    out = {}
    for n, l in enumerate(topo.split("\n"), 1):
        m = re.search(rf"\]\({SUBDIR}/([^)]+)\.md\) — (\d+) memórias", l)
        if m:
            out[m.group(1)] = (n, int(m.group(2)))
    return out


def _sem_prefixo(arquivo: str) -> str:
    return arquivo[3:] if arquivo.startswith("../") else arquivo


def verificar(memdir: Path, aplicar: bool = False) -> list:
    memdir = Path(memdir)
    probs = []
    idx = memdir / "MEMORY.md"
    if not idx.is_file():
        return [f"não existe {idx}"]
    topo, eol = _ler(idx)
    b = len(topo.encode("utf-8"))
    if b > TETO_TOPO:
        probs.append(f"topo com {b} bytes — acima do teto de {TETO_TOPO} (orçamento de partida)")
    if not (memdir / SUBDIR).is_dir():
        return probs + [f"sem {memdir / SUBDIR}/ — índice plano; rode `memoria_indice.py dividir`"]
    declarados = _n_do_topo(topo)
    for s in declarados:
        if not (memdir / SUBDIR / f"{s}.md").is_file():
            probs.append(f"topo aponta subíndice inexistente: {SUBDIR}/{s}.md")
    linhas = _linhas_dos_subindices(memdir)
    por_arquivo = {}
    for sub, n, it in linhas:
        alvo = _sem_prefixo(it.arquivo)
        por_arquivo.setdefault(alvo, []).append(f"{sub.name}:{n}")
        if "/" not in alvo and not (memdir / alvo).is_file():
            probs.append(f"ponteiro quebrado em {sub.name}:{n}: {it.arquivo}")
        if len(it.linha.encode("utf-8")) > TETO_LINHA:
            probs.append(f"linha acima de {TETO_LINHA} bytes em {sub.name}:{n}")
    for md in _memorias(memdir):
        onde = por_arquivo.get(md.name, [])
        if not onde and not frontmatter(md).get("obsoleta"):
            probs.append(f"{md.name} sem linha em nenhum subíndice (memória invisível)")
        if len(onde) > 1:
            probs.append(f"{md.name} tem mais de uma linha: {', '.join(onde)}")
    contagem = {}
    for sub, _, _ in linhas:
        contagem[sub.stem] = contagem.get(sub.stem, 0) + 1
    novo_topo = topo
    for s, (n, declarado) in declarados.items():
        real = contagem.get(s, 0)
        if real != declarado:
            probs.append(f"N do topo em {s}: diz {declarado}, subíndice tem {real}")
            novo_topo = novo_topo.replace(f"]({SUBDIR}/{s}.md) — {declarado} memórias",
                                          f"]({SUBDIR}/{s}.md) — {real} memórias")
    for s in contagem:
        if s not in declarados:
            probs.append(f"subíndice {SUBDIR}/{s}.md sem linha no topo")
    if aplicar and novo_topo != topo:
        _gravar(idx, novo_topo, eol)
    return probs


def fila(memdir: Path) -> dict:
    memdir = Path(memdir)
    sem = [md.name for md in _memorias(memdir)
           if not frontmatter(md).get("gatilho") and not frontmatter(md).get("obsoleta")]
    fams_sem_frase = []
    if (memdir / SUBDIR).is_dir():
        linhas = _linhas_dos_subindices(memdir)
        for sub in sorted((memdir / SUBDIR).glob("*.md")):
            fam = Familia(sub.stem, [Item(it.linha, it.titulo, _sem_prefixo(it.arquivo))
                                     for s, _, it in linhas if s == sub])
            if not frases_de_gatilho(fam, memdir):
                fams_sem_frase.append(sub.stem)
    return {"sem_gatilho": sem, "familias_sem_frase": fams_sem_frase}


# ------------------------------------------------------------------ motor de casamento (hook + buscar)

TETO_INJECAO = 600
MINIMO_TOKENS = 2
STOPWORDS = {"para", "pelo", "pela", "pelos", "pelas", "como", "quando", "onde", "isso", "esse", "essa",
             "este", "esta", "aqui", "mais", "menos", "muito", "ainda", "então", "entao", "porque", "mesmo",
             "mesma", "nunca", "sempre", "está", "estão", "estao", "sendo", "cada", "sobre",
             "entre", "depois", "antes", "qual", "quais", "coisa", "fazer", "feito", "todo", "toda", "todos",
             "nada", "algo", "outro", "outra", "acho", "pode", "deve", "vamos", "você", "voce"}
RE_IDENT = re.compile(r"`([^`]+)`|\b([A-Za-z0-9]+(?:[_.][A-Za-z0-9]+)+)\b|\b([a-z]+[A-Z][A-Za-z0-9]*)\b")
RE_TOKEN = re.compile(r"[a-z0-9_]{4,}")
RE_LINHA_DIARIO = re.compile(r"^- \[([^\]]+)\]\s*(.*?)(?:→\s*(sessions/\S+))?\s*$")
RE_LINHA_EVALS = re.compile(r"^\| (F-\d{3}) \|")
PRIO = {"memoria": 0, "indice": 1, "evals": 2, "decisao": 3, "diario": 4}


@dataclass
class Fonte:
    texto: str        # o que casa
    ponteiro: str     # o que se injeta
    prio: int
    arquivo: str = "" # memória a que se refere (dedup memória × linha do índice)


@dataclass
class Ponteiro:
    score: int
    prio: int
    ponteiro: str


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def tokens(texto: str):
    """(tokens úteis, identificadores) — sem acento/caixa, ≥ 4 chars, sem stopwords.
    Identificador = code span, `a_b`/`a.b`, camelCase — vale 2 no score (é o que separa COD_CORR de 'código')."""
    ids = set()
    for m in RE_IDENT.finditer(texto):
        for grupo in m.groups():
            if grupo:
                ids.update(t for t in RE_TOKEN.findall(_norm(grupo)) if t not in STOPWORDS)
    toks = {t for t in RE_TOKEN.findall(_norm(texto)) if t not in STOPWORDS}
    return toks | ids, ids


def _corta(s: str, n: int = 120) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def fontes(proj: Path) -> list:
    proj = Path(proj)
    memdir = proj / "memory"
    out = []
    if not memdir.is_dir():
        return out
    for md in _memorias(memdir):
        fm = frontmatter(md)
        if fm.get("obsoleta"):
            continue
        texto = " ".join(x for x in (fm.get("name"), fm.get("description"), fm.get("gatilho")) if x)
        if texto.strip():
            out.append(Fonte(texto, f"memory/{md.name} — {_corta(fm.get('gatilho') or fm.get('description') or '')}",
                             PRIO["memoria"], md.name))
    indices = list((memdir / SUBDIR).glob("*.md")) if (memdir / SUBDIR).is_dir() else [memdir / "MEMORY.md"]
    for sub in sorted(indices):
        if not sub.is_file():
            continue
        texto, _ = _ler(sub)
        rel = sub.relative_to(proj).as_posix()
        for n, l in enumerate(texto.split("\n"), 1):
            m = RE_ITEM.match(l)
            if m and "indice/" not in m.group("arquivo"):
                out.append(Fonte(l, f"{rel}:{n} — {m.group('titulo')}", PRIO["indice"], _sem_prefixo(m.group("arquivo"))))
    ev = proj / "docs" / "EVALS.md"
    if ev.is_file():
        texto, _ = _ler(ev)
        for l in texto.split("\n"):
            m = RE_LINHA_EVALS.match(l)
            if m:
                cel = [c.strip() for c in l.strip("|").split("|")]
                if len(cel) >= 3:
                    out.append(Fonte(cel[2], f"docs/EVALS.md — {m.group(1)} {_corta(cel[2])}", PRIO["evals"]))
    dec = proj / "docs" / "decisoes.md"
    if dec.is_file():
        texto, _ = _ler(dec)
        for n, l in enumerate(texto.split("\n"), 1):
            if re.match(r"^- \d{4}-\d{2}-\d{2}", l):
                out.append(Fonte(l, f"docs/decisoes.md:{n} — {_corta(l[2:])}", PRIO["decisao"]))
    dia = memdir / "DIARIO.md"
    if dia.is_file():
        texto, _ = _ler(dia)
        for n, l in enumerate(texto.split("\n"), 1):
            m = RE_LINHA_DIARIO.match(l)
            if m and m.group(1) != "<assunto>":
                alvo = f"memory/{m.group(3)}" if m.group(3) else f"memory/DIARIO.md:{n}"
                out.append(Fonte(f"{m.group(1)} {m.group(2)}", f"{alvo} — {_corta(m.group(2))}", PRIO["diario"]))
    return out


def casar(proj: Path, prompt: str, limite: int = 3, minimo: int = MINIMO_TOKENS) -> list:
    """Ponteiros ordenados por score desc, prioridade asc. Memória e sua linha de índice: sai só a memória."""
    toks, _ = tokens(prompt)
    if len(toks) < minimo:
        return []
    achados = []
    for f in fontes(proj):
        ftoks, fids = tokens(f.texto)
        comum = toks & ftoks
        if len(comum) < minimo:
            continue
        score = sum(2 if t in fids else 1 for t in comum)
        achados.append((score, f))
    achados.sort(key=lambda x: (-x[0], x[1].prio, x[1].ponteiro))
    vistos, out = set(), []
    for score, f in achados:
        if f.arquivo:
            if f.arquivo in vistos:
                continue
            vistos.add(f.arquivo)
        out.append(Ponteiro(score, f.prio, f.ponteiro))
        if len(out) >= limite:
            break
    return out


def formatar_injecao(ponteiros: list, teto: int = TETO_INJECAO) -> str:
    """Texto que o hook injeta: cabeçalho + até 3 linhas, nunca acima do teto, nunca cortando linha ao meio."""
    if not ponteiros:
        return ""
    txt = "[mss-spec recall] casou com o seu prompt — abra antes de agir:"
    for p in ponteiros:
        cand = txt + "\n- " + p.ponteiro
        if len(cand.encode("utf-8")) > teto:
            break
        txt = cand
    return txt if "\n- " in txt else ""


# ------------------------------------------------------------------ CLI

def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["dividir", "verificar", "fila", "buscar"])
    ap.add_argument("termo", nargs="?", default="")
    ap.add_argument("--proj", default=".", help="raiz do projeto (default: diretório atual)")
    ap.add_argument("--aplicar", action="store_true", help="grava (sem isto é dry-run)")
    ap.add_argument("--limite", type=int, default=10)
    a = ap.parse_args(argv)
    proj = Path(a.proj).resolve()
    memdir = proj / "memory"
    if a.modo == "dividir":
        rel = dividir(memdir, aplicar=a.aplicar)
        if not rel.ok:
            print("NÃO dividido:\n- " + "\n- ".join(rel.problemas))
            return 1
        print(f"índice plano: {rel.bytes_antes} bytes → topo: {rel.bytes_topo} bytes "
              f"(−{100 - rel.bytes_topo * 100 // max(rel.bytes_antes, 1)}%)\n")
        print(_tabela(rel) + "\n")
        print("topo resultante:\n```markdown\n" + rel.topo + "```")
        for av in rel.avisos:
            print("aviso:", av)
        print("GRAVADO." if rel.gravou else "DRY-RUN — nada gravado. Rode com --aplicar para gravar.")
        return 0
    if a.modo == "verificar":
        probs = verificar(memdir, aplicar=a.aplicar)
        if probs:
            print("problemas:\n- " + "\n- ".join(probs))
            return 1
        print("índice de memória: ok (topo + subíndices consistentes)")
        return 0
    if a.modo == "fila":
        f = fila(memdir)
        print(f"memórias sem `gatilho:` ({len(f['sem_gatilho'])}):")
        for n in f["sem_gatilho"]:
            print("  -", n)
        print(f"famílias sem frase de gatilho no topo ({len(f['familias_sem_frase'])}): "
              + ", ".join(f["familias_sem_frase"]))
        return 0
    if not a.termo.strip():
        print("uso: memoria_indice.py buscar \"<termo>\" [--proj DIR] [--limite N]")
        return 2
    achados = casar(proj, a.termo, limite=a.limite, minimo=1)
    if not achados:
        print("nada casou com:", a.termo)
        return 1
    for p in achados:
        print(f"- {p.ponteiro}   (score {p.score})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
