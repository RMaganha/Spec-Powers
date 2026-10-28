"""converter_to_dolist.py — leva o to-dolist e o fora de escopo de um projeto pro desenho do kit (0.48.0).

Por que: "fora de escopo" quer dizer "não agora" e é uma linha do `to-dolist.md` com a tag `#fora-de-escopo`, e o
to-dolist vai pro git (docs/decisoes.md, 2026-10-28). Projetos criados antes disso têm a seção "Fora de escopo" no
INDEX, o `docs/superpowers/FORA-DE-ESCOPO.md` e um to-dolist fora do git e fora do formato. Quem converte é o
`/mss-spec:upgrade`, no projeto, com o OK do owner. Spec: docs/specs/fora-de-escopo-no-to-dolist.md.

Nunca perder nada:
- `liberar`   tempo 1: tira o `to-dolist.md` do `.gitignore` (a linha e o comentário dela). O upgrade commita o
              to-dolist EXATAMENTE como está antes de qualquer conversão — o "antes" fica no git.
- `converter` tempo 2: recado (item `-`/`1.` com as linhas que continuam embaixo) vira UMA linha, com o título da seção
              na frente e a data dele; fora de escopo vira `- <item> #fora-de-escopo (decidido: <data>, <texto
              inteiro>)`. Sem data → a data do dia; DD/MM/AAAA → AAAA-MM-DD. Riscado/FEITA/CONCLUÍDO, data sem ano,
              parágrafo solto, citação, tabela e código vão pra uma LISTA no fim, sem mudar uma letra. Ordem: data
              mais antiga em cima. Toda linha de origem tem um destino (convertida · título usado · lista ·
              marcação) e as palavras de cada recado reaparecem na linha nova — senão, nada é gravado.
              Com `--aplicar` só grava se o to-dolist já está no git e os arquivos tocados estão limpos.
- `checar`    só lê: o que ainda está no formato antigo (o `/mss-spec:doctor` usa).

Uso:  python converter_to_dolist.py checar    [--proj DIR]
      python converter_to_dolist.py liberar   [--proj DIR] [--aplicar]
      python converter_to_dolist.py converter [--proj DIR] [--aplicar] [--hoje AAAA-MM-DD]
      (sem --aplicar é prévia: não grava nada; exit 1 = problema, nada gravado)
"""
import argparse
import datetime as _dt
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

TODO = "to-dolist.md"
SP = ("docs", "superpowers")
FORA = "FORA-DE-ESCOPO.md"
MARCA_LISTA = "<!-- upgrade: linhas que a conversão não soube converter"

RE_ITEM = re.compile(r"^ {0,3}(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
RE_TITULO = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
RE_DATA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RE_DATA_BR = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
RE_DATA_SEM_ANO = re.compile(r"\b(\d{1,2})/(\d{1,2})\b(?!/)")
RE_FEITO = re.compile(r"~~|\b(?:FEIT[AO]|CONCLU[IÍ]D[AO])\b")
RE_NO_FORMATO = re.compile(r"^- .+ (?:\(add: \d{4}-\d{2}-\d{2}\)|#fora-de-escopo \(decidido: \d{4}-\d{2}-\d{2}, .+\))$")
RE_DATA_LINHA = re.compile(r"\((?:add|decidido): (\d{4}-\d{2}-\d{2})")
RE_SECAO_FORA = re.compile(r"fora de escopo", re.I)
RE_PALAVRA = re.compile(r"\w+")
RE_SIMBOLO_INICIAL = re.compile(r"^[^\w*`~(\[\"']+")


# ------------------------------------------------------------------ leitura

def _ler(p: Path):
    b = p.read_bytes()
    bom = b.startswith(b"\xef\xbb\xbf")
    t = b.decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in t else "\n"
    return t.replace("\r\n", "\n"), eol, bom


def _gravar(p: Path, texto: str, eol: str, bom: bool):
    dados = texto.replace("\n", eol).encode("utf-8")
    p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + dados)


def _data(texto: str):
    """1ª data completa do texto, em AAAA-MM-DD (data inválida não conta)."""
    achados = [(m.start(), m.group(1), m.group(2), m.group(3)) for m in RE_DATA_ISO.finditer(texto)]
    achados += [(m.start(), m.group(3), m.group(2), m.group(1)) for m in RE_DATA_BR.finditer(texto)]
    for _, a, m, d in sorted(achados):
        try:
            return _dt.date(int(a), int(m), int(d)).isoformat()
        except ValueError:
            continue
    return None


def _data_sem_ano(texto: str) -> bool:
    for m in RE_DATA_SEM_ANO.finditer(texto):
        if 1 <= int(m.group(1)) <= 31 and 1 <= int(m.group(2)) <= 12:
            return True
    return False


def _palavras(texto: str) -> set:
    return {w.lower() for w in RE_PALAVRA.findall(texto)}


# ------------------------------------------------------------------ blocos

@dataclass
class Bloco:
    tipo: str                  # item · titulo · outro · marcacao
    linhas: list               # texto original de cada linha
    titulo: object = None      # Bloco do título da seção (pra item)
    nivel: int = 0             # nível do título
    usado: bool = False        # título que virou prefixo de algum item


def _blocos(texto: str, nota_rodizio: bool = False) -> list:
    """Divide em blocos sem perder linha: a soma das linhas dos blocos é o texto inteiro."""
    out, titulo, cerca, comentario = [], None, False, False
    for l in texto.split("\n"):
        s = l.strip()
        if cerca or comentario:
            out.append(Bloco("outro", [l]))
            if cerca and s.startswith("```"):
                cerca = False
            if comentario and "-->" in s:
                comentario = False
            continue
        if s.startswith("```"):
            cerca = True
            out.append(Bloco("outro", [l]))
            continue
        if s.startswith("<!--"):
            if "-->" not in s:
                comentario = True
            marca = "-->" in s and ("Movido da partida" in s or "Movido para [" in s)
            out.append(Bloco("marcacao" if marca else "outro", [l]))
            continue
        if not s or re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", s) or s.startswith("- Movido para ["):
            out.append(Bloco("marcacao", [l]))
            continue
        m = RE_TITULO.match(l)
        if m:
            titulo = Bloco("titulo", [l], nivel=len(m.group(1)))
            out.append(titulo)
            continue
        if RE_ITEM.match(l):
            out.append(Bloco("item", [l], titulo=titulo))
            continue
        ant = out[-1] if out else None
        continua = (ant is not None and ant.tipo == "item" and not s.startswith(("> ", ">", "|")))
        if continua:
            ant.linhas.append(l)
        else:
            out.append(Bloco("outro", [l]))
    return out


def _texto_item(b: Bloco) -> str:
    primeira = RE_ITEM.match(b.linhas[0]).group(1)
    resto = []
    for l in b.linhas[1:]:
        m = RE_ITEM.match(l.strip()) if l[:1].isspace() else None
        resto.append(m.group(1) if m else l.strip())
    return " ".join([primeira, *resto])


def _titulo_limpo(t: Bloco, data: str) -> str:
    texto = RE_TITULO.match(t.linhas[0]).group(2)
    texto = RE_SIMBOLO_INICIAL.sub("", texto).strip()
    if data:
        texto = re.sub(r"\s*\(" + re.escape(data) + r"\)", "", texto).strip()
    return texto


def _o_que_e_motivo(corpo: str):
    """'**X** resto — motivo' → ('X resto', 'motivo'). O que vem em negrito no começo, até o 1º separador
    (' — ' ou ': ') logo depois dele; sem negrito, até o 1º ' — '. Nenhuma palavra se perde: só muda de lugar."""
    m = re.match(r"^\*\*(.+?)\*\*(.*)$", corpo)
    if m:
        resto = m.group(2)
        cortes = [i for i in (resto.find(" — "), resto.find(": ")) if 0 <= i <= 160]
        if resto.startswith((":", "—")):
            cortes.append(0)
        if cortes:
            i = min(cortes)
            sep = re.match(r"\s*(?:—|:)\s*", resto[i:])
            return (m.group(1) + resto[:i]).strip(), resto[i + sep.end():].strip()
        return m.group(1).strip(), resto.strip()
    if " — " in corpo:
        o_que, motivo = corpo.split(" — ", 1)
        return o_que.strip(), motivo.strip()
    return corpo, ""


def _titulo_feito(t) -> bool:
    return t is not None and bool(RE_FEITO.search(t.linhas[0]))


# ------------------------------------------------------------------ conversão

@dataclass
class Linha:
    data: str
    texto: str
    ordem: int


@dataclass
class Resultado:
    todo_novo: str = ""
    index_novo: object = None          # None = INDEX não muda
    apagar_fora: bool = False
    contagem: dict = field(default_factory=dict)
    exemplos: list = field(default_factory=list)  # (antes, depois)
    problemas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    gravou: bool = False


def _secao_fora(texto: str):
    """(texto sem a seção 'Fora de escopo', corpo da seção) — None no corpo se não há seção."""
    linhas = texto.split("\n")
    for i, l in enumerate(linhas):
        m = RE_TITULO.match(l)
        if m and len(m.group(1)) >= 2 and RE_SECAO_FORA.search(m.group(2)):
            nivel, fim = len(m.group(1)), len(linhas)
            for j in range(i + 1, len(linhas)):
                mj = RE_TITULO.match(linhas[j])
                if mj and len(mj.group(1)) <= nivel:
                    fim = j
                    break
            return "\n".join(linhas[:i] + linhas[fim:]), "\n".join(linhas[i:fim])
    return texto, None


def _converter_fonte(texto: str, fora: bool, hoje: str, novas: list, lista: list, cont: dict, exemplos: dict,
                     problemas: list, rotulo: str):
    blocos = _blocos(texto)
    for b in blocos:
        cont["total"] += len(b.linhas)
        if b.tipo != "item":
            continue
        corpo = _texto_item(b)
        if not fora and RE_NO_FORMATO.match(b.linhas[0]) and len(b.linhas) == 1:
            novas.append(Linha(RE_DATA_LINHA.search(b.linhas[0]).group(1), b.linhas[0], len(novas)))
            cont["convertidas"] += 1
            b.tipo = "feito"
            continue
        if RE_FEITO.search(corpo) or _titulo_feito(b.titulo):
            continue                                      # fica "item": vai pra lista
        data = _data(corpo)
        if data is None and _data_sem_ano(corpo):
            continue
        titulo = b.titulo
        estrutural = titulo is not None and (fora and (titulo.nivel == 1 or RE_SECAO_FORA.search(titulo.linhas[0])
                                                       or "movido do INDEX" in titulo.linhas[0]))
        if data is None and titulo is not None and not estrutural:
            data = _data(titulo.linhas[0])
        data = data or hoje
        prefixo = ""
        if titulo is not None and not estrutural:
            prefixo = _titulo_limpo(titulo, data) + ": "
            titulo.usado = True
        if fora:
            o_que, motivo = _o_que_e_motivo(corpo)
            nova = f"- {prefixo}{o_que} #fora-de-escopo (decidido: {data}, {motivo or 'motivo não registrado'})"
        else:
            nova = f"- {prefixo}{corpo} (add: {data})"
        faltam = _palavras(corpo) - _palavras(nova)
        if faltam:
            problemas.append(f"{rotulo}: palavras sumiriam ({', '.join(sorted(faltam))}) em: {b.linhas[0].strip()}")
        novas.append(Linha(data, nova, len(novas)))
        cont["convertidas"] += len(b.linhas)
        b.tipo = "feito"
        exemplos.setdefault(rotulo, ("\n".join(b.linhas), nova))
    for b in blocos:
        if b.tipo == "titulo" and fora and not b.usado:
            b.tipo = "marcacao"                           # "# Fora de escopo", "## 2026-10-27 — movido do INDEX.md"
        if b.tipo == "titulo" and b.usado:
            cont["titulos"] += 1
        elif b.tipo == "marcacao":
            cont["marcacao"] += 1
        elif b.tipo != "feito":
            lista.append((rotulo, b.linhas))
            cont["lista"] += len(b.linhas)


def converter(proj, hoje: str = None, aplicar: bool = False) -> Resultado:
    proj = Path(proj)
    hoje = hoje or _dt.date.today().isoformat()
    res = Resultado()
    cont = {"total": 0, "convertidas": 0, "titulos": 0, "lista": 0, "marcacao": 0}
    novas, lista, exemplos = [], [], {}
    p_todo, p_index, p_fora = proj / TODO, proj.joinpath(*SP, "INDEX.md"), proj.joinpath(*SP, FORA)
    eol, bom = "\n", False
    if p_todo.is_file():
        t, eol, bom = _ler(p_todo)
        if MARCA_LISTA in t:
            res.problemas.append(f"{TODO} já foi convertido (tem a lista do fim): decida as linhas de lá à mão")
            return res
        _converter_fonte(t, False, hoje, novas, lista, cont, exemplos, res.problemas, TODO)
    if p_index.is_file():
        t, _, _ = _ler(p_index)
        sem, corpo = _secao_fora(t)
        if corpo is not None:
            res.index_novo = sem
            _converter_fonte(corpo, True, hoje, novas, lista, cont, exemplos, res.problemas, "/".join((*SP, "INDEX.md")))
    if p_fora.is_file():
        t, _, _ = _ler(p_fora)
        res.apagar_fora = True
        _converter_fonte(t, True, hoje, novas, lista, cont, exemplos, res.problemas, "/".join((*SP, FORA)))
    res.contagem = cont
    soma = cont["convertidas"] + cont["titulos"] + cont["lista"] + cont["marcacao"]
    if soma != cont["total"]:
        res.problemas.append(f"a soma não bate: {soma} de {cont['total']} linhas com destino")
    novas.sort(key=lambda x: (x.data, x.ordem))
    texto = "\n".join(l.texto for l in novas)
    if lista:
        texto += f"\n\n{MARCA_LISTA} ({hoje}) — decida cada uma; o original inteiro está no git -->\n"
        for rotulo, linhas in lista:
            texto += "\n".join(linhas) + "\n"
    res.todo_novo = texto.rstrip("\n") + "\n" if texto.strip() else ""
    res.exemplos = list(exemplos.values())[:3]
    if len(res.exemplos) < 3:                              # completa com outros recados convertidos
        vistos = {d for _, d in res.exemplos}
        for antes, depois in _exemplos_extras(proj, hoje):
            if depois not in vistos and len(res.exemplos) < 3:
                res.exemplos.append((antes, depois))
                vistos.add(depois)
    if not aplicar:
        return res
    res.problemas += _conferir_git(proj, [p for p in (p_todo, p_index, p_fora) if p.is_file()])
    if res.problemas:
        return res
    if res.todo_novo:
        _gravar(p_todo, res.todo_novo, eol, bom)
    if res.index_novo is not None:
        _, eol_i, bom_i = _ler(p_index)
        _gravar(p_index, res.index_novo, eol_i, bom_i)
    if res.apagar_fora:
        p_fora.unlink()
    res.gravou = True
    return res


def _exemplos_extras(proj: Path, hoje: str) -> list:
    """Outros pares antes/depois do to-dolist, pra completar 3 quando uma fonte não existe."""
    p = proj / TODO
    if not p.is_file():
        return []
    t, _, _ = _ler(p)
    pares = []
    for b in _blocos(t):
        if b.tipo != "item" or RE_NO_FORMATO.match(b.linhas[0]):
            continue
        novas, lista, cont, ex = [], [], {k: 0 for k in ("total", "convertidas", "titulos", "lista", "marcacao")}, {}
        _converter_fonte("\n".join(([b.titulo.linhas[0]] if b.titulo else []) + b.linhas), False, hoje,
                         novas, lista, cont, ex, [], TODO)
        if novas:
            pares.append(("\n".join(b.linhas), novas[0].texto))
    return pares


def _conferir_git(proj: Path, arquivos: list) -> list:
    def git(*a):
        return subprocess.run(["git", *a], cwd=proj, capture_output=True, text=True, encoding="utf-8")
    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        return ["o projeto não é um repositório git: sem o git não há como voltar atrás"]
    probs = []
    if (proj / TODO).is_file() and git("ls-files", "--error-unmatch", TODO).returncode != 0:
        probs.append(f"{TODO} ainda não está no git: faça o tempo 1 (liberar + commit do arquivo como está) antes")
    rel = [str(a.relative_to(proj)).replace("\\", "/") for a in arquivos]
    sujos = [l for l in git("status", "--porcelain", "--", *rel).stdout.splitlines() if l.strip()]
    if sujos:
        probs.append("arquivos com mudança não commitada (commite ou descarte antes): " + "; ".join(sujos))
    return probs


# ------------------------------------------------------------------ tempo 1 e checagem

def _linhas_gitignore(texto: str) -> list:
    """Índices das linhas que ignoram o to-dolist + o comentário logo acima que fala dele."""
    linhas = texto.split("\n")
    saem = []
    for i, l in enumerate(linhas):
        if l.strip() in ("/" + TODO, TODO):
            saem.append(i)
            j = i
            while j > 0 and linhas[j - 1].lstrip().startswith("#"):
                j -= 1
            if any("to-dolist" in linhas[k] for k in range(j, i)):
                saem += range(j, i)
    return sorted(set(saem))


def liberar(proj, aplicar: bool = False) -> str:
    """Tempo 1: tira o to-dolist do .gitignore. Devolve as linhas que saem (vazio = nada a fazer)."""
    p = Path(proj) / ".gitignore"
    if not p.is_file():
        return ""
    t, eol, bom = _ler(p)
    saem = _linhas_gitignore(t)
    if not saem:
        return ""
    linhas = t.split("\n")
    if aplicar:
        _gravar(p, "\n".join(l for i, l in enumerate(linhas) if i not in saem), eol, bom)
    return "\n".join(linhas[i] for i in saem)


def checar(proj) -> list:
    proj = Path(proj)
    achados = []
    p_index = proj.joinpath(*SP, "INDEX.md")
    if p_index.is_file():
        _, corpo = _secao_fora(_ler(p_index)[0])
        if corpo is not None:
            achados.append(f"seção \"Fora de escopo\" no docs/superpowers/INDEX.md ({len(corpo.splitlines())} linhas)")
    if proj.joinpath(*SP, FORA).is_file():
        achados.append("docs/superpowers/FORA-DE-ESCOPO.md existe")
    gi = proj / ".gitignore"
    if gi.is_file() and _linhas_gitignore(_ler(gi)[0]):
        achados.append(".gitignore ainda ignora o to-dolist.md")
    p_todo = proj / TODO
    if p_todo.is_file():
        uteis = [l for l in _ler(p_todo)[0].split("\n") if l.strip()]
        fora = [l for l in uteis if not RE_NO_FORMATO.match(l)]
        if fora:
            achados.append(f"to-dolist.md: {len(fora)} de {len(uteis)} linhas fora do formato do kit")
    return achados


# ------------------------------------------------------------------ CLI

def _relatorio(res: Resultado, aplicar: bool) -> str:
    c = res.contagem
    s = ["Gravado." if res.gravou else "Prévia — nada gravado.",
         f"Linhas de origem: {c.get('total', 0)} = {c.get('convertidas', 0)} em recados convertidos + "
         f"{c.get('titulos', 0)} títulos usados na frente dos recados + {c.get('lista', 0)} na lista do fim + "
         f"{c.get('marcacao', 0)} de marcação (em branco, separador, ponteiro do formato antigo)."]
    if res.index_novo is not None:
        s.append("INDEX.md: a seção \"Fora de escopo\" sai (o resto fica igual).")
    if res.apagar_fora:
        s.append("FORA-DE-ESCOPO.md: sai (cada item virou linha do to-dolist).")
    for i, (antes, depois) in enumerate(res.exemplos, 1):
        s.append(f"\nExemplo {i}\n  antes:\n" + "\n".join("    " + l for l in antes.split("\n")) +
                 f"\n  depois:\n    {depois}")
    for p in res.problemas:
        s.append(f"PROBLEMA: {p}")
    if not aplicar and not res.problemas:
        s.append("\nPara gravar: rode de novo com --aplicar (depois do tempo 1 commitado).")
    return "\n".join(s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("acao", choices=("checar", "liberar", "converter"))
    ap.add_argument("--proj", default=".")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--hoje")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if a.acao == "checar":
        achados = checar(a.proj)
        print("\n".join(f"formato antigo: {x}" for x in achados) or "no desenho do kit")
        return 0
    if a.acao == "liberar":
        saem = liberar(a.proj, aplicar=a.aplicar)
        if not saem:
            print("nada a fazer: o .gitignore não ignora o to-dolist.md")
        else:
            print(("Gravado" if a.aplicar else "Prévia — nada gravado") + ". Saem do .gitignore:\n" + saem)
        return 0
    res = converter(a.proj, hoje=a.hoje, aplicar=a.aplicar)
    print(_relatorio(res, a.aplicar))
    return 1 if res.problemas else 0


if __name__ == "__main__":
    sys.exit(main())
