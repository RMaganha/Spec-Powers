"""memoria_indice.py — índice de memória do projeto em DOIS níveis.

Topo (`memory/MEMORY.md`): 1 linha por FAMÍLIA de gatilho, teto 6 KB — é o que entra em toda janela.
Subíndice (`memory/indice/<familia>.md`): 1 linha por memória, aberto só quando a família bate.

Por que: o índice plano cresce 1 linha por memória; num projeto grande (93 memórias no Whats) passou de
25 KB (~6.400 tokens em TODA janela) e o kit mandou podar — contra a decisão "mover, nunca apagar".
Este script MOVE: `dividir` é dry-run por padrão, verifica conservação byte a byte e só grava com
`--aplicar`. `verificar` audita o par topo+subíndices — e, desde o benchmark MSIG_Agentes (2026-11-06),
acusa **gatilho fraco** (curto/genérico: o recall nunca casa) e **possível duplicata** (mesmo `name:` ou
descrições quase iguais); `citacoes` lista caminho citado em memória/spec que não existe mais; `fila` lista o
que falta de conteúdo (memória sem `gatilho:`); `buscar` acha ponteiros por termo — o mesmo motor `casar()`
que o hook de recall usa.

Uso:  python memoria_indice.py dividir  [--proj DIR] [--aplicar]
      python memoria_indice.py verificar [--proj DIR] [--aplicar]   (--aplicar corrige o N do topo)
      python memoria_indice.py citacoes  [--proj DIR]
      python memoria_indice.py fila      [--proj DIR]
      python memoria_indice.py buscar    "<termo>" [--proj DIR] [--limite N]
"""
import argparse
import re
import subprocess
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
            continue
        mt = re.match(r"^\s+type:\s*(.*)$", l)          # `metadata:\n  type: procedimento`
        if mt and "type" not in campos:
            campos["type"] = mt.group(1).strip()
    return campos


def corpo(p: Path) -> str:
    """O markdown depois do frontmatter ('' se não há arquivo/frontmatter)."""
    try:
        texto, _ = _ler(p)
    except (OSError, UnicodeDecodeError):
        return ""
    m = RE_FRONT.match(texto)
    return texto[m.end():] if m else texto


# ------------------------------------------------------------------ procedimento (benchmark MSIG_Agentes, item 1)
# Passo a passo ensinado uma vez vira memória `type: procedimento`: gatilho no frontmatter (como toda memória),
# corpo com **Passos:** numerados (quem · como · para se), **Ferramentas:** e **Saída:**. O `verificar` recusa
# formato errado; o recall aponta com o prefixo PROCEDIMENTO e manda ler inteiro e seguir "passo k/N".
TIPO_PROCEDIMENTO = "procedimento"
RE_PASSO = re.compile(r"^\s*\d+[.)]\s+\S", re.M)
MARCAS_PROCEDIMENTO = ("**Passos:**", "**Ferramentas:**", "**Saída:**")
INSTRUCAO_PROCEDIMENTO = ("- procedimento casou → leia o arquivo INTEIRO antes de agir, siga os passos na ordem "
                          "anunciando `Seguindo [[slug]] — passo k/N`, e feche com feitos × pendentes "
                          "(inclusive os de terceiros)")


def validar_procedimento(texto_corpo: str) -> list:
    """Erros de formato de um procedimento ('' = ok). Marcas obrigatórias e pelo menos 2 passos numerados."""
    erros = [f"falta a marca `{m}`" for m in MARCAS_PROCEDIMENTO if m not in texto_corpo]
    if "**Passos:**" in texto_corpo:
        depois = texto_corpo.split("**Passos:**", 1)[1]
        fim = min([depois.find(m) for m in MARCAS_PROCEDIMENTO if m != "**Passos:**" and m in depois] or [len(depois)])
        if len(RE_PASSO.findall(depois[:fim])) < 2:
            erros.append("menos de 2 passos numerados em **Passos:** (`1. <ação> — quem: … — como: …`)")
    return erros


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


# ------------------------------------------------------------------ gatilho de ação (decisão 24 do owner, 2026-11-11)
# "Consultar a memória pela ação" ficou assim: não se busca por palavras a cada comando (decisão de 2026-09-25,
# mantida); a anotação que é REGRA sobre o que o assistente faz (`type: feedback`) declara o gatilho de ação —
# `gatilho_comando:` ou `gatilho_resposta:`, lidos por `hooks/_memoria_de_acao.py` — ou diz por que não tem
# (`sem_gatilho_de_acao: <motivo>`). A captura cobra a NOVA (ainda sem commit) pelo nome; as antigas vão pra `fila`,
# que o owner aprova de uma vez — nunca viram N problemas (o assistente sairia corrigindo sozinho).
CAMPOS_DE_ACAO = ("gatilho_comando", "gatilho_resposta")
CAMPO_SEM_ACAO = "sem_gatilho_de_acao"
TIPO_DE_REGRA = "feedback"


def _sem_commit(memdir: Path) -> set:
    """Nomes dos arquivos de `memory/` que o git ainda não tem (novos nesta captura). Em bytes e com `-z`
    (`text=True` quebra a chamada ao git no Windows). Sem git, fora de repositório ou com defeito → vazio:
    sem saber o que é novo, nada é cobrado pelo nome."""
    try:
        r = subprocess.run(["git", "-C", str(memdir), "status", "--porcelain", "-z", "--untracked-files=all", "--", "."],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return set()
    if r.returncode != 0:
        return set()
    return {item[3:].rsplit("/", 1)[-1] for item in r.stdout.decode("utf-8", "ignore").split("\0")
            if len(item) > 3 and (item[:2] == "??" or item[0] == "A")}


def sem_gatilho_de_acao(memdir: Path) -> list:
    """Anotações de regra (`type: feedback`, não obsoletas) sem gatilho de ação e sem o motivo de não ter."""
    out = []
    for md in _memorias(Path(memdir)):
        fm = frontmatter(md)
        if fm.get("obsoleta") or fm.get("type") != TIPO_DE_REGRA:
            continue
        if not any(fm.get(c) for c in CAMPOS_DE_ACAO) and not fm.get(CAMPO_SEM_ACAO):
            out.append(md.name)
    return out


def verificar(memdir: Path, aplicar: bool = False, sem_commit=None) -> list:
    """`sem_commit`: nomes das anotações novas (default: o que o git ainda não tem commitado em `memory/`)."""
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
        fm = frontmatter(md)
        if not onde and not fm.get("obsoleta"):
            probs.append(f"{md.name} sem linha em nenhum subíndice (memória invisível)")
        if len(onde) > 1:
            probs.append(f"{md.name} tem mais de uma linha: {', '.join(onde)}")
        if not fm.get("obsoleta") and fm.get("gatilho"):
            motivo = gatilho_fraco(fm["gatilho"])
            if motivo:
                probs.append(f"gatilho fraco em {md.name}: {motivo} — o recall nunca vai casar; "
                             f"diga a condição observável (tela, arquivo, comando, erro)")
        if not fm.get("obsoleta") and fm.get("type") == TIPO_PROCEDIMENTO:
            if not fm.get("gatilho"):
                probs.append(f"procedimento sem `gatilho:` em {md.name} — sem gatilho ele nunca chega ao assistente")
            for erro in validar_procedimento(corpo(md)):
                probs.append(f"procedimento fora do formato em {md.name}: {erro}")
        for campo in CAMPOS_DE_ACAO:
            if not fm.get("obsoleta") and fm.get(campo):
                try:
                    re.compile(fm[campo])
                except re.error as erro:
                    probs.append(f"regex quebrado em `{campo}:` de {md.name} ({erro}) — o hook ignora a anotação "
                                 f"calado e ela nunca dispara; corrija o regex")
    novas = _sem_commit(memdir) if sem_commit is None else set(sem_commit)
    for nome in sem_gatilho_de_acao(memdir):
        if nome in novas:
            probs.append(f"regra de ação sem gatilho de ação em {nome}: anotação `type: {TIPO_DE_REGRA}` declara "
                         f"`gatilho_comando:` ou `gatilho_resposta:` (regex testado contra o caso real e contra 2-3 "
                         f"que não devem casar) — ou `{CAMPO_SEM_ACAO}: <motivo>` quando a ação não tem sinal que "
                         f"dê pra ver num comando ou numa resposta")
    for a, b, motivo in duplicatas(memdir):
        probs.append(f"possível duplicata: {a} × {b} — {motivo}; atualize uma e marque a outra `obsoleta:`")
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


# ------------------------------------------------------------------ qualidade do que foi gravado
# Benchmark MSIG_Agentes (2026-11-06): lá o `agente-criar` recusa texto de roteamento fraco, o `gravar` avisa
# duplicata (mesma tag, título diferente) e o `doctor` lista script citado no KB que não existe no kit.
# Aqui o gatilho É o roteamento do recall, a duplicata é memória que o owner reescreveu em vez de atualizar, e a
# citação morta é caminho que mudou depois da memória — as três entram no `verificar`/`citacoes`.
GATILHO_MIN_CHARS = 15        # depois de tirar "quando/ao/sempre que"
GATILHO_MIN_TOKENS = 2        # palavras úteis (≥ 4 letras, sem stopwords)
DUP_MIN_TOKENS = 4
DUP_JACCARD = 0.8
RE_INICIO_GATILHO = re.compile(r"^(quando|ao|na|no|em|sempre que|se)\s+", re.I)
RE_CITACAO = re.compile(r"`([^`\s]+?\.(?:py|md|json|ya?ml|sql|html?|js|tsx?|ps1|txt|toml|cfg|ini|css|csv|bat|sh))"
                        r"(?::\d+)?`")
PASTAS_CITACOES = ("memory", "docs/specs")
PASTAS_IGNORADAS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
KIT = Path(__file__).resolve().parents[1]


def gatilho_fraco(gatilho: str) -> str:
    """Motivo (str) se o gatilho é curto ou genérico demais pra casar com um prompt; '' se está bom."""
    g = RE_INICIO_GATILHO.sub("", (gatilho or "").strip())
    if len(g) < GATILHO_MIN_CHARS:
        return f"{len(g)} caracteres (mínimo {GATILHO_MIN_CHARS})"
    uteis, _ = tokens(g)
    if len(uteis) < GATILHO_MIN_TOKENS:
        return f"{len(uteis)} palavra(s) útil(eis) (mínimo {GATILHO_MIN_TOKENS})"
    return ""


def duplicatas(memdir: Path) -> list:
    """[(arquivo a, arquivo b, motivo)] — mesmo `name:` em dois arquivos, ou descrições quase iguais."""
    mems = [(md.name, frontmatter(md)) for md in _memorias(Path(memdir))]
    mems = [(n, fm) for n, fm in mems if not fm.get("obsoleta")]
    out, por_name = [], {}
    for n, fm in mems:
        if fm.get("name"):
            por_name.setdefault(fm["name"], []).append(n)
    for name, arqs in por_name.items():
        for outro in arqs[1:]:
            out.append((arqs[0], outro, f"mesmo `name: {name}`"))
    descs = [(n, tokens(fm.get("description", ""))[0]) for n, fm in mems]
    for i, (a, ta) in enumerate(descs):
        for b, tb in descs[i + 1:]:
            if len(ta) >= DUP_MIN_TOKENS and len(tb) >= DUP_MIN_TOKENS:
                jac = len(ta & tb) / len(ta | tb)
                if jac >= DUP_JACCARD:
                    out.append((a, b, f"descrições quase iguais ({int(jac * 100)}% das palavras)"))
    return out


def _nomes_de_arquivo(raiz: Path) -> set:
    try:
        return {p.name for p in raiz.rglob("*") if not PASTAS_IGNORADAS & set(p.parts)}
    except OSError:
        return set()


def citacoes_mortas(proj: Path, pastas=PASTAS_CITACOES) -> list:
    """[(arquivo:linha, citação)] de todo caminho em crase, fora de bloco de código, que não existe no projeto
    nem no kit. Caminho com separador resolve relativo ao projeto (ou ao kit); nome solto vale se existe algum
    arquivo com esse nome. Placeholder (`<x>`, `${X}`, `{x}`, `*`) não é citação. Memória `obsoleta:` fica fora."""
    proj = Path(proj)
    nomes = {}

    def existe(cit: str) -> bool:
        if any(x in cit for x in ("<", "${", "{", "*")):
            return True
        c = cit.replace("\\", "/")
        if c.startswith("~/"):                      # caminho da casa do usuário (ex.: `~/.claude/...`)
            return (Path.home() / c[2:]).exists()
        p = Path(c)
        if p.is_absolute() and not c.startswith("/"):
            return p.exists()
        while c.startswith(("./", "/")):
            c = c[2:] if c.startswith("./") else c[1:]
        nome = c.rsplit("/", 1)[-1]
        if len(nome.rsplit(".", 1)[0]) <= 1:        # `x.sql`, `x.md`: exemplo, não citação
            return True
        if not nomes:
            nomes["todos"] = _nomes_de_arquivo(proj) | _nomes_de_arquivo(KIT)
            nomes["moldes"] = _nomes_de_arquivo(KIT / "templates")
        if "/" in c:
            # molde do kit (`docs/ARQUITETURA.md`, `docs/SEGURANCA.md`): nasce no projeto pelo kickoff/upgrade
            return (proj / c).exists() or (KIT / c).exists() or nome in nomes["moldes"]
        return nome in nomes["todos"]

    out = []
    for pasta in pastas:
        base = proj / pasta
        if not base.is_dir():
            continue
        for md in sorted(base.glob("*.md")):
            if md.name in INDICES or frontmatter(md).get("obsoleta"):
                continue
            texto, _ = _ler(md)
            cerca = False
            for n, l in enumerate(texto.split("\n"), 1):
                if l.strip().startswith("```"):
                    cerca = not cerca
                    continue
                if cerca:
                    continue
                for m in RE_CITACAO.finditer(l):
                    if not existe(m.group(1)):
                        out.append((f"{pasta}/{md.name}:{n}", m.group(0).strip("`")))
    return out


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
    return {"sem_gatilho": sem, "familias_sem_frase": fams_sem_frase,
            "sem_gatilho_de_acao": sem_gatilho_de_acao(memdir)}


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
PRIO = {"procedimento": -1, "memoria": 0, "ambientes": 0, "indice": 1, "evals": 2, "decisao": 3, "diario": 5}
# docs/AMBIENTES.md (0.50.0, F-048): cada seção `## <ambiente>` casa pelo próprio nome (contado em dobro) e
# por estas palavras genéricas — nunca pelo nome dos OUTROS ambientes, senão "produção" casaria com todas
PALAVRAS_AMBIENTE = ("ambiente ambientes servidor host variável variavel valor valores app setting setting "
                     "banco web url porta acesso acessa")
# linha marcada como vencida não é injetada: o que é velho não pode voltar como fato (F-030)
# — só como STATUS (início da linha ou segmento após " — "), não citada entre crases numa explicação
RE_VENCIDA = re.compile(r"(?:^|[—–]\s*|^- \s*)\**(?:obsoleta|pausada)\s*:")


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


def fontes_ambientes(proj: Path) -> list:
    """Uma fonte por seção `## <ambiente>` de `docs/AMBIENTES.md` (0.50.0, F-048): o texto da seção (nomes,
    variáveis, quem acessa) mais as palavras de ambiente; o ponteiro é a linha da seção."""
    amb = Path(proj) / "docs" / "AMBIENTES.md"
    if not amb.is_file():
        return []
    texto, _ = _ler(amb)
    out, secao, inicio, corpo = [], None, 0, []

    def fechar():
        if secao and not secao.startswith("<"):
            variaveis = re.findall(r"^\| `([^`]+)`", "\n".join(corpo), re.M)
            out.append(Fonte(f"`{secao}` {secao} {PALAVRAS_AMBIENTE} " + " ".join(corpo),
                             f"docs/AMBIENTES.md:{inicio} — ambiente {secao}: o que é, quem acessa o quê, "
                             f"{len(variaveis)} variável(is) com valor",
                             PRIO["ambientes"]))

    for n, l in enumerate(texto.split("\n"), 1):
        m = RE_SECAO.match(l)
        if m:
            fechar()
            secao, inicio, corpo = m.group(1), n, []
        elif secao is not None:
            corpo.append(l)
    fechar()
    return out


def fontes(proj: Path, diario: bool = True) -> list:
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
            gancho = _corta(fm.get("gatilho") or fm.get("description") or "")
            if fm.get("type") == TIPO_PROCEDIMENTO:
                out.append(Fonte(texto, f"PROCEDIMENTO memory/{md.name} — {gancho}", PRIO["procedimento"], md.name))
            else:
                out.append(Fonte(texto, f"memory/{md.name} — {gancho}", PRIO["memoria"], md.name))
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
    # fora de escopo é "não agora" e só aparece quando o owner pede ao to-dolist (0.47.0): nem o
    # `to-dolist.md` nem o `FORA-DE-ESCOPO.md` antigo entram aqui — a busca roda a cada mensagem e repetia o item
    out.extend(fontes_ambientes(proj))
    dia = memdir / "DIARIO.md"
    if diario and dia.is_file():
        texto, _ = _ler(dia)
        for n, l in enumerate(texto.split("\n"), 1):
            m = RE_LINHA_DIARIO.match(l)
            if m and m.group(1) != "<assunto>":
                alvo = f"memory/{m.group(3)}" if m.group(3) else f"memory/DIARIO.md:{n}"
                out.append(Fonte(f"{m.group(1)} {m.group(2)}", f"{alvo} — {_corta(m.group(2))}", PRIO["diario"]))
    return [f for f in out if not RE_VENCIDA.search(_norm(f.texto))]


def casar(proj: Path, prompt: str, limite: int = 3, minimo: int = MINIMO_TOKENS, diario: bool = True) -> list:
    """Ponteiros ordenados por score desc, prioridade asc. Memória e sua linha de índice: sai só a memória.
    `diario=False` (o hook): diário de sessão é passado, sob demanda — injetado sozinho vira "estado atual" (F-030)."""
    toks, _ = tokens(prompt)
    if len(toks) < minimo:
        return []
    achados = []
    for f in fontes(proj, diario=diario):
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
    # procedimento casou: a instrução de "ler inteiro e seguir passo k/N" entra junto, dentro do teto
    com_procedimento = any(p.ponteiro.startswith("PROCEDIMENTO ") for p in ponteiros)
    reserva = len(("\n" + INSTRUCAO_PROCEDIMENTO).encode("utf-8")) if com_procedimento else 0
    for p in ponteiros:
        cand = txt + "\n- " + p.ponteiro
        if len(cand.encode("utf-8")) + reserva > teto:
            break
        txt = cand
    if "\n- " not in txt:
        return ""
    if com_procedimento and "PROCEDIMENTO " in txt:
        txt += "\n" + INSTRUCAO_PROCEDIMENTO
    return txt


# ------------------------------------------------------------------ CLI

def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["dividir", "verificar", "fila", "buscar", "citacoes"])
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
        novas = _sem_commit(memdir)
        antigas = [n for n in sem_gatilho_de_acao(memdir) if n not in novas] if memdir.is_dir() else []
        if antigas:
            print(f"aviso: {len(antigas)} anotação(ões) antiga(s) de regra sem gatilho de ação — NÃO corrija por "
                  f"conta própria: `memoria_indice.py fila` lista, e o owner aprova de uma vez quais ganham "
                  f"`gatilho_comando:`/`gatilho_resposta:` e quais ficam com `{CAMPO_SEM_ACAO}: <motivo>`")
        if probs:
            print("problemas:\n- " + "\n- ".join(probs))
            return 1
        print("índice de memória: ok (topo + subíndices consistentes)")
        return 0
    if a.modo == "citacoes":
        mortas = citacoes_mortas(proj)
        if mortas:
            print(f"citações mortas ({len(mortas)}) — caminho citado em memória/spec que não existe no projeto nem no kit:")
            for onde, cit in mortas:
                print(f"  - {onde}: `{cit}`")
            print("corrija o caminho, ou marque a memória `obsoleta:` se o que ela descreve não existe mais.")
            return 1
        print("citações: ok (todo caminho citado em memory/ e docs/specs/ existe)")
        return 0
    if a.modo == "fila":
        f = fila(memdir)
        print(f"memórias sem `gatilho:` ({len(f['sem_gatilho'])}):")
        for n in f["sem_gatilho"]:
            print("  -", n)
        print(f"famílias sem frase de gatilho no topo ({len(f['familias_sem_frase'])}): "
              + ", ".join(f["familias_sem_frase"]))
        print(f"anotações de regra (`type: {TIPO_DE_REGRA}`) sem gatilho de ação ({len(f['sem_gatilho_de_acao'])}) — "
              f"lista pro owner aprovar de uma vez:")
        for n in f["sem_gatilho_de_acao"]:
            print("  -", n)
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
