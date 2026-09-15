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

Uso:  python rodizio_partida.py mapa  [--proj DIR] [--aplicar]
      python rodizio_partida.py index [--proj DIR] [--aplicar]
"""
import argparse
import datetime as _dt
import functools
import importlib.util
import re
import sys
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


def rodizio_mapa(proj: Path, hoje=None, aplicar: bool = False) -> Relatorio:
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
        if len(bls) <= MANTER_BLOCOS:
            novas += linhas
            continue
        ficam, saem = bls[:MANTER_BLOCOS], bls[MANTER_BLOCOS:]
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


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["mapa", "index"])
    ap.add_argument("--proj", default=".")
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    proj = Path(a.proj).resolve()
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
