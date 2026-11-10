"""Somente leitura: garimpa, nas conversas dos 4 projetos, os casos para o gabarito.

Para cada pedido real do owner guarda:
  - o pedido;
  - as anotacoes (memory/*.md, memory/sessions/*.md) que o assistente ABRIU ate o pedido seguinte;
  - as anotacoes que o assistente CITOU no texto da resposta;
  - se o pedido e um REFORCO (o owner lembrando algo que ja tinha dito/feito), e qual era o pedido anterior;
  - se e um `/mss-spec:memory buscar`.
Grava casos.json no scratchpad e imprime contagens + amostra.
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import mesa  # noqa: E402

AQUI = Path(__file__).parent


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


FORTE = re.compile(
    r"\bja (te )?(falei|falamos|disse|dissemos|expliquei|explicamos|fizemos|resolvemos|passei|mandei|informei|avisei|pedi|combinamos|definimos|tinhamos|conversamos|discutimos|vimos)\b"
    r"|\b(eu )?ja tinha (dito|falado|feito|pedido|passado|explicado|resolvido|avisado|um|uma)\b"
    r"|\bcomo (eu )?(ja )?(disse|falei|expliquei|pedi)\b"
    r"|\b(voce|vc) (ja )?(esqueceu|nao lembra|nao lembrou|ignorou)\b|\besqueceu\b"
    r"|\b(esta|ta|estava|tem|deveria estar|tinha que estar) (gravado |registrado |salvo |anotado )?(na|em) (sua |nossa |a )?memoria\b"
    r"|\b(em|na|numa|de) (outra|outras) conversa|\bconversa(s)? anterior(es)?\b|\bconversa(s)? passada(s)?\b"
    r"|\bquantas vezes\b|\btoda (santa )?vez\b|\bde novo (isso|esse|essa|o mesmo)\b|\bmais uma vez (eu|voce|tenho)\b"
    r"|\bja (foi|estava|esta) (feito|resolvido|definido|decidido|combinado|documentado|registrado|gravado)\b"
    r"|\beu tinha (um|uma|feito|pedido|dito)\b|\bnos (ja )?(fizemos|resolvemos|tinhamos)\b|\blembra (que|do|da|de|quando)\b|\bnao lembra\b"
)
PULAR = ("<", "Caveat", "[Image", "This session", "Stop hook", "**Responda", "Base directory", "Another Claude")
RE_CITA = re.compile(r"memory/(?:sessions/)?[\w\-.]+\.md")


def texto_user(conteudo) -> str:
    partes = [conteudo] if isinstance(conteudo, str) else [
        b.get("text", "") for b in (conteudo or []) if isinstance(b, dict) and b.get("type") == "text"]
    return " ".join(partes)


def casos_do_projeto(nome: str, raiz: Path, chave: str, existentes: set) -> list:
    casos = []
    pastas = [d for d in mesa.TRANSCRICOES.iterdir() if d.is_dir() and d.name.endswith(chave)]
    raiz_norm = str(raiz).replace("\\", "/").lower()
    for arq in sorted(a for d in pastas for a in d.glob("*.jsonl")):
        atual, anterior = None, None

        def fechar():
            nonlocal anterior
            if atual:
                atual["lidos"] = [x for x in atual["lidos"] if x not in atual["escritos"]]
                atual["citados"] = [x for x in atual["citados"] if x not in atual["escritos"]]
                casos.append(atual)
                anterior = atual

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
                    t = texto_user(conteudo)
                    buscar = False
                    m = re.search(r"<command-name>/?([\w:\-]+)</command-name>", t)
                    args = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
                    if args:
                        buscar = bool(m and m.group(1).endswith("memory") and args.group(1).strip().lower().startswith("buscar"))
                        t = args.group(1)
                    t = re.sub(r"<[^>]+>.*?</[^>]+>", " ", t, flags=re.S)
                    t = " ".join(t.split())
                    if len(t) < 25 or t.startswith(PULAR) or "hook feedback" in t[:60] or "[mss-spec]" in t[:40]:
                        continue
                    fechar()
                    atual = dict(projeto=nome, conversa=arq.stem[:8], quando=reg.get("timestamp", "")[:10],
                                 pedido=t[:1500], lidos=[], citados=[], escritos=[], buscar=buscar,
                                 reforco=bool(FORTE.search(norm(t[:700]))),
                                 anterior=(anterior or {}).get("pedido", "")[:1500])
                elif reg.get("type") == "assistant" and atual:
                    for b in conteudo or []:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_use" and b.get("name") == "Read":
                            p = str(b.get("input", {}).get("file_path", "")).replace("\\", "/")
                            if raiz_norm in p.lower() and "/memory/" in p and p.endswith(".md"):
                                rel = p[p.lower().index("/memory/") + 1:]
                                if rel in existentes and rel not in atual["lidos"]:
                                    atual["lidos"].append(rel)
                        elif b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit"):
                            p = str(b.get("input", {}).get("file_path", "")).replace("\\", "/")
                            if "/memory/" in p and p.endswith(".md"):
                                atual["escritos"].append(p[p.lower().index("/memory/") + 1:])
                        elif b.get("type") == "text":
                            for c in RE_CITA.findall(b.get("text", "")):
                                if c in existentes and c not in atual["citados"]:
                                    atual["citados"].append(c)
        fechar()
    return casos


def main():
    todos = []
    for nome, (raiz, chave) in mesa.PROJETOS.items():
        existentes = {r["arquivo"] for r in mesa.linhas_do_projeto(nome, raiz)}
        casos = casos_do_projeto(nome, raiz, chave, existentes)
        todos.extend(casos)
        c = Counter()
        for k in casos:
            c["pedidos"] += 1
            c["com anotacao aberta"] += bool(k["lidos"])
            c["com anotacao citada"] += bool(k["citados"])
            c["reforco"] += k["reforco"]
            c["reforco com gabarito"] += k["reforco"] and bool(k["lidos"] or k["citados"])
            c["memory buscar"] += k["buscar"]
            c["memory buscar com gabarito"] += k["buscar"] and bool(k["lidos"] or k["citados"])
        conversas = len({k["conversa"] for k in casos})
        print(f"{nome}: {conversas} conversas | {dict(c)}")
    (AQUI / "casos.json").write_text(json.dumps(todos, ensure_ascii=False), encoding="utf-8")
    print(f"total de pedidos: {len(todos)}")
    amostra = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if amostra:
        import random
        random.seed(7)
        ref = [k for k in todos if k["reforco"]]
        for k in random.sample(ref, min(amostra, len(ref))):
            m = FORTE.search(norm(k["pedido"][:700]))
            print(f"\n--- {k['projeto']} {k['quando']} | casou: «{m.group(0)}» | abertas {len(k['lidos'])} citadas {len(k['citados'])}")
            print("  ANTES :", k["anterior"][:200])
            print("  REFORCO:", k["pedido"][:330])


if __name__ == "__main__":
    main()
