"""Compara estruturas de tabela contra o gabarito (somente leitura nos projetos).

E1  uma linha por anotacao: titulo, gatilho, descricao, corpo (pesos 3,4,2,1)
E1p idem, pesos iguais (1,1,1,1)
E1x idem E1, palavra exata (sem radical)
E1t idem E1, indice por pedacos de 3 letras (trigram)
E2  uma linha por TRECHO da anotacao (paragrafos / secoes), devolve a anotacao do melhor trecho
E3  E1 + coluna "nomes" (tabelas, arquivos, variaveis, comandos entre crases), peso 5
HOJE o motor atual do kit

Gabaritos:
  T1  gatilho escondido -> a propria anotacao
  T2  pedido real -> anotacoes abertas ou citadas na resposta (menos as gravadas na mesma rodada)
  REF pedidos de reforco com anotacao conhecida      BUS /mss-spec:memory buscar
"""
import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import avaliar  # noqa: E402
import mesa  # noqa: E402

toks = avaliar.toks_exatos
RE_NOME = re.compile(r"`([^`\n]{2,80})`|\b[A-Za-z]+[_.][\w.]+\b|\b[A-Z]{3,}[A-Z0-9_]*\b")


def nomes(texto: str) -> str:
    return " ".join(m.group(1) or m.group(0) for m in RE_NOME.finditer(texto))


def trechos(r: dict) -> list:
    partes = [" ".join((r["titulo"], r["gatilho"], r["descricao"]))]
    bloco = ""
    for par in re.split(r"\n\s*\n|\n(?=## )", r["corpo"]):
        par = par.strip()
        if not par:
            continue
        if len(bloco) + len(par) < 700:
            bloco = (bloco + "\n" + par).strip()
        else:
            if bloco:
                partes.append(bloco)
            bloco = par
    if bloco:
        partes.append(bloco)
    return partes


class Estrutura:
    def __init__(self, linhas, modo, esconder=()):
        self.modo = modo
        self.c = sqlite3.connect(":memory:")
        tok = "trigram" if modo == "E1t" else "unicode61 remove_diacritics 2"
        ls = []
        for r in linhas:
            r = dict(r)
            if r["tipo"] not in ("diario", "decisao", "falha"):
                for campo in esconder:
                    r[campo] = ""
            ls.append(r)
        if modo == "E2":
            self.c.execute(f"CREATE VIRTUAL TABLE n USING fts5(arquivo UNINDEXED, titulo, texto, tokenize=\"{tok}\")")
            for r in ls:
                for t in trechos(r):
                    self.c.execute("INSERT INTO n VALUES (?,?,?)", (r["arquivo"], r["titulo"], t))
            self.pesos = "0, 2.0, 1.0"
        elif modo == "E3":
            self.c.execute(f"CREATE VIRTUAL TABLE n USING fts5(arquivo UNINDEXED, titulo, gatilho, descricao, corpo, nomes, tokenize=\"{tok}\")")
            for r in ls:
                self.c.execute("INSERT INTO n VALUES (?,?,?,?,?,?)", (r["arquivo"], r["titulo"], r["gatilho"], r["descricao"],
                                                                     r["corpo"], nomes(" ".join((r["descricao"], r["corpo"])))))
            self.pesos = "0, 3.0, 4.0, 2.0, 1.0, 5.0"
        else:
            self.c.execute(f"CREATE VIRTUAL TABLE n USING fts5(arquivo UNINDEXED, titulo, gatilho, descricao, corpo, tokenize=\"{tok}\")")
            self.c.executemany("INSERT INTO n VALUES (:arquivo,:titulo,:gatilho,:descricao,:corpo)", ls)
            self.pesos = "0, 1.0, 1.0, 1.0, 1.0" if modo == "E1p" else "0, 3.0, 4.0, 2.0, 1.0"

    def buscar(self, pergunta: str, top: int = 10) -> list:
        ts = sorted(toks(pergunta))
        if self.modo == "E1t":
            ts = [t for t in ts if len(t) >= 3]
        if not ts:
            return []
        if self.modo in ("E1x", "E1t"):
            termos = [f'"{t}"' for t in ts]
        else:
            termos = [(t[:6] + "*") if len(t) > 6 else f'"{t}"' for t in ts]
        linhas = self.c.execute(f"SELECT arquivo FROM n WHERE n MATCH ? ORDER BY bm25(n, {self.pesos}) LIMIT ?",
                                (" OR ".join(termos), top * 12 if self.modo == "E2" else top)).fetchall()
        out = []
        for (a,) in linhas:
            if a not in out:
                out.append(a)
            if len(out) >= top:
                break
        return out


MODOS = ("E1", "E1p", "E1x", "E1t", "E2", "E3")


def main():
    casos = json.loads((AQUI / "casos.json").read_text(encoding="utf-8"))
    res = defaultdict(lambda: defaultdict(list))
    tempos = defaultdict(list)
    max_hoje = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    n_hoje = 0
    for nome, (raiz, _chave) in mesa.PROJETOS.items():
        linhas = mesa.linhas_do_projeto(nome, raiz)
        # T1
        alvo = [r for r in linhas if r["gatilho"].strip() and r["tipo"] not in ("diario", "decisao", "falha")]
        for modo in MODOS:
            e = Estrutura(linhas, modo, esconder=("gatilho",))
            for r in alvo:
                res["T1"][modo].append(avaliar.posicao(e.buscar(r["gatilho"]), {r["arquivo"]}))
        # T2 / REF / BUS
        ests = {m: Estrutura(linhas, m) for m in MODOS}
        meus = [k for k in casos if k["projeto"] == nome]
        for k in meus:
            certos = set(k["lidos"]) | set(k["citados"])
            if not certos or len(certos) > 6:
                continue
            grupos = ["T2"] + (["REF"] if k["reforco"] else []) + (["BUS"] if k["buscar"] else [])
            for modo, e in ests.items():
                t0 = time.perf_counter()
                p = avaliar.posicao(e.buscar(k["pedido"]), certos)
                tempos[modo].append(time.perf_counter() - t0)
                for g in grupos:
                    res[g][modo].append(p)
            if n_hoje < max_hoje or k["reforco"] or k["buscar"]:
                n_hoje += 1
                p = avaliar.posicao(avaliar.hoje(raiz, k["pedido"], 10, diario=True), certos)
                for g in grupos:
                    res[g + " (so nos casos em que HOJE foi medido)"]["HOJE"].append(p)
                    res[g + " (so nos casos em que HOJE foi medido)"]["E1"].append(avaliar.posicao(ests["E1"].buscar(k["pedido"]), certos))
    for g in sorted(res):
        print(f"\n=== {g}")
        for modo, v in res[g].items():
            print(f"n={len(v):4d}" + avaliar.placar(modo, v))
    print()
    for modo, v in tempos.items():
        v.sort()
        print(f"tempo {modo}: mediana {v[len(v)//2]*1000:.1f} ms")

    # o que os pedidos reais citam (para decidir colunas)
    c = Counter()
    for k in casos:
        t = avaliar.mesa.mi._norm(k["pedido"])
        c["total"] += 1
        c["tempo (ontem, semana passada, mes, data)"] += bool(re.search(r"\b(ontem|anteontem|semana passada|mes passado|ultim[ao]s? (dias|semanas?|mes|conversas?)|em (janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)|\d{1,2}/\d{1,2}|20\d\d-\d\d-\d\d|alguns dias|dias atras)\b", t))
        c["ambiente (homologacao, producao, dev, local, d0)"] += bool(re.search(r"\b(homolog\w*|producao|prd|prod|hml|dev|local|d0|azure)\b", t))
        c["nome tecnico (tabela, arquivo, variavel)"] += bool(re.search(r"\b[a-z]+_[a-z0-9_]+\b|\b\w+\.(py|sql|md|html|json|yaml|yml|js|css|env)\b", t))
        c["comando ou SQL"] += bool(re.search(r"\b(select|update|insert|delete|curl|git|docker|pip|az) ", t))
        c["outro projeto / outra conversa"] += bool(re.search(r"\b(outro projeto|outra conversa|conversa anterior|projeto (do|da) |no whats|transportes|mss-utils|plugin)\b", t))
    print("\n=== o que os pedidos reais citam")
    for k2, v in c.items():
        print(f"  {k2}: {v} ({v*100//c['total']}%)")


if __name__ == "__main__":
    main()
