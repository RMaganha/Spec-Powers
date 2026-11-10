"""Somente leitura: prepara 60 casos reais (sorteio) com os 30 candidatos da busca, em 3 lotes, SEM a resposta.
A resposta fica em gabarito_lotes.json, que os ajudantes nao recebem."""
import json, random, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import avaliar, mesa, mesa2
casos = json.loads((AQUI / "casos2.json").read_text(encoding="utf-8"))
validos = [(i, k) for i, k in enumerate(casos) if mesa2.certos_de(k)]
random.seed(42)
sorteio = random.sample(validos, 60)
tabs = {}
gab, lotes = {}, [[], [], []]
for n, (i, k) in enumerate(sorteio):
    nome = k["projeto"]
    if nome not in tabs:
        tabs[nome] = mesa2.Tabela(mesa2.acervo(nome, mesa.PROJETOS[nome][0]))
    ctx = " ".join(k["ant"] + [k["pedido"]])
    ts = sorted(avaliar.toks_exatos(ctx))
    termos = [(t[:6] + "*") if len(t) > 6 else f'"{t}"' for t in ts]
    achado = tabs[nome].c.execute("SELECT arq, tipo, titulo, resumo, substr(texto,1,220) FROM n WHERE n MATCH ? "
                                  "ORDER BY bm25(n, 0,0,0,0,0, 3.0, 4.0, 2.0, 1.0) LIMIT 450", (" OR ".join(termos),)).fetchall()
    cands, vistos = [], set()
    for arq, tipo, tit, res, txt in achado:
        if arq in vistos:
            continue
        vistos.add(arq)
        trecho = " ".join((res or txt or "").split())[:170]
        cands.append((arq, f"{tipo} | {arq} | {tit[:80]} | {trecho}"))
        if len(cands) >= 30:
            break
    cid = f"c{n+1:02d}"
    gab[cid] = dict(certos=sorted(mesa2.certos_de(k)), cands=[a for a, _ in cands], projeto=nome)
    bloco = [f"## Caso {cid} (projeto {nome})"]
    for j, ant in enumerate(k["ant"]):
        bloco.append(f"Pedido anterior {j+1}: {ant[:300]}")
    bloco.append(f"PEDIDO ATUAL: {k['pedido'][:700]}")
    bloco.append("Candidatos:")
    bloco += [f"{j+1}. {linha}" for j, (_a, linha) in enumerate(cands)]
    lotes[n % 3].append("\n".join(bloco))
for j, l in enumerate(lotes, 1):
    (AQUI / f"lote{j}.md").write_text("\n\n".join(l), encoding="utf-8")
    print(f"lote{j}.md: {len(l)} casos, {(AQUI / f'lote{j}.md').stat().st_size//1024} KB")
(AQUI / "gabarito_lotes.json").write_text(json.dumps(gab, ensure_ascii=False), encoding="utf-8")
no30 = sum(1 for g in gab.values() if set(g["certos"]) & set(g["cands"]))
no10 = sum(1 for g in gab.values() if set(g["certos"]) & set(g["cands"][:10]))
no3 = sum(1 for g in gab.values() if set(g["certos"]) & set(g["cands"][:3]))
print(f"nos 60 casos: certo entre os 3 = {no3} | entre os 10 = {no10} | entre os 30 (teto) = {no30}")
