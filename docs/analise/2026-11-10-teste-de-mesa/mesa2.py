"""mesa2.py — teste de mesa COMPLETO (somente leitura nos projetos; saidas so no scratchpad).

ACERVO por projeto (tudo o que e tratado como memoria):
  anotacoes (memory/*.md) + frase do subindice de cada uma + diarios (memory/sessions) + linha do DIARIO.md
  + decisoes (docs/decisoes.md, 1 por linha) + falhas (docs/EVALS.md, 1 por caso)
  + todo .md/.html de docs/ (specs, planos, MAPA, INDEX, historicos, demais) e to-dolist.md, por SECAO.
  Fora de proposito: .txt/.env (podem ter segredo).

GABARITOS:
  K1 situacao -> regra      : pergunta = situacao da falha (EVALS); certo = anotacao citada como guardrail
  K2 descricao -> anotacao  : pergunta = frase "quando usar" (subindice/cabecalho), ESCONDIDA da busca
  K3 pedido real -> arquivo : certo = arquivo .md/.html aberto ou citado na resposta (menos os gravados na
                              mesma rodada e menos os indices lidos por ritual na partida)

uso: python mesa2.py garimpar | python mesa2.py medir [max_hoje]
"""
import html
import json
import random
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
import minerar  # noqa: E402

mi = mesa.mi
PARTIDA = {"MAPA.md", "INDEX.md", "MEMORY.md", "DIARIO.md", "EVALS.md", "decisoes.md", "CLAUDE.md", "PROXIMO-PASSO.md"}
RE_APONT = re.compile(
    r"^(nao\b|errado|esta errado|mas |porem|por ?que|pq |como assim|de novo|novamente|ainda |falt(a|ou)|discordo|continua|nada |ja |voce (nao|esta|errou|esqueceu|deveria))"
    r"|!!|\?\?|\bnao (funcion|deu|abriu|aparece|mudou|e isso|era isso|foi isso|entend|faz sentido)|\berrad|\bequivoc|\bdiscordo|\besqueceu|\babsurd|\bnovamente\b|\bde novo\b|\bincorret|\bconfus")


def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def secoes_md(texto: str) -> list:
    out, titulo, ini, buf = [], "(inicio)", 1, []
    for n, l in enumerate(texto.split("\n"), 1):
        if re.match(r"^#{1,4}\s+\S", l):
            if buf:
                out.append((ini, titulo, "\n".join(buf)))
            titulo, ini, buf = l.lstrip("# ").strip(), n, []
        else:
            buf.append(l)
    if buf:
        out.append((ini, titulo, "\n".join(buf)))
    return out


def html_para_md(t: str) -> str:
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", t)
    t = re.sub(r"(?is)<h[1-4][^>]*>(.*?)</h[1-4]>", lambda m: "\n## " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n", t)
    t = re.sub(r"(?i)<(br|/p|/li|/tr|/div)\b[^>]*>", "\n", t)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))


def tipo_doc(rel: str) -> str:
    nome = rel.rsplit("/", 1)[-1]
    if "/specs/" in rel:
        return "spec"
    if "/plans/" in rel:
        return "plano"
    if nome.startswith(("MAPA", "INDEX", "PROXIMO", "BACKLOG", "EM-ANDAMENTO", "FORA-DE-ESCOPO")) or nome == "to-dolist.md":
        return "mapa"
    return "doc"


def acervo(nome: str, raiz: Path, com_sub=True, com_docs=True, diario_secao=False) -> list:
    rows = []
    mem = raiz / "memory"

    def add(tipo, arq, ponteiro, titulo, quando="", resumo="", texto="", data=""):
        for i in range(0, max(len(texto), 1), 5000):
            rows.append(dict(projeto=nome, tipo=tipo, arq=arq, ponteiro=ponteiro, titulo=titulo, quando=quando,
                             resumo=resumo, texto=texto[i:i + 5000], data=data))

    sub = defaultdict(lambda: [[], []])
    fontes = list((mem / "indice").glob("*.md")) if (mem / "indice").is_dir() else [mem / "MEMORY.md"]
    for s in fontes:
        if s.is_file():
            for l in ler(s).split("\n"):
                m = mi.RE_ITEM.match(l)
                if m and "indice/" not in m.group("arquivo"):
                    k = Path(m.group("arquivo")).name
                    sub[k][0].append(re.sub(r"[*`]", "", m.group("prefixo")).strip(" →-"))
                    sub[k][1].append(m.group("resto").strip(" —-"))
    for p in sorted(mem.glob("*.md")):
        if p.name in ("MEMORY.md", "DIARIO.md"):
            continue
        fm = mi.frontmatter(p)
        quando = str(fm.get("gatilho") or "")
        resumo = str(fm.get("description") or "")
        if com_sub:
            quando = " · ".join([quando] + sub[p.name][0]).strip(" ·")
        add(str(fm.get("type") or "nota"), f"memory/{p.name}", f"memory/{p.name}", str(fm.get("name") or p.stem).replace("-", " ").replace("_", " "),
            quando, resumo, mi.corpo(p))
    linha_diario = {}
    if (mem / "DIARIO.md").is_file():
        for l in ler(mem / "DIARIO.md").split("\n"):
            m = mi.RE_LINHA_DIARIO.match(l)
            if m:
                linha_diario[m.group(1)] = m.group(2)
                if m.group(3):
                    linha_diario[Path(m.group(3)).stem[11:]] = m.group(2)
    if (mem / "sessions").is_dir():
        for p in sorted((mem / "sessions").glob("*.md")):
            arq = f"memory/sessions/{p.name}"
            resumo = linha_diario.get(p.stem[11:], "") if com_sub else ""
            if diario_secao:
                for ini, tit, txt in secoes_md(ler(p)):
                    if len(txt.strip()) > 40:
                        add("diario", arq, f"{arq}:{ini}", f"{p.stem[11:].replace('-', ' ')} › {tit}", "", resumo, txt, p.stem[:10])
            else:
                add("diario", arq, arq, p.stem[11:].replace("-", " "), "", resumo, ler(p), p.stem[:10])
    dec = raiz / "docs" / "decisoes.md"
    if dec.is_file():
        for n, l in enumerate(ler(dec).split("\n"), 1):
            m = re.match(r"^- (\d{4}-\d{2}-\d{2}) — (.*)", l)
            if m:
                neg = re.search(r"\*\*(.+?)\*\*", m.group(2))
                add("decisao", "docs/decisoes.md", f"docs/decisoes.md:{n}", neg.group(1) if neg else m.group(2)[:100], "", "", m.group(2), m.group(1))
    ev = raiz / "docs" / "EVALS.md"
    if ev.is_file():
        for n, l in enumerate(ler(ev).split("\n"), 1):
            if re.match(r"^\|\s*F-\d+", l):
                cel = [c.strip() for c in l.strip().strip("|").split("|")]
                if len(cel) >= 5:
                    add("falha", "docs/EVALS.md", f"docs/EVALS.md:{n}", f"{cel[0]} {cel[3][:80]}", cel[2], "", " | ".join(cel[3:]), cel[1][:10])
    if com_docs:
        arquivos = [p for p in sorted((raiz / "docs").rglob("*")) if p.suffix.lower() in (".md", ".html") and p.is_file()]
        for extra in ("to-dolist.md", "projeto.md"):
            if (raiz / extra).is_file():
                arquivos.append(raiz / extra)
        for p in arquivos:
            rel = p.relative_to(raiz).as_posix()
            if rel in ("docs/decisoes.md", "docs/EVALS.md") or p.stat().st_size > 1_500_000:
                continue
            texto = ler(p)
            if p.suffix.lower() == ".html":
                texto = html_para_md(texto)
            for ini, tit, txt in secoes_md(texto):
                if len(txt.strip()) > 40:
                    add(tipo_doc(rel), rel, f"{rel}:{ini}" if p.suffix.lower() == ".md" else rel, f"{p.stem} › {tit}"[:160], "", "", txt)
    return rows


class Tabela:
    def __init__(self, rows, banco=":memory:", esconder_quando=False):
        self.c = sqlite3.connect(banco)
        self.c.execute("CREATE VIRTUAL TABLE n USING fts5(projeto UNINDEXED, tipo UNINDEXED, arq UNINDEXED, ponteiro UNINDEXED, "
                       "data UNINDEXED, titulo, quando, resumo, texto, tokenize=\"unicode61 remove_diacritics 2\")")
        self.c.executemany("INSERT INTO n VALUES (?,?,?,?,?,?,?,?,?)", [
            (r["projeto"], r["tipo"], r["arq"], r["ponteiro"], r["data"], r["titulo"],
             "" if (esconder_quando and r["arq"].startswith("memory/") and r["tipo"] != "diario") else r["quando"],
             r["resumo"], r["texto"]) for r in rows])
        self.c.commit()

    def buscar(self, pergunta, top=10, sem_tipos=(), linhas=False):
        ts = sorted(avaliar.toks_exatos(pergunta))
        if not ts:
            return []
        termos = [(t[:6] + "*") if len(t) > 6 else f'"{t}"' for t in ts]
        achado = self.c.execute("SELECT arq, tipo, ponteiro, titulo, resumo FROM n WHERE n MATCH ? "
                                "ORDER BY bm25(n, 0,0,0,0,0, 3.0, 4.0, 2.0, 1.0) LIMIT ?", (" OR ".join(termos), top * 15)).fetchall()
        out, vistos = [], set()
        for arq, tipo, pont, tit, res in achado:
            if tipo in sem_tipos or arq in vistos:
                continue
            vistos.add(arq)
            out.append((arq, tipo, pont, tit, res) if linhas else arq)
            if len(out) >= top:
                break
        return out


class SemTabela:
    def __init__(self, rows):
        self.rows = [(r["arq"], r["tipo"], tuple({t[:6] for t in avaliar.toks_exatos(r[k])} for k in ("quando", "titulo", "resumo", "texto"))) for r in rows]

    def buscar(self, pergunta, top=10, sem_tipos=()):
        q = {t[:6] for t in avaliar.toks_exatos(pergunta)}
        melhor = {}
        for arq, tipo, (g, ti, d, co) in self.rows:
            if tipo in sem_tipos:
                continue
            s = 4 * len(q & g) + 3 * len(q & ti) + 2 * len(q & d) + len(q & co)
            if s > melhor.get(arq, 0):
                melhor[arq] = s
        return [a for a, _s in sorted(melhor.items(), key=lambda x: -x[1])[:top]]


def hoje(raiz, pergunta, top=10, sem_evals=False):
    toks, _ = mi.tokens(pergunta)
    ach = []
    for f in mi.fontes(raiz, diario=True):
        if sem_evals and f.ponteiro.startswith("docs/EVALS.md"):
            continue
        ft, fi = mi.tokens(f.texto)
        com = toks & ft
        if len(com) >= mi.MINIMO_TOKENS:
            ach.append((sum(2 if t in fi else 1 for t in com), f))
    ach.sort(key=lambda x: (-x[0], x[1].prio, x[1].ponteiro))
    out = []
    for _s, f in ach:
        a = getattr(f, "arquivo", None)
        if a:
            arq = "memory/" + Path(a).name
        else:
            m = re.match(r"((?:memory|docs)/[\w\-./]+\.md)", f.ponteiro)
            arq = m.group(1) if m else f.ponteiro.split(" — ")[0]
        if arq not in out:
            out.append(arq)
        if len(out) >= top:
            break
    return out


# ---------------------------------------------------------------- garimpo K3
def garimpar():
    todos = []
    for nome, (raiz, chave) in mesa.PROJETOS.items():
        validos = {r["arq"] for r in acervo(nome, raiz)}
        raiz_norm = str(raiz).replace("\\", "/").lower()
        pastas = [d for d in mesa.TRANSCRICOES.iterdir() if d.is_dir() and d.name.endswith(chave)]
        n0 = len(todos)
        for arq in sorted(a for d in pastas for a in d.glob("*.jsonl")):
            atual, hist = None, []

            def fechar():
                if atual:
                    for k in ("lidos", "citados"):
                        atual[k] = [x for x in atual[k] if x not in atual["escritos"]]
                    todos.append(atual)
                    hist.append(atual["pedido"][:600])

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
                        t = minerar.texto_user(conteudo)
                        args = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
                        if args:
                            t = args.group(1)
                        t = re.sub(r"<[^>]+>.*?</[^>]+>", " ", t, flags=re.S)
                        t = " ".join(t.split())
                        if len(t) < 25 or t.startswith(minerar.PULAR) or "hook feedback" in t[:60] or "[mss-spec]" in t[:40]:
                            continue
                        fechar()
                        tn = minerar.norm(t[:700])
                        atual = dict(projeto=nome, conversa=arq.stem[:8], pedido=t[:1500], ant=hist[-3:], lidos=[], citados=[], escritos=[],
                                     pergunta="?" in t, apont=bool(RE_APONT.search(tn)), reforco=bool(minerar.FORTE.search(tn)))
                    elif reg.get("type") == "assistant" and atual:
                        for b in conteudo or []:
                            if not isinstance(b, dict):
                                continue
                            if b.get("type") == "tool_use" and b.get("name") in ("Read", "Write", "Edit"):
                                p = str(b.get("input", {}).get("file_path", "")).replace("\\", "/")
                                i = p.lower().find(raiz_norm)
                                if i < 0:
                                    continue
                                rel = p[i + len(raiz_norm):].lstrip("/")
                                if b["name"] == "Read":
                                    if rel in validos and rel not in atual["lidos"]:
                                        atual["lidos"].append(rel)
                                else:
                                    atual["escritos"].append(rel)
                            elif b.get("type") == "text":
                                for c in re.findall(r"(?:memory|docs)/[\w\-./]+?\.(?:md|html)|to-dolist\.md", b.get("text", "")):
                                    if c in validos and c not in atual["citados"]:
                                        atual["citados"].append(c)
            fechar()
        print(f"{nome}: {len(todos) - n0} pedidos")
    (AQUI / "casos2.json").write_text(json.dumps(todos, ensure_ascii=False), encoding="utf-8")


def certos_de(k):
    c = {a for a in set(k["lidos"]) | set(k["citados"])
         if a.rsplit("/", 1)[-1] not in PARTIDA and not a.startswith("memory/indice/")}
    return c if 0 < len(c) <= 6 else set()


# ---------------------------------------------------------------- medir
def medir(max_hoje: int):
    casos = json.loads((AQUI / "casos2.json").read_text(encoding="utf-8"))
    random.seed(5)
    R = defaultdict(lambda: defaultdict(list))
    par = Counter()
    custo = {}
    todas = []
    for nome, (raiz, _chave) in mesa.PROJETOS.items():
        t0 = time.perf_counter()
        a_mem = acervo(nome, raiz, com_sub=False, com_docs=False)
        a_sub = acervo(nome, raiz, com_sub=True, com_docs=False)
        a_tudo = acervo(nome, raiz)
        a_sec = acervo(nome, raiz, diario_secao=True)
        todas.extend(a_tudo)
        T = {"so anotacoes": Tabela(a_mem), "+ subindice": Tabela(a_sub), "+ tudo": Tabela(a_tudo), "+ tudo, diario por secao": Tabela(a_sec)}
        PY = SemTabela(a_tudo)
        print(f"\n################ {nome}: linhas so anotacoes {len(a_mem)} | com tudo {len(a_tudo)} | por tipo {dict(Counter(r['tipo'] for r in a_tudo))} | {time.perf_counter()-t0:.1f}s")

        # ---- K2
        esc_mem, esc_tudo = Tabela(a_sub, esconder_quando=True), Tabela(a_tudo, esconder_quando=True)
        for r in {r["arq"]: r for r in a_sub if r["arq"].startswith("memory/") and r["tipo"] != "diario" and r["quando"].strip()}.values():
            R["K2 descricao->anotacao"]["tabela so anotacoes"].append(avaliar.posicao(esc_mem.buscar(r["quando"]), {r["arq"]}))
            R["K2 descricao->anotacao"]["tabela com tudo"].append(avaliar.posicao(esc_tudo.buscar(r["quando"]), {r["arq"]}))

        # ---- K1
        notas = {Path(r["arq"]).stem: r["arq"] for r in a_sub if r["arq"].startswith("memory/") and r["tipo"] != "diario"}
        ev = raiz / "docs" / "EVALS.md"
        if ev.is_file():
            for l in ler(ev).split("\n"):
                if not re.match(r"^\|\s*F-\d+", l):
                    continue
                cel = [c.strip() for c in l.strip().strip("|").split("|")]
                if len(cel) < 5:
                    continue
                certos = set()
                for m in re.finditer(r"memory/([\w\-.]+)\.md|\[\[([\w\-]+)\]\]|`([\w\-]{8,})`", " ".join(cel[3:])):
                    ch = m.group(1) or m.group(2) or m.group(3)
                    a = notas.get(ch) or notas.get(ch.replace("-", "_")) or next((v for k2, v in notas.items() if k2.replace("_", "-").endswith(ch.replace("_", "-"))), None)
                    if a:
                        certos.add(a)
                if not certos:
                    continue
                g = "K1 situacao->regra"
                ph = avaliar.posicao(hoje(raiz, cel[2], sem_evals=True), certos)
                R[g]["hoje"].append(ph)
                for rot, t in T.items():
                    R[g]["tabela " + rot].append(avaliar.posicao(t.buscar(cel[2], sem_tipos=("falha",)), certos))
                pt = R[g]["tabela + tudo"][-1]
                par[("K1", bool(ph), bool(pt))] += 1

        # ---- K3
        meus = [k for k in casos if k["projeto"] == nome and certos_de(k)]
        amostra_hoje = set(random.sample(range(len(meus)), min(max_hoje, len(meus))))
        bytes_saida = []
        for i, k in enumerate(meus):
            certos = certos_de(k)
            so_mem = all(a.startswith("memory/") for a in certos)
            grupos = ["K3 todos", "K3 gabarito so em anotacoes/diarios" if so_mem else "K3 gabarito inclui documentos"]
            if k["pergunta"] or k["apont"]:
                grupos.append("K3 perguntas e apontamentos")
            if k["reforco"]:
                grupos.append("K3 reforcos")
            ctx = " ".join(k["ant"] + [k["pedido"]])
            res = {
                "tabela so anotacoes": T["so anotacoes"].buscar(k["pedido"]),
                "tabela + subindice": T["+ subindice"].buscar(k["pedido"]),
                "tabela + tudo": T["+ tudo"].buscar(k["pedido"]),
                "tabela + tudo, com contexto": T["+ tudo"].buscar(ctx),
                "tabela + tudo, diario por secao, com contexto": T["+ tudo, diario por secao"].buscar(ctx),
                "sem tabela + tudo, com contexto": PY.buscar(ctx),
            }
            if i in amostra_hoje:
                res["hoje"] = hoje(raiz, k["pedido"])
                res["hoje, com contexto"] = hoje(raiz, ctx)
            for g in grupos + [f"K3 projeto {nome}"]:
                for rot, lista in res.items():
                    R[g][rot].append(avaliar.posicao(lista, certos))
            if "hoje" in res:
                par[("K3", bool(avaliar.posicao(res["hoje, com contexto"], certos)), bool(avaliar.posicao(res["tabela + tudo, com contexto"], certos)))] += 1
            if i % 7 == 0:
                linhas = T["+ tudo"].buscar(ctx, linhas=True)
                bytes_saida.append(sum(len(f"{p} | {tp} | {ti[:80]} | {(rs or '')[:110]}\n".encode()) for _a, tp, p, ti, rs in linhas))
        mem = raiz / "memory"
        subs = [p.stat().st_size for p in (mem / "indice").glob("*.md")] if (mem / "indice").is_dir() else [0]
        notas_tam = sorted(p.stat().st_size for p in mem.glob("*.md") if p.name not in ("MEMORY.md", "DIARIO.md"))
        custo[nome] = ((mem / "MEMORY.md").stat().st_size, sum(subs) // max(len(subs), 1), notas_tam[len(notas_tam) // 2],
                       sum(bytes_saida) // max(len(bytes_saida), 1))

    print("\n================ RESULTADOS (acerto = arquivo certo entre os N primeiros)")
    for g in sorted(R):
        print(f"\n=== {g}")
        for rot, v in R[g].items():
            print(f"n={len(v):4d}" + avaliar.placar(rot, v))
    print("\n=== comparacao caso a caso (ate 10): hoje x tabela com tudo")
    for chave in ("K1", "K3"):
        print(f"  {chave}: os dois acham {par[(chave, True, True)]} | so a tabela {par[(chave, False, True)]} | so o de hoje {par[(chave, True, False)]} | nenhum {par[(chave, False, False)]}")
    print("\n=== custo de leitura por consulta (bytes): hoje = MEMORY.md + subindice medio + anotacao | busca = 10 linhas + anotacao")
    for nome, (topo, subm, nota, saida) in custo.items():
        print(f"  {nome}: hoje {topo + subm + nota} ({topo}+{subm}+{nota}) | busca {saida + nota} ({saida}+{nota})")
    banco = AQUI / "acervo_completo.sqlite3"
    if banco.exists():
        banco.unlink()
    t0 = time.perf_counter()
    t = Tabela(todas, banco=str(banco))
    dt = time.perf_counter() - t0
    t1 = time.perf_counter()
    for k in casos[:200]:
        t.buscar(k["pedido"])
    print(f"\n=== tabela completa dos 4 projetos: {len(todas)} linhas | gravar {dt:.1f}s | arquivo {banco.stat().st_size//1024} KB | busca {((time.perf_counter()-t1)/200)*1000:.1f} ms")


if __name__ == "__main__":
    if sys.argv[1] == "garimpar":
        garimpar()
    else:
        medir(int(sys.argv[2]) if len(sys.argv) > 2 else 120)
