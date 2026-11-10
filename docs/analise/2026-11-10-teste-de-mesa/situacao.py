"""Somente leitura. (1) Conta as falhas registradas por tema. (2) Teste montado nelas:
pergunta = a SITUACAO da falha (coluna gatilho do EVALS); certo = a anotacao que a propria linha cita como guardrail.
Mede: a tabela (sem as linhas de EVALS, para nao achar a si mesma) x o motor de hoje (idem)."""
import re, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import avaliar, estruturas, mesa
mi = mesa.mi
TEMAS = [
    ("regra/anotacao que ja existia e nao foi usada", r"reincid|memoria (existente|existe|nao)|regra .{0,40}(ignorad|violad)|decisao (registrada|lida)|ja conhecid|nao consultad|roteiro do kit nao seguido|kit ficou de fora|fora de escopo nao|reperguntei|trabalho recente lido|sem os subindices"),
    ("afirmar sem medir / premissa / amostra pequena", r"premissa|afirm|sem medir|sem fonte|amostra|hipotese|causa afirmada|numero (de cabeca|lido)|generalizei|assumid|sem evidencia|sem ler|lido cortad|ganho vendido|ausencia no documento|medi por fora|recorte errado|verdade|declarei"),
    ("forma da resposta (longa, confusa, roteiro ruim)", r"comunica|explicacao|resposta maior|escopo inflado|forma errada|dado sem conclusao|ilegivel|roteiro (incoerente|espalhado|inteiro)|sequencia|silencio|progresso|conducao sem mapa|pedacos|owner decide sem ver|cartoes soltos|recusas"),
    ("defeito silencioso no que foi entregue", r"silencios|tela vazia|invisivel|codigo morto|regressao|robustez|corrida|mascara|tempo|parser"),
]
def tema(txt):
    t = mi._norm(txt)
    for nome, rx in TEMAS:
        if re.search(rx, t):
            return nome
    return "outros"
def hoje_sem_evals(raiz, pergunta, top):
    toks, _ = mi.tokens(pergunta)
    ach = []
    for f in mi.fontes(raiz, diario=True):
        if f.ponteiro.startswith("docs/EVALS.md"):
            continue
        ft, fi = mi.tokens(f.texto)
        com = toks & ft
        if len(com) >= mi.MINIMO_TOKENS:
            ach.append((sum(2 if t in fi else 1 for t in com), f))
    ach.sort(key=lambda x: (-x[0], x[1].prio, x[1].ponteiro))
    vistos, out = set(), []
    for _s, f in ach:
        a = getattr(f, "arquivo", None)
        if a:
            if a in vistos: continue
            vistos.add(a); out.append("memory/" + Path(a).name)
        else:
            out.append(f.ponteiro.split(" — ")[0])
        if len(out) >= top: break
    return out
cont = Counter(); res = defaultdict(list); por_tema = defaultdict(lambda: defaultdict(list)); com_acao = Counter()
for nome, (raiz, _c) in mesa.PROJETOS.items():
    ev = raiz / "docs" / "EVALS.md"
    if not ev.is_file():
        continue
    linhas = [r for r in mesa.linhas_do_projeto(nome, raiz) if r["tipo"] != "falha"]
    notas = {Path(r["arquivo"]).stem: r["arquivo"] for r in linhas if r["tipo"] not in ("diario", "decisao")}
    slug = {}
    for r in linhas:
        if r["tipo"] not in ("diario", "decisao"):
            slug[r["titulo"].replace(" ", "-")] = r["arquivo"]
    e = estruturas.Estrutura(linhas, "E1")
    mem = raiz / "memory"
    com_acao[nome] = sum(1 for p in mem.glob("*.md") if mi.frontmatter(p).get("gatilho_comando") or mi.frontmatter(p).get("gatilho_resposta"))
    for l in ev.read_text(encoding="utf-8", errors="replace").split("\n"):
        if not re.match(r"^\|\s*F-\d+", l):
            continue
        cel = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cel) < 5:
            continue
        t = tema(cel[3])
        cont[t] += 1
        certos = set()
        resto = " ".join(cel[3:])
        for m in re.finditer(r"memory/([\w\-.]+)\.md|\[\[([\w\-]+)\]\]|`([\w\-]{8,})`", resto):
            chave = m.group(1) or m.group(2) or m.group(3)
            a = notas.get(chave) or slug.get(chave) or notas.get(chave.replace("-", "_")) or next((v for k, v in notas.items() if k.endswith(chave) or k.replace("_", "-").endswith(chave)), None)
            if a:
                certos.add(a)
        if not certos:
            continue
        pt = avaliar.posicao(e.buscar(cel[2]), certos)
        ph = avaliar.posicao(hoje_sem_evals(raiz, cel[2], 10), certos)
        res["tabela"].append(pt); res["hoje"].append(ph)
        por_tema[t]["tabela"].append(pt); por_tema[t]["hoje"].append(ph)
tot = sum(cont.values())
print(f"== {tot} falhas registradas, por tema")
for k, v in cont.most_common():
    print(f"  {v:3d} ({v*100//tot}%) {k}")
print("\n== anotacoes com gatilho de ACAO (gatilho_comando/gatilho_resposta):", dict(com_acao))
print(f"\n== teste: pergunta = a situacao da falha; certo = a anotacao citada como guardrail")
for k, v in res.items():
    print(f"n={len(v):3d}" + avaliar.placar(k, v))
for t, d in por_tema.items():
    for k, v in d.items():
        print(f"  [{t[:38]:38s}] n={len(v):3d}" + avaliar.placar(k, v))
