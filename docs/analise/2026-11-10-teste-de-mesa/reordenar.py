"""Somente leitura: buscar 30 e reordenar para ficar com 10 — vale a pena? Regua K3 (pedido real -> arquivo), K1 e K2.
Os casos sao divididos em duas metades (par/impar) para conferir se o ganho se repete."""
import json, math, re, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import avaliar, mesa, mesa2
casos = json.loads((AQUI / "casos2.json").read_text(encoding="utf-8"))
rad = lambda t: {x[:6] for x in avaliar.toks_exatos(t)}
R = defaultdict(lambda: defaultdict(list))

def fundir(*ordens, k=10):
    pts = Counter()
    for o in ordens:
        for i, a in enumerate(o):
            pts[a] += 1.0 / (k + i)
    return [a for a, _ in pts.most_common()]

for nome, (raiz, _c) in mesa.PROJETOS.items():
    a = mesa2.acervo(nome, raiz)
    T = mesa2.Tabela(a)
    Tesc = mesa2.Tabela(a, esconder_quando=True)
    campos = defaultdict(lambda: [set(), set(), set(), set()])
    for r in a:
        c = campos[r["arq"]]
        for i, k in enumerate(("quando", "titulo", "resumo", "texto")):
            c[i] |= rad(r[k])
    df = Counter()
    for c in campos.values():
        df.update(c[0] | c[1] | c[2] | c[3])
    N = len(campos)
    idf = lambda t: math.log(1 + N / (1 + df.get(t, 0)))

    def cobertura(q, arq, esc=False):
        g, ti, d, co = campos[arq]
        if esc and arq.startswith("memory/") and "/sessions/" not in arq:
            g = set()
        return sum(idf(t) * (4 * (t in g) + 3 * (t in ti) + 2 * (t in d) + 1 * (t in co)) for t in q)

    def jeitos(tab, larga, estreita, esc=False, sem=()):
        c30 = tab.buscar(larga, top=30, sem_tipos=sem)
        ql, qe = rad(larga), rad(estreita)
        por_cob_larga = sorted(c30, key=lambda x: -cobertura(ql, x, esc))
        por_cob_estreita = sorted(c30, key=lambda x: -cobertura(qe, x, esc))
        est = tab.buscar(estreita, top=60, sem_tipos=sem)
        pos_est = {x: i for i, x in enumerate(est)}
        por_bm_estreita = sorted(c30, key=lambda x: pos_est.get(x, 99))
        return {
            "A  10 direto (como esta)": c30[:10],
            "B  30 -> reordena por palavras raras casadas": por_cob_larga[:10],
            "C  30 -> reordena so pelo ultimo pedido": por_cob_estreita[:10],
            "D  30 -> junta a ordem original com a de palavras raras": fundir(c30, por_cob_larga)[:10],
            "E  30 -> junta a ordem original com a do ultimo pedido": fundir(c30, por_bm_estreita)[:10],
            "F  30 -> junta as tres ordens": fundir(c30, por_cob_larga, por_bm_estreita)[:10],
            "TETO  os 30 inteiros": c30,
        }
    n = 0
    for k in casos:
        if k["projeto"] != nome:
            continue
        certos = mesa2.certos_de(k)
        if not certos:
            continue
        n += 1
        ctx = " ".join(k["ant"] + [k["pedido"]])
        for rot, l in jeitos(T, ctx, k["pedido"]).items():
            p = avaliar.posicao(l, certos)
            R["K3 pedido real -> arquivo"][rot].append(p)
            R[f"K3 metade {n % 2 + 1}"][rot].append(p)
    for r in {r["arq"]: r for r in a if r["arq"].startswith("memory/") and r["tipo"] != "diario" and r["quando"].strip()}.values():
        for rot, l in jeitos(Tesc, r["quando"], r["quando"], esc=True).items():
            R["K2 descricao -> anotacao"][rot].append(avaliar.posicao(l, {r["arq"]}))
    notas = {Path(r["arq"]).stem: r["arq"] for r in a if r["arq"].startswith("memory/") and r["tipo"] != "diario"}
    ev = raiz / "docs" / "EVALS.md"
    if ev.is_file():
        for l in mesa2.ler(ev).split("\n"):
            if not re.match(r"^\|\s*F-\d+", l):
                continue
            cel = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cel) < 5:
                continue
            certos = set()
            for m in re.finditer(r"memory/([\w\-.]+)\.md|\[\[([\w\-]+)\]\]|`([\w\-]{8,})`", " ".join(cel[3:])):
                ch = m.group(1) or m.group(2) or m.group(3)
                x = notas.get(ch) or notas.get(ch.replace("-", "_")) or next((v for k2, v in notas.items() if k2.replace("_", "-").endswith(ch.replace("_", "-"))), None)
                if x:
                    certos.add(x)
            if certos:
                for rot, lst in jeitos(T, cel[2], cel[2], sem=("falha",)).items():
                    R["K1 situacao -> regra"][rot].append(avaliar.posicao(lst, certos))
for g in sorted(R):
    print(f"\n=== {g}")
    for rot, v in R[g].items():
        n = len(v)
        print(f"n={n:4d}  {rot:58s} 1o: {sum(1 for p in v if p == 1)*100//n:3d}% | ate 3: {sum(1 for p in v if p and p<=3)*100//n:3d}% | ate 10: {sum(1 for p in v if p and p<=10)*100//n:3d}% | na lista: {sum(1 for p in v if p)*100//n:3d}%")
