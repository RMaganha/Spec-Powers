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
import json
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
TIPO_CONTROLE = "controle"    # 1 linha por projeto, dentro da mesma tabela: a assinatura do disco na última montagem
VIGIADOS = ("CLAUDE.md", ".gitignore")   # não entram na tabela, mas mudam o nome do projeto ou o que o git enxerga
MUITOS_ARQUIVOS = 40          # acima disso o `git log` de dono e data olha as pastas, não arquivo por arquivo
LIMITE_BUSCA = 30             # linhas que a busca devolve: 30 arquivos diferentes, o assistente escolhe (decisão 18)
PESOS = "0, 0, 0, 0, 0, 0, 0, 0, 0, 3.0, 4.0, 2.0, 1.0"   # 9 colunas que não entram na busca + título, quando, resumo, texto
TETO_TITULO_DA_LINHA = 80     # letras do título na linha devolvida
TETO_TRECHO_DA_LINHA = 170    # letras do trecho na linha devolvida
PEDIDOS_NA_BUSCA = 4          # o pedido atual + os 3 anteriores do owner (decisão 17; medido: 32% → 41%)
TETO_PEDIDO = 600             # letras de cada pedido que entram na busca
PEDIDO_MINIMO = 25            # menos que isso ("ok", "pode") não é pedido que ajude a buscar
NAO_E_PEDIDO = ("<", "Caveat", "[Image", "This session", "Stop hook", "**Responda", "Base directory", "Another Claude")
RESERVA = ("vá nos arquivos: `memory/MEMORY.md` → o subíndice da família → a memória; e procure a palavra em "
           "`memory/` e `docs/`.")
RE_PALAVRA = re.compile(r"[a-z0-9]+")
RE_SESSAO = re.compile(r"^[A-Za-z0-9_-]{6,80}$")
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


def _criacao(raiz: Path, caminhos=None) -> dict:
    """arquivo → (data, autor) do commit que o criou. Vazio sem git. `caminhos` limita a pergunta a poucos
    arquivos (a atualização depois de uma gravação não precisa do histórico das pastas inteiras)."""
    saida = _git(raiz, "-c", "core.quotepath=false", "log", "--diff-filter=A", "--date=short",
                 "--format=@@%ad|%an", "--name-only", "--", *(caminhos or PASTAS + SOLTOS))
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


def assinatura_do_disco(raiz: Path) -> str:
    """Nome, tamanho e data de cada `.md`/`.html` de `memory/`, `docs/`, dos soltos e dos vigiados — SEM ler
    conteúdo e sem git. É a conferência rápida: igual à guardada na linha de controle → nada mudou."""
    raiz = Path(raiz)
    itens = []

    def anota(p: Path, rel: str):
        try:
            s = p.stat()
        except OSError:
            return
        itens.append(f"{rel}|{s.st_size}|{s.st_mtime_ns}")

    for pasta in PASTAS:
        for base, _pastas, nomes in os.walk(raiz / pasta):
            for nome in nomes:
                if nome.lower().endswith(EXTENSOES):
                    p = Path(base) / nome
                    anota(p, p.relative_to(raiz).as_posix())
    for solto in SOLTOS + VIGIADOS:
        anota(raiz / solto, solto)
    return hashlib.sha1("\n".join(sorted(itens)).encode("utf-8")).hexdigest()[:16]


def _ler_projeto(raiz: Path, usar_git: bool, criacao=None):
    """(linhas, arquivos grandes demais que ficaram fora) — cada arquivo é lido uma vez. `criacao` já pronto
    (o `montar` passa `{}` e preenche dono e data só do que mudou) evita o `git log` das pastas inteiras."""
    mi = _motor()
    raiz = Path(raiz).resolve()
    projeto, raiz_txt = nome_projeto(raiz), raiz.as_posix()
    rels = _relativos(raiz, usar_git)
    if criacao is None:
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
    gravados = dict(conn.execute("SELECT arq, min(assinatura) FROM memoria WHERE raiz = ? AND tipo <> ? GROUP BY arq",
                                 (raiz_txt, TIPO_CONTROLE)))
    novos = [a for a in grupos if a not in gravados]
    refeitos = [a for a in grupos if a in gravados and gravados[a] != grupos[a][0]["assinatura"]]
    removidos = [a for a in gravados if a not in grupos]
    return novos, refeitos, removidos, len(grupos) - len(novos) - len(refeitos)


def _dono_e_data(raiz: Path, grupos: dict, mudados: list) -> None:
    """Preenche dono e data (criação no git) só nas linhas dos arquivos novos ou refeitos."""
    criacao = _criacao(raiz, mudados if len(mudados) <= MUITOS_ARQUIVOS else None)
    for arq in mudados:
        data, dono = criacao.get(arq, ("", ""))
        for linha in grupos[arq]:
            linha["data"], linha["dono"] = linha["data"] or data, dono


def _controle(tabela: Path, raiz_txt: str):
    """Assinatura do disco guardada na última montagem deste projeto, ou None (tabela de outra versão, sem a
    linha de controle ou sem a tabela `memoria`)."""
    conn = sqlite3.connect(str(tabela), timeout=2)
    try:
        if (conn.execute("PRAGMA user_version").fetchone()[0] != VERSAO_ESQUEMA
                or not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'memoria'").fetchone()):
            return None
        achado = conn.execute("SELECT assinatura FROM memoria WHERE raiz = ? AND tipo = ? LIMIT 1",
                              (raiz_txt, TIPO_CONTROLE)).fetchone()
    finally:
        conn.close()
    return achado[0] if achado else None


def atualizar(raiz: Path, tabela: Path = None, usar_git: bool = True):
    """A tabela em dia, sem ninguém pedir: `None` quando nada mudou no disco (não lê arquivo, não chama o git);
    senão monta o que mudou e devolve o `Resultado`. Tabela ausente é montada na hora."""
    raiz = Path(raiz).resolve()
    tabela = Path(tabela) if tabela else caminho_tabela()
    if tabela.is_file() and _controle(tabela, raiz.as_posix()) == assinatura_do_disco(raiz):
        return None
    return montar(raiz, tabela, usar_git=usar_git, com_pendencias=False)


def montar(raiz: Path, tabela: Path = None, usar_git: bool = True, com_pendencias: bool = True) -> Resultado:
    raiz = Path(raiz).resolve()
    tabela = Path(tabela) if tabela else caminho_tabela()
    tabela.parent.mkdir(parents=True, exist_ok=True)
    disco = assinatura_do_disco(raiz)          # antes de ler: o que mudar durante a leitura é pego na próxima
    linhas, grandes = _ler_projeto(raiz, usar_git, criacao={})
    grupos, raiz_txt, projeto = _por_arquivo(linhas), raiz.as_posix(), nome_projeto(raiz)
    conn = _abrir(tabela)
    try:
        novos, refeitos, removidos, iguais = _diferenca(conn, raiz_txt, grupos)
        if usar_git and (novos or refeitos):
            _dono_e_data(raiz, grupos, novos + refeitos)
        for arq in refeitos + removidos:
            conn.execute("DELETE FROM memoria WHERE raiz = ? AND arq = ?", (raiz_txt, arq))
        marcas = ",".join("?" * len(COLUNAS))
        for arq in novos + refeitos:
            conn.executemany(f"INSERT INTO memoria ({','.join(COLUNAS)}) VALUES ({marcas})",
                             [tuple(l[c] for c in COLUNAS) for l in grupos[arq]])
        conn.execute("DELETE FROM memoria WHERE raiz = ? AND tipo = ?", (raiz_txt, TIPO_CONTROLE))
        conn.execute(f"INSERT INTO memoria ({','.join(COLUNAS)}) VALUES ({marcas})",
                     tuple({"projeto": projeto, "raiz": raiz_txt, "tipo": TIPO_CONTROLE, "assinatura": disco}.get(c, "")
                           for c in COLUNAS))
        conn.execute("UPDATE memoria SET projeto = ? WHERE raiz = ? AND projeto <> ?", (projeto, raiz_txt, projeto))
        conn.commit()
        por_tipo = dict(conn.execute("SELECT tipo, count(*) FROM memoria WHERE raiz = ? AND tipo <> ? GROUP BY tipo",
                                     (raiz_txt, TIPO_CONTROLE)))
    finally:
        conn.close()
    pendencias = _pendencias(raiz) if (usar_git and com_pendencias) else []
    if grandes:
        pendencias.append(f"{len(grandes)} arquivo(s) acima de 1,5 MB ficaram fora: " + ", ".join(grandes[:5]))
    return Resultado(tabela, projeto, por_tipo, len(novos), len(refeitos), len(removidos), iguais, pendencias)


# ---------------------------------------------------------------- buscar (parte 2)
# A regra de palavras e os pesos são os do teste de mesa que deu 41% entre os 10
# (`docs/analise/2026-11-10-teste-de-mesa/mesa2.py`): outra regra só entra medida (caso F-054).

def _termos(texto: str) -> list:
    """Palavras úteis do pedido (as do recall: sem acento, ≥ 4 letras, sem stopwords); palavra de mais de 6
    letras casa pelo começo. Tudo entre aspas: nada do que o owner digitou vira sintaxe da consulta."""
    palavras, _ = _motor().tokens(texto)
    return [f'"{p[:6]}"*' if len(p) > 6 else f'"{p}"' for p in sorted(palavras) if RE_PALAVRA.fullmatch(p)]


def buscar(raiz: Path, texto: str, contexto=(), tabela: Path = None, limite: int = LIMITE_BUSCA, sem_tipos=()) -> list:
    """Até `limite` achados — um por arquivo (o melhor trecho), só do projeto da raiz, do mais provável pro menos.
    `contexto` são os pedidos anteriores do owner, palavra por palavra (não se resume o pedido: medido, piora).
    Tabela ausente ou presa → `sqlite3.Error` (quem chama manda buscar nos arquivos)."""
    raiz = Path(raiz).resolve()
    tabela = Path(tabela) if tabela else caminho_tabela()
    if not tabela.is_file():
        raise sqlite3.OperationalError(f"a tabela de memória não existe em {tabela}")
    termos = _termos(" ".join([*contexto, texto]))
    if not termos:
        return []
    conn = sqlite3.connect(str(tabela), timeout=5)
    try:
        linhas = conn.execute(
            "SELECT arq, tipo, ponteiro, titulo, resumo, substr(texto, 1, 220) FROM memoria "
            f"WHERE memoria MATCH ? AND raiz = ? AND tipo <> ? ORDER BY bm25(memoria, {PESOS}) LIMIT ?",
            (" OR ".join(termos), raiz.as_posix(), TIPO_CONTROLE, limite * 15)).fetchall()
    finally:
        conn.close()
    achados, vistos = [], set()
    for arq, tipo, ponteiro, titulo, resumo, texto_da_linha in linhas:
        if arq in vistos or tipo in sem_tipos:
            continue
        vistos.add(arq)
        achados.append(dict(arq=arq, tipo=tipo, ponteiro=ponteiro, titulo=titulo,
                            trecho=" ".join((resumo or texto_da_linha or "").split())[:TETO_TRECHO_DA_LINHA]))
        if len(achados) >= limite:
            break
    return achados


def formatar(achados: list) -> str:
    """Dois blocos — Anotações (o que está em `memory/`, menos os diários) e Documentos (todo o resto) —, uma
    linha curta por arquivo: `tipo | ponteiro | título | trecho`. O assistente lê e escolhe quais abrir."""
    def bloco(nome, itens):
        linhas = [f"- {a['tipo']} | {a['ponteiro']} | {a['titulo'].replace('|', '/')[:TETO_TITULO_DA_LINHA]} | "
                  f"{a['trecho'].replace('|', '/')}" for a in itens]
        return "\n".join([f"{nome} ({len(itens)})"] + (linhas or ["(nenhuma)"]))

    anotacoes = [a for a in achados if a["tipo"] == "anotacao"]
    documentos = [a for a in achados if a["tipo"] != "anotacao"]
    return bloco("Anotações", anotacoes) + "\n\n" + bloco("Documentos", documentos)


def _pedido_do_owner(reg, minimo: int = PEDIDO_MINIMO) -> str:
    """O texto que o owner escreveu num registro da conversa, ou "" (ajudante, corpo de comando ou skill,
    retorno de hook, saída de ferramenta, resposta curta). Mesmo filtro do garimpo do teste de mesa, mais dois
    cuidados: registro `isMeta` não é do owner, e o texto colado por ele É pedido dele (caso F-053)."""
    if not isinstance(reg, dict) or reg.get("type") != "user" or reg.get("isSidechain") or reg.get("isMeta"):
        return ""
    conteudo = (reg.get("message") or {}).get("content")
    partes = [conteudo] if isinstance(conteudo, str) else [
        b.get("text", "") for b in (conteudo or []) if isinstance(b, dict) and b.get("type") == "text"]
    t = " ".join(p for p in partes if isinstance(p, str))
    args = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
    if args:
        t = args.group(1)
    t = re.sub(r"</?pasted_content[^>]*>", " ", t)
    t = " ".join(re.sub(r"<[^>]+>.*?</[^>]+>", " ", t, flags=re.S).split())
    if len(t) < minimo or t.startswith(NAO_E_PEDIDO) or "hook feedback" in t[:60] or "[mss-spec]" in t[:40]:
        return ""
    return t


def pedidos_da_conversa(arquivo, quantos: int = PEDIDOS_NA_BUSCA, teto: int = TETO_PEDIDO) -> list:
    """Os últimos `quantos` pedidos do owner nesta conversa, do mais antigo pro mais novo, cada um cortado em
    `teto` letras. O ÚLTIMO entra mesmo curto (é o pedido em curso: `/mss-spec:duvida e o deploy?`); os
    anteriores curtos ("ok", "pode seguir") ficam fora. Sem arquivo, ou com linha torta, devolve o que der."""
    textos = []
    try:
        with open(arquivo, encoding="utf-8", errors="replace") as f:
            for bruto in f:
                if '"user"' not in bruto:
                    continue
                try:
                    texto = _pedido_do_owner(json.loads(bruto), minimo=1)
                except ValueError:
                    continue
                if texto:
                    textos.append(texto)
    except (OSError, TypeError):
        return []
    if not textos:
        return []
    pedidos = [t for t in textos[:-1] if len(t) >= PEDIDO_MINIMO] + [textos[-1]]
    return [p[:teto] for p in pedidos[-quantos:]]


def arquivo_da_conversa(ambiente=None):
    """O `.jsonl` da conversa em curso (`<pasta do app>/projects/<projeto>/<sessão>.jsonl`), achado pelo número da
    sessão que o app põe no ambiente; `None` quando não dá pra saber — aí a busca usa só o texto informado."""
    ambiente = os.environ if ambiente is None else ambiente
    sessao = str(ambiente.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    if not RE_SESSAO.match(sessao):
        return None
    base = Path(ambiente.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    try:
        for pasta in base.iterdir():
            arq = pasta / f"{sessao}.jsonl"
            if arq.is_file():
                return arq
    except OSError:
        pass
    return None


def _modo_buscar(raiz: Path, tabela: Path, a) -> int:
    """0 = achou (imprime os dois blocos) · 1 = nada pra este pedido · 2 = tabela indisponível. Em 1 e 2 a saída
    diz pra ir nos arquivos: a busca nunca falha calada."""
    texto, contexto = " ".join(a.texto).strip(), []
    if not texto:
        pedidos = pedidos_da_conversa(Path(a.conversa) if a.conversa else arquivo_da_conversa())
        if not pedidos:
            print("sem texto pra buscar e sem o arquivo desta conversa: rode de novo com o pedido do owner entre "
                  f"aspas, palavra por palavra — ou {RESERVA}")
            return 1
        texto, contexto = pedidos[-1], pedidos[:-1]
    try:
        atualizar(raiz, tabela, usar_git=not a.sem_git)
        achados = buscar(raiz, texto, contexto, tabela, limite=a.limite)
    except (sqlite3.Error, OSError) as erro:
        print(f"tabela de memória indisponível ({erro}) — {RESERVA}")
        return 2
    if not achados:
        print(f"nada na tabela pra este pedido — {RESERVA}")
        return 1
    print(formatar(achados))
    print(f"\nAbra só o que servir (o ponteiro diz arquivo e linha). Nenhuma linha serve? Então {RESERVA}")
    return 0


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
        linhas = conn.execute("SELECT count(*) FROM memoria WHERE raiz = ? AND tipo <> ?",
                              (raiz_txt, TIPO_CONTROLE)).fetchone()[0]
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
    ap.add_argument("modo", choices=["montar", "status", "onde", "buscar"])
    ap.add_argument("texto", nargs="*", help="buscar: o que procurar; vazio = o último pedido do owner + os 3 anteriores")
    ap.add_argument("--conversa", default="", help="buscar: arquivo .jsonl da conversa (default: o desta sessão)")
    ap.add_argument("--limite", type=int, default=LIMITE_BUSCA, help="buscar: quantas linhas devolver (default: 30)")
    ap.add_argument("--proj", default=".", help="raiz do projeto (default: diretório atual)")
    ap.add_argument("--tabela", default="", help="arquivo da tabela (default: ~/mss-spec/memoria.sqlite3 ou MSS_MEMORIA_TABELA)")
    ap.add_argument("--sem-git", action="store_true", help="não chama o git: lê os arquivos da pasta, sem dono, data nem pendências")
    a = ap.parse_args(argv)
    raiz = Path(a.proj).resolve()
    tabela = Path(a.tabela) if a.tabela else caminho_tabela()
    if a.modo == "onde":
        print(tabela)
        return 0
    if a.modo == "buscar":
        return _modo_buscar(raiz, tabela, a)
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
