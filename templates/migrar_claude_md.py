"""migrar_claude_md.py — leva o CLAUDE.md de um projeto pro formato em que as regras do kit vêm do plugin.

Por que: o CLAUDE.md do projeto era o molde copiado UMA vez no kickoff + o que é do projeto. A cópia velha das
regras do kit ocupava ~6,4 KB do teto e nunca recebia regra nova; e os FATOS de infra do Whats tinham ido pra
`.claude/rules/deploy-e-ambiente.md`, que só carrega ao tocar Dockerfile (F-040). Spec:
`docs/specs/regras-do-kit-pelo-plugin.md`, seção "Migração dos projetos existentes".

Esta parte só MONTA em memória e CONFERE — nunca grava no projeto e nunca roda git que escreve:
- `montar`   classifica cada linha do CLAUDE.md antigo: ponteiro de `## Contexto` pra `.claude/rules/` vira o
             item de mesmo rótulo em negrito (que sai do arquivo de regra); linha que aponta documento do projeto
             fica; linha igual a uma linha de alguma versão do molde do kit sai (o plugin entrega); o resto FICA.
             Na dúvida, fica.
- `conferir` conservação (nenhuma linha sem destino), `## Contexto` sem ponteiro e com os rótulos de antes,
             marca, índice com cada regra uma vez, working tree limpo nos arquivos tocados. Teto = aviso.

Uso:  python migrar_claude_md.py historico     (regenera regras-do-kit/linhas-do-kit.txt a partir do git do kit)
"""
import argparse
import re
from collections import Counter
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PASTA_TEMPLATES = Path(__file__).resolve().parent
PASTA_REGRAS_DO_KIT = PASTA_TEMPLATES / "regras-do-kit"
ARQ_LINHAS_KIT = PASTA_REGRAS_DO_KIT / "linhas-do-kit.txt"
MOLDE = PASTA_TEMPLATES / "CLAUDE.md"
MOLDE_NO_GIT = "templates/CLAUDE.md"

MARCA = "<!-- mss-spec:regras-do-kit -->"
TETO_PROJETO = 10000
SECAO_REGRAS = "Regras obrigatórias do projeto"
SECAO_INDICE = "Índice de regras por tipo de arquivo"
PASTA_REGRAS = (".claude", "rules")

RE_SECAO = re.compile(r"^## +(.*\S)\s*$")
RE_MARCADOR = re.compile(r"^(?:[-*]\s+|\d+\.\s+)")
RE_ROTULO = re.compile(r"^\*\*(.+?)\*\*")
RE_ALVO_RULES = re.compile(r"`\.claude/rules/([^`]+?\.md)`")
RE_CITA_RULES = re.compile(r"\.claude/rules/([^\s`)\]]+?\.md)")
RE_ALVO_ARQUIVO = re.compile(r"`([^`\s]+)`|\]\(([^)\s]+)\)")
# Fato + fragmento de ponteiro no fim, como o molde de antes da marca escrevia no `## Contexto`:
# "- **Banco:** PostgreSQL — ver `.claude/rules/banco-e-segredo.md`" / "…; ver `.claude/rules/frontend.md`".
RE_FRAGMENTO = re.compile(r"\s*[—;,]\s*ver\s+`\.claude/rules/([^`]+?\.md)`(?=\s*[>).]?\s*$)")
PARA_FRAGMENTO = "ponteiro removido"

# Tipos de seção do CLAUDE.md antigo. VERBATIM = título parecido com Contexto/Mapa ("Contexto do negócio") ou o
# mesmo título com outra grafia: seção própria, inteira, sem classificar linha.
KIT, CONTEXTO, MAPA, REGRAS, OUTRA, VERBATIM, PREAMBULO = (
    "kit", "contexto", "mapa", "regras", "outra", "verbatim", "preambulo")
TITULOS_EXATOS = {"contexto": CONTEXTO, "mapa de arquivos": MAPA, SECAO_REGRAS.casefold(): REGRAS}


@dataclass
class Migracao:
    claude_novo: str = ""
    regras_novas: dict = field(default_factory=dict)       # nome em .claude/rules/ → texto novo (só as alteradas)
    saiu_do_kit: list = field(default_factory=list)        # linhas NORMALIZADAS (⊂ linhas-do-kit.txt)
    moveu: list = field(default_factory=list)              # (linha, de, para)
    ficou_por_duvida: list = field(default_factory=list)   # linhas originais
    falhas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    ja_migrado: bool = False


# --- texto -------------------------------------------------------------------------------------------

def normalizar(linha: str) -> str:
    """Tira BOM, `\\r`, espaços das pontas e o marcador de lista (`- `, `* `, `N. `); colapsa espaços."""
    s = linha.replace("﻿", "").replace("\r", "").strip()
    s = RE_MARCADOR.sub("", s, count=1)
    return re.sub(r"\s+", " ", s).strip()


def _ler(p: Path):
    bruto = p.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in bruto else "\n"
    return bruto.replace("\r\n", "\n"), eol


def _lf(texto: str) -> str:
    return texto.replace("\r\n", "\n")


def _canon_rotulo(rotulo: str) -> str:
    return re.sub(r"\s+", " ", rotulo).strip().rstrip(":").strip().casefold()


def _rotulo(linha: str):
    m = RE_ROTULO.match(normalizar(linha))
    return _canon_rotulo(m.group(1)) if m else None


def _bytes(texto: str) -> int:
    return len(texto.encode("utf-8"))


# --- linhas do kit -----------------------------------------------------------------------------------

def _git_leitura(repo: Path, *args) -> str:
    """git SÓ de leitura (`--no-optional-locks`: nem o índice é atualizado)."""
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def gerar_linhas_do_kit(repo: Path) -> list:
    """Linhas normalizadas não vazias de TODAS as versões do molde no histórico do kit (renomeação inclusa)
    + o molde e os blocos de `templates/regras-do-kit/` como estão no disco. Ordenadas, sem repetição."""
    repo = Path(repo)
    log = _git_leitura(repo, "log", "--follow", "--format=%x00%H", "--name-only", "--", MOLDE_NO_GIT)
    textos = []
    for bloco in log.split("\x00"):
        partes = [p.strip() for p in bloco.strip().split("\n") if p.strip()]
        if len(partes) < 2:
            continue
        commit, caminho = partes[0], partes[-1]
        try:
            textos.append(_git_leitura(repo, "show", f"{commit}:{caminho}"))
        except RuntimeError:
            continue
    pasta = repo / "templates"
    textos.append((pasta / "CLAUDE.md").read_bytes().decode("utf-8"))
    for bloco in sorted((pasta / "regras-do-kit").glob("*.md")):
        textos.append(bloco.read_bytes().decode("utf-8"))
    return sorted({n for t in textos for n in (normalizar(l) for l in t.split("\n")) if n})


def carregar_linhas_do_kit() -> list:
    texto = ARQ_LINHAS_KIT.read_bytes().decode("utf-8")
    return [l for l in (x.strip("\r") for x in texto.split("\n")) if l]


def gravar_linhas_do_kit(repo: Path) -> int:
    linhas = gerar_linhas_do_kit(repo)
    ARQ_LINHAS_KIT.write_bytes(("\n".join(linhas) + "\n").encode("utf-8"))
    return len(linhas)


# --- estrutura do CLAUDE.md --------------------------------------------------------------------------

def _secoes(texto: str) -> list:
    """[(título ou None no preâmbulo, cabeçalho ou None, [linhas do corpo])]. `## ` dentro de comentário HTML
    ou de bloco de código não abre seção."""
    out, titulo, cab, corpo = [], None, None, []
    em_comentario = em_codigo = False
    for l in texto.split("\n"):
        m = RE_SECAO.match(l)
        if m and not em_comentario and not em_codigo:
            out.append((titulo, cab, corpo))
            titulo, cab, corpo = m.group(1), l, []
            continue
        corpo.append(l)
        if l.strip().startswith("```"):
            em_codigo = not em_codigo
        elif not em_codigo:
            em_comentario = _dentro_de_comentario(l, em_comentario)
    out.append((titulo, cab, corpo))
    return out


def _dentro_de_comentario(linha: str, estava: bool) -> bool:
    pos = 0
    while True:
        if estava:
            fim = linha.find("-->", pos)
            if fim < 0:
                return True
            estava, pos = False, fim + 3
        else:
            ini = linha.find("<!--", pos)
            if ini < 0:
                return False
            estava, pos = True, ini + 4


def _unidades(corpo: list) -> list:
    """Agrupa o corpo em unidades que saem ou ficam INTEIRAS: comentário HTML de várias linhas; item com as
    linhas indentadas que o seguem; linha solta. Linhas vazias viram unidade vazia ([""])."""
    out, i = [], 0
    while i < len(corpo):
        l = corpo[i]
        if not l.strip():
            out.append([l])
            i += 1
            continue
        if _dentro_de_comentario(l, False):
            j = i + 1
            while j < len(corpo) and _comentario_aberto(corpo[i:j]):
                j += 1
            out.append(corpo[i:j])
            i = j
            continue
        j = i + 1
        while j < len(corpo) and corpo[j].strip() and corpo[j][:1] in " \t":
            j += 1
        out.append(corpo[i:j])
        i = j
    return out


def _comentario_aberto(linhas: list) -> bool:
    estado = False
    for l in linhas:
        estado = _dentro_de_comentario(l, estado)
    return estado


def _titulo_exato(titulo: str) -> str:
    """Título pra comparação EXATA: casefold, espaços colapsados, sem parêntese no fim
    (`Mapa de arquivos (só o que não se infere lendo o repo)` → `mapa de arquivos`)."""
    t = re.sub(r"\s+", " ", titulo).strip().casefold()
    return re.sub(r"\s*\([^()]*\)$", "", t).strip()


def _tipo(titulo, cab, linhas_kit) -> str:
    if titulo is None:
        return PREAMBULO
    t = titulo.casefold()
    if t.startswith(("modo de trabalho", "regras críticas", "regras criticas", "contexto de janela")):
        return KIT if normalizar(cab) in linhas_kit else OUTRA
    exato = TITULOS_EXATOS.get(_titulo_exato(titulo))
    if exato:
        return exato
    if t.startswith(("contexto", "mapa de arquivos")):
        return VERBATIM
    return OUTRA


def _tipos_das_secoes(texto: str, linhas_kit) -> list:
    """[(tipo, cabeçalho, corpo)] — Contexto/Mapa repetidos com o MESMO cabeçalho somam; com outra grafia viram
    VERBATIM (o `montar` e o `conferir` leem as seções do mesmo jeito)."""
    out, primeiro = [], {}
    for titulo, cab, corpo in _secoes(texto):
        tipo = _tipo(titulo, cab, linhas_kit)
        if tipo in (CONTEXTO, MAPA):
            if primeiro.setdefault(tipo, cab) != cab:
                tipo = VERBATIM
        out.append((tipo, cab, corpo))
    return out


def _corpo_do_tipo(texto: str, tipo: str, linhas_kit=frozenset()):
    """Corpo somado das seções do tipo (None se não há)."""
    corpos = [c for t, _, c in _tipos_das_secoes(texto, linhas_kit) if t == tipo]
    return None if not corpos else [l for c in corpos for l in c]


RE_LINHA_PONTEIRO = re.compile(r"^\*\*.+?\*\*\s*:?\s*→(.*)$")


def _aponta_doc_do_projeto(unidade: list) -> bool:
    """Linha-ponteiro (título em negrito e LOGO depois `→`) pra um arquivo que NÃO é de `.claude/rules/` (ex.:
    `**Nível de cerimônia** → texto inteiro em docs/MODO-DE-TRABALHO.md`). Seta no meio da frase não conta."""
    for l in unidade:
        m = RE_LINHA_PONTEIRO.match(normalizar(l))
        if not m:
            continue
        depois = m.group(1)
        alvos = [a or b for a, b in RE_ALVO_ARQUIVO.findall(depois)]
        alvos = [a for a in alvos if "/" in a or re.search(r"\.\w{1,5}$", a)]
        if alvos and not any(".claude/rules/" in a for a in alvos):
            return True
    return False


def _eh_ponteiro_rules(linha: str) -> bool:
    return "→" in linha and RE_ALVO_RULES.search(linha.split("→", 1)[1]) is not None


# --- regras do projeto (.claude/rules/) --------------------------------------------------------------

def _separar_frontmatter(texto: str):
    """(paths, corpo, ok). Mesmo jeito de `hooks/regra_antes_de_gravar.py` (copiado: o kit não importa hooks)."""
    linhas = texto.lstrip("﻿").split("\n")
    if not linhas or linhas[0].strip() != "---":
        return [], linhas, True
    fim = next((i for i in range(1, len(linhas)) if linhas[i].strip() == "---"), None)
    if fim is None:
        return [], linhas, False
    paths, em_paths = [], False
    for linha in linhas[1:fim]:
        chave = re.match(r"^paths:\s*(.*)$", linha)
        if chave:
            resto = chave.group(1).strip()
            em_paths = not resto
            if resto.startswith("[") and resto.endswith("]"):
                paths += [_aspas(p) for p in resto[1:-1].split(",") if _aspas(p)]
            elif resto:
                paths.append(_aspas(resto))
        elif em_paths and re.match(r"^\s*-\s", linha):
            item = _aspas(linha.strip()[1:])
            if item:
                paths.append(item)
        elif linha.strip() and not linha.startswith((" ", "\t")):
            em_paths = False
    return paths, linhas[fim + 1:], True


def _aspas(item: str) -> str:
    item = item.strip()
    if len(item) >= 2 and item[0] == item[-1] and item[0] in "\"'":
        item = item[1:-1]
    return item.strip()


def _ler_regras(proj: Path) -> dict:
    """{nome relativo a .claude/rules/ (com `/`): (texto LF, eol)} em ordem de nome."""
    pasta = Path(proj).joinpath(*PASTA_REGRAS)
    if not pasta.is_dir():
        return {}
    return {p.relative_to(pasta).as_posix(): _ler(p) for p in sorted(pasta.rglob("*.md")) if p.is_file()}


def _tirar_item(texto: str, rotulo: str):
    """(item, texto sem o item) — o item é a linha que começa com o rótulo em negrito + as linhas indentadas
    que a seguem. Some também 1 linha vazia vizinha, pra não sobrar buraco. Não achou / achou mais de 1 →
    (None, quantas)."""
    linhas = texto.split("\n")
    _, corpo, _ = _separar_frontmatter(texto)
    ini_corpo = len(linhas) - len(corpo)
    achados = [i for i in range(ini_corpo, len(linhas)) if _rotulo(linhas[i]) == rotulo]
    if len(achados) != 1:
        return None, len(achados)
    i = achados[0]
    j = i + 1
    while j < len(linhas) and linhas[j].strip() and linhas[j][:1] in " \t":
        j += 1
    item = linhas[i:j]
    ini, fim = i, j
    if fim < len(linhas) - 1 and not linhas[fim].strip():
        fim += 1
    elif ini > 0 and not linhas[ini - 1].strip():
        ini -= 1
    return item, "\n".join(linhas[:ini] + linhas[fim:])


def _linha_indice(nome: str, texto: str) -> str:
    paths, corpo, ok = _separar_frontmatter(texto)
    titulo = next((l[2:].strip() for l in corpo if l.startswith("# ")), nome[:-3])
    if not ok:
        quando = "frontmatter sem fechamento: confira o `paths:`"
    elif paths:
        quando = "carrega ao tocar " + ", ".join(f"`{p}`" for p in paths)
    else:
        quando = "carrega sempre"
    return f"- `.claude/rules/{nome}` — {titulo} — {quando}"


def _so_titulo(texto: str) -> bool:
    _, corpo, _ = _separar_frontmatter(texto)
    estado, sobra = False, []
    for l in corpo:
        dentro = estado or "<!--" in l
        estado = _dentro_de_comentario(l, estado)
        if l.strip() and not l.startswith("# ") and not dentro:
            sobra.append(l)
    return not sobra


# --- montar ------------------------------------------------------------------------------------------

def _cabeca_do_molde() -> list:
    linhas = _lf(MOLDE.read_bytes().decode("utf-8")).split("\n")
    fim = next(i for i, l in enumerate(linhas) if l.strip() == MARCA)
    return linhas[:fim + 1]


def _juntar(linhas: list) -> list:
    """Tira vazias das pontas e colapsa vazias seguidas."""
    out = []
    for l in linhas:
        if not l.strip() and (not out or not out[-1].strip()):
            continue
        out.append(l)
    while out and not out[-1].strip():
        out.pop()
    return out


def montar(proj: Path, linhas_kit: set, teto: int = TETO_PROJETO) -> Migracao:
    proj = Path(proj)
    linhas_kit = set(linhas_kit)
    mig = Migracao()
    arq = proj / "CLAUDE.md"
    if not arq.is_file():
        mig.falhas.append(f"não existe {arq}")
        return mig
    bruto = arq.read_bytes().decode("utf-8")
    if any(l.strip() == MARCA for l in _lf(bruto).split("\n")):
        mig.claude_novo, mig.ja_migrado = bruto, True
        return mig
    texto, eol = _ler(arq)
    regras = {n: t for n, (t, _) in _ler_regras(proj).items()}
    eol_regras = {n: e for n, (_, e) in _ler_regras(proj).items()}
    atuais = dict(regras)
    titulos_kit = {r for r in (_rotulo(l) for l in linhas_kit) if r}
    tirados = set()

    preambulo, regras_proj, contexto, mapa, outras = [], [], None, None, []
    for tipo, cab, corpo in _tipos_das_secoes(texto, linhas_kit):
        if tipo == CONTEXTO:
            novo = []
            for un in _unidades(corpo):
                if _eh_ponteiro_rules(un[0]):
                    novo += _trocar_ponteiro(un, atuais, tirados, mig)
                elif RE_FRAGMENTO.search(un[0]):
                    novo += _tirar_fragmento(un, atuais, mig)
                else:
                    novo += un
            contexto = (cab, (contexto[1] + [""] if contexto else []) + novo)
            continue
        if tipo == MAPA:
            mapa = (cab, (mapa[1] + [""] if mapa else []) + corpo)
            continue
        if tipo == REGRAS:
            regras_proj += [""] + corpo
            continue
        if tipo == VERBATIM:
            outras.append((cab, corpo))
            continue
        ficam = []
        for un in _unidades(corpo):
            if not un[0].strip():
                ficam += un
                continue
            if tipo == PREAMBULO and un[0].startswith("# "):
                ficam += un
            elif _aponta_doc_do_projeto(un):
                ficam += un
            elif all(normalizar(l) in linhas_kit for l in un if l.strip()):
                mig.saiu_do_kit += [normalizar(l) for l in un if l.strip()]
            else:
                ficam += un
                if tipo == KIT and _rotulo(un[0]) in titulos_kit:
                    mig.ficou_por_duvida.append(un[0])
        if tipo == PREAMBULO:
            preambulo += ficam
        elif tipo == KIT:
            mig.saiu_do_kit.append(normalizar(cab))
            regras_proj += [""] + ficam
            mig.moveu += [(l, f"CLAUDE.md › {cab}", f"CLAUDE.md › ## {SECAO_REGRAS}") for l in ficam if l.strip()]
        elif not [l for l in ficam if l.strip()] and normalizar(cab) in linhas_kit:
            mig.saiu_do_kit.append(normalizar(cab))
        else:
            outras.append((cab, ficam))

    for nome in sorted(atuais):
        if atuais[nome] != regras[nome]:
            mig.regras_novas[nome] = atuais[nome].replace("\n", eol_regras[nome])
            if _so_titulo(atuais[nome]):
                mig.avisos.append(f"`.claude/rules/{nome}` ficou só com título/comentário: o item voltou pro "
                                  "`## Contexto` — decida se o arquivo ainda tem regra de escrita")

    partes = _cabeca_do_molde() + [""] + _juntar(preambulo)
    if _juntar(regras_proj):
        partes += ["", f"## {SECAO_REGRAS}"] + _juntar(regras_proj)
    if contexto is None:
        mig.avisos.append("o CLAUDE.md não tem `## Contexto`: preencha os fatos do projeto (Infra, Stack, Como roda…)")
    else:
        partes += ["", contexto[0]] + _juntar(contexto[1])
    if mapa is not None:
        partes += ["", mapa[0]] + _juntar(mapa[1])
    for cab, corpo in outras:
        partes += ["", cab] + _juntar(corpo)
    if atuais:
        partes += ["", f"## {SECAO_INDICE}"] + [_linha_indice(n, atuais[n]) for n in sorted(atuais)]
    mig.claude_novo = ("\n".join(partes).rstrip("\n") + "\n").replace("\n", eol)

    tamanho = _bytes(mig.claude_novo)
    if tamanho > teto:
        mig.avisos.append(f"CLAUDE.md novo com {tamanho} B, acima do teto de {teto} B — é aviso, não trava: mova um "
                          "bloco pra `docs/`/spec com ponteiro, nunca comprima (o `## Contexto` nunca sai)")
    return mig


def _tirar_fragmento(un: list, atuais: dict, mig: Migracao) -> list:
    """Fato + ` — ver `.claude/rules/x.md`` no `## Contexto`: o fato fica, só o fragmento sai (x.md está no índice).
    x.md não existe → falha e a linha fica como está."""
    linha = un[0]
    nome = RE_FRAGMENTO.search(linha).group(1)
    if nome not in atuais:
        mig.falhas.append(f"ponteiro do `## Contexto` pra `.claude/rules/{nome}`, que não existe: {linha}")
        return un
    mig.moveu.append((linha, "CLAUDE.md › ## Contexto", f"{PARA_FRAGMENTO}: `.claude/rules/{nome}` (fica no índice)"))
    return [RE_FRAGMENTO.sub("", linha, count=1)] + un[1:]


def _trocar_ponteiro(un: list, atuais: dict, tirados: set, mig: Migracao) -> list:
    """Ponteiro do `## Contexto` → o item de mesmo rótulo do arquivo de regra. Falhou → a linha fica e vira falha."""
    linha = un[0]
    alvos = set(RE_ALVO_RULES.findall(linha.split("→", 1)[1]))
    rotulo = _rotulo(linha)
    if len(alvos) != 1 or not rotulo:
        mig.falhas.append(f"ponteiro do `## Contexto` sem rótulo em negrito ou com mais de um arquivo: {linha}")
        return un
    nome = alvos.pop()
    if nome not in atuais:
        mig.falhas.append(f"ponteiro do `## Contexto` pra `.claude/rules/{nome}`, que não existe: {linha}")
        return un
    if (nome, rotulo) in tirados:
        mig.falhas.append(f"rótulo repetido no `## Contexto` pro mesmo arquivo `.claude/rules/{nome}`: {linha}")
        return un
    item, resto = _tirar_item(atuais[nome], rotulo)
    if item is None:
        qual = "não existe" if resto == 0 else f"aparece {resto} vezes"
        mig.falhas.append(f"rótulo do `## Contexto` {qual} em `.claude/rules/{nome}`: {linha}")
        return un
    atuais[nome] = resto
    tirados.add((nome, rotulo))
    mig.moveu += [(l, f".claude/rules/{nome}", "CLAUDE.md › ## Contexto") for l in item if l.strip()]
    return item + un[1:]


# --- conferir ----------------------------------------------------------------------------------------

def _corpo_secao(texto: str, inicio: str):
    """Linhas do corpo da 1ª seção cujo título começa com `inicio` (ou None)."""
    for titulo, _, corpo in _secoes(texto):
        if titulo is not None and titulo.casefold().startswith(inicio.casefold()):
            return corpo
    return None


def _git_status(proj: Path, tocados: list) -> list:
    falhas = []
    base = ["git", "--no-optional-locks", "-C", str(proj)]
    try:
        dentro = subprocess.run(base + ["rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    except OSError as e:
        return [f"sem git não há ponto de volta (git não roda: {e})"]
    if dentro.returncode or dentro.stdout.strip() != "true":
        return [f"sem git não há ponto de volta: {proj} não está num repositório git"]
    rastreados = subprocess.run(base + ["ls-files", "-z", "--", *tocados], capture_output=True)
    fora = sorted(set(tocados) - set(rastreados.stdout.decode("utf-8", "replace").split("\x00")))
    if rastreados.returncode or fora:
        falhas.append("arquivo que a migração toca está fora do git (sem ponto de volta): " + ", ".join(fora))
    st = subprocess.run(base + ["status", "--porcelain", "-z", "--", *tocados], capture_output=True)
    sujos = [s for s in st.stdout.decode("utf-8", "replace").split("\x00") if s.strip()]
    if st.returncode:
        falhas.append(f"git status falhou: {st.stderr.decode('utf-8', 'replace').strip()}")
    elif sujos:
        falhas.append("working tree sujo nos arquivos que a migração toca — commite ou descarte antes: "
                      + " | ".join(sujos))
    return falhas


def conferir(proj: Path, m: Migracao, linhas_kit=None) -> list:
    """Falhas que impedem gravar (vazio = ok). Só lê: nem o projeto nem o git do projeto mudam."""
    if m.ja_migrado:
        return []
    proj = Path(proj)
    falhas = list(m.falhas)
    linhas_kit = set(carregar_linhas_do_kit() if linhas_kit is None else linhas_kit)
    arq = proj / "CLAUDE.md"
    if not arq.is_file():
        return falhas or [f"não existe {arq}"]
    antes, _ = _ler(arq)
    regras_antes = {n: t for n, (t, _) in _ler_regras(proj).items()}
    novo = _lf(m.claude_novo)
    sobrando = sorted(set(m.regras_novas) - set(regras_antes))
    if sobrando:
        falhas.append("arquivo de regra alterado que não existe no projeto: " + ", ".join(sobrando))
    regras_depois = {n: _lf(m.regras_novas.get(n, t)) for n, t in regras_antes.items()}

    # marca
    if MARCA not in [l.strip() for l in novo.split("\n")]:
        falhas.append(f"marca `{MARCA}` ausente do CLAUDE.md novo")

    # índice: cada regra uma vez; todo arquivo de regra citado existe
    indice = _corpo_secao(novo, SECAO_INDICE)
    corpo_indice = "\n".join(indice or [])
    for nome in regras_antes:
        vezes = corpo_indice.count(f"`.claude/rules/{nome}`")
        if vezes != 1:
            falhas.append(f"índice cita `.claude/rules/{nome}` {vezes} vez(es) — tem que ser 1")
    for nome in sorted(set(RE_CITA_RULES.findall(novo))):
        if nome not in regras_antes:
            falhas.append(f"CLAUDE.md novo cita `.claude/rules/{nome}`, que não existe")

    # fatos sempre carregados: Contexto sem ponteiro e com os rótulos de antes
    ctx_antes = _corpo_do_tipo(antes, CONTEXTO, linhas_kit) or []
    ctx_novo = _corpo_do_tipo(novo, CONTEXTO, linhas_kit)
    if ctx_antes and ctx_novo is None:
        falhas.append("a seção `## Contexto` sumiu do CLAUDE.md novo")
    ctx_novo = ctx_novo or []
    for l in ctx_novo:
        if ".claude/rules/" in l:
            falhas.append(f"`## Contexto` ainda aponta pra `.claude/rules/` (fato atrás de gatilho de arquivo): {l}")
    rotulos_novos = {_rotulo(l) for l in ctx_novo if not l[:1].isspace()} - {None}
    for l in ctx_antes:
        r = _rotulo(l)
        if r and not l[:1].isspace() and r not in rotulos_novos:
            falhas.append(f"rótulo do `## Contexto` sumiu: {l.strip()}")

    # conservação, por CONTAGEM: cada ocorrência do antes casa com uma ocorrência do depois, ou com uma saída
    # como do kit, ou é uma das duas transformações registradas do `## Contexto` (ponteiro → item; fragmento
    # `— ver .claude/rules/x.md` tirado). Cabeçalho `## ` conta por presença (Contexto/Mapa repetido é somado).
    saiu = Counter(m.saiu_do_kit)
    fora_do_kit = sorted(set(saiu) - linhas_kit)
    if fora_do_kit:
        falhas.append("saiu como do kit, mas não está em linhas-do-kit.txt: " + " | ".join(fora_do_kit))
    depois = Counter(normalizar(l) for t in [novo, *regras_depois.values()] for l in t.split("\n"))
    ponteiros_ok = {l for l in ctx_antes if _eh_ponteiro_rules(l) and _rotulo(l) in rotulos_novos
                    and all(f"`.claude/rules/{n}`" in corpo_indice for n in RE_ALVO_RULES.findall(l))}
    fragmentos = {linha for linha, de, para in m.moveu
                  if de == "CLAUDE.md › ## Contexto" and para.startswith(PARA_FRAGMENTO)}
    com_fragmento = []
    origem = [("CLAUDE.md", antes)] + [(f".claude/rules/{n}", t) for n, t in regras_antes.items()]
    for nome, texto in origem:
        for l in texto.split("\n"):
            n = normalizar(l)
            if not n:
                continue
            if nome == "CLAUDE.md" and l in ponteiros_ok:
                continue
            if nome == "CLAUDE.md" and l in fragmentos and l in ctx_antes:
                com_fragmento.append(l)
                continue
            if nome == "CLAUDE.md" and l.startswith("## ") and depois[n] > 0:
                continue
            if depois[n] > 0:
                depois[n] -= 1
            elif saiu[n] > 0 and n in linhas_kit:
                saiu[n] -= 1
            else:
                falhas.append(f"conservação: linha sem destino ({nome}): {l.strip()}")
    for l in com_fragmento:
        alvo = RE_FRAGMENTO.search(l)
        fato = normalizar(RE_FRAGMENTO.sub("", l, count=1))
        if alvo and f"`.claude/rules/{alvo.group(1)}`" in corpo_indice and depois[fato] > 0:
            depois[fato] -= 1
        else:
            falhas.append(f"conservação: linha sem destino (CLAUDE.md): {l.strip()}")

    # ponto de volta
    tocados = ["CLAUDE.md"] + [f".claude/rules/{n}" for n in sorted(m.regras_novas)]
    falhas += _git_status(proj, tocados)
    return falhas


# --- CLI ---------------------------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("historico", help="regenera regras-do-kit/linhas-do-kit.txt a partir do git do kit")
    args = ap.parse_args(argv)
    if args.cmd == "historico":
        n = gravar_linhas_do_kit(PASTA_TEMPLATES.parent)
        print(f"{ARQ_LINHAS_KIT}: {n} linhas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
