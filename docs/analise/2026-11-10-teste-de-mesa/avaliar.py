"""Revisao do teste de mesa, com gabarito (somente leitura nos projetos).

TESTE 1 — "achar pela descricao da situacao": para cada anotacao que tem o campo `gatilho`
  (quando usar), a pergunta e o proprio gatilho e o campo gatilho fica ESCONDIDO da busca.
  A anotacao certa e conhecida. Mede em que posicao ela aparece. (O jeito de hoje nao entra:
  ele indexa justamente o gatilho.)
TESTE 2 — "o que foi aberto de verdade": para cada pedido real das conversas, o gabarito sao as
  anotacoes que o assistente abriu (Read) logo depois daquele pedido. Vies conhecido: nessas
  conversas o jeito de hoje ja sugeria anotacoes, o que favorece o jeito de hoje.
"""
import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import mesa  # noqa: E402

mi = mesa.mi
MAX_T2 = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 60


def toks_exatos(texto: str) -> set:
    t, _ = mi.tokens(texto)
    return {x for x in t if re.fullmatch(r"[a-z0-9]+", x)}


class Indice:
    """Tabela FTS5 em memoria de um projeto + pre-calculo para a busca sem banco."""

    def __init__(self, linhas: list, esconder=()):
        self.linhas = []
        for r in linhas:
            r = dict(r)
            for campo in esconder:
                if r["tipo"] not in ("diario", "decisao", "falha"):
                    r[campo] = ""
            self.linhas.append(r)
        self.c = sqlite3.connect(":memory:")
        self.c.execute("CREATE VIRTUAL TABLE nota USING fts5(arquivo UNINDEXED, titulo, gatilho, descricao, corpo, "
                       "tokenize=\"unicode61 remove_diacritics 2\")")
        self.c.executemany("INSERT INTO nota VALUES (:arquivo,:titulo,:gatilho,:descricao,:corpo)", self.linhas)
        self.rad = [tuple({t[:6] for t in toks_exatos(r[k])} for k in ("gatilho", "titulo", "descricao", "corpo"))
                    for r in self.linhas]
        self.df = Counter()
        for r in self.linhas:
            self.df.update({t[:6] for t in toks_exatos(" ".join((r["titulo"], r["gatilho"], r["descricao"], r["corpo"])))})

    def raras(self, pergunta: str, k: int) -> list:
        ts = [t for t in toks_exatos(pergunta) if self.df.get(t[:6])]
        ts.sort(key=lambda t: (self.df[t[:6]], t))
        return ts[:k]

    def fts(self, toks, radical: bool, top: int) -> list:
        toks = sorted(toks)
        if not toks:
            return []
        termos = [(t[:6] + "*") if (radical and len(t) > 6) else f'"{t}"' for t in toks]
        return [x[0] for x in self.c.execute(
            "SELECT arquivo FROM nota WHERE nota MATCH ? ORDER BY bm25(nota, 0, 3.0, 4.0, 2.0, 1.0) LIMIT ?",
            (" OR ".join(termos), top))]

    def python(self, toks, top: int) -> list:
        q = {t[:6] for t in toks}
        pontos = []
        for r, (g, ti, d, co) in zip(self.linhas, self.rad):
            s = 4 * len(q & g) + 3 * len(q & ti) + 2 * len(q & d) + len(q & co)
            if s:
                pontos.append((s, r["arquivo"]))
        pontos.sort(key=lambda x: -x[0])
        return [a for _s, a in pontos[:top]]


def posicao(lista: list, certos: set):
    for i, a in enumerate(lista, 1):
        if a in certos:
            return i
    return None


def placar(nome: str, posicoes: list) -> str:
    n = len(posicoes) or 1
    em = lambda k: sum(1 for p in posicoes if p and p <= k)  # noqa: E731
    return f"  {nome:34s} 1o: {em(1)*100//n:3d}% | ate 3: {em(3)*100//n:3d}% | ate 10: {em(10)*100//n:3d}% | nao achou: {sum(1 for p in posicoes if not p)*100//n:3d}%"


# ---------------------------------------------------------------- hoje (A), devolvendo o arquivo
def hoje(raiz: Path, pergunta: str, top: int, diario: bool) -> list:
    toks, _ = mi.tokens(pergunta)
    if len(toks) < mi.MINIMO_TOKENS:
        return []
    achados = []
    for f in mi.fontes(raiz, diario=diario):
        ftoks, fids = mi.tokens(f.texto)
        comum = toks & ftoks
        if len(comum) < mi.MINIMO_TOKENS:
            continue
        achados.append((sum(2 if t in fids else 1 for t in comum), f))
    achados.sort(key=lambda x: (-x[0], x[1].prio, x[1].ponteiro))
    vistos, out = set(), []
    for _s, f in achados:
        arq = getattr(f, "arquivo", None)
        if arq:
            if arq in vistos:
                continue
            vistos.add(arq)
            out.append("memory/" + Path(arq).name)
        else:
            m = re.match(r"(memory/sessions/\S+\.md)", f.ponteiro)
            out.append(m.group(1) if m else f.ponteiro.split(" — ")[0])
        if len(out) >= top:
            break
    return out


# ---------------------------------------------------------------- gabarito do teste 2
def casos_reais(chave: str, raiz: Path, existentes: set, maximo: int) -> list:
    casos = []
    pastas = [d for d in mesa.TRANSCRICOES.iterdir() if d.is_dir() and d.name.endswith(chave)]
    arquivos = sorted((a for d in pastas for a in d.glob("*.jsonl")), key=lambda a: -a.stat().st_mtime)
    raiz_norm = str(raiz).replace("\\", "/").lower()
    for arq in arquivos:
        pedido, abertos = None, set()

        def fechar():
            if pedido and abertos:
                casos.append((pedido, set(abertos)))

        with open(arq, encoding="utf-8", errors="replace") as f:
            for bruto in f:
                try:
                    reg = json.loads(bruto)
                except ValueError:
                    continue
                if reg.get("isSidechain"):
                    continue
                conteudo = reg.get("message", {}).get("content")
                if reg.get("type") == "user":
                    partes = [conteudo] if isinstance(conteudo, str) else [
                        b.get("text", "") for b in (conteudo or []) if isinstance(b, dict) and b.get("type") == "text"]
                    t = " ".join(partes)
                    m = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
                    if m:
                        t = m.group(1)
                    t = re.sub(r"<[^>]+>.*?</[^>]+>", " ", t, flags=re.S)
                    t = " ".join(t.split())
                    if (len(t) >= 30 and not t.startswith(("<", "Caveat", "[Image", "This session", "Stop hook", "**Responda", "Base directory", "Another Claude"))
                            and "hook feedback" not in t[:60]):
                        fechar()
                        pedido, abertos = t[:1500], set()
                elif reg.get("type") == "assistant" and pedido:
                    for b in conteudo or []:
                        if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Read":
                            p = str(b.get("input", {}).get("file_path", "")).replace("\\", "/")
                            if raiz_norm in p.lower() and "/memory/" in p and p.endswith(".md"):
                                rel = p[p.lower().index("/memory/") + 1:]
                                if rel in existentes:
                                    abertos.add(rel)
        fechar()
        if len(casos) >= maximo:
            break
    return casos[:maximo]


def main():
    geral1, geral2 = defaultdict(list), defaultdict(list)
    for nome, (raiz, chave) in mesa.PROJETOS.items():
        linhas = mesa.linhas_do_projeto(nome, raiz)
        print(f"\n################ {nome} ({len(linhas)} linhas)")

        # ---------- TESTE 1
        for rotulo, esconder in (("gatilho escondido", ("gatilho",)), ("gatilho e descricao escondidos", ("gatilho", "descricao"))):
            ind = Indice(linhas, esconder)
            alvo = [r for r in linhas if r["gatilho"].strip() and r["tipo"] not in ("diario", "decisao", "falha")]
            res = defaultdict(list)
            for r in alvo:
                q, certo = r["gatilho"], {r["arquivo"]}
                t = toks_exatos(q)
                res["tabela, palavra exata"].append(posicao(ind.fts(t, False, 10), certo))
                res["tabela, por radical"].append(posicao(ind.fts(t, True, 10), certo))
                res["tabela, 5 palavras mais raras"].append(posicao(ind.fts(ind.raras(q, 5), True, 10), certo))
                res["sem tabela (python)"].append(posicao(ind.python(t, 10), certo))
            print(f"TESTE 1 — {rotulo}: {len(alvo)} casos")
            for k, v in res.items():
                print(placar(k, v))
                geral1[(rotulo, k)].extend(v)

        # ---------- TESTE 2
        ind = Indice(linhas)
        existentes = {r["arquivo"] for r in linhas}
        casos = casos_reais(chave, raiz, existentes, MAX_T2)
        res = defaultdict(list)
        t0 = time.perf_counter()
        for pedido, certos in casos:
            t = toks_exatos(pedido)
            res["hoje (como o aviso automatico)"].append(posicao(hoje(raiz, pedido, 10, diario=False), certos))
            res["hoje (com diario)"].append(posicao(hoje(raiz, pedido, 10, diario=True), certos))
            res["tabela, frase inteira"].append(posicao(ind.fts(t, True, 10), certos))
            res["tabela, 5 palavras mais raras"].append(posicao(ind.fts(ind.raras(pedido, 5), True, 10), certos))
            res["tabela, 8 palavras mais raras"].append(posicao(ind.fts(ind.raras(pedido, 8), True, 10), certos))
            res["sem tabela (python)"].append(posicao(ind.python(t, 10), certos))
        print(f"TESTE 2 — pedidos reais com anotacao aberta em seguida: {len(casos)} casos ({time.perf_counter()-t0:.0f} s)")
        for k, v in res.items():
            print(placar(k, v))
            geral2[k].extend(v)

    print("\n================ TODOS OS PROJETOS")
    for (rotulo, k), v in geral1.items():
        print(f"T1 {rotulo:32s} n={len(v)}" + placar(k, v))
    for k, v in geral2.items():
        print(f"T2 n={len(v)}" + placar(k, v))


if __name__ == "__main__":
    main()
