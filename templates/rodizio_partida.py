"""rodizio_partida.py — mantém o ritual de partida dentro do orçamento MOVENDO, nunca apagando.

`mapa`  : em "Onde estamos" e "Próximo passo" (blocos separados por `---`, mais novo em cima) ficam os
          2 primeiros blocos (atual + 1 anterior — o que templates/MAPA.md promete); do 3º em diante vão
          para docs/superpowers/MAPA-historico.md, em prepend datado. "Conexões" não se toca.
`index` : linha de item com status `fechada` vai para docs/superpowers/INDEX-historico.md (prepend
          datado). Ficam `aberta`, `em andamento`, `pausada: …`, a seção "Fora de escopo" inteira e cabeçalhos.

Por que: MAPA do Whats com 89.651 bytes (teto 6.000) e INDEX com 61.399 (teto 7.000) relidos em toda
janela — o `doctor` avisava, ninguém movia. Dry-run por padrão; `--aplicar` grava depois de conferir que
toda linha movida reapareceu no histórico. Se o MAPA ainda estourar depois do rodízio, o excesso é o
bloco ATUAL e isso é conteúdo (edição do owner) — o script diz, não corta.

`enxugar`: `mapa` + `index` e, se ainda passar do teto, a 2ª etapa (F-030 — o que o owner moveu à mão no
          Whats), parando assim que cabe: INDEX → `## Backlog` → BACKLOG.md · `## Fora de escopo` →
          FORA-DE-ESCOPO.md · `## Assuntos existentes` → ASSUNTOS-EXISTENTES.md · linha longa de `## Em andamento`
          → EM-ANDAMENTO.md (fica nome/link — ponteiro — status VERBATIM, que o hook lê); MAPA → corpo de
          `## Conexões` → CONEXOES.md (fica a lista de nomes). Destino que já existe recebe prepend datado,
          nunca é sobrescrito. Arquivo com conflito de merge não é tocado. É o que o hook `teto_ao_gravar.py`
          chama depois de cada gravação.

Uso:  python rodizio_partida.py mapa    [--proj DIR] [--aplicar]
      python rodizio_partida.py index   [--proj DIR] [--aplicar]
      python rodizio_partida.py enxugar [--proj DIR] [--aplicar]
"""
import argparse
import datetime as _dt
import functools
import importlib.util
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

TETO_MAPA = 6000
TETO_INDEX = 7000
MANTER_BLOCOS = 2
SECOES_ROTATIVAS = ("onde estamos", "próximo passo", "proximo passo")
SP = ("docs", "superpowers")
RE_SECAO = re.compile(r"^## +(.*\S)\s*$")


@dataclass
class Relatorio:
    bytes_antes: int = 0
    bytes_depois: int = 0
    movidas: int = 0
    problemas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    gravou: bool = False
    passos: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problemas


def _ler(p: Path):
    bruto = p.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in bruto else "\n"
    return bruto.replace("\r\n", "\n"), eol


def _gravar(p: Path, texto: str, eol: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(texto.replace("\n", eol).encode("utf-8"))


def secoes(texto: str) -> list:
    """[(título ou None para o preâmbulo, [linhas])] na ordem do arquivo."""
    out, titulo, linhas = [], None, []
    for l in texto.split("\n"):
        m = RE_SECAO.match(l)
        if m:
            out.append((titulo, linhas))
            titulo, linhas = m.group(1), [l]
        else:
            linhas.append(l)
    out.append((titulo, linhas))
    return out


def blocos(linhas: list) -> list:
    """Divide o corpo de uma seção (sem a linha `## `) em blocos separados por linhas `---`."""
    out, atual = [], []
    for l in linhas:
        if l.strip() == "---":
            out.append(atual)
            atual = []
        else:
            atual.append(l)
    out.append(atual)
    return out


def _juntar_blocos(bls: list) -> list:
    out = []
    for i, b in enumerate(bls):
        if i:
            out += ["", "---", ""] if not (b and b[0] == "") else ["", "---"]
        out += b
    return out


def _nao_vazias(linhas: list) -> list:
    return [l for l in linhas if l.strip()]


def _prepend_historico(path: Path, titulo_novo: str, secoes_novas: list, eol: str) -> None:
    """Insere as seções novas logo depois do H1 do histórico (cria o arquivo se não existe)."""
    corpo = "\n".join(secoes_novas).rstrip("\n") + "\n"
    if path.is_file():
        texto, eol_h = _ler(path)
        linhas = texto.split("\n")
        pos = next((i for i, l in enumerate(linhas) if l.startswith("# ")), None)
        if pos is None:
            novo = corpo + "\n" + texto
        else:
            novo = "\n".join(linhas[:pos + 1]) + "\n\n" + corpo + "\n" + "\n".join(linhas[pos + 1:]).lstrip("\n")
        _gravar(path, novo, eol_h)
    else:
        _gravar(path, f"{titulo_novo}\n\n{corpo}", eol)


def rodizio_mapa(proj: Path, hoje=None, aplicar: bool = False, manter: int = MANTER_BLOCOS) -> Relatorio:
    proj = Path(proj)
    hoje = hoje or _dt.date.today().isoformat()
    rel = Relatorio()
    mapa = proj.joinpath(*SP, "MAPA.md")
    if not mapa.is_file():
        rel.problemas.append(f"não existe {mapa}")
        return rel
    texto, eol = _ler(mapa)
    rel.bytes_antes = len(texto.encode("utf-8"))
    novas, movidos = [], []
    for titulo, linhas in secoes(texto):
        if titulo is None or titulo.strip().lower() not in SECOES_ROTATIVAS:
            novas += linhas
            continue
        bls = blocos(linhas[1:])
        if len(bls) <= manter:
            novas += linhas
            continue
        ficam, saem = bls[:manter], bls[manter:]
        novas += [linhas[0]] + _juntar_blocos(ficam)
        corpo = _juntar_blocos(saem)
        movidos.append((titulo, corpo))
        rel.movidas += len([l for l in _nao_vazias(corpo) if l.strip() != "---"])
    novo = "\n".join(novas)
    if not novo.endswith("\n"):
        novo += "\n"
    rel.bytes_depois = len(novo.encode("utf-8"))
    # conservação: toda linha não vazia que saiu está no que vai pro histórico; nada além disso sumiu
    saiu = sorted(_nao_vazias([l for _, c in movidos for l in c]))
    perdidas = sorted(_nao_vazias(texto.split("\n")))
    for l in _nao_vazias(novo.split("\n")) + saiu:
        if l in perdidas:
            perdidas.remove(l)
    perdidas = [l for l in perdidas if l.strip() != "---"]
    if perdidas:
        rel.problemas.append("conservação falhou — linhas que sumiriam: " + " | ".join(perdidas[:3]))
        return rel
    if rel.bytes_depois > TETO_MAPA:
        rel.avisos.append(f"MAPA ainda acima do teto depois do rodízio ({rel.bytes_depois} > {TETO_MAPA}): "
                          "o excesso é o bloco atual — isso é conteúdo, não se corta por script")
    if aplicar and movidos:
        nome = (re.sub(r"^# +(mapa de contexto\s+[—–-]\s+)?", "", texto.split("\n")[0], flags=re.I).strip()
                if texto.startswith("# ") else proj.name)
        secs = []
        for titulo, corpo in movidos:
            secs += [f'## {hoje} — rodízio de "{titulo}"', ""] + corpo + [""]
        _prepend_historico(proj.joinpath(*SP, "MAPA-historico.md"),
                           f"# Histórico do mapa de contexto — {nome}", secs, eol)
        _gravar(mapa, novo, eol)
        rel.gravou = True
    return rel


@functools.lru_cache(maxsize=1)
def _hook_um_item():
    """Reusa RE_ITEM/RE_SEPARADOR/FECHADOS do hook um_item_por_janela.py (mesma leitura de status).
    Cacheado: é chamado por linha do INDEX."""
    caminho = Path(__file__).resolve().parent.parent / "hooks" / "um_item_por_janela.py"
    spec = importlib.util.spec_from_file_location("um_item_por_janela", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def fechada(linha: str) -> bool:
    """Item cujo status (segmentos após ` — `) começa por `fechada` — `pausada` NÃO é fechada."""
    h = _hook_um_item()
    m = h.RE_ITEM.match(linha)
    if not m:
        return False
    for seg in h.RE_SEPARADOR.split(m.group(1))[1:]:
        if seg.strip().strip("*").strip().lower().startswith("fechada"):
            return True
    return False


def rodizio_index(proj: Path, hoje=None, aplicar: bool = False) -> Relatorio:
    proj = Path(proj)
    hoje = hoje or _dt.date.today().isoformat()
    rel = Relatorio()
    idx = proj.joinpath(*SP, "INDEX.md")
    if not idx.is_file():
        rel.problemas.append(f"não existe {idx}")
        return rel
    texto, eol = _ler(idx)
    rel.bytes_antes = len(texto.encode("utf-8"))
    ficam, saem, abertas = [], [], 0
    for titulo, linhas in secoes(texto):
        fora = titulo is not None and "fora de escopo" in titulo.lower()
        for l in linhas:
            if not fora and fechada(l):
                saem.append(l)
            else:
                ficam.append(l)
                if not fora and _hook_um_item().RE_ITEM.match(l) and not fechada(l):
                    abertas += 1
    novo = "\n".join(ficam)
    if not novo.endswith("\n"):
        novo += "\n"
    rel.movidas = len(saem)
    rel.bytes_depois = len(novo.encode("utf-8"))
    originais = sorted(_nao_vazias(texto.split("\n")))
    depois = sorted(_nao_vazias(novo.split("\n")) + saem)
    if originais != depois:
        rel.problemas.append("conservação falhou: linhas do INDEX antes ≠ (ficam + movidas)")
        return rel
    if rel.bytes_depois > TETO_INDEX:
        rel.avisos.append(f"INDEX ainda acima do teto ({rel.bytes_depois} > {TETO_INDEX}) com {abertas} item(ns) "
                          "aberta/em andamento/pausada — quais seguem abertos é decisão do owner, não do script")
    if aplicar and saem:
        _prepend_historico(proj.joinpath(*SP, "INDEX-historico.md"),
                           "# Índice de tarefas — histórico (fechadas)",
                           [f"## {hoje} — fechadas", ""] + saem + [""], eol)
        _gravar(idx, novo, eol)
        rel.gravou = True
    return rel


# ------------------------------------------------------------------ enxugar (2ª etapa, F-030)

LINHA_CURTA = 300          # bytes — linha de "Em andamento" acima disso vira nome — ponteiro — status
PONTEIRO_MOVIDO = "- Movido para ["
STATUS_ITEM = ("aberta", "em andamento", "pausada", "fechada")
SECOES_INDEX = (           # (casa o título, arquivo, descrição do ponteiro) — nesta ordem, até caber
    ("backlog", "BACKLOG.md", "ideias ainda não começadas, fora da partida (não são o estado atual); item que "
     "vira feature SOBE pro `## Em andamento`"),
    ("fora de escopo", "FORA-DE-ESCOPO.md", "decisões de NÃO fazer; consulte antes de propor algo novo "
     "(o recall também lê este arquivo)"),
    ("assuntos existentes", "ASSUNTOS-EXISTENTES.md", "o que o código já faz, 1 linha por assunto; abra quando "
     "o assunto pedir"),
)
NOTA_MOVIDO = ("<!-- Movido da partida pelo rodizio_partida.py (caso F-030 do kit): texto VERBATIM, lido sob "
               "demanda. Nada foi apagado — só saiu do que toda janela lê. -->")


def _bytes(texto: str) -> int:
    return len(texto.encode("utf-8"))


def _conflito(texto: str) -> bool:
    return any(l.startswith(("<<<<<<< ", ">>>>>>> ")) for l in texto.split("\n"))


def _titulo_casa(titulo, chave: str) -> bool:
    t = (titulo or "").strip().lower()
    return chave in t if chave == "fora de escopo" else t.startswith(chave)


def _aparar(linhas: list) -> list:
    while linhas and not linhas[0].strip():
        linhas = linhas[1:]
    while linhas and not linhas[-1].strip():
        linhas = linhas[:-1]
    return linhas


def _tirar_secao(texto: str, chave: str, arquivo: str, descricao: str, hoje: str):
    """(texto novo, linhas que saem). A seção fica com o título + 1 ponteiro (o que já existia, ou um novo)."""
    novas, saem = [], []
    for titulo, linhas in secoes(texto):
        if titulo is None or not _titulo_casa(titulo, chave):
            novas += linhas
            continue
        corpo = linhas[1:]
        ponteiros = [l for l in corpo if l.startswith(PONTEIRO_MOVIDO)]
        mover = _aparar([l for l in corpo if not l.startswith(PONTEIRO_MOVIDO)])
        if not _nao_vazias(mover):
            novas += linhas
            continue
        saem += mover
        ponteiro = ponteiros[0] if ponteiros else f"{PONTEIRO_MOVIDO}{arquivo}]({arquivo}) em {hoje} — {descricao}."
        novas += [linhas[0], "", ponteiro, ""]
    return "\n".join(novas), saem


def _encurtar_em_andamento(texto: str):
    """Linha longa de `## Em andamento` → `<nome/link> — detalhe em [EM-ANDAMENTO.md] — <status verbatim>`."""
    h = _hook_um_item()
    novas, saem = [], []
    for titulo, linhas in secoes(texto):
        if titulo is None or not titulo.strip().lower().startswith("em andamento"):
            novas += linhas
            continue
        for l in linhas:
            m = h.RE_ITEM.match(l)
            if not m or len(l.encode("utf-8")) <= LINHA_CURTA or "EM-ANDAMENTO.md" in l:
                novas.append(l)
                continue
            segs = h.RE_SEPARADOR.split(m.group(1))
            status = [s for s in segs[1:] if s.strip().strip("*").strip().lower().startswith(STATUS_ITEM)]
            if not status:
                novas.append(l)                      # sem status legível: não mexe
                continue
            novas.append(f"{l[:m.start(1)]}{segs[0]} — detalhe em [EM-ANDAMENTO.md](EM-ANDAMENTO.md) — {status[-1]}")
            saem += [l, ""]
    return "\n".join(novas), _aparar(saem)


def _nomes_de_conexao(linhas: list) -> list:
    return [l[2:].split(":", 1)[0].split(" (")[0].strip() for l in linhas if l.startswith("- ")]


def _tirar_conexoes(texto: str, hoje: str):
    novas, saem = [], []
    for titulo, linhas in secoes(texto):
        if titulo is None or not titulo.strip().lower().startswith("conex"):
            novas += linhas
            continue
        corpo = linhas[1:]
        ponteiro = [l for l in corpo if "](CONEXOES.md)" in l]
        mover = _aparar([l for l in corpo if "](CONEXOES.md)" not in l])
        if not _nao_vazias(mover):
            novas += linhas
            continue
        nomes = []
        if ponteiro and "Conexões: " in ponteiro[0]:
            nomes = [n.strip() for n in ponteiro[0].split("Conexões: ", 1)[1].rstrip().rstrip(".").split(" · ")]
        for n in _nomes_de_conexao(mover):
            if n and n not in nomes:
                nomes.append(n)
        saem += mover
        linha = (f"- Detalhe em [CONEXOES.md](CONEXOES.md) (contratos, tokens, topologia), movido em {hoje}. "
                 "Conexões: " + " · ".join(nomes) + ".")
        novas += [linhas[0], "", linha, ""]
    return "\n".join(novas), saem


def _gravar_destino(path: Path, h1: str, hoje: str, origem: str, linhas: list, eol: str) -> None:
    secao = [f"## {hoje} — movido do {origem}", ""] + linhas + [""]
    if path.is_file():
        _prepend_historico(path, h1, secao, eol)
    else:
        _gravar(path, h1 + "\n\n" + NOTA_MOVIDO + "\n\n" + "\n".join(secao).rstrip("\n") + "\n", eol)


def _conserva(antes: str, depois: str, movidas: list) -> list:
    """Linhas não vazias de antes que não estão nem no texto novo nem no que foi movido."""
    ficam = set(depois.split("\n")) | set(movidas)
    return [l for l in _nao_vazias(antes.split("\n")) if l not in ficam]


def aliviar(proj: Path, qual: str, hoje: str) -> Relatorio:
    """2ª etapa, sempre gravando (o `enxugar` é quem decide dry-run). Para assim que o arquivo cabe."""
    teto, nome = (TETO_INDEX, "INDEX.md") if qual == "index" else (TETO_MAPA, "MAPA.md")
    rel = Relatorio()
    alvo = Path(proj).joinpath(*SP, nome)
    texto, eol = _ler(alvo)
    rel.bytes_antes = _bytes(texto)
    atual, destinos = texto, []
    if qual == "index":
        for chave, arquivo, descricao in SECOES_INDEX:
            if _bytes(atual) <= teto:
                break
            atual, saem = _tirar_secao(atual, chave, arquivo, descricao, hoje)
            if saem:
                destinos.append((arquivo, f"# {arquivo[:-3].replace('-', ' ').capitalize()}", saem))
        if _bytes(atual) > teto:
            atual, saem = _encurtar_em_andamento(atual)
            if saem:
                destinos.append(("EM-ANDAMENTO.md", "# Em andamento — o texto completo de cada linha", saem))
    elif _bytes(atual) > teto:
        atual, saem = _tirar_conexoes(atual, hoje)
        if saem:
            destinos.append(("CONEXOES.md", "# Conexões — o detalhe de cada integração", saem))
    movidas = [l for _, _, ls in destinos for l in ls]
    perdidas = _conserva(texto, atual, movidas)
    if perdidas:
        rel.problemas.append("conservação falhou — linhas que sumiriam: " + " | ".join(p[:60] for p in perdidas[:3]))
        return rel
    if not atual.endswith("\n"):
        atual += "\n"
    for arquivo, h1, linhas in destinos:
        _gravar_destino(Path(proj).joinpath(*SP, arquivo), h1, hoje, nome, linhas, eol)
        rel.passos.append(f"{len(_nao_vazias(linhas))} linha(s) → {arquivo}")
    if destinos:
        _gravar(alvo, atual, eol)
        rel.gravou = True
    rel.movidas = len(_nao_vazias(movidas))
    rel.bytes_depois = _bytes(atual)
    if rel.bytes_depois > teto:
        rel.avisos.append(f"{nome} ainda acima do teto ({rel.bytes_depois} > {teto}) depois de tudo que é mecânico: "
                          "o excesso é conteúdo vivo — mova o detalhe pra spec do assunto (nunca apague)")
    return rel


def _enxugar_gravando(proj: Path, hoje: str) -> dict:
    out = {}
    for qual, nome, teto, etapa1 in (("mapa", "MAPA.md", TETO_MAPA, rodizio_mapa),
                                     ("index", "INDEX.md", TETO_INDEX, rodizio_index)):
        alvo = Path(proj).joinpath(*SP, nome)
        if not alvo.is_file():
            continue
        texto, _ = _ler(alvo)
        rel = Relatorio(bytes_antes=_bytes(texto), bytes_depois=_bytes(texto))
        out[qual] = rel
        if _conflito(texto):
            rel.problemas.append(f"{nome} tem marcador de conflito de merge — não mexo até o merge ser resolvido")
            continue
        if _bytes(texto) <= teto:
            continue
        r1 = etapa1(proj, hoje=hoje, aplicar=True)
        rel.problemas += r1.problemas
        if not r1.ok:
            continue
        if r1.movidas:
            rel.passos.append(f"{r1.movidas} linha(s) antigas → {nome[:-3]}-historico.md")
            rel.gravou = r1.gravou
        if _bytes(_ler(alvo)[0]) > teto:
            r2 = aliviar(proj, qual, hoje)
            rel.problemas += r2.problemas
            rel.passos += r2.passos
            rel.avisos += r2.avisos
            rel.gravou = rel.gravou or r2.gravou
        if qual == "mapa" and rel.ok and _bytes(_ler(alvo)[0]) > teto:
            r3 = rodizio_mapa(proj, hoje=hoje, aplicar=True, manter=1)    # acima do teto: só o bloco atual fica
            rel.problemas += r3.problemas
            if r3.ok and r3.movidas:
                rel.passos.append(f"{r3.movidas} linha(s) do bloco anterior → MAPA-historico.md")
                rel.gravou = True
        rel.bytes_depois = _bytes(_ler(alvo)[0])
        rel.avisos = [] if rel.bytes_depois <= teto else [
            f"{nome} ainda acima do teto ({rel.bytes_depois} > {teto}) depois de tudo que é mecânico: o excesso é "
            "conteúdo vivo" + (" (o bloco atual)" if qual == "mapa" else " (linhas de tarefa aberta)") +
            " — resuma e mova o detalhe pra spec do assunto; nunca apague"]
        rel.movidas = sum(int(p.split(" ", 1)[0]) for p in rel.passos)
    return out


def enxugar(proj: Path, hoje=None, aplicar: bool = False) -> dict:
    """{"mapa": Relatorio, "index": Relatorio} (só dos que existem). Dry-run roda tudo numa CÓPIA e descarta —
    mede exatamente o que o `--aplicar` gravaria."""
    hoje = hoje or _dt.date.today().isoformat()
    proj = Path(proj)
    if aplicar:
        return _enxugar_gravando(proj, hoje)
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "proj"
        origem = proj.joinpath(*SP)
        if origem.is_dir():
            shutil.copytree(origem, copia.joinpath(*SP))
        rels = _enxugar_gravando(copia, hoje)
    for r in rels.values():
        r.gravou = False
    return rels


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["mapa", "index", "enxugar"])
    ap.add_argument("--proj", default=".")
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    proj = Path(a.proj).resolve()
    if a.modo == "enxugar":
        rels = enxugar(proj, aplicar=a.aplicar)
        for qual, r in rels.items():
            teto = TETO_MAPA if qual == "mapa" else TETO_INDEX
            print(f"{qual}: {r.bytes_antes} → {r.bytes_depois} bytes (teto {teto})"
                  + (": " + " · ".join(r.passos) if r.passos else ""))
            for x in r.problemas + r.avisos:
                print("aviso:", x)
        print("GRAVADO." if any(r.gravou for r in rels.values())
              else "DRY-RUN — nada gravado. Rode com --aplicar para gravar.")
        return 0 if all(r.ok for r in rels.values()) else 1
    rel = rodizio_mapa(proj, aplicar=a.aplicar) if a.modo == "mapa" else rodizio_index(proj, aplicar=a.aplicar)
    teto = TETO_MAPA if a.modo == "mapa" else TETO_INDEX
    if not rel.ok:
        print("NÃO aplicado:\n- " + "\n- ".join(rel.problemas))
        return 1
    print(f"{a.modo}: {rel.bytes_antes} → {rel.bytes_depois} bytes (teto {teto}); linhas movidas: {rel.movidas}")
    for av in rel.avisos:
        print("aviso:", av)
    print("GRAVADO." if rel.gravou else "DRY-RUN — nada gravado. Rode com --aplicar para gravar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
