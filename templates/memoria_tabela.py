"""memoria_tabela.py — tudo o que é memória do projeto numa tabela SQLite local (CÓPIA para busca).

Por que existe: o teste de mesa de 2026-11-10 (4 projetos, 3.046 trechos, 944 casos reais) mostrou que a
tabela com tudo o que é memória acha o arquivo certo entre os 10 em 41% dos pedidos, contra 12% do jeito
de hoje, lendo 4 vezes menos no Whats (`docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`).

Contrato:
- **o arquivo no git é o original; a tabela é cópia.** Este script SÓ LÊ o projeto e só grava a tabela.
  Apagar a tabela não perde nada: `montar` refaz;
- a tabela mora em `~/mss-spec/memoria.sqlite3` — pasta do usuário, **fora do `.claude`** (o owner vetou:
  "qualquer alteração perde") **e fora de qualquer repo** (uma por máquina, todos os projetos juntos).
  `MSS_MEMORIA_TABELA` troca o caminho (a suíte usa pra não tocar a do owner);
- **uma tabela só** (`memoria`, FTS5), com a coluna `tipo`: anotacao · diario · decisao · falha · spec ·
  plano · mapa · documento. Várias tabelas foram medidas e não ganharam;
- entra só `.md`/`.html` de `memory/`, `docs/`, `to-dolist.md` e `projeto.md` que o git do projeto enxerga
  (rastreado ou novo não ignorado). `.env`, `.txt` e trecho `<private>…</private>` nunca;
- `montar` relê só o que mudou (assinatura por arquivo), tira o que saiu do projeto e nunca toca as linhas
  de outro projeto (a chave é a raiz, não o nome da pasta);
- chamada ao git em bytes, com `timeout`; git ausente ou falhando nunca derruba o `montar`.

Uso: `python memoria_tabela.py montar|status|onde [--proj DIR] [--tabela ARQ] [--sem-git]`
"""
import argparse
import hashlib
import html
import importlib.util
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

VERSAO_ESQUEMA = 1
TETO_ARQUIVO = 1_500_000      # bytes — acima disso o arquivo é pulado e listado nas pendências
TETO_TRECHO = 6000            # caracteres por linha da tabela; seção maior vira mais de uma linha
PASTAS = ("memory", "docs")
SOLTOS = ("to-dolist.md", "projeto.md")
EXTENSOES = (".md", ".html")
COLUNAS = ("projeto", "raiz", "tipo", "classe", "arq", "ponteiro", "data", "dono", "assinatura",
           "titulo", "quando", "resumo", "texto")
INDICES_DA_MEMORIA = {"MEMORY.md", "DIARIO.md"}
NOMES_DE_MAPA = ("MAPA", "INDEX", "PROXIMO", "BACKLOG", "EM-ANDAMENTO", "FORA-DE-ESCOPO")

RE_PRIVADO = re.compile(r"(?is)<private>.*?</private>")
RE_TITULO = re.compile(r"^#{1,4}\s+\S")
RE_DECISAO = re.compile(r"^- (\d{4}-\d{2}-\d{2}) — (.*)")
RE_FALHA = re.compile(r"^\|\s*(F-\d+)")
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class Resultado:
    tabela: Path
    projeto: str
    por_tipo: dict = field(default_factory=dict)
    novos: int = 0
    refeitos: int = 0
    removidos: int = 0
    iguais: int = 0
    pendencias: list = field(default_factory=list)


@dataclass
class Situacao:
    existe: bool
    linhas: int
    mudaram: int
    mensagem: str


def _motor():
    """`memoria_indice.py` (irmão desta pasta): o mesmo parse de cabeçalho, subíndice e diário do recall."""
    if "memoria_indice" in sys.modules:
        return sys.modules["memoria_indice"]
    spec = importlib.util.spec_from_file_location("memoria_indice", Path(__file__).resolve().parent / "memoria_indice.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses (3.14) resolve anotações via sys.modules
    spec.loader.exec_module(mod)
    return mod


def caminho_tabela() -> Path:
    informado = os.environ.get("MSS_MEMORIA_TABELA", "").strip()
    return Path(informado) if informado else Path.home() / "mss-spec" / "memoria.sqlite3"


def _limpo(bruto: bytes) -> str:
    """Conteúdo sem `\\r` e sem trecho `<private>`; bytes fora de UTF-8 viram substituição, nunca exceção."""
    return RE_PRIVADO.sub(" ", bruto.decode("utf-8", "replace").replace("\r\n", "\n"))


def _texto(p: Path) -> str:
    return _limpo(p.read_bytes())


def nome_projeto(raiz: Path) -> str:
    raiz = Path(raiz)
    claude = raiz / "CLAUDE.md"
    if claude.is_file():
        for linha in _texto(claude).split("\n"):
            if linha.startswith("# "):
                nome = linha[2:].split(" — ")[0].strip()
                if nome and not nome.startswith("<"):
                    return nome
                break
    return raiz.name


def _git(raiz: Path, *args):
    """Saída do git em bytes, ou None se o git não existe, falhou ou a pasta não é repositório."""
    try:
        r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def _relativos(raiz: Path, usar_git: bool) -> list:
    rels = None
    if usar_git:
        saida = _git(raiz, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *PASTAS, *SOLTOS)
        if saida is not None:
            rels = [x for x in saida.decode("utf-8", "ignore").split("\0") if x]
    if rels is None:                       # sem git: a pasta como está (os.walk já devolve só arquivo)
        rels = [(Path(base) / nome).relative_to(raiz).as_posix()
                for pasta in PASTAS for base, _pastas, nomes in os.walk(raiz / pasta) for nome in nomes]
        rels += [s for s in SOLTOS if (raiz / s).is_file()]
        return sorted({r for r in rels if Path(r).suffix.lower() in EXTENSOES})
    # com git: o índice lista também arquivo apagado e ainda não commitado — esse não entra
    return sorted({r for r in rels if Path(r).suffix.lower() in EXTENSOES and (raiz / r).is_file()})


def arquivos_do_projeto(raiz: Path, usar_git: bool = True) -> list:
    raiz = Path(raiz).resolve()
    return [raiz / r for r in _relativos(raiz, usar_git)]


def _criacao(raiz: Path) -> dict:
    """arquivo → (data, autor) do commit que o criou. Vazio sem git."""
    saida = _git(raiz, "-c", "core.quotepath=false", "log", "--diff-filter=A", "--date=short",
                 "--format=@@%ad|%an", "--name-only", "--", *PASTAS, *SOLTOS)
    achados, atual = {}, ("", "")
    for linha in (saida or b"").decode("utf-8", "ignore").split("\n"):
        linha = linha.strip()
        if linha.startswith("@@"):
            data, _, autor = linha[2:].partition("|")
            atual = (data, autor)
        elif linha:
            achados[linha] = atual        # o log vem do mais novo pro mais velho: fica a criação
    return achados


def _pendencias(raiz: Path) -> list:
    avisos = []
    saida = _git(raiz, "status", "--porcelain", "-z", "--untracked-files=all", "--", *PASTAS, *SOLTOS)
    if saida is not None:
        mexidos = [x for x in saida.decode("utf-8", "ignore").split("\0")
                   if len(x) > 3 and Path(x[3:]).suffix.lower() in EXTENSOES]
        if mexidos:
            avisos.append(f"{len(mexidos)} arquivo(s) de memória com mudança ainda não commitada")
    adiante = _git(raiz, "rev-list", "--count", "@{u}..HEAD")
    if adiante and adiante.strip().isdigit() and int(adiante.strip()) > 0:
        avisos.append(f"{int(adiante.strip())} commit(s) ainda não publicados (publicar é ato do owner)")
    return avisos


def _secoes(texto: str) -> list:
    """(linha do título, título, texto) de cada seção `#`…`####`; o que vem antes do 1º título é "(início)"."""
    saida, titulo, inicio, corpo = [], "(início)", 1, []
    for n, linha in enumerate(texto.split("\n"), 1):
        if RE_TITULO.match(linha):
            saida.append((inicio, titulo, "\n".join(corpo).strip()))
            titulo, inicio, corpo = linha.lstrip("# ").strip(), n, []
        else:
            corpo.append(linha)
    saida.append((inicio, titulo, "\n".join(corpo).strip()))
    return [s for s in saida if s[2]]


def _html_para_md(t: str) -> str:
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", t)
    t = re.sub(r"(?is)<h[1-4][^>]*>(.*?)</h[1-4]>", lambda m: "\n## " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n", t)
    t = re.sub(r"(?i)<(br|/p|/li|/tr|/div)\b[^>]*>", "\n", t)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))


def _tipo_do_documento(rel: str) -> str:
    nome = rel.rsplit("/", 1)[-1]
    if "/specs/" in rel:
        return "spec"
    if "/plans/" in rel:
        return "plano"
    if nome.startswith(NOMES_DE_MAPA) or rel == "to-dolist.md":
        return "mapa"
    return "documento"


def _subindice(raiz: Path, rels: list, mi) -> dict:
    """arquivo da anotação → ([frases de quando usar], [ganchos]) lidos de memory/indice/*.md (ou do MEMORY.md plano)."""
    fontes = [r for r in rels if r.startswith(f"memory/{mi.SUBDIR}/")] or [r for r in rels if r == "memory/MEMORY.md"]
    achados = {}
    for rel in fontes:
        for linha in _texto(raiz / rel).split("\n"):
            m = mi.RE_ITEM.match(linha)
            if m and f"{mi.SUBDIR}/" not in m.group("arquivo"):
                frases, ganchos = achados.setdefault(Path(m.group("arquivo")).name, ([], []))
                frases.append(re.sub(r"[*`]", "", m.group("prefixo")).strip(" →-"))
                ganchos.append(m.group("resto").strip(" —-"))
    return achados


def _linhas_do_diario(raiz: Path, mi) -> dict:
    achados = {}
    indice = raiz / "memory" / "DIARIO.md"
    if indice.is_file():
        for linha in _texto(indice).split("\n"):
            m = mi.RE_LINHA_DIARIO.match(linha)
            if m:
                achados[m.group(1)] = m.group(2).strip()
                if m.group(3):
                    achados[Path(m.group(3)).stem[11:]] = m.group(2).strip()
    return achados


def linhas_do_projeto(raiz: Path, usar_git: bool = True) -> list:
    return _ler_projeto(raiz, usar_git)[0]


def _ler_projeto(raiz: Path, usar_git: bool):
    """(linhas, arquivos grandes demais que ficaram fora) — cada arquivo é lido uma vez."""
    mi = _motor()
    raiz = Path(raiz).resolve()
    projeto, raiz_txt = nome_projeto(raiz), raiz.as_posix()
    rels = _relativos(raiz, usar_git)
    criacao = _criacao(raiz) if usar_git else {}
    sub, diario = _subindice(raiz, rels, mi), _linhas_do_diario(raiz, mi)
    linhas, grandes = [], []

    def junta(tipo, classe, rel, ponteiro, titulo, quando, resumo, texto, data, assinatura):
        feito = criacao.get(rel, ("", ""))
        for i in range(0, max(len(texto), 1), TETO_TRECHO):
            linhas.append(dict(projeto=projeto, raiz=raiz_txt, tipo=tipo, classe=classe, arq=rel, ponteiro=ponteiro,
                               data=data or feito[0], dono=feito[1], assinatura=assinatura, titulo=titulo,
                               quando=quando, resumo=resumo, texto=texto[i:i + TETO_TRECHO]))

    for rel in rels:
        p = raiz / rel
        bruto = p.read_bytes()
        if len(bruto) > TETO_ARQUIVO:
            grandes.append(rel)
            continue
        partes = rel.split("/")

        def assina(extra=""):
            return hashlib.sha1(bruto + b"\0" + extra.encode("utf-8")).hexdigest()[:16]

        if partes[0] == "memory":
            if len(partes) == 2 and partes[1] not in INDICES_DA_MEMORIA and rel.endswith(".md"):
                try:
                    fm, corpo = mi.frontmatter(p), RE_PRIVADO.sub(" ", mi.corpo(p))
                except Exception:                                    # noqa: BLE001 — anotação torta não derruba a tabela
                    fm, corpo = {}, _limpo(bruto)
                frases, ganchos = sub.get(partes[1], ([], []))
                quando = " · ".join(x for x in [str(fm.get("gatilho") or "")] + frases if x)
                resumo = " · ".join(x for x in [str(fm.get("description") or "")] + ganchos if x)
                junta("anotacao", str(fm.get("type") or ""), rel, rel,
                      str(fm.get("name") or p.stem).replace("-", " ").replace("_", " "),
                      quando, resumo, corpo.strip(), "", assina(quando + "\0" + resumo))
            elif len(partes) == 3 and partes[1] == "sessions" and rel.endswith(".md"):
                slug, data = p.stem[11:], p.stem[:10]
                resumo = diario.get(slug, "")
                junta("diario", "", rel, rel, slug.replace("-", " "), "", resumo, _limpo(bruto).strip(),
                      data if RE_DATA.match(data) else "", assina(resumo))
            continue
        if rel == "docs/decisoes.md":
            for n, linha in enumerate(_limpo(bruto).split("\n"), 1):
                m = RE_DECISAO.match(linha)
                if m:
                    negrito = re.search(r"\*\*(.+?)\*\*", m.group(2))
                    junta("decisao", "", rel, f"{rel}:{n}", negrito.group(1) if negrito else m.group(2)[:100],
                          "", "", m.group(2), m.group(1), assina())
            continue
        if rel == "docs/EVALS.md":
            for n, linha in enumerate(_limpo(bruto).split("\n"), 1):
                if RE_FALHA.match(linha):
                    cel = [c.strip() for c in linha.strip().strip("|").split("|")]
                    if len(cel) >= 5:
                        data = cel[1][:10]
                        junta("falha", cel[3], rel, f"{rel}:{n}", f"{cel[0]} {cel[3]}"[:160], cel[2], "",
                              " | ".join(cel[3:]), data if RE_DATA.match(data) else "", assina())
            continue
        texto = _limpo(bruto)
        eh_html = p.suffix.lower() == ".html"
        if eh_html:
            texto = _html_para_md(texto)
        for inicio, titulo, corpo in _secoes(texto):
            junta(_tipo_do_documento(rel), "", rel, rel if eh_html else f"{rel}:{inicio}",
                  f"{p.stem} › {titulo}"[:160], "", "", corpo, "", assina())
    return linhas, grandes


def _abrir(tabela: Path):
    conn = sqlite3.connect(str(tabela), timeout=5)
    versao = conn.execute("PRAGMA user_version").fetchone()[0]
    existe = conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'memoria'").fetchone()
    if versao != VERSAO_ESQUEMA or not existe:        # é cópia: esquema diferente se refaz do zero
        conn.execute("DROP TABLE IF EXISTS memoria")
        conn.execute("CREATE VIRTUAL TABLE memoria USING fts5("
                     "projeto UNINDEXED, raiz UNINDEXED, tipo UNINDEXED, classe UNINDEXED, arq UNINDEXED, "
                     "ponteiro UNINDEXED, data UNINDEXED, dono UNINDEXED, assinatura UNINDEXED, "
                     "titulo, quando, resumo, texto, tokenize=\"unicode61 remove_diacritics 2\")")
        conn.execute(f"PRAGMA user_version = {VERSAO_ESQUEMA}")
        conn.commit()
    return conn


def _por_arquivo(linhas: list) -> dict:
    grupos = {}
    for linha in linhas:
        grupos.setdefault(linha["arq"], []).append(linha)
    return grupos


def _diferenca(conn, raiz_txt: str, grupos: dict):
    gravados = dict(conn.execute("SELECT arq, min(assinatura) FROM memoria WHERE raiz = ? GROUP BY arq", (raiz_txt,)))
    novos = [a for a in grupos if a not in gravados]
    refeitos = [a for a in grupos if a in gravados and gravados[a] != grupos[a][0]["assinatura"]]
    removidos = [a for a in gravados if a not in grupos]
    return novos, refeitos, removidos, len(grupos) - len(novos) - len(refeitos)


def montar(raiz: Path, tabela: Path = None, usar_git: bool = True) -> Resultado:
    raiz = Path(raiz).resolve()
    tabela = Path(tabela) if tabela else caminho_tabela()
    tabela.parent.mkdir(parents=True, exist_ok=True)
    linhas, grandes = _ler_projeto(raiz, usar_git)
    grupos, raiz_txt, projeto = _por_arquivo(linhas), raiz.as_posix(), nome_projeto(raiz)
    conn = _abrir(tabela)
    try:
        novos, refeitos, removidos, iguais = _diferenca(conn, raiz_txt, grupos)
        for arq in refeitos + removidos:
            conn.execute("DELETE FROM memoria WHERE raiz = ? AND arq = ?", (raiz_txt, arq))
        marcas = ",".join("?" * len(COLUNAS))
        for arq in novos + refeitos:
            conn.executemany(f"INSERT INTO memoria ({','.join(COLUNAS)}) VALUES ({marcas})",
                             [tuple(l[c] for c in COLUNAS) for l in grupos[arq]])
        conn.execute("UPDATE memoria SET projeto = ? WHERE raiz = ? AND projeto <> ?", (projeto, raiz_txt, projeto))
        conn.commit()
        por_tipo = dict(conn.execute("SELECT tipo, count(*) FROM memoria WHERE raiz = ? GROUP BY tipo", (raiz_txt,)))
    finally:
        conn.close()
    pendencias = _pendencias(raiz) if usar_git else []
    if grandes:
        pendencias.append(f"{len(grandes)} arquivo(s) acima de 1,5 MB ficaram fora: " + ", ".join(grandes[:5]))
    return Resultado(tabela, projeto, por_tipo, len(novos), len(refeitos), len(removidos), iguais, pendencias)


def _como_remontar(raiz: Path) -> str:
    return f'python "{Path(__file__).resolve()}" montar --proj "{raiz}"'


def status(raiz: Path, tabela: Path = None, usar_git: bool = True) -> Situacao:
    raiz = Path(raiz).resolve()
    tabela = Path(tabela) if tabela else caminho_tabela()
    if not tabela.is_file():
        return Situacao(False, 0, 0, f"a tabela de memória não existe em {tabela} — rode: {_como_remontar(raiz)}")
    grupos, raiz_txt = _por_arquivo(linhas_do_projeto(raiz, usar_git)), raiz.as_posix()
    conn = sqlite3.connect(str(tabela), timeout=5)
    try:
        em_dia = (conn.execute("PRAGMA user_version").fetchone()[0] == VERSAO_ESQUEMA
                  and conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'memoria'").fetchone())
        if not em_dia:
            return Situacao(True, 0, len(grupos), f"a tabela em {tabela} é de outra versão — rode: {_como_remontar(raiz)}")
        novos, refeitos, removidos, _ = _diferenca(conn, raiz_txt, grupos)
        linhas = conn.execute("SELECT count(*) FROM memoria WHERE raiz = ?", (raiz_txt,)).fetchone()[0]
    finally:
        conn.close()
    mudaram = len(novos) + len(refeitos) + len(removidos)
    if mudaram:
        return Situacao(True, linhas, mudaram,
                        f"tabela desatualizada: {mudaram} arquivo(s) mudaram desde a última montagem — rode: {_como_remontar(raiz)}")
    return Situacao(True, linhas, 0, f"tabela em dia: {linhas} linha(s) deste projeto em {tabela}")


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["montar", "status", "onde"])
    ap.add_argument("--proj", default=".", help="raiz do projeto (default: diretório atual)")
    ap.add_argument("--tabela", default="", help="arquivo da tabela (default: ~/mss-spec/memoria.sqlite3 ou MSS_MEMORIA_TABELA)")
    ap.add_argument("--sem-git", action="store_true", help="não chama o git: lê os arquivos da pasta, sem dono, data nem pendências")
    a = ap.parse_args(argv)
    raiz = Path(a.proj).resolve()
    tabela = Path(a.tabela) if a.tabela else caminho_tabela()
    if a.modo == "onde":
        print(tabela)
        return 0
    try:
        if a.modo == "status":
            s = status(raiz, tabela, usar_git=not a.sem_git)
            print(s.mensagem)
            return 0 if s.existe and not s.mudaram else 1
        r = montar(raiz, tabela, usar_git=not a.sem_git)
    except sqlite3.Error as erro:
        print(f"não consegui abrir ou gravar a tabela em {tabela} ({erro}) — ela está aberta em outro programa, "
              f"ou o arquivo não é uma tabela do kit? Nada foi alterado no projeto.")
        return 2
    print(f"tabela: {r.tabela}")
    print(f"projeto: {r.projeto} ({raiz})")
    print(f"arquivos: {r.novos} novo(s) · {r.refeitos} refeito(s) · {r.removidos} removido(s) · {r.iguais} igual(is)")
    print("linhas por tipo: " + " · ".join(f"{t} {n}" for t, n in sorted(r.por_tipo.items())))
    for aviso in r.pendencias:
        print("pendência:", aviso)
    return 0


if __name__ == "__main__":
    sys.exit(main())
