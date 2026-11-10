"""Somente leitura: UMA tabela x VARIAS tabelas (uma por tipo), na mesma regua (K1, K2, K3)."""
import json, re, sys, time
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import avaliar, mesa, mesa2
casos = json.loads((AQUI / "casos2.json").read_text(encoding="utf-8"))
GRUPO = {"feedback": "anotacao", "project": "anotacao", "reference": "anotacao", "user": "anotacao", "nota": "anotacao",
         "diario": "diario", "decisao": "decisao", "falha": "falha", "spec": "spec", "plano": "plano", "mapa": "mapa", "doc": "doc"}
ORDEM = ["anotacao", "diario", "spec", "decisao", "doc", "mapa", "falha", "plano"]
R = defaultdict(lambda: defaultdict(list)); tempo = defaultdict(list); tam = defaultdict(list)

def revezar(listas, top):
    out = []
    for i in range(top or max((len(l) for l in listas), default=0)):
        for l in listas:
            if i < len(l) and l[i] not in out:
                out.append(l[i])
    return out[:top] if top else out

for nome, (raiz, _c) in mesa.PROJETOS.items():
    a = mesa2.acervo(nome, raiz)
    def monta(esc):
        uma = mesa2.Tabela(a, esconder_quando=esc)
        por = {g: mesa2.Tabela([r for r in a if GRUPO[r["tipo"]] == g], esconder_quando=esc) for g in ORDEM if any(GRUPO[r["tipo"]] == g for r in a)}
        duas = {"mem": mesa2.Tabela([r for r in a if GRUPO[r["tipo"]] in ("anotacao", "diario", "decisao", "falha")], esconder_quando=esc),
                "doc": mesa2.Tabela([r for r in a if GRUPO[r["tipo"]] in ("spec", "plano", "mapa", "doc")], esconder_quando=esc)}
        return uma, por, duas
    def jeitos(tabs, pergunta, sem=()):
        uma, por, duas = tabs
        t0 = time.perf_counter(); r1 = uma.buscar(pergunta, sem_tipos=sem); tempo["1 tabela"].append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        l2 = [duas["mem"].buscar(pergunta, top=5, sem_tipos=sem), duas["doc"].buscar(pergunta, top=5)]
        tempo["2 tabelas"].append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        l8 = [por[g].buscar(pergunta, top=3) for g in ORDEM if g in por and g not in sem]
        tempo["8 tabelas"].append(time.perf_counter() - t0)
        return {"1 tabela, tudo misturado (10 resultados)": r1,
                "2 tabelas: anotacoes | documentos (5 + 5)": revezar(l2, 10),
                "8 tabelas, uma por tipo, revezando (10 resultados)": revezar(l8, 10),
                "8 tabelas, 3 de cada tipo (ate 24 resultados)": revezar(l8, 0)}
    normal, escond = monta(False), monta(True)
    # K2
    for r in {r["arq"]: r for r in a if r["arq"].startswith("memory/") and r["tipo"] != "diario" and r["quando"].strip()}.values():
        for rot, l in jeitos(escond, r["quando"]).items():
            R["K2 descricao -> anotacao"][rot].append(avaliar.posicao(l, {r["arq"]}))
    # K1
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
                for rot, lst in jeitos(normal, cel[2], sem=("falha",)).items():
                    R["K1 situacao -> regra"][rot].append(avaliar.posicao(lst, certos))
    # K3
    for k in casos:
        if k["projeto"] != nome:
            continue
        certos = mesa2.certos_de(k)
        if not certos:
            continue
        for rot, lst in jeitos(normal, " ".join(k["ant"] + [k["pedido"]])).items():
            R["K3 pedido real -> arquivo"][rot].append(avaliar.posicao(lst, certos))
            tam[rot].append(len(lst))
            if k["pergunta"] or k["apont"]:
                R["K3 so perguntas e apontamentos"][rot].append(avaliar.posicao(lst, certos))
for g in sorted(R):
    print(f"\n=== {g}")
    for rot, v in R[g].items():
        n = len(v)
        ach = sum(1 for p in v if p)
        print(f"n={n:4d}  {rot:52s} entre os 3: {sum(1 for p in v if p and p<=3)*100//n:3d}% | entre os 10: {sum(1 for p in v if p and p<=10)*100//n:3d}% | na lista inteira: {ach*100//n:3d}%")
print()
for k, v in tempo.items():
    v.sort(); print(f"tempo {k}: mediana {v[len(v)//2]*1000:.1f} ms")
for k, v in tam.items():
    print(f"resultados devolvidos, media: {k}: {sum(v)/len(v):.1f}")
