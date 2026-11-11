"""Régua da parte 2 da memória em tabela — mede o código ENTREGUE (`templates/memoria_tabela.py`: `montar` e
`buscar`), não o do teste de mesa. Somente leitura nos projetos; a tabela de teste e os casos ficam ao lado
deste roteiro (rode uma CÓPIA dele fora do repositório: os dados trazem pedidos reais do owner em outros
projetos — `memory/project_dados_de_outros_projetos_fora_do_repo_do_kit.md`).

Antes: `python mesa2.py garimpar` (gera `casos2.json` a partir das conversas dos 4 projetos).
Uso:   `python regua_parte2.py`

O que sai (aceite da spec, critério 19 — arquivo certo entre os N primeiros):
- K3 pedido real → arquivo: busca entregue (pedido + 3 anteriores) × só o pedido × o jeito de hoje, nos MESMOS casos;
  no total, por projeto e nas duas metades dos casos (um ganho que não se repete nas metades não é ganho);
- K1 situação da falha → anotação que a falha cita; K2 frase de "quando usar" (escondida da busca) → anotação;
- o aviso automático de 3 anotações: "entre os 3 primeiros", por projeto, hoje × tabela.
"""
import importlib.util
import json
import re
import shutil
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import mesa  # noqa: E402  (caminhos dos 4 projetos e do kit)
import mesa2  # noqa: E402  (certos_de: o gabarito do K3)

mi = mesa.mi
CORTES = (1, 3, 10, 30)


def _kit():
    spec = importlib.util.spec_from_file_location("memoria_tabela", mesa.KIT / "templates" / "memoria_tabela.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


mt = _kit()


def posicao(lista, certos):
    for i, arq in enumerate(lista, 1):
        if arq in certos:
            return i
    return None


def placar(posicoes):
    n = len(posicoes) or 1
    return " | ".join(f"até {c}: {100 * sum(1 for p in posicoes if p and p <= c) / n:5.1f}%" for c in CORTES)


class Hoje:
    """O motor de hoje (`memoria_indice.casar`), com as fontes lidas uma vez por projeto — mesma pontuação do
    `mesa2.hoje` (2 pontos por identificador, 1 por palavra; mínimo de palavras em comum; um arquivo por linha)."""

    def __init__(self, raiz, diario, sem_evals=False):
        self.fontes = []
        for f in mi.fontes(raiz, diario=diario):
            if sem_evals and f.ponteiro.startswith("docs/EVALS.md"):
                continue
            self.fontes.append((f, mi.tokens(f.texto)))

    def buscar(self, pergunta, top=30):
        toks, _ = mi.tokens(pergunta)
        achados = []
        for f, (ft, fi) in self.fontes:
            comuns = toks & ft
            if len(comuns) >= mi.MINIMO_TOKENS:
                achados.append((sum(2 if t in fi else 1 for t in comuns), f))
        achados.sort(key=lambda x: (-x[0], x[1].prio, x[1].ponteiro))
        saida = []
        for _pontos, f in achados:
            arquivo = getattr(f, "arquivo", None)
            if arquivo:
                arq = "memory/" + Path(arquivo).name
            else:
                m = re.match(r"((?:memory|docs)/[\w\-./]+\.md)", f.ponteiro)
                arq = m.group(1) if m else f.ponteiro.split(" — ")[0]
            if arq not in saida:
                saida.append(arq)
            if len(saida) >= top:
                break
        return saida


def tabela_busca(raiz, tabela, texto, contexto=(), limite=30, sem_tipos=()):
    return [a["arq"] for a in mt.buscar(raiz, texto, contexto, tabela, limite=limite, sem_tipos=sem_tipos)]


def main():
    casos = json.loads((AQUI / "casos2.json").read_text(encoding="utf-8"))
    tabela = AQUI / "regua_parte2.sqlite3"
    if tabela.exists():
        tabela.unlink()
    print("=== tabela de teste, montada pelo código entregue (só leitura nos projetos, sem git)")
    for nome, (raiz, _chave) in mesa.PROJETOS.items():
        t0 = time.perf_counter()
        r = mt.montar(raiz, tabela, usar_git=False)
        print(f"  {nome}: {sum(r.por_tipo.values())} linhas em {time.perf_counter() - t0:.1f}s | {r.por_tipo}")
    escondida = AQUI / "regua_parte2_k2.sqlite3"            # K2: a frase de "quando usar" não pode se achar sozinha
    shutil.copyfile(tabela, escondida)
    c = sqlite3.connect(str(escondida))
    c.execute("UPDATE memoria SET quando = '' WHERE tipo = 'anotacao'")
    c.commit()
    c.close()

    R = defaultdict(lambda: defaultdict(list))
    tempos = []
    for nome, (raiz, _chave) in mesa.PROJETOS.items():
        hoje_tudo, hoje_aviso = Hoje(raiz, diario=True), Hoje(raiz, diario=False)

        # ---- K3: pedido real -> arquivo aberto ou citado na resposta
        meus = [k for k in casos if k["projeto"] == nome and mesa2.certos_de(k)]
        for i, k in enumerate(meus):
            certos, ctx = mesa2.certos_de(k), " ".join(k["ant"] + [k["pedido"]])
            t0 = time.perf_counter()
            com = tabela_busca(raiz, tabela, k["pedido"], k["ant"])
            tempos.append(time.perf_counter() - t0)
            res = {
                "tabela, pedido + 3 anteriores (entregue)": com,
                "tabela, só o pedido": tabela_busca(raiz, tabela, k["pedido"]),
                "hoje, só o pedido": hoje_tudo.buscar(k["pedido"]),
                "hoje, pedido + 3 anteriores": hoje_tudo.buscar(ctx),
            }
            grupos = ["K3 todos", f"K3 projeto {nome}", f"K3 metade {'A' if i % 2 == 0 else 'B'}"]
            if not all(a.rsplit("/", 1)[-1] in mesa2.PARTIDA or a == "to-dolist.md" for a in certos):
                grupos.append("K3 sem os arquivos de rotina")
            for g in grupos:
                for rotulo, lista in res.items():
                    R[g][rotulo].append(posicao(lista, certos))
            aviso = {
                "hoje, só o pedido, sem diário (como o aviso faz)": hoje_aviso.buscar(k["pedido"], top=3),
                "hoje, pedido + 3 anteriores, sem diário": hoje_aviso.buscar(ctx, top=3),
                "tabela, pedido + 3 anteriores": com[:3],
                "tabela, só o pedido": res["tabela, só o pedido"][:3],
            }
            for rotulo, lista in aviso.items():
                R[f"AVISO {nome} (entre os 3)"][rotulo].append(posicao(lista, certos))

        # ---- K1: situação da falha -> anotação que a falha cita
        linhas = sqlite3.connect(str(tabela)).execute(
            "SELECT arq, quando FROM memoria WHERE raiz = ? AND tipo = 'anotacao'", (Path(raiz).resolve().as_posix(),)).fetchall()
        notas = {Path(arq).stem: arq for arq, _q in linhas}
        hoje_k1 = Hoje(raiz, diario=True, sem_evals=True)
        evals = raiz / "docs" / "EVALS.md"
        if evals.is_file():
            for linha in mesa2.ler(evals).split("\n"):
                if not re.match(r"^\|\s*F-\d+", linha):
                    continue
                cel = [x.strip() for x in linha.strip().strip("|").split("|")]
                if len(cel) < 5:
                    continue
                certos = set()
                for m in re.finditer(r"memory/([\w\-.]+)\.md|\[\[([\w\-]+)\]\]|`([\w\-]{8,})`", " ".join(cel[3:])):
                    ch = m.group(1) or m.group(2) or m.group(3)
                    a = notas.get(ch) or notas.get(ch.replace("-", "_")) or next(
                        (v for k2, v in notas.items() if k2.replace("_", "-").endswith(ch.replace("_", "-"))), None)
                    if a:
                        certos.add(a)
                if certos:
                    R["K1 situação -> regra"]["hoje"].append(posicao(hoje_k1.buscar(cel[2], top=10), certos))
                    R["K1 situação -> regra"]["tabela (entregue)"].append(
                        posicao(tabela_busca(raiz, tabela, cel[2], limite=10, sem_tipos=("falha",)), certos))

        # ---- K2: frase de "quando usar" (escondida) -> anotação
        for arq, quando in {a: q for a, q in linhas if q.strip()}.items():
            R["K2 descrição -> anotação"]["tabela (entregue)"].append(
                posicao(tabela_busca(raiz, escondida, quando, limite=10), {arq}))

    print("\n=== RESULTADOS (arquivo certo entre os N primeiros)")
    for g in sorted(R):
        print(f"\n--- {g}")
        for rotulo, v in R[g].items():
            print(f"  n={len(v):4d} | {placar(v)} | {rotulo}")
    if tempos:
        print(f"\n=== busca entregue: {1000 * sum(tempos) / len(tempos):.1f} ms por pedido, em média ({len(tempos)} buscas, "
              "tabela com os 4 projetos)")


if __name__ == "__main__":
    main()
