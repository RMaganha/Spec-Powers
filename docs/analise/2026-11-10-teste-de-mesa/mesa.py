"""Teste de mesa (somente leitura nos projetos; a tabela de teste nasce no scratchpad).

Compara, com pedidos reais do owner (1a fala das conversas recentes de cada projeto):
  A = recall de hoje do kit (memoria_indice.casar: nome/descricao/gatilho + linhas de indice/decisao/EVALS)
  B = tabela SQLite com busca por palavras (FTS5), palavra exata        -> B1
      idem, por radical (6 letras + *)                                  -> B2
  C = sem banco: pontuacao em Python direto nos arquivos (radical de 6 letras)
"""
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
KIT = Path(r"C:\Ronaldo\_Mitsui\Python\Spec-Powers")
sys.path.insert(0, str(KIT / "templates"))
import memoria_indice as mi  # noqa: E402

PROJETOS = {
    "kit": (KIT, "Spec-Powers"),
    "whats": (Path(r"C:\Ronaldo\_Mitsui\Python\IA Bot Agent\IA Bot Agent - Whats"), "IA-Bot-Agent---Whats"),
    "transportes": (Path(r"C:\Ronaldo\_Mitsui\Python\Transportes\V2"), "Transportes-V2"),
    "mss-utils": (Path(r"C:\Ronaldo\_Mitsui\Python\MSS-UTILS"), "MSS-UTILS"),
}
TRANSCRICOES = Path.home() / ".claude" / "projects"
POR_PROJETO = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 6


# ---------------------------------------------------------------- coleta
def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def linhas_do_projeto(nome: str, raiz: Path) -> list:
    out = []
    mem = raiz / "memory"
    for p in sorted(mem.glob("*.md")):
        if p.name in ("MEMORY.md", "DIARIO.md"):
            continue
        fm = mi.frontmatter(p)
        out.append(dict(projeto=nome, tipo=str(fm.get("type") or "-"), arquivo=f"memory/{p.name}",
                        titulo=str(fm.get("name") or p.stem).replace("-", " "),
                        gatilho=str(fm.get("gatilho") or ""), descricao=str(fm.get("description") or ""),
                        corpo=mi.corpo(p), data=""))
    ses = mem / "sessions"
    if ses.is_dir():
        for p in sorted(ses.glob("*.md")):
            out.append(dict(projeto=nome, tipo="diario", arquivo=f"memory/sessions/{p.name}",
                            titulo=p.stem[11:].replace("-", " "), gatilho="", descricao="",
                            corpo=ler(p), data=p.stem[:10]))
    dec = raiz / "docs" / "decisoes.md"
    if dec.is_file():
        for n, l in enumerate(ler(dec).split("\n"), 1):
            m = re.match(r"^- (\d{4}-\d{2}-\d{2}) — (.*)", l)
            if m:
                negrito = re.search(r"\*\*(.+?)\*\*", m.group(2))
                out.append(dict(projeto=nome, tipo="decisao", arquivo=f"docs/decisoes.md:{n}",
                                titulo=negrito.group(1) if negrito else m.group(2)[:100], gatilho="",
                                descricao="", corpo=m.group(2), data=m.group(1)))
    ev = raiz / "docs" / "EVALS.md"
    if ev.is_file():
        for n, l in enumerate(ler(ev).split("\n"), 1):
            m = re.match(r"^\|\s*(F-\d+)", l)
            if m:
                cel = [c.strip() for c in l.strip("|").split("|")]
                out.append(dict(projeto=nome, tipo="falha", arquivo=f"docs/EVALS.md:{n}", titulo=m.group(1),
                                gatilho="", descricao=cel[2] if len(cel) > 2 else "", corpo=l, data=""))
    return out


def pedidos_reais(pasta_chave: str, quantos: int) -> list:
    achados = []
    pastas = [d for d in TRANSCRICOES.iterdir() if d.is_dir() and d.name.endswith(pasta_chave)]
    arquivos = sorted((a for d in pastas for a in d.glob("*.jsonl")), key=lambda a: -a.stat().st_mtime)
    for arq in arquivos:
        texto = ""
        with open(arq, encoding="utf-8", errors="replace") as f:
            for bruto in f:
                try:
                    reg = json.loads(bruto)
                except ValueError:
                    continue
                if reg.get("type") != "user" or reg.get("isSidechain"):
                    continue
                c = reg.get("message", {}).get("content")
                partes = [c] if isinstance(c, str) else [b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text"]
                t = " ".join(partes)
                m = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
                if m:
                    t = m.group(1)
                t = re.sub(r"<[^>]+>.*?</[^>]+>", " ", t, flags=re.S)
                t = " ".join(t.split())
                if len(t) >= 30 and not t.startswith(("<", "Caveat", "[Image", "This session")):
                    texto = t[:400]
                    break
        if texto and texto not in achados:
            achados.append(texto)
        if len(achados) >= quantos:
            break
    return achados


# ---------------------------------------------------------------- B: SQLite + FTS5
def montar(banco: Path, linhas: list) -> float:
    if banco.exists():
        banco.unlink()
    t0 = time.perf_counter()
    c = sqlite3.connect(banco)
    c.execute("CREATE VIRTUAL TABLE nota USING fts5(projeto UNINDEXED, tipo UNINDEXED, arquivo UNINDEXED, "
              "data UNINDEXED, titulo, gatilho, descricao, corpo, tokenize=\"unicode61 remove_diacritics 2\")")
    c.executemany("INSERT INTO nota VALUES (:projeto,:tipo,:arquivo,:data,:titulo,:gatilho,:descricao,:corpo)", linhas)
    c.commit()
    c.close()
    return time.perf_counter() - t0


def palavras(pergunta: str) -> list:
    toks, _ = mi.tokens(pergunta)
    return sorted(t for t in toks if re.fullmatch(r"[a-z0-9]+", t))


def buscar_fts(c, pergunta: str, projeto, radical: bool, top: int = 3) -> list:
    toks = palavras(pergunta)
    if not toks:
        return []
    termos = [(t[:6] + "*") if (radical and len(t) > 6) else f'"{t}"' for t in toks]
    sql = ("SELECT projeto, tipo, arquivo FROM nota WHERE nota MATCH ? "
           + ("AND projeto = ? " if projeto else "")
           + "ORDER BY bm25(nota, 0, 0, 0, 0, 3.0, 4.0, 2.0, 1.0) LIMIT ?")
    args = [" OR ".join(termos)] + ([projeto] if projeto else []) + [top]
    return c.execute(sql, args).fetchall()


# ---------------------------------------------------------------- C: sem banco
def radicais(texto: str) -> set:
    toks, _ = mi.tokens(texto)
    return {t[:6] for t in toks}


def buscar_python(linhas: list, pergunta: str, top: int = 3) -> list:
    q = radicais(pergunta)
    pontos = []
    for r in linhas:
        s = (4 * len(q & radicais(r["gatilho"])) + 3 * len(q & radicais(r["titulo"]))
             + 2 * len(q & radicais(r["descricao"])) + 1 * len(q & radicais(r["corpo"])))
        if s:
            pontos.append((s, r))
    pontos.sort(key=lambda x: -x[0])
    return [(r["projeto"], r["tipo"], r["arquivo"]) for _s, r in pontos[:top]]


def curto(trio) -> str:
    _p, tipo, arq = trio
    return f"[{tipo[:4]}] {arq.replace('memory/', '').replace('sessions/', 's/')[:58]}"


def main():
    todas, por_proj = [], {}
    t0 = time.perf_counter()
    for nome, (raiz, _chave) in PROJETOS.items():
        por_proj[nome] = linhas_do_projeto(nome, raiz)
        todas.extend(por_proj[nome])
    t_leitura = time.perf_counter() - t0
    banco = AQUI / "teste_memoria.sqlite3"
    t_montar = montar(banco, todas)
    print(f"linhas na tabela: {len(todas)} | por projeto: { {k: len(v) for k, v in por_proj.items()} }")
    print(f"ler os arquivos: {t_leitura*1000:.0f} ms | gravar a tabela: {t_montar*1000:.0f} ms | arquivo: {banco.stat().st_size//1024} KB")

    c = sqlite3.connect(banco)
    tempos = {"A": [], "B": [], "C": []}
    resumo = {"A_vazio": 0, "B1_vazio": 0, "B2_vazio": 0, "C_vazio": 0, "total": 0, "B2_igual_C_top1": 0, "A_top1_em_B2": 0}
    for nome, (raiz, chave) in PROJETOS.items():
        print(f"\n################ {nome}")
        for pedido in pedidos_reais(chave, POR_PROJETO):
            resumo["total"] += 1
            print(f"\nPEDIDO: {pedido[:170]}")
            t = time.perf_counter()
            a = mi.casar(raiz, pedido, limite=3, diario=False)
            tempos["A"].append(time.perf_counter() - t)
            a_arqs = [p.ponteiro.split(" — ")[0].replace("PROCEDIMENTO ", "") for p in a]
            t = time.perf_counter()
            b1 = buscar_fts(c, pedido, nome, radical=False)
            b2 = buscar_fts(c, pedido, nome, radical=True)
            tempos["B"].append((time.perf_counter() - t) / 2)
            t = time.perf_counter()
            cc = buscar_python(por_proj[nome], pedido)
            tempos["C"].append(time.perf_counter() - t)
            print("  A hoje   :", " | ".join(x.replace("memory/", "")[:58] for x in a_arqs) or "(nada)")
            print("  B1 exata :", " | ".join(curto(x) for x in b1) or "(nada)")
            print("  B2 radic :", " | ".join(curto(x) for x in b2) or "(nada)")
            print("  C python :", " | ".join(curto(x) for x in cc) or "(nada)")
            resumo["A_vazio"] += not a
            resumo["B1_vazio"] += not b1
            resumo["B2_vazio"] += not b2
            resumo["C_vazio"] += not cc
            if b2 and cc and b2[0][2] == cc[0][2]:
                resumo["B2_igual_C_top1"] += 1
            if a_arqs and any(a_arqs[0] == x[2] for x in b2):
                resumo["A_top1_em_B2"] += 1
            outros = [x for x in buscar_fts(c, pedido, None, radical=True, top=5) if x[0] != nome]
            if outros:
                print("  outros projetos (B2, top 5 geral):", " | ".join(f"{x[0]}:{curto(x)}" for x in outros[:2]))
    print("\n================ resumo")
    print(resumo)
    for k, v in tempos.items():
        if v:
            v.sort()
            print(f"tempo {k}: mediana {v[len(v)//2]*1000:.1f} ms | pior {v[-1]*1000:.1f} ms")


if __name__ == "__main__":
    main()
