# Orçamento de partida e recall determinístico — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Limitar por script e teste o que o kit enfia na janela em toda partida (índice de memória em dois níveis, rodízio mecânico do MAPA/INDEX) e entregar o recall por hook, injetando só os ponteiros que casam com o prompt — sem apagar conteúdo em lugar nenhum.

**Architecture:** Dois scripts novos em `templates/` (`memoria_indice.py` = dividir/verificar/fila/buscar + o motor de casamento; `rodizio_partida.py` = mapa/index), um hook novo em `hooks/` (`recall_memoria.py`, `UserPromptSubmit`, ligado, não bloqueia, falha aberta) que importa o motor do `templates/`, e correção de texto em todos os pontos que citavam "acima de 25 KB o excedente não carrega" para o índice do repo. Todo script é dry-run por padrão e só grava com `--aplicar` após checar conservação byte a byte.

**Tech Stack:** Python 3 stdlib (re, json, argparse, pathlib, dataclasses, unicodedata), pytest. Sem dependência nova. Windows: leitura/gravação preservando o EOL original (`newline=""`).

**Spec:** `docs/superpowers/specs/2026-09-15-orcamento-de-partida-e-recall-deterministico-design.md`

**Branch:** `feature/orcamento-de-partida-e-recall` (já criada; a spec é o 1º commit).

---

## Mapa de arquivos

| arquivo | papel |
|---|---|
| `templates/memoria_indice.py` (novo) | parse do índice plano · `dividir` · `verificar` · `fila` · `buscar` · motor `casar()` (usado pelo hook) |
| `hooks/recall_memoria.py` (novo) | hook `UserPromptSubmit`: lê o prompt, chama `casar()`, injeta ≤ 600 B via `additionalContext`; falha aberta |
| `templates/rodizio_partida.py` (novo) | `mapa` (mantém 2 blocos por seção) · `index` (move `fechada`) · histórico com prepend datado |
| `hooks/hooks.json` | registra o `recall_memoria.py` em `UserPromptSubmit` (2ª entrada) |
| `hooks/README.md` | 5ª linha da tabela + seção curta do recall |
| `templates/MEMORY.md` | vira molde do **topo** (famílias) e explica `memory/indice/` |
| `templates/CLAUDE.md:20` | regra de leitura: topo na partida; família bateu → abre o subíndice |
| `commands/memory.md` | passo 3 do `capturar` (grava no subíndice, teto = orçamento) + modo `buscar` |
| `commands/doctor.md` | checks 8 e 9: roda `verificar`; imprime o comando exato do conserto mecânico |
| `commands/upgrade.md` | oferece `dividir` (dry-run) quando acha índice plano |
| `templates/anatomia.py:24-29` | `TETOS["memory/MEMORY.md"] = 6000` |
| `tests/fixtures/memoria_whats_2026-09-14/MEMORY.md` (novo) | cópia do índice do Whats (93 memórias, 5 seções) |
| `tests/test_memoria_indice.py` (novo) | dividir/verificar/fila/buscar/casar |
| `tests/test_hook_recall_memoria.py` (novo) | hook por módulo e por subprocesso |
| `tests/test_rodizio_partida.py` (novo) | mapa/index |
| `tests/test_orcamento_contexto.py` | `TETO_MEMORY_TOPO`, moldes sem "não carrega" fora da nativa |
| `tests/test_memoria_gatilho.py` | lê as linhas dos subíndices; teto do topo |
| `tests/test_smoke_kit.py` | hook registrado + README com 5 hooks |
| `memory/MEMORY.md` + `memory/indice/*.md` (kit) | dogfood: o próprio kit dividido pelo script |
| `CHANGELOG.md` · `.claude-plugin/plugin.json` · `docs/decisoes.md` · `docs/EVALS.md` · `docs/superpowers/INDEX.md` · `docs/superpowers/MAPA.md` | registro 0.27.0 |

Comando de teste do repo: `python -m pytest tests -q` (rodar na raiz do kit).

---

### Task 1: Fixture do índice do Whats

**Files:**
- Create: `tests/fixtures/memoria_whats_2026-09-14/MEMORY.md`

- [ ] **Step 1: Copiar o índice (só leitura no outro projeto)**

```bash
mkdir -p tests/fixtures/memoria_whats_2026-09-14
cp "/c/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats/memory/MEMORY.md" tests/fixtures/memoria_whats_2026-09-14/MEMORY.md
wc -c -l tests/fixtures/memoria_whats_2026-09-14/MEMORY.md
```

Expected: `128 25421` (linhas, bytes). Se o Whats tiver mudado desde 2026-09-14, a contagem pode variar; o que importa é ter 5 seções `## ` e ≥ 90 linhas `- [`.

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/memoria_whats_2026-09-14/MEMORY.md
git commit -m "test(memoria): fixture do indice plano do Whats (93 memorias, 5 secoes)"
```

---

### Task 2: `memoria_indice.py` — parse e `dividir` (dry-run)

**Files:**
- Create: `templates/memoria_indice.py`
- Test: `tests/test_memoria_indice.py`

- [ ] **Step 1: Escrever os testes de parse e dividir (falham)**

```python
"""memoria_indice.py — índice de memória em dois níveis (topo por família + memory/indice/).

Por que existe: o índice plano do Whats chegou a 25.421 bytes (~6.355 tokens em TODA janela) e o kit
mandou PODAR — contra a própria decisão "mover, nunca apagar". O topo passa a ter 1 linha por família
(teto 6 KB) e as memórias vivem em subíndices lidos só quando a família bate.
"""
import importlib.util
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_indice.py"
FIXTURE = REPO / "tests" / "fixtures" / "memoria_whats_2026-09-14" / "MEMORY.md"

FRONT_COM_GATILHO = "---\nname: {name}\ndescription: {desc}\ngatilho: quando {gat}\nmetadata:\n  type: project\n---\n\ncorpo\n"
FRONT_SEM_GATILHO = "---\nname: {name}\ndescription: {desc}\nmetadata:\n  type: project\n---\n\ncorpo\n"


def _mod():
    spec = importlib.util.spec_from_file_location("memoria_indice", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _projeto_whats(tmp_path, com_gatilho=("app-setting-faltando-cai-no-default.md",
                                          "chatwoot-deduplica-contato-por-telefone.md")):
    """Projeto sintético: o índice REAL do Whats + um stub por arquivo apontado (2 com gatilho)."""
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    mem.mkdir(parents=True)
    shutil.copy(FIXTURE, mem / "MEMORY.md")
    for arq in re.findall(r"\]\(([^)/]+\.md)\)", FIXTURE.read_text(encoding="utf-8")):
        if arq == "<arquivo>.md":
            continue
        molde = FRONT_COM_GATILHO if arq in com_gatilho else FRONT_SEM_GATILHO
        (mem / arq).write_text(molde.format(name=arq[:-3], desc=f"desc de {arq}",
                                            gat=f"a situação de {arq[:-3].replace('-', ' ')}"),
                               encoding="utf-8")
    return raiz


# --- parse ---------------------------------------------------------------------------

def test_le_5_familias_e_93_itens_do_indice_do_whats():
    mod = _mod()
    fams = mod.ler_indice_plano(FIXTURE.read_text(encoding="utf-8"))
    assert [f.titulo for f in fams] == ["Como trabalhar neste projeto", "Ambiente e build", "Integrações",
                                        "Padrões e ferramentas", "Como eu devo trabalhar (correções do owner)"]
    assert sum(len(f.itens) for f in fams) == 93
    assert fams[1].itens[0].titulo == "Build quebra por CA desatualizada"
    assert fams[1].itens[0].arquivo == "build-quebra-por-ca-desatualizada.md"


def test_slug_sem_acento_sem_parenteses():
    mod = _mod()
    assert mod.slug("Como eu devo trabalhar (correções do owner)") == "como-eu-devo-trabalhar"
    assert mod.slug("Integrações") == "integracoes"


def test_relink_so_muda_link_local():
    mod = _mod()
    assert mod.relink("- [T](arquivo.md) — g") == "- [T](../arquivo.md) — g"
    assert mod.relink("- **quando x** → [T](arquivo.md) — veja [[outra]] e https://a.b/c.md") == \
        "- **quando x** → [T](../arquivo.md) — veja [[outra]] e https://a.b/c.md"
    assert mod.relink("- [T](../arquivo.md) — g") == "- [T](../arquivo.md) — g"


# --- dividir ---------------------------------------------------------------------------

def test_dividir_dry_run_nao_escreve_nada(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    antes = (raiz / "memory" / "MEMORY.md").read_bytes()
    rel = mod.dividir(raiz / "memory", aplicar=False)
    assert rel.ok, rel.problemas
    assert not (raiz / "memory" / "indice").exists()
    assert (raiz / "memory" / "MEMORY.md").read_bytes() == antes
    assert len(rel.familias) == 5 and rel.bytes_topo < 6000


def test_dividir_aplicar_conserva_toda_linha_byte_a_byte(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    linhas_antes = [l for l in FIXTURE.read_text(encoding="utf-8").splitlines() if l.startswith("- [")]
    rel = mod.dividir(raiz / "memory", aplicar=True)
    assert rel.ok, rel.problemas
    subs = sorted((raiz / "memory" / "indice").glob("*.md"))
    assert [p.name for p in subs] == ["ambiente-e-build.md", "como-eu-devo-trabalhar.md",
                                      "como-trabalhar-neste-projeto.md", "integracoes.md", "padroes-e-ferramentas.md"]
    linhas_depois = [l for p in subs for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    assert len(linhas_depois) == len(linhas_antes) == 93
    assert sorted(linhas_depois) == sorted(mod.relink(l) for l in linhas_antes)
    topo = (raiz / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert "<!-- MODELO" not in topo, "o comentário-modelo não é memória: sai do topo"
    assert topo.count("→ [subíndice](indice/") == 5
    assert "— 22 memórias" in topo  # Ambiente e build


def test_topo_usa_frases_do_gatilho_e_nao_palavras_raspadas(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    mod.dividir(raiz / "memory", aplicar=True)
    topo = (raiz / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    linha_amb = next(l for l in topo.splitlines() if "indice/ambiente-e-build.md" in l)
    assert "a situação de app setting faltando cai no default" in linha_amb
    linha_padroes = next(l for l in topo.splitlines() if "indice/padroes-e-ferramentas.md" in l)
    assert "quando:" not in linha_padroes, "família sem nenhum gatilho: sai só com título e N"
    for lixo in ("Esta", ".md ·", "GET"):
        assert lixo not in topo


def test_dividir_recusa_quando_ponteiro_quebrado(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    (raiz / "memory" / "build-quebra-por-ca-desatualizada.md").unlink()
    rel = mod.dividir(raiz / "memory", aplicar=True)
    assert not rel.ok
    assert any("build-quebra-por-ca-desatualizada.md" in p for p in rel.problemas)
    assert not (raiz / "memory" / "indice").exists(), "conservação falhou: NADA se grava"


def test_dividir_recusa_linha_solta_dentro_de_secao(tmp_path):
    """Linha que não é item nem vazia dentro de uma seção seria perdida em silêncio: o script recusa."""
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    p = raiz / "memory" / "MEMORY.md"
    p.write_text(p.read_text(encoding="utf-8").replace("## Integrações\n", "## Integrações\nNota solta que não é item.\n"), encoding="utf-8")
    rel = mod.dividir(raiz / "memory", aplicar=True)
    assert not rel.ok and any("linha solta" in x and "Integrações" in x for x in rel.problemas)
    assert not (raiz / "memory" / "indice").exists()


def test_dividir_preserva_crlf(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    p = raiz / "memory" / "MEMORY.md"
    p.write_bytes(p.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    mod.dividir(raiz / "memory", aplicar=True)
    assert b"\r\n" in p.read_bytes()
    assert b"\r\n" in (raiz / "memory" / "indice" / "integracoes.md").read_bytes()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_memoria_indice.py -q`
Expected: erro de import/`FileNotFoundError` em `templates/memoria_indice.py` (módulo não existe).

- [ ] **Step 3: Implementar parse + dividir**

```python
"""memoria_indice.py — índice de memória do projeto em DOIS níveis.

Topo (`memory/MEMORY.md`): 1 linha por FAMÍLIA de gatilho, teto 6 KB — é o que entra em toda janela.
Subíndice (`memory/indice/<familia>.md`): 1 linha por memória, aberto só quando a família bate.

Por que: o índice plano cresce 1 linha por memória; num projeto grande (93 memórias no Whats) passou de
25 KB (~6.400 tokens em TODA janela) e o kit mandou podar — contra a decisão "mover, nunca apagar".
Este script MOVE: `dividir` é dry-run por padrão, verifica conservação byte a byte e só grava com
`--aplicar`. `verificar` audita o par topo+subíndices; `fila` lista o que falta de conteúdo (memória
sem `gatilho:`); `buscar` acha ponteiros por termo — o mesmo motor `casar()` que o hook de recall usa.

Uso:  python memoria_indice.py dividir  [--proj DIR] [--aplicar]
      python memoria_indice.py verificar [--proj DIR] [--aplicar]   (--aplicar corrige o N do topo)
      python memoria_indice.py fila      [--proj DIR]
      python memoria_indice.py buscar    "<termo>" [--proj DIR] [--limite N]
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

TETO_TOPO = 6000          # bytes — entra em toda janela
TETO_LINHA = 600          # bytes — linha maior é procedimento disfarçado de índice
INDICES = {"MEMORY.md", "DIARIO.md"}
SUBDIR = "indice"
MAX_FRASES = 4
MAX_FRASE = 60

RE_SECAO = re.compile(r"^## +(.*\S)\s*$")
RE_ITEM = re.compile(r"^- (?P<prefixo>.*?)\[(?P<titulo>[^\]]+)\]\((?P<arquivo>[^)]+)\)(?P<resto>.*)$")
RE_LINK_LOCAL = re.compile(r"\]\((?!\.\./)(?![a-z]+://)([^)/]+\.md)\)")
RE_FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)


@dataclass
class Item:
    linha: str
    titulo: str
    arquivo: str          # relativo a memory/


@dataclass
class Familia:
    titulo: str
    itens: list = field(default_factory=list)

    @property
    def slug(self) -> str:
        return slug(self.titulo)


@dataclass
class Relatorio:
    familias: list = field(default_factory=list)
    topo: str = ""
    bytes_antes: int = 0
    bytes_topo: int = 0
    problemas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    gravou: bool = False

    @property
    def ok(self) -> bool:
        return not self.problemas


# ------------------------------------------------------------------ utilidades de texto

def _ler(p: Path):
    """(texto com \\n, eol original) — preserva CRLF de repo Windows."""
    bruto = p.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in bruto else "\n"
    return bruto.replace("\r\n", "\n"), eol


def _gravar(p: Path, texto: str, eol: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(texto.replace("\n", eol).encode("utf-8"))


def slug(titulo: str) -> str:
    s = re.sub(r"\(.*?\)", "", titulo)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def relink(linha: str) -> str:
    """`](arquivo.md)` → `](../arquivo.md)`; não toca em `../`, URL nem `[[wikilink]]`."""
    return RE_LINK_LOCAL.sub(r"](../\1)", linha)


def frontmatter(p: Path) -> dict:
    try:
        texto, _ = _ler(p)
    except (OSError, UnicodeDecodeError):
        return {}
    m = RE_FRONT.match(texto)
    if not m:
        return {}
    campos = {}
    for l in m.group(1).splitlines():
        mm = re.match(r"^([a-z_]+):\s*(.*)$", l)
        if mm:
            campos[mm.group(1)] = mm.group(2).strip()
    return campos


# ------------------------------------------------------------------ parse

def ler_indice_plano(texto: str, soltas: list | None = None) -> list:
    """Famílias com itens. `soltas` (se passado) recebe (família, linha) de toda linha não vazia dentro
    de uma seção que NÃO é item — o `dividir` recusa nesse caso, pra nada sumir em silêncio."""
    fams, atual = [], None
    for linha in texto.replace("\r\n", "\n").split("\n"):
        m = RE_SECAO.match(linha)
        if m:
            atual = Familia(m.group(1))
            fams.append(atual)
            continue
        mi = RE_ITEM.match(linha)
        if mi and atual is not None:
            atual.itens.append(Item(linha, mi.group("titulo"), mi.group("arquivo")))
        elif atual is not None and linha.strip() and soltas is not None:
            soltas.append((atual.titulo, linha))
    return [f for f in fams if f.itens]


def _frase(gatilho: str) -> str:
    g = re.sub(r"^(quando|ao|na|no|em)\s+", "", gatilho.strip(), flags=re.I)
    g = re.split(r"\s+[—–-]\s+|;|\(", g, 1)[0].strip().rstrip(".:")
    return g if len(g) <= MAX_FRASE else g[:MAX_FRASE].rsplit(" ", 1)[0] + "…"


def frases_de_gatilho(fam: Familia, memdir: Path) -> list:
    frases = []
    for it in fam.itens:
        g = frontmatter(memdir / it.arquivo).get("gatilho")
        if g:
            f = _frase(g)
            if f and f not in frases:
                frases.append(f)
        if len(frases) >= MAX_FRASES:
            break
    return frases


def montar_topo(fams: list, memdir: Path) -> str:
    out = ["# Memória do projeto — índice por gatilho", "",
           "<!-- 1 linha por FAMÍLIA. Gatilho bateu? abra o subíndice da família ANTES de agir.",
           f"     Teto deste topo: {TETO_TOPO // 1000} KB (orçamento de partida). Memória nova entra no",
           "     subíndice; `python memoria_indice.py verificar` confere e corrige o N. -->", ""]
    for f in fams:
        frases = frases_de_gatilho(f, memdir)
        cauda = f" · quando: {' · '.join(frases)}" if frases else ""
        out.append(f"- **{f.titulo}** → [subíndice]({SUBDIR}/{f.slug}.md) — {len(f.itens)} memórias{cauda}")
    return "\n".join(out) + "\n"


def montar_subindice(f: Familia) -> str:
    return "\n".join([f"# {f.titulo}", ""] + [relink(it.linha) for it in f.itens]) + "\n"


# ------------------------------------------------------------------ dividir

def dividir(memdir: Path, aplicar: bool = False) -> Relatorio:
    memdir = Path(memdir)
    rel = Relatorio()
    idx = memdir / "MEMORY.md"
    if not idx.is_file():
        rel.problemas.append(f"não existe {idx}")
        return rel
    texto, eol = _ler(idx)
    rel.bytes_antes = len(texto.encode("utf-8"))
    if (memdir / SUBDIR).exists():
        rel.problemas.append(f"{memdir / SUBDIR} já existe — o índice já foi dividido? use `verificar`")
        return rel
    soltas = []
    fams = ler_indice_plano(texto, soltas)
    if not fams:
        rel.problemas.append("nenhuma seção `## ` com itens `- [Título](arquivo.md)` no índice")
        return rel
    for fam, linha in soltas:
        rel.problemas.append(f"linha solta (não é item) em '{fam}' — seria perdida: {linha[:80]!r}")
    # conservação 1: nenhum ponteiro quebrado
    for f in fams:
        for it in f.itens:
            if "/" not in it.arquivo and not (memdir / it.arquivo).is_file():
                rel.problemas.append(f"ponteiro quebrado em '{f.titulo}': {it.arquivo}")
    # conservação 2: slug único
    slugs = [f.slug for f in fams]
    for s in set(slugs):
        if slugs.count(s) > 1:
            rel.problemas.append(f"duas seções viram o mesmo subíndice: {s}")
    if rel.problemas:
        return rel
    rel.familias = fams
    rel.topo = montar_topo(fams, memdir)
    rel.bytes_topo = len(rel.topo.encode("utf-8"))
    if rel.bytes_topo > TETO_TOPO:
        rel.problemas.append(f"topo ficaria com {rel.bytes_topo} bytes (teto {TETO_TOPO}) — famílias demais?")
        return rel
    subs = {f.slug: montar_subindice(f) for f in fams}
    # conservação 3: cada linha original reaparece (relinkada) exatamente uma vez
    originais = sorted(relink(it.linha) for f in fams for it in f.itens)
    movidas = sorted(l for s in subs.values() for l in s.split("\n") if l.startswith("- "))
    if originais != movidas:
        rel.problemas.append("conservação falhou: linhas movidas ≠ linhas originais")
        return rel
    gordas = [l for l in movidas if len(l.encode("utf-8")) > TETO_LINHA]
    if gordas:
        rel.avisos.append(f"{len(gordas)} linha(s) acima de {TETO_LINHA} bytes (movidas assim mesmo; encurtar é conteúdo)")
    if texto.lstrip().startswith("<!--"):
        rel.avisos.append("o comentário-modelo do índice antigo não é memória: sai do topo")
    if aplicar:
        for s, corpo in subs.items():
            _gravar(memdir / SUBDIR / f"{s}.md", corpo, eol)
        _gravar(idx, rel.topo, eol)
        rel.gravou = True
    return rel


def _tabela(rel: Relatorio) -> str:
    out = ["| família | linhas | bytes | tokens ≈ | carrega |", "|---|---:|---:|---:|---|",
           f"| topo `memory/MEMORY.md` | {rel.topo.count(chr(10))} | {rel.bytes_topo} | {rel.bytes_topo // 4} | toda partida |"]
    for f in rel.familias:
        b = len(montar_subindice(f).encode("utf-8"))
        out.append(f"| `memory/{SUBDIR}/{f.slug}.md` | {len(f.itens)} | {b} | {b // 4} | só quando a família bate |")
    return "\n".join(out)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["dividir", "verificar", "fila", "buscar"])
    ap.add_argument("termo", nargs="?", default="")
    ap.add_argument("--proj", default=".", help="raiz do projeto (default: diretório atual)")
    ap.add_argument("--aplicar", action="store_true", help="grava (sem isto é dry-run)")
    ap.add_argument("--limite", type=int, default=10)
    a = ap.parse_args(argv)
    proj = Path(a.proj).resolve()
    memdir = proj / "memory"
    if a.modo == "dividir":
        rel = dividir(memdir, aplicar=a.aplicar)
        if not rel.ok:
            print("NÃO dividido:\n- " + "\n- ".join(rel.problemas))
            return 1
        print(f"índice plano: {rel.bytes_antes} bytes → topo: {rel.bytes_topo} bytes "
              f"(−{100 - rel.bytes_topo * 100 // max(rel.bytes_antes, 1)}%)\n")
        print(_tabela(rel) + "\n")
        print("topo resultante:\n```markdown\n" + rel.topo + "```")
        for av in rel.avisos:
            print("aviso:", av)
        print("GRAVADO." if rel.gravou else "DRY-RUN — nada gravado. Rode com --aplicar para gravar.")
        return 0
    return _main_resto(a, proj, memdir)   # verificar / fila / buscar — Task 3 e 4


def _main_resto(a, proj, memdir) -> int:
    raise SystemExit("modo ainda não implementado")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar os testes**

Run: `python -m pytest tests/test_memoria_indice.py -q`
Expected: 9 passed.

- [ ] **Step 5: Dry-run real contra o Whats (só leitura) e conferir a tabela**

Run: `python templates/memoria_indice.py dividir --proj "/c/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats"`
Expected: `NÃO dividido` **não** aparece; tabela com 5 famílias, topo < 2.000 bytes, última linha `DRY-RUN — nada gravado.` Confirme com `git -C "<Whats>" status --short memory/` que nada mudou lá.

- [ ] **Step 6: Commit**

```bash
git add templates/memoria_indice.py tests/test_memoria_indice.py
git commit -m "feat(memoria): memoria_indice.py dividir -- indice em dois niveis, dry-run e conservacao byte a byte"
```

---

### Task 3: `memoria_indice.py` — `verificar` e `fila`

**Files:**
- Modify: `templates/memoria_indice.py`
- Test: `tests/test_memoria_indice.py`

- [ ] **Step 1: Testes (falham)**

```python
# --- verificar / fila ------------------------------------------------------------------

def _dividido(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    assert mod.dividir(raiz / "memory", aplicar=True).ok
    return mod, raiz


def test_verificar_limpo_depois_de_dividir(tmp_path):
    mod, raiz = _dividido(tmp_path)
    assert mod.verificar(raiz / "memory") == []


def test_verificar_acusa_memoria_sem_linha_e_ponteiro_quebrado(tmp_path):
    mod, raiz = _dividido(tmp_path)
    (raiz / "memory" / "nova-memoria.md").write_text(FRONT_SEM_GATILHO.format(name="nova-memoria", desc="x"), encoding="utf-8")
    (raiz / "memory" / "crm-www4-dois-nomes.md").unlink()
    probs = mod.verificar(raiz / "memory")
    assert any("nova-memoria.md" in p and "sem linha" in p for p in probs)
    assert any("crm-www4-dois-nomes.md" in p and "quebrado" in p for p in probs)


def test_verificar_ignora_obsoleta(tmp_path):
    mod, raiz = _dividido(tmp_path)
    (raiz / "memory" / "velha.md").write_text(
        "---\nname: velha\ndescription: x\nobsoleta: 2026-09-01 — superada por [[nova]]\n---\n", encoding="utf-8")
    assert mod.verificar(raiz / "memory") == []


def test_verificar_corrige_n_do_topo_com_aplicar(tmp_path):
    mod, raiz = _dividido(tmp_path)
    sub = raiz / "memory" / "indice" / "integracoes.md"
    sub.write_text(sub.read_text(encoding="utf-8") + "- [Extra](../crm-www4-dois-nomes.md) — dup de teste\n", encoding="utf-8")
    probs = mod.verificar(raiz / "memory")
    assert any("N do topo" in p and "integracoes" in p for p in probs)
    assert any("mais de uma linha" in p for p in probs)
    mod.verificar(raiz / "memory", aplicar=True)
    assert "— 27 memórias" in (raiz / "memory" / "MEMORY.md").read_text(encoding="utf-8")


def test_verificar_acusa_topo_acima_do_teto(tmp_path):
    mod, raiz = _dividido(tmp_path)
    p = raiz / "memory" / "MEMORY.md"
    p.write_text(p.read_text(encoding="utf-8") + "x" * 6000, encoding="utf-8")
    assert any("teto" in pr for pr in mod.verificar(raiz / "memory"))


def test_fila_lista_memorias_sem_gatilho(tmp_path):
    mod, raiz = _dividido(tmp_path)
    fila = mod.fila(raiz / "memory")
    assert len(fila["sem_gatilho"]) == 91          # 93 stubs − 2 com gatilho
    assert "padroes-e-ferramentas" in fila["familias_sem_frase"]
    assert "ambiente-e-build" not in fila["familias_sem_frase"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_memoria_indice.py -q -k "verificar or fila"`
Expected: `AttributeError: module has no attribute 'verificar'`.

- [ ] **Step 3: Implementar**

Substitua `_main_resto` e acrescente antes dele:

```python
# ------------------------------------------------------------------ verificar / fila

def _memorias(memdir: Path) -> list:
    return sorted(p for p in memdir.glob("*.md") if p.name not in INDICES)


def _linhas_dos_subindices(memdir: Path) -> list:
    """[(subíndice Path, nº da linha, Item)] de todos os memory/indice/*.md."""
    out = []
    for sub in sorted((memdir / SUBDIR).glob("*.md")):
        texto, _ = _ler(sub)
        for n, linha in enumerate(texto.split("\n"), 1):
            m = RE_ITEM.match(linha)
            if m:
                out.append((sub, n, Item(linha, m.group("titulo"), m.group("arquivo"))))
    return out


def _n_do_topo(topo: str) -> dict:
    """{slug: (nº da linha, N declarado)} a partir das linhas `→ [subíndice](indice/<slug>.md) — N memórias`."""
    out = {}
    for n, l in enumerate(topo.split("\n"), 1):
        m = re.search(rf"\]\({SUBDIR}/([^)]+)\.md\) — (\d+) memórias", l)
        if m:
            out[m.group(1)] = (n, int(m.group(2)))
    return out


def verificar(memdir: Path, aplicar: bool = False) -> list:
    memdir = Path(memdir)
    probs = []
    idx = memdir / "MEMORY.md"
    if not idx.is_file():
        return [f"não existe {idx}"]
    topo, eol = _ler(idx)
    b = len(topo.encode("utf-8"))
    if b > TETO_TOPO:
        probs.append(f"topo com {b} bytes — acima do teto de {TETO_TOPO} (orçamento de partida)")
    if not (memdir / SUBDIR).is_dir():
        return probs + [f"sem {memdir / SUBDIR}/ — índice plano; rode `memoria_indice.py dividir`"]
    declarados = _n_do_topo(topo)
    for s in declarados:
        if not (memdir / SUBDIR / f"{s}.md").is_file():
            probs.append(f"topo aponta subíndice inexistente: {SUBDIR}/{s}.md")
    linhas = _linhas_dos_subindices(memdir)
    por_arquivo = {}
    for sub, n, it in linhas:
        alvo = it.arquivo[3:] if it.arquivo.startswith("../") else it.arquivo
        por_arquivo.setdefault(alvo, []).append(f"{sub.name}:{n}")
        if "/" not in alvo and not (memdir / alvo).is_file():
            probs.append(f"ponteiro quebrado em {sub.name}:{n}: {it.arquivo}")
        if len(it.linha.encode("utf-8")) > TETO_LINHA:
            probs.append(f"linha acima de {TETO_LINHA} bytes em {sub.name}:{n}")
    for md in _memorias(memdir):
        onde = por_arquivo.get(md.name, [])
        if not onde and not frontmatter(md).get("obsoleta"):
            probs.append(f"{md.name} sem linha em nenhum subíndice (memória invisível)")
        if len(onde) > 1:
            probs.append(f"{md.name} tem mais de uma linha: {', '.join(onde)}")
    contagem = {}
    for sub, _, _ in linhas:
        contagem[sub.stem] = contagem.get(sub.stem, 0) + 1
    novo_topo = topo
    for s, (n, declarado) in declarados.items():
        real = contagem.get(s, 0)
        if real != declarado:
            probs.append(f"N do topo em {s}: diz {declarado}, subíndice tem {real}")
            novo_topo = novo_topo.replace(f"]({SUBDIR}/{s}.md) — {declarado} memórias",
                                          f"]({SUBDIR}/{s}.md) — {real} memórias")
    for s in contagem:
        if s not in declarados:
            probs.append(f"subíndice {SUBDIR}/{s}.md sem linha no topo")
    if aplicar and novo_topo != topo:
        _gravar(idx, novo_topo, eol)
    return probs


def fila(memdir: Path) -> dict:
    memdir = Path(memdir)
    sem = [md.name for md in _memorias(memdir)
           if not frontmatter(md).get("gatilho") and not frontmatter(md).get("obsoleta")]
    fams_sem_frase = []
    for sub in sorted((memdir / SUBDIR).glob("*.md")) if (memdir / SUBDIR).is_dir() else []:
        fam = Familia(sub.stem, [it for s, _, it in _linhas_dos_subindices(memdir) if s == sub])
        fam.itens = [Item(it.linha, it.titulo, it.arquivo[3:] if it.arquivo.startswith("../") else it.arquivo)
                     for it in fam.itens]
        if not frases_de_gatilho(fam, memdir):
            fams_sem_frase.append(sub.stem)
    return {"sem_gatilho": sem, "familias_sem_frase": fams_sem_frase}


def _main_resto(a, proj, memdir) -> int:
    if a.modo == "verificar":
        probs = verificar(memdir, aplicar=a.aplicar)
        if probs:
            print("problemas:\n- " + "\n- ".join(probs))
            return 1
        print("índice de memória: ok (topo + subíndices consistentes)")
        return 0
    if a.modo == "fila":
        f = fila(memdir)
        print(f"memórias sem `gatilho:` ({len(f['sem_gatilho'])}):")
        for n in f["sem_gatilho"]:
            print("  -", n)
        print(f"famílias sem frase de gatilho no topo ({len(f['familias_sem_frase'])}): "
              + ", ".join(f["familias_sem_frase"]))
        return 0
    return _main_buscar(a, proj)   # Task 4


def _main_buscar(a, proj) -> int:
    raise SystemExit("buscar ainda não implementado")
```

- [ ] **Step 4: Rodar**

Run: `python -m pytest tests/test_memoria_indice.py -q`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/memoria_indice.py tests/test_memoria_indice.py
git commit -m "feat(memoria): memoria_indice.py verificar (audita topo+subindices, corrige N) e fila (sem gatilho)"
```

---

### Task 4: motor `casar()` e `buscar`

**Files:**
- Modify: `templates/memoria_indice.py`
- Test: `tests/test_memoria_indice.py`

- [ ] **Step 1: Testes (falham)**

```python
# --- casar / buscar --------------------------------------------------------------------

def _projeto_recall(tmp_path):
    """Projeto pequeno com as 5 fontes do recall."""
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    (mem / "indice").mkdir(parents=True)
    (mem / "sessions").mkdir()
    (raiz / "docs").mkdir()
    (mem / "resolvedor-de-token-prefere-processo-ao-header.md").write_text(
        "---\nname: resolvedor-de-token-prefere-processo-ao-header\n"
        "description: validar_corretor resolve a credencial pelo cache de processo antes do header\n"
        "gatilho: quando chamar `validar_corretor` numa rota que atende mais de um corretor\n"
        "metadata:\n  type: project\n---\n", encoding="utf-8")
    (mem / "dns-search-inerte-sem-ndots.md").write_text(
        "---\nname: dns-search-inerte-sem-ndots\ndescription: nome curto resolve no host e falha no contêiner\n"
        "gatilho: quando nome curto resolve no host e falha só no contêiner (Docker injeta ndots:0)\n---\n", encoding="utf-8")
    (mem / "sem-gatilho.md").write_text("---\nname: sem-gatilho\ndescription: proxy do Docker em minúsculas\n---\n", encoding="utf-8")
    (mem / "MEMORY.md").write_text("# topo\n- **Integrações** → [subíndice](indice/integracoes.md) — 2 memórias\n", encoding="utf-8")
    (mem / "indice" / "integracoes.md").write_text(
        "# Integrações\n"
        "- **quando chamar `validar_corretor` com 2 corretores** → [Resolvedor de token prefere processo ao header](../resolvedor-de-token-prefere-processo-ao-header.md) — passe token= explícito\n"
        "- **quando o nome curto falha no contêiner** → [dns_search inerte sem ndots](../dns-search-inerte-sem-ndots.md) — dns_opt ndots:1\n",
        encoding="utf-8")
    (mem / "DIARIO.md").write_text(
        "# Diário\n- [handoff-chatwoot] handoff pro Chatwoot: contato deduplicado por telefone, e-mail não vai → sessions/2026-07-30-handoff-chatwoot.md\n",
        encoding="utf-8")
    (raiz / "docs" / "decisoes.md").write_text(
        "# Decisões\n- 2026-09-11 — **token explícito por corretor** em vez de cache de processo no validar_corretor\n",
        encoding="utf-8")
    (raiz / "docs" / "EVALS.md").write_text(
        "| id | data | gatilho | classe | guardrail | status |\n|---|---|---|---|---|---|\n"
        "| F-005 | 2026-09-14 | quando confiar que a memória do repo já está no contexto | memória não carregou | ponteiro | fechado |\n",
        encoding="utf-8")
    return raiz


def test_tokens_normaliza_e_marca_identificadores():
    mod = _mod()
    t, ids = mod.tokens("O `validar_corretor` do corretor B saiu com o COD_CORR do A, não é?")
    assert "validar_corretor" in t and "cod_corr" in t and "corretor" in t
    assert "validar_corretor" in ids and "cod_corr" in ids
    assert "não" not in t and "com" not in t          # curtas/stopwords fora


def test_casar_acha_memoria_por_gatilho_e_prefere_o_arquivo_a_linha_do_indice(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    r = mod.casar(raiz, "o corretor B saiu validado com o token do A na rota que chama validar_corretor")
    assert r, "nada casou"
    assert r[0].ponteiro.startswith("memory/resolvedor-de-token-prefere-processo-ao-header.md")
    assert sum("resolvedor-de-token" in x.ponteiro for x in r) == 1, "arquivo e linha do índice não podem sair em dobro"
    assert any(x.ponteiro.startswith("docs/decisoes.md:2") for x in r)


def test_casar_exige_dois_tokens_distintos(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    assert mod.casar(raiz, "fala sobre corretor") == []


def test_casar_sem_acento_e_caixa(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    r = mod.casar(raiz, "NOME CURTO resolve no host mas falha no CONTEINER")
    assert r and "dns-search-inerte-sem-ndots.md" in r[0].ponteiro


def test_casar_le_diario_e_evals(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    r = mod.casar(raiz, "o contato do Chatwoot está sendo deduplicado pelo telefone?", limite=5)
    assert any(x.ponteiro.startswith("memory/sessions/2026-07-30-handoff-chatwoot.md") for x in r)
    r2 = mod.casar(raiz, "confiar que a memória do repo já está no contexto", limite=5)
    assert any("docs/EVALS.md — F-005" in x.ponteiro for x in r2)


def test_casar_funciona_com_indice_plano_antes_da_divisao(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    shutil.rmtree(raiz / "memory" / "indice")
    (raiz / "memory" / "MEMORY.md").write_text(
        "## Integrações\n- [dns_search inerte sem ndots](dns-search-inerte-sem-ndots.md) — nome curto falha no contêiner\n",
        encoding="utf-8")
    for p in ("resolvedor-de-token-prefere-processo-ao-header.md", "dns-search-inerte-sem-ndots.md"):
        (raiz / "memory" / p).write_text("---\nname: x\n---\n", encoding="utf-8")   # sem gatilho: só a linha do índice casa
    r = mod.casar(raiz, "nome curto falha no contêiner e no host resolve")
    assert r and "memory/MEMORY.md:2" in r[0].ponteiro


def test_formatar_injecao_respeita_600_bytes_sem_cortar_linha(tmp_path):
    mod = _mod()
    # cada linha ≈ 259 B: cabeçalho (64 B) + 2 linhas = 582 ≤ 600; a 3ª estouraria e fica fora inteira
    ponteiros = [mod.Ponteiro(9, 0, "memory/" + "a" * 240 + ".md — g"), mod.Ponteiro(8, 0, "memory/" + "b" * 240 + ".md — g"),
                 mod.Ponteiro(7, 0, "memory/" + "c" * 240 + ".md — g")]
    txt = mod.formatar_injecao(ponteiros)
    assert len(txt.encode("utf-8")) <= 600
    assert txt.count("\n- ") == 2 and "ccc" not in txt


def test_buscar_cli_lista_ponteiros(tmp_path, capsys):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    assert mod.main(["buscar", "validar_corretor corretor", "--proj", str(raiz)]) == 0
    out = capsys.readouterr().out
    assert "memory/resolvedor-de-token-prefere-processo-ao-header.md" in out
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_memoria_indice.py -q -k "casar or tokens or buscar or injecao"`
Expected: `AttributeError` em `tokens`/`casar`.

- [ ] **Step 3: Implementar o motor**

Acrescente antes de `_main_buscar` e substitua `_main_buscar`:

```python
# ------------------------------------------------------------------ motor de casamento (hook + buscar)

TETO_INJECAO = 600
MINIMO_TOKENS = 2
STOPWORDS = {"para", "pelo", "pela", "pelos", "pelas", "como", "quando", "onde", "isso", "esse", "essa",
             "este", "esta", "aqui", "mais", "menos", "muito", "ainda", "então", "entao", "porque", "mesmo",
             "mesma", "nunca", "sempre", "está", "esta", "estão", "estao", "tem", "sendo", "cada", "sobre",
             "entre", "depois", "antes", "qual", "quais", "coisa", "fazer", "feito", "todo", "toda", "todos",
             "nada", "algo", "outro", "outra", "acho", "pode", "deve", "vamos", "vou", "você", "voce"}
RE_IDENT = re.compile(r"`([^`]+)`|\b([A-Za-z0-9]+(?:[_.][A-Za-z0-9]+)+)\b|\b([a-z]+[A-Z][A-Za-z0-9]*)\b")
RE_TOKEN = re.compile(r"[a-z0-9_]{4,}")
RE_LINHA_DIARIO = re.compile(r"^- \[([^\]]+)\]\s*(.*?)(?:→\s*(sessions/\S+))?\s*$")
RE_LINHA_EVALS = re.compile(r"^\| (F-\d{3}) \|")
PRIO = {"memoria": 0, "indice": 1, "evals": 2, "decisao": 3, "diario": 4}


@dataclass
class Fonte:
    texto: str        # o que casa
    ponteiro: str     # o que se injeta
    prio: int
    arquivo: str = "" # memória a que se refere (dedup memória × linha do índice)


@dataclass
class Ponteiro:
    score: int
    prio: int
    ponteiro: str


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def tokens(texto: str):
    """(tokens úteis, identificadores) — sem acento/caixa, ≥ 4 chars, sem stopwords.
    Identificador = code span, `a_b`/`a.b`, camelCase — vale 2 no score (é o que separa COD_CORR de 'código')."""
    ids = set()
    for m in RE_IDENT.finditer(texto):
        for grupo in m.groups():
            if grupo:
                ids.update(t for t in RE_TOKEN.findall(_norm(grupo)) if t not in STOPWORDS)
    toks = {t for t in RE_TOKEN.findall(_norm(texto)) if t not in STOPWORDS}
    return toks | ids, ids


def _corta(s: str, n: int = 120) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def fontes(proj: Path) -> list:
    proj = Path(proj)
    memdir = proj / "memory"
    out = []
    if not memdir.is_dir():
        return out
    for md in _memorias(memdir):
        fm = frontmatter(md)
        if fm.get("obsoleta"):
            continue
        texto = " ".join(x for x in (fm.get("name"), fm.get("description"), fm.get("gatilho")) if x)
        if texto.strip():
            out.append(Fonte(texto, f"memory/{md.name} — {_corta(fm.get('gatilho') or fm.get('description') or '')}",
                             PRIO["memoria"], md.name))
    indices = list((memdir / SUBDIR).glob("*.md")) if (memdir / SUBDIR).is_dir() else [memdir / "MEMORY.md"]
    for sub in sorted(indices):
        if not sub.is_file():
            continue
        texto, _ = _ler(sub)
        rel = sub.relative_to(proj).as_posix()
        for n, l in enumerate(texto.split("\n"), 1):
            m = RE_ITEM.match(l)
            if m and "indice/" not in m.group("arquivo"):
                arq = m.group("arquivo")[3:] if m.group("arquivo").startswith("../") else m.group("arquivo")
                out.append(Fonte(l, f"{rel}:{n} — {m.group('titulo')}", PRIO["indice"], arq))
    ev = proj / "docs" / "EVALS.md"
    if ev.is_file():
        texto, _ = _ler(ev)
        for l in texto.split("\n"):
            m = RE_LINHA_EVALS.match(l)
            if m:
                cel = [c.strip() for c in l.strip("|").split("|")]
                if len(cel) >= 3:
                    out.append(Fonte(cel[2], f"docs/EVALS.md — {m.group(1)} {_corta(cel[2])}", PRIO["evals"]))
    dec = proj / "docs" / "decisoes.md"
    if dec.is_file():
        texto, _ = _ler(dec)
        for n, l in enumerate(texto.split("\n"), 1):
            if re.match(r"^- \d{4}-\d{2}-\d{2}", l):
                out.append(Fonte(l, f"docs/decisoes.md:{n} — {_corta(l[2:])}", PRIO["decisao"]))
    dia = memdir / "DIARIO.md"
    if dia.is_file():
        texto, _ = _ler(dia)
        for n, l in enumerate(texto.split("\n"), 1):
            m = RE_LINHA_DIARIO.match(l)
            if m and m.group(1) != "<assunto>":
                alvo = f"memory/{m.group(3)}" if m.group(3) else f"memory/DIARIO.md:{n}"
                out.append(Fonte(f"{m.group(1)} {m.group(2)}", f"{alvo} — {_corta(m.group(2))}", PRIO["diario"]))
    return out


def casar(proj: Path, prompt: str, limite: int = 3, minimo: int = MINIMO_TOKENS) -> list:
    """Ponteiros ordenados por score desc, prioridade asc. Memória e sua linha de índice: sai só a memória."""
    toks, _ = tokens(prompt)
    if len(toks) < minimo:
        return []
    achados = []
    for f in fontes(proj):
        ftoks, fids = tokens(f.texto)
        comum = toks & ftoks
        if len(comum) < minimo:
            continue
        score = sum(2 if t in fids else 1 for t in comum)
        achados.append((score, f))
    achados.sort(key=lambda x: (-x[0], x[1].prio, x[1].ponteiro))
    vistos, out = set(), []
    for score, f in achados:
        if f.arquivo:
            if f.arquivo in vistos:
                continue
            vistos.add(f.arquivo)
        out.append(Ponteiro(score, f.prio, f.ponteiro))
        if len(out) >= limite:
            break
    return out


def formatar_injecao(ponteiros: list, teto: int = TETO_INJECAO) -> str:
    """Texto que o hook injeta: cabeçalho + até 3 linhas, nunca acima do teto, nunca cortando linha ao meio."""
    if not ponteiros:
        return ""
    txt = "[mss-spec recall] casou com o seu prompt — abra antes de agir:"
    for p in ponteiros:
        cand = txt + "\n- " + p.ponteiro
        if len(cand.encode("utf-8")) > teto:
            break
        txt = cand
    return txt if "\n- " in txt else ""


def _main_buscar(a, proj) -> int:
    if not a.termo.strip():
        print("uso: memoria_indice.py buscar \"<termo>\" [--proj DIR] [--limite N]")
        return 2
    achados = casar(proj, a.termo, limite=a.limite, minimo=1)
    if not achados:
        print("nada casou com:", a.termo)
        return 1
    for p in achados:
        print(f"- {p.ponteiro}   (score {p.score})")
    return 0
```

- [ ] **Step 4: Rodar**

Run: `python -m pytest tests/test_memoria_indice.py -q`
Expected: 23 passed.

- [ ] **Step 5: Buscar real no Whats (só leitura)**

Run: `python templates/memoria_indice.py buscar "ndots" --proj "/c/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats"`
Expected: lista com `memory/dns-search-inerte-sem-ndots.md` no topo (o índice ainda é plano lá — a fonte é `memory/MEMORY.md:<n>` mais o `gatilho:` do arquivo).

- [ ] **Step 6: Commit**

```bash
git add templates/memoria_indice.py tests/test_memoria_indice.py
git commit -m "feat(memoria): motor casar() + buscar -- 5 fontes, identificador vale 2, injecao <= 600 B"
```

---

### Task 5: hook `recall_memoria.py`

**Files:**
- Create: `hooks/recall_memoria.py`
- Modify: `hooks/hooks.json`
- Test: `tests/test_hook_recall_memoria.py`

- [ ] **Step 1: Testes (falham)**

```python
"""Recall determinístico — hook UserPromptSubmit que injeta os ponteiros de memória que casam com o prompt.

Por que existe: o owner de um projeto grande voltava às conversas antigas pra re-explicar ao assistente onde
um assunto foi tratado. O índice estava lá; ninguém abria. Agora o Python casa e injeta ≤ 600 bytes.

Propriedades: não bloqueia nunca · silêncio quando nada casa · ignora `/comando` e prompt curto · projeto
sem memory/ → silêncio · falha ABERTA (bug → exit 0, stdout vazio) · escape `MSS_RECALL_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "recall_memoria.py"


def _mod():
    spec = importlib.util.spec_from_file_location("recall_memoria", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path):
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("# topo\n", encoding="utf-8")
    (mem / "mount-de-codigo-no-docker-pelo-git-bash.md").write_text(
        "---\nname: mount-de-codigo-no-docker-pelo-git-bash\n"
        "description: montar a fonte com -v no Git Bash do Windows cai em silêncio\n"
        "gatilho: quando montar código com `docker -v` no Git Bash e o teste novo der No such file\n---\n",
        encoding="utf-8")
    return raiz


def _evento(prompt, raiz):
    return {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": prompt}


def _rodar(evento, raw=None, env_extra=None):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_RECALL_OFF", "CLAUDE_PROJECT_DIR")}
    amb.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(evento),
                          capture_output=True, text=True, env=amb, timeout=30)


def test_injeta_ponteiro_quando_casa(tmp_path):
    mod = _mod()
    saida = mod.responder(_evento("o docker -v pelo git bash montou pasta vazia e o teste deu No such file", _projeto(tmp_path)), {})
    assert saida is not None
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("[mss-spec recall]") and "memory/mount-de-codigo-no-docker-pelo-git-bash.md" in ctx
    assert len(ctx.encode("utf-8")) <= 600


def test_silencio_quando_nada_casa(tmp_path):
    mod = _mod()
    assert mod.responder(_evento("ajusta o rodapé da página de login por favor", _projeto(tmp_path)), {}) is None


def test_ignora_comando_prompt_curto_e_projeto_sem_memoria(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    assert mod.responder(_evento("/mss-spec:doctor docker git bash mount teste", raiz), {}) is None
    assert mod.responder(_evento("docker bash", raiz), {}) is None
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    assert mod.responder(_evento("o docker -v pelo git bash montou pasta vazia e o teste deu No such file", vazio), {}) is None


def test_escape_e_falha_aberta(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    ev = _evento("o docker -v pelo git bash montou pasta vazia e o teste deu No such file", raiz)
    assert mod.responder(ev, {"MSS_RECALL_OFF": "1"}) is None
    assert mod.responder("isto não é um dict", {}) is None
    assert mod.responder({"prompt": 42, "cwd": str(raiz)}, {}) is None


def test_claude_project_dir_vence_o_cwd(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    outro = tmp_path / "outro"
    outro.mkdir()
    ev = _evento("o docker -v pelo git bash montou pasta vazia e o teste deu No such file", outro)
    assert mod.responder(ev, {"CLAUDE_PROJECT_DIR": str(raiz)}) is not None


def test_processo_injeta_json_e_sai_zero(tmp_path):
    raiz = _projeto(tmp_path)
    proc = _rodar(_evento("o docker -v pelo git bash montou pasta vazia e o teste deu No such file", raiz))
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert "mount-de-codigo-no-docker-pelo-git-bash.md" in saida["hookSpecificOutput"]["additionalContext"]


def test_processo_json_malformado_sai_zero_e_calado(tmp_path):
    proc = _rodar(None, raw="{isto não é json")
    assert proc.returncode == 0 and proc.stdout.strip() == ""


def test_hook_registrado_em_user_prompt_submit():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["UserPromptSubmit"]
    comandos = [h["command"] for g in grupos for h in g["hooks"]]
    assert any("recall_memoria.py" in c and "CLAUDE_PLUGIN_ROOT" in c for c in comandos), comandos
    assert any("um_item_por_janela.py" in c for c in comandos), "não pode derrubar a cerca que já existia"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_hook_recall_memoria.py -q`
Expected: falha por arquivo inexistente.

- [ ] **Step 3: Implementar o hook**

```python
"""Hook do mss-spec: RECALL DETERMINÍSTICO — aponta a memória que casou com o prompt.

Por que existe: num projeto grande o owner voltava às conversas antigas e re-explicava ao assistente
onde um assunto já tinha sido tratado. A memória estava no repo; o índice de 25 KB estava na janela;
ninguém abria a linha certa. Aqui o Python casa o prompt com `gatilho:`/índice/diário/decisões/EVALS
e injeta só os ponteiros (≤ 600 bytes). Zero tokens pra buscar; ~80 tokens quando acha.

Contrato:
- evento `UserPromptSubmit`; **nunca bloqueia** (rede, não cerca) — saída é `additionalContext`;
- silêncio (stdout vazio, exit 0) quando: nada casa · prompt começa com `/` (comando tem ritual
  próprio) · prompt com < 4 tokens úteis · projeto sem `memory/`;
- projeto = `CLAUDE_PROJECT_DIR` (âncora da janela), fallback `cwd` do evento;
- **falha ABERTA**: qualquer exceção → exit 0 calado (`MSS_RECALL_DEBUG=1` mostra o traceback);
- escape consciente, só do owner: `MSS_RECALL_OFF=1`.
O motor de casamento é o de `templates/memoria_indice.py` (o mesmo do `/mss-spec:memory buscar`).
"""
import json
import os
import sys
import traceback
from pathlib import Path

ENV_DESLIGA = "MSS_RECALL_OFF"
ENV_DEBUG = "MSS_RECALL_DEBUG"
MIN_TOKENS_PROMPT = 4
LIMITE = 3


def _motor():
    """Importa templates/memoria_indice.py pelo caminho do plugin (hooks/ e templates/ são irmãos)."""
    import importlib.util
    caminho = Path(__file__).resolve().parent.parent / "templates" / "memoria_indice.py"
    spec = importlib.util.spec_from_file_location("memoria_indice", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None
        if not isinstance(evento, dict):
            return None
        prompt = evento.get("prompt")
        if not isinstance(prompt, str) or prompt.lstrip().startswith("/"):
            return None
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip():
            return None
        proj = Path(raiz)
        if not (proj / "memory").is_dir():
            return None
        motor = _motor()
        toks, _ = motor.tokens(prompt)
        if len(toks) < MIN_TOKENS_PROMPT:
            return None
        texto = motor.formatar_injecao(motor.casar(proj, prompt, limite=LIMITE))
        if not texto:
            return None
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": texto}}
    except Exception:                                # noqa: BLE001 — falha ABERTA
        if str((ambiente or os.environ).get(ENV_DEBUG, "")).strip():
            traceback.print_exc(file=sys.stderr)
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    saida = responder(evento)
    if saida is None:
        sys.exit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print(json.dumps(saida, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Registrar no `hooks/hooks.json`** — o bloco `UserPromptSubmit` fica:

```json
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/um_item_por_janela.py\""
          },
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/recall_memoria.py\""
          }
        ]
      }
    ]
```

- [ ] **Step 5: Rodar**

Run: `python -m pytest tests/test_hook_recall_memoria.py tests/test_hook_um_item_por_janela.py tests/test_smoke_kit.py -q`
Expected: tudo verde (o smoke ainda não sabe do recall; Task 6 acrescenta).

- [ ] **Step 6: Prova manual no Whats (só leitura)**

```bash
echo '{"hook_event_name":"UserPromptSubmit","cwd":"C:/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats","prompt":"o corretor B saiu validado com o token do corretor A na mesma rota"}' | python hooks/recall_memoria.py
```

Expected: JSON com `additionalContext` citando `resolvedor-de-token-prefere-processo-ao-header` (ou a linha do índice dele). Guarde a saída para o CHANGELOG.

- [ ] **Step 7: Commit**

```bash
git add hooks/recall_memoria.py hooks/hooks.json tests/test_hook_recall_memoria.py
git commit -m "feat(hooks): recall_memoria.py -- UserPromptSubmit injeta <= 600 B de ponteiros que casam com o prompt (ligado, nao bloqueia, falha aberta)"
```

---

### Task 6: README dos hooks + smoke

**Files:**
- Modify: `hooks/README.md` (tabela do topo + seção nova ao fim)
- Modify: `tests/test_smoke_kit.py`

- [ ] **Step 1: Teste (falha)** — acrescente ao fim de `tests/test_smoke_kit.py`:

```python
def test_recall_hook_documentado_e_registrado():
    """Recall determinístico: 5º hook, ligado, NÃO bloqueia, falha aberta, com escape — e no README."""
    assert (REPO / "hooks" / "recall_memoria.py").exists(), "falta hooks/recall_memoria.py"
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "recall_memoria.py" in doc, "README dos hooks não lista o recall"
    assert "MSS_RECALL_OFF" in doc, "README não documenta o escape do recall"
    assert "Cinco hooks" in doc, "a contagem do README ficou velha"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_smoke_kit.py -q -k recall`
Expected: FAIL em "README dos hooks não lista o recall".

- [ ] **Step 3: Editar o README** — troque `Quatro hooks, em duas filosofias` por `Cinco hooks, em duas filosofias`, acrescente a linha na tabela:

```markdown
| `recall_memoria.py` | `UserPromptSubmit` | **ligado por padrão** | não (só injeta) | rede: aponta a memória/decisão/diário que casou com o prompt |
```

e a seção, ao fim do arquivo:

```markdown
---

# Hook ligado — recall determinístico

`recall_memoria.py` casa cada prompt do owner com os `gatilho:` das memórias, as linhas de
`memory/indice/*.md` (ou do `MEMORY.md` plano), o gist do `DIARIO.md`, as `docs/decisoes.md` e a coluna
gatilho do `docs/EVALS.md`, e injeta **só os 3 melhores ponteiros** (≤ 600 bytes) como
`additionalContext`. Nada casou → silêncio. Motor: `templates/memoria_indice.py` (o mesmo do
`/mss-spec:memory buscar`).

**Por que existe:** num projeto com 93 memórias o índice de 25 KB estava na janela e mesmo assim o owner
voltava às conversas antigas pra re-explicar onde o assunto tinha sido tratado. Recall que depende de o
modelo lembrar de abrir o arquivo não é recall.

**Por que vem ligado e não bloqueia:** custo de disparar = ~80 tokens quando casa, zero quando não; custo
de não existir = o owner virar índice humano. Ignora `/comando` e prompt com < 4 tokens úteis.

**Falha ABERTA:** exceção → exit 0 calado (`MSS_RECALL_DEBUG=1` mostra o traceback). Escape consciente,
só do owner: `MSS_RECALL_OFF=1`.
```

- [ ] **Step 4: Rodar**

Run: `python -m pytest tests/test_smoke_kit.py -q`
Expected: verde.

- [ ] **Step 5: Commit**

```bash
git add hooks/README.md tests/test_smoke_kit.py
git commit -m "docs(hooks): README com o 5o hook (recall) + smoke"
```

---

### Task 7: `rodizio_partida.py mapa`

**Files:**
- Create: `templates/rodizio_partida.py`
- Test: `tests/test_rodizio_partida.py`

- [ ] **Step 1: Testes (falham)**

```python
"""rodizio_partida.py — MAPA com 2 blocos por seção, INDEX só com tarefa viva; o resto vai pro histórico.

Por que: o MAPA do Whats tinha 89.651 bytes (teto 6.000) e o INDEX 61.399 (teto 7.000) — relidos em toda
janela. O template já prometia "atual + 1 anterior" e "fechada sai"; faltava quem MOVESSE. Move, nunca apaga;
dry-run por padrão; conservação byte a byte antes de gravar.
"""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "rodizio_partida.py"

MAPA = """# Mapa de contexto — Proj

## Onde estamos

📍 **Branch atual: `feature/x`** — estado atual, linha 1.
linha 2 do atual.

---

✅ **2026-09-13 — anterior 1** verificado.

---

✅ **2026-09-10 — anterior 2** coisa velha.
detalhe do anterior 2.

---

⚠️ **2026-09-01 — anterior 3** mais velho ainda.

## Próximo passo

1. passo atual.

---

1. passo anterior.

---

1. passo velho.

## Conexões

- outro projeto — não mexer.
"""

INDEX = """# Índice de tarefas

## Em andamento
- [formatação](../specs/formatacao.md) — juntar linhas — aberta
- [relatório](../specs/relatorio.md) — PDF — fechada
- [importador](../specs/importador.md) — CSV — pausada: aguardando layout
5. upgrade — sincroniza — **em andamento** (sem commit)

## Backlog
- [alerta](../specs/alerta.md) — e-mail — fechada

## Fora de escopo — decidido NÃO fazer (2026-07-28)
- login social — fechada de propósito, fica aqui pra não re-litigar
"""


def _mod():
    spec = importlib.util.spec_from_file_location("rodizio_partida", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path, mapa=MAPA, index=INDEX):
    raiz = tmp_path / "proj"
    sp = raiz / "docs" / "superpowers"
    sp.mkdir(parents=True)
    (sp / "MAPA.md").write_text(mapa, encoding="utf-8")
    (sp / "INDEX.md").write_text(index, encoding="utf-8")
    return raiz


# --- mapa -------------------------------------------------------------------------------

def test_mapa_mantem_dois_blocos_por_secao_e_move_o_resto(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok, rel.problemas
    mapa = (raiz / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8")
    assert "anterior 1" in mapa and "anterior 2" not in mapa and "anterior 3" not in mapa
    assert "passo anterior." in mapa and "passo velho." not in mapa
    assert "outro projeto — não mexer." in mapa
    assert mapa.count("\n---\n") == 2
    hist = (raiz / "docs" / "superpowers" / "MAPA-historico.md").read_text(encoding="utf-8")
    assert '## 2026-09-15 — rodízio de "Onde estamos"' in hist and "anterior 2" in hist and "anterior 3" in hist
    assert '## 2026-09-15 — rodízio de "Próximo passo"' in hist and "passo velho." in hist
    assert hist.index("anterior 2") < hist.index("anterior 3"), "ordem original preservada (mais novo em cima)"
    assert rel.movidas == 4           # linhas de conteúdo movidas (anterior 2 ×2, anterior 3, passo velho); `---` não conta
    assert rel.bytes_depois < rel.bytes_antes


def test_mapa_dry_run_nao_escreve(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    antes = (raiz / "docs" / "superpowers" / "MAPA.md").read_bytes()
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=False)
    assert rel.ok and rel.movidas == 4
    assert (raiz / "docs" / "superpowers" / "MAPA.md").read_bytes() == antes
    assert not (raiz / "docs" / "superpowers" / "MAPA-historico.md").exists()


def test_mapa_bloco_unico_e_intocado_e_nada_a_mover(tmp_path):
    mod = _mod()
    curto = "# Mapa\n\n## Onde estamos\n\nsó um bloco.\n\n## Próximo passo\n\n1. só um.\n\n## Conexões\n\n- x\n"
    raiz = _projeto(tmp_path, mapa=curto)
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok and rel.movidas == 0
    assert (raiz / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8") == curto
    assert not (raiz / "docs" / "superpowers" / "MAPA-historico.md").exists()


def test_mapa_historico_existente_recebe_prepend_depois_do_titulo(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    hist = raiz / "docs" / "superpowers" / "MAPA-historico.md"
    hist.write_text("<!-- comentário -->\n\n# Histórico do mapa — Proj\n\n## 2026-08-01 — antigo\n\nvelho.\n", encoding="utf-8")
    mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    t = hist.read_text(encoding="utf-8")
    assert t.startswith("<!-- comentário -->\n\n# Histórico do mapa — Proj\n")
    assert t.index("2026-09-15") < t.index("2026-08-01")


def test_mapa_avisa_quando_ainda_acima_do_teto(tmp_path):
    mod = _mod()
    gordo = MAPA.replace("linha 2 do atual.", "linha 2 do atual. " + "x" * 7000)
    raiz = _projeto(tmp_path, mapa=gordo)
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok and any("ainda acima do teto" in a and "conteúdo" in a for a in rel.avisos)
    assert "x" * 7000 in (raiz / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8"), "bloco atual NUNCA se corta"


def test_mapa_preserva_crlf(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path, mapa=MAPA.replace("\n", "\r\n"))
    mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert b"\r\n" in (raiz / "docs" / "superpowers" / "MAPA.md").read_bytes()
    assert b"\r\n" in (raiz / "docs" / "superpowers" / "MAPA-historico.md").read_bytes()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_rodizio_partida.py -q`
Expected: falha por arquivo inexistente.

- [ ] **Step 3: Implementar**

```python
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
from __future__ import annotations

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


def rodizio_mapa(proj: Path, hoje: str | None = None, aplicar: bool = False) -> Relatorio:
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


def rodizio_index(proj: Path, hoje: str | None = None, aplicar: bool = False) -> Relatorio:
    raise NotImplementedError   # Task 8


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar**

Run: `python -m pytest tests/test_rodizio_partida.py -q`
Expected: 6 passed.

- [ ] **Step 5: Dry-run real no Whats (só leitura)**

Run: `python templates/rodizio_partida.py mapa --proj "/c/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats"`
Expected: `mapa: 89651 → <N> bytes`, `DRY-RUN — nada gravado.` Anote N para a spec/CHANGELOG (estimativa: 8 a 12 KB; o aviso "ainda acima do teto" é esperado).

- [ ] **Step 6: Commit**

```bash
git add templates/rodizio_partida.py tests/test_rodizio_partida.py
git commit -m "feat(partida): rodizio_partida.py mapa -- 2 blocos por secao, resto pro MAPA-historico (move, dry-run, conservacao)"
```

---

### Task 8: `rodizio_partida.py index`

**Files:**
- Modify: `templates/rodizio_partida.py`
- Test: `tests/test_rodizio_partida.py`

- [ ] **Step 1: Testes (falham)**

```python
# --- index ------------------------------------------------------------------------------

def test_index_move_so_fechada_e_preserva_fora_de_escopo(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    rel = mod.rodizio_index(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok, rel.problemas
    idx = (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8")
    assert "[formatação]" in idx and "pausada: aguardando layout" in idx and "**em andamento**" in idx
    assert "[relatório]" not in idx and "[alerta]" not in idx
    assert "login social — fechada de propósito" in idx, "'Fora de escopo' NUNCA se move"
    assert "## Backlog" in idx, "cabeçalho fica mesmo esvaziado"
    hist = (raiz / "docs" / "superpowers" / "INDEX-historico.md").read_text(encoding="utf-8")
    assert "## 2026-09-15 — fechadas" in hist and "[relatório]" in hist and "[alerta]" in hist
    assert rel.movidas == 2


def test_index_dry_run_nao_escreve(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    antes = (raiz / "docs" / "superpowers" / "INDEX.md").read_bytes()
    rel = mod.rodizio_index(raiz, hoje="2026-09-15", aplicar=False)
    assert rel.ok and rel.movidas == 2
    assert (raiz / "docs" / "superpowers" / "INDEX.md").read_bytes() == antes


def test_index_reusa_a_regra_de_status_do_hook():
    """`pausada` não é fechada; `fechada` em negrito também conta — a mesma leitura do um_item_por_janela."""
    mod = _mod()
    assert mod.fechada("- [x](../specs/x.md) — obj — **fechada** (2026-09-01)")
    assert not mod.fechada("- [x](../specs/x.md) — obj — pausada: espera")
    assert not mod.fechada("- [x](../specs/x.md) — obj — aberta")


def test_index_avisa_abertas_que_nao_cabem(tmp_path):
    mod = _mod()
    muitas = "# Índice\n\n## Em andamento\n" + "".join(
        f"- [tarefa {i}](../specs/t{i}.md) — {'objetivo ' * 30} — aberta\n" for i in range(40))
    raiz = _projeto(tmp_path, index=muitas)
    rel = mod.rodizio_index(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok and rel.movidas == 0
    assert any("aberta" in a and "owner" in a for a in rel.avisos)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_rodizio_partida.py -q -k index`
Expected: `NotImplementedError` / `AttributeError: fechada`.

- [ ] **Step 3: Implementar** — substitua o `rodizio_index` de rascunho e acrescente `fechada`:

```python
@functools.lru_cache(maxsize=1)
def _hook_um_item():
    """Reusa RE_ITEM/RE_SEPARADOR/FECHADOS do hook um_item_por_janela.py (mesma leitura de status).
    Cacheado: é chamado por linha do INDEX."""
    caminho = Path(__file__).resolve().parent.parent / "hooks" / "um_item_por_janela.py"
    spec = importlib.util.spec_from_file_location("um_item_por_janela", caminho)
    mod = importlib.util.module_from_spec(spec)
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


def rodizio_index(proj: Path, hoje: str | None = None, aplicar: bool = False) -> Relatorio:
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
```

- [ ] **Step 4: Rodar**

Run: `python -m pytest tests/test_rodizio_partida.py tests/test_hook_um_item_por_janela.py -q`
Expected: 10 passed (rodízio) + hook verde.

- [ ] **Step 5: Dry-run real no Whats (só leitura)**

Run: `python templates/rodizio_partida.py index --proj "/c/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats"`
Expected: `linhas movidas: 13`, aviso das abertas, `DRY-RUN — nada gravado.`

- [ ] **Step 6: Commit**

```bash
git add templates/rodizio_partida.py tests/test_rodizio_partida.py
git commit -m "feat(partida): rodizio_partida.py index -- fechada vai pro INDEX-historico; Fora de escopo e abertas ficam"
```

---

### Task 9: tetos e moldes — `test_orcamento_contexto`, `anatomia.py`, `templates/MEMORY.md`, `templates/CLAUDE.md`

**Files:**
- Modify: `tests/test_orcamento_contexto.py`
- Modify: `templates/anatomia.py:24-29`
- Modify: `templates/MEMORY.md` (reescrever)
- Modify: `templates/CLAUDE.md:20`

- [ ] **Step 1: Testes (falham)** — em `tests/test_orcamento_contexto.py`, acrescente após `TETO_INDEX`:

```python
TETO_MEMORY_TOPO = 6000     # bytes — o TOPO do índice de memória (famílias); os subíndices carregam sob demanda
```

e ao fim do arquivo:

```python
def test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega():
    """L — 'acima de 25 KB o excedente não carrega' vale só pra pasta NATIVA do Claude Code. O índice do repo
    entra pelo Read (2.000 linhas). Copiar o teto da nativa pro repo mandou PODAR um índice de 93 memórias."""
    for rel in ("templates/MEMORY.md", "commands/memory.md", "commands/doctor.md"):
        low = (REPO / rel).read_text(encoding="utf-8").lower()
        for frase in ("excedente nem carrega", "excedente não carrega", "200 linhas / 25 kb", "200 linhas e 25 kb"):
            assert frase not in low, f"{rel} ainda repete a premissa falsa: {frase!r}"
        assert "orçamento" in low, f"{rel} não explica que o teto é orçamento de partida"


def test_molde_de_memoria_ensina_o_topo_e_o_subindice():
    txt = (REPO / "templates" / "MEMORY.md").read_text(encoding="utf-8")
    assert "indice/" in txt and "subíndice" in txt.lower(), "templates/MEMORY.md não ensina os dois níveis"
    assert "6 KB" in txt, "templates/MEMORY.md não documenta o teto do topo"
    assert "memoria_indice.py" in txt, "templates/MEMORY.md não aponta o script que divide/verifica"


def test_claude_md_manda_abrir_o_subindice_quando_a_familia_bate():
    low = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").lower()
    assert "memory/indice/" in low, "CLAUDE.md não diz onde estão os subíndices"
    assert "antes de agir" in low, "CLAUDE.md não manda abrir o subíndice ANTES de agir"


def test_anatomia_usa_o_teto_do_topo():
    src = (REPO / "templates" / "anatomia.py").read_text(encoding="utf-8")
    assert '"memory/MEMORY.md": 6000' in src, "anatomia.py ainda mede o índice contra 25 KB"


def test_doctor_aponta_o_conserto_mecanico():
    """G — o doctor só reporta, mas agora o conserto é UMA linha que o owner manda rodar."""
    txt = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    for script, modo in (("rodizio_partida", "mapa"), ("rodizio_partida", "index"),
                         ("memoria_indice", "dividir"), ("memoria_indice", "verificar")):
        # aceita `…/rodizio_partida.py" mapa` (caminho entre aspas) e `rodizio_partida.py mapa`
        assert re.search(rf'{script}\.py"?\s+{modo}\b', txt), f"doctor não aponta `{script}.py {modo}` como conserto"
```

Em `tests/test_memoria_gatilho.py` troque o bloco de tetos e os 3 testes do índice:

```python
# teto do TOPO do índice (famílias) — orçamento de partida; os subíndices carregam sob demanda
TETO_TOPO_BYTES = 6000

INDICES = {"MEMORY.md", "DIARIO.md"}


def _linhas_dos_subindices() -> list:
    subs = sorted((REPO / "memory" / "indice").glob("*.md"))
    assert subs, "memory/indice/ vazio — rode `python templates/memoria_indice.py dividir --aplicar`"
    return [l for p in subs for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]


def test_indice_memoria_dentro_do_teto():
    """CA6 — o topo entra em toda janela: 6 KB. (O teto de 25 KB era o da pasta NATIVA, copiado por engano.)"""
    idx = REPO / "memory" / "MEMORY.md"
    tamanho = len(idx.read_text(encoding="utf-8").encode("utf-8"))
    assert tamanho <= TETO_TOPO_BYTES, f"memory/MEMORY.md tem {tamanho} bytes (teto {TETO_TOPO_BYTES})"


def test_indice_agrupado_por_gatilho():
    """CA6 — topo aponta subíndices por família; cada linha de subíndice começa pelo gatilho."""
    topo = (REPO / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert "→ [subíndice](indice/" in topo, "memory/MEMORY.md não é o topo por família"
    ruins = [l for l in _linhas_dos_subindices() if not l.lower().startswith("- **quando ")]
    assert not ruins, "linhas de subíndice que não começam pelo gatilho:\n" + "\n".join(ruins)


def test_toda_memoria_esta_no_indice():
    """Memória fora dos subíndices é memória invisível — exceto a marcada `obsoleta:`."""
    txt = "\n".join(_linhas_dos_subindices())
    faltando = [md.name for md in _memorias()
                if md.name not in txt and not re.search(r"^obsoleta:", _frontmatter(md), re.M)]
    assert not faltando, "memórias fora dos subíndices:\n" + "\n".join(faltando)


def test_template_memory_documenta_gatilho_e_teto():
    """O molde que vai pros outros projetos carrega a mesma regra."""
    txt = (REPO / "templates" / "MEMORY.md").read_text(encoding="utf-8")
    assert "gatilho:" in txt, "templates/MEMORY.md não documenta o campo gatilho:"
    assert "6 KB" in txt, "templates/MEMORY.md não documenta o teto do topo (6 KB)"
```

(`_memorias()` passa a excluir também a pasta `indice/`: como ela usa `glob("*.md")` em `memory/`, subpastas já ficam de fora — nada a mudar.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_orcamento_contexto.py tests/test_memoria_gatilho.py -q`
Expected: falham os 5 testes novos + os 3 do índice (o kit ainda é plano; Task 11 divide).

- [ ] **Step 3: `templates/anatomia.py`** — em `TETOS`, troque `"memory/MEMORY.md": 25 * 1024,` por `"memory/MEMORY.md": 6000,` e o comentário da linha 23 por `# tetos do orçamento de contexto (os mesmos de tests/test_orcamento_contexto.py; MEMORY.md = só o TOPO)`.

- [ ] **Step 4: `templates/MEMORY.md`** — substitua o arquivo inteiro:

```markdown
<!-- MODELO do TOPO do índice de memória — copie para `memory/MEMORY.md` (dentro do repo do projeto).

     O índice tem DOIS níveis:
     - TOPO (este arquivo): 1 linha por FAMÍLIA de gatilho. Entra em toda janela → teto **6 KB**
       (orçamento de partida — o que se lê antes de qualquer trabalho útil).
     - SUBÍNDICE (`memory/indice/<familia>.md`): 1 linha por memória, aberto SÓ quando a família bate.
       Não tem teto de carga; tem teto de 600 bytes por linha.
     Regra de leitura: na partida lê-se o topo; uma família casou com a situação → abra o subíndice
     ANTES de agir. O hook `recall_memoria.py` faz o casamento por prompt e injeta os ponteiros.

     Cresceu? NÃO pode. Mova: `python <kit>/templates/memoria_indice.py dividir` transforma um índice
     plano em topo + subíndices (dry-run; `--aplicar` grava depois de conferir conservação byte a byte);
     `memoria_indice.py verificar` audita e corrige o N; `memoria_indice.py fila` lista memória sem
     `gatilho:`. (O limite que o Claude Code aplica à pasta NATIVA — 200 linhas, 25 KB — não vale
     para este arquivo: a nativa só guarda um ponteiro pra cá, e este entra pelo `Read`.)

     Cada memória em `memory/` tem este frontmatter:
         ---
         name: slug-curto
         description: 1 linha objetiva — usada pra decidir relevância
         gatilho: quando <condição observável que faz esta memória valer a leitura>
         metadata:
           type: user | feedback | project | reference
         ---
     e corpo curto (para feedback/project: regra/fato + **Why:** + **How to apply:**).
     - Memória superada ganha `obsoleta: <data> — superada por [[slug]]` e SAI do subíndice.
     - Gatilho que é ARQUIVO ("quando editar HTML de aplicação") merece virar também regra path-scoped
       em `.claude/rules/` — o Claude Code carrega sozinho. Ver `templates/rules/`.
     - Falha que já aconteceu não mora aqui: vai pro corpus `docs/EVALS.md`. -->

# Memória do projeto — índice por gatilho

<!-- 1 linha por FAMÍLIA. Gatilho bateu? abra o subíndice da família ANTES de agir. -->

- **<Família — ex.: Ao diagnosticar uma falha>** → [subíndice](indice/<familia>.md) — <N> memórias · quando: <frase 1> · <frase 2>

<!-- memory/indice/<familia>.md:
# <Família>
- **quando <condição observável>** → [Título](../arquivo.md) — <gancho de uma frase> -->
```

- [ ] **Step 5: `templates/CLAUDE.md` linha 20** — o teto é 8.000 bytes e o arquivo está a ~60 bytes dele: a troca tem de ser **do mesmo tamanho**. Substitua exatamente

`memory/MEMORY.md` (índice por **gatilho**: *quando* abrir cada memória)`

por

`memory/MEMORY.md` (famílias; bateu → `memory/indice/<f>.md` antes de agir)`

Medido em 2026-09-15: o arquivo tinha 7.991 bytes e a troca acrescenta 4 → **7.995** (teto 8.000). Confira: `python -c "from pathlib import Path; print(len(Path('templates/CLAUDE.md').read_bytes()))"` → `7995`. Se o molde tiver crescido desde então e passar de 8.000, **não** corte esta linha: mova outra regra-procedimento do `CLAUDE.md` pro seu lar (comando/`.claude/rules/`), como o `test_poda_moveu_e_nao_apagou` exige, sem apagar negação.

- [ ] **Step 6: Rodar o que já pode passar**

Run: `python -m pytest tests/test_orcamento_contexto.py -q`
Expected: só `test_doctor_aponta_o_conserto_mecanico` e `test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega` seguem vermelhos (dependem da Task 10); o resto verde, inclusive `test_claude_md_dentro_do_orcamento`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_orcamento_contexto.py tests/test_memoria_gatilho.py templates/anatomia.py templates/MEMORY.md templates/CLAUDE.md
git commit -m "feat(moldes): teto do indice de memoria = 6 KB no TOPO (orcamento), molde em dois niveis, CLAUDE.md abre o subindice antes de agir"
```

---

### Task 10: comandos — `memory.md` (passo 3 + `buscar`), `doctor.md` (checks 8 e 9), `upgrade.md`

**Files:**
- Modify: `commands/memory.md`
- Modify: `commands/doctor.md:23-24`
- Modify: `commands/upgrade.md`

- [ ] **Step 1: `commands/memory.md`**

Frontmatter: `description: Memória do projeto — resgatar a nativa pro repo · capturar a sessão · buscar um termo` e `argument-hint: "resgatar | capturar | buscar <termo> (sem argumento: pergunto qual)"`. Na lista de modos, acrescente:
`- **`buscar <termo>`** — aponta arquivo:linha onde o termo aparece em memórias, subíndices, diário, decisões e EVALS, sem abrir nada.`

No **modo capturar, passo 2**, item "aprendizado durável atemporal", troque `+ 1 linha no índice **`memory/MEMORY.md`**` por `+ 1 linha no **subíndice da família** (`memory/indice/<familia>.md`; o topo `memory/MEMORY.md` só ganha família nova) — depois rode `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" verificar --aplicar` pra conferir ponteiros e corrigir o N`.

No **passo 3** substitua a frase a partir de "O índice tem teto de" até "antes de acrescentar." por:

`O **topo** do índice (`memory/MEMORY.md`) tem teto de **6 KB** porque entra em toda janela (orçamento de partida); os subíndices não têm teto de carga. Estourou: **não pode** — é sinal de família demais ou de linha de família gorda; mova para `memory/indice/` (a divisão mecânica é `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" dividir`, dry-run por padrão). Se o projeto ainda tem índice plano, ofereça a divisão antes de acrescentar.`

Ao fim do arquivo, o modo novo:

```markdown
---

## Modo: buscar

Você vai **apontar onde um assunto já foi tratado** — sem abrir arquivo, sem reler conversa. É o mesmo motor
do hook `recall_memoria.py`, sem o teto de 3 resultados.

1. Rode `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" buscar "<termo>" --limite 10` (se a
   variável não resolveu, ache o script no clone do kit como o `doctor` faz no check 1).
2. Reporte os ponteiros **como vieram** (`arquivo:linha — gancho`), em ordem de score. **Não abra** os
   arquivos, salvo pedido: o objetivo é o owner ver onde está, não pagar a leitura de tudo.
3. Nada casou → diga isso e sugira 1 termo alternativo (sinônimo/identificador), sem inventar resultado.
```

- [ ] **Step 2: `commands/doctor.md`**

Check 8, troque a última frase `Confira também o teto do índice do repo: **≤ 200 linhas / 25 KB** — acima disso o excedente nem carrega.` por:
`Confira também o índice do repo com `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" verificar` (topo ≤ 6 KB, ponteiros íntegros, toda memória com linha): **⚠** com a saída do script; índice ainda plano → **⚠** "rode `memoria_indice.py dividir` (dry-run) e me mostre a tabela".`

Check 9, troque `· `memory/MEMORY.md` (**25 KB / 200 linhas**)` por `· `memory/MEMORY.md` (**6 KB** — só o topo; subíndices carregam sob demanda)` e, na frase do conserto, troque `histórico do MAPA vai pro `MAPA-historico.md`, tarefa fechada pro `INDEX-historico.md`,` por:
`MAPA acima do teto → mostre `python "${CLAUDE_PLUGIN_ROOT}/templates/rodizio_partida.py" mapa` (dry-run: mantém 2 blocos por seção, o resto vai pro `MAPA-historico.md`) · INDEX acima → `rodizio_partida.py index` (move só `fechada`) · índice de memória plano ou acima → `memoria_indice.py dividir` / `verificar` —`.
Mantenha o resto da frase (CLAUDE.md → comando/rules; `obsoleta:`; "Nunca sugira apagar guardrail"; "Só reporta; não edita nada").

- [ ] **Step 3: `commands/upgrade.md`** — na seção das categorias (após "Três categorias:"), acrescente ao fim da lista de categoria 1 (referência) uma linha:
`- **Índice de memória plano** (`memory/MEMORY.md` com linhas `- [` e sem `memory/indice/`): não sobrescreva; mostre `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" dividir` em dry-run e peça OK antes do `--aplicar` (move, não apaga).`

- [ ] **Step 4: Rodar**

Run: `python -m pytest tests/test_orcamento_contexto.py tests/test_smoke_kit.py -q`
Expected: verde (o smoke tem testes que leem `commands/*.md`; se algum quebrar por texto trocado, leia a mensagem — só ajuste o texto se o teste estiver certo).

- [ ] **Step 5: Commit**

```bash
git add commands/memory.md commands/doctor.md commands/upgrade.md
git commit -m "feat(comandos): memory buscar; doctor aponta o conserto mecanico (rodizio/dividir/verificar); upgrade oferece dividir"
```

---

### Task 11: dogfood — dividir o índice do próprio kit

**Files:**
- Modify: `memory/MEMORY.md` (vira topo)
- Create: `memory/indice/*.md`

- [ ] **Step 1: Dry-run**

Run: `python templates/memoria_indice.py dividir --proj .`
Expected: 10 famílias (as `##` atuais), topo < 6 KB, `DRY-RUN`. Leia a tabela. Aviso do comentário-modelo é esperado.

- [ ] **Step 2: Aplicar e verificar**

```bash
python templates/memoria_indice.py dividir --proj . --aplicar
python templates/memoria_indice.py verificar --proj .
python templates/memoria_indice.py fila --proj .
```

Expected: `GRAVADO.` · `índice de memória: ok` · fila com 0 memórias sem gatilho (o kit já exige).

- [ ] **Step 3: Suíte inteira**

Run: `python -m pytest tests -q`
Expected: tudo verde, inclusive `test_memoria_gatilho.py` e `test_anatomia.py`. Se `test_anatomia.py` citar `25 * 1024`/`25600`, atualize para 6000 no teste com a mesma justificativa da Task 9.

- [ ] **Step 4: Prova do hook no próprio kit**

```bash
echo '{"hook_event_name":"UserPromptSubmit","cwd":"'"$(pwd -W 2>/dev/null || pwd)"'","prompt":"vou fazer git push da branch depois do merge na main"}' | python hooks/recall_memoria.py
```

Expected: JSON apontando a memória/decisão sobre publicar ser ato do owner.

- [ ] **Step 5: Commit**

```bash
git add memory/MEMORY.md memory/indice/
git commit -m "chore(memoria): indice do kit dividido em topo + memory/indice/ (dogfood do memoria_indice.py)"
```

---

### Task 12: registro 0.27.0 — CHANGELOG, plugin.json, decisões, EVALS, INDEX, MAPA

**Files:**
- Modify: `CHANGELOG.md` (topo), `.claude-plugin/plugin.json` (`"version": "0.27.0"`), `docs/decisoes.md` (1 linha ao fim), `docs/EVALS.md` (1 linha na tabela), `docs/superpowers/INDEX.md`, `docs/superpowers/MAPA.md`

- [ ] **Step 1: CHANGELOG** — insira após a linha 3:

```markdown
## 0.27.0 — 2026-09-15 (orçamento de partida por script · recall por hook)
- **o que motivou:** o kit reclamou do `memory/MEMORY.md` do Whats (25.711 bytes) dizendo que "acima de 25 KB o excedente não carrega" e mandou podar. A premissa vale só pra pasta NATIVA do Claude Code; o índice do repo entra pelo `Read`. E o índice era 12% do problema: MAPA 89.651 B (teto 6.000), INDEX 61.399 B (teto 7.000), `CLAUDE.md` 27.377 B (teto 8.000) — ~214 KB ≈ 53 mil tokens em TODA janela, e o `doctor` só avisava.
- feat(**índice de memória em dois níveis**): topo `memory/MEMORY.md` com 1 linha por família (teto **6 KB**, travado por teste) + `memory/indice/<familia>.md` aberto só quando a família bate. `templates/memoria_indice.py dividir` move byte a byte (dry-run; `--aplicar` só após conservação), `verificar` audita e corrige o N, `fila` lista memória sem `gatilho:`. Medido no índice do Whats: 25.421 → <topo> bytes na partida (−9x%).
- feat(**`hooks/recall_memoria.py`, ligado por padrão, NÃO bloqueia**): `UserPromptSubmit` casa o prompt com `gatilho:`/subíndices/diário/decisões/EVALS e injeta ≤ 600 B de ponteiros (`additionalContext`); silêncio quando nada casa; ignora `/comando`; falha aberta; escape `MSS_RECALL_OFF=1`. É o "bloco de notas" que aponta onde o assunto foi tratado sem o owner reler conversa.
- feat(**`/mss-spec:memory buscar <termo>`**): mesmo motor, até 10 ponteiros `arquivo:linha`, sem abrir arquivo.
- feat(**`templates/rodizio_partida.py`**): `mapa` mantém 2 blocos por seção ("Onde estamos"/"Próximo passo", separados por `---`) e move o resto pro `MAPA-historico.md` (prepend datado); `index` move só `fechada` pro `INDEX-historico.md`, "Fora de escopo" e abertas ficam. Dry-run por padrão; conservação byte a byte; se ainda estourar, diz que é conteúdo e **não corta**. Dry-run no Whats: MAPA 89.651 → <N> B; INDEX move 13.
- fix(**premissa falsa removida**): `templates/MEMORY.md`, `commands/memory.md`, `doctor` (checks 8 e 9), `anatomia.py`: teto do índice do repo é **orçamento** (6 KB no topo); "não carrega" fica só pra nativa; o conserto indicado é dividir/rodízio, nunca "funda linhas"/"pode" (`test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega`).
- feat(**`doctor` check 9 aponta o comando exato**): MAPA/INDEX/índice acima do teto → imprime `rodizio_partida.py mapa|index` / `memoria_indice.py dividir|verificar` em dry-run. Continua só reportando.
- chore(dogfood): o índice do próprio kit foi dividido pelo script (10 famílias).
```

Preencha `<topo>`, `9x%` e `<N>` com os números medidos nas Tasks 2, 7 e 8.

- [ ] **Step 2: `plugin.json`** — `"version": "0.27.0"`.

- [ ] **Step 3: `docs/decisoes.md`** — acrescente ao fim:

```markdown
- 2026-09-15 — **o teto do índice de memória do repo é ORÇAMENTO (6 KB, só o topo por família), não truncamento — e o recall passa a ser injetado por hook.** "Acima de 25 KB o excedente não carrega" vale só pra pasta nativa do Claude Code (copiamos o número errado em 2026-08-18, e o efeito foi mandar podar 93 memórias). Índice em dois níveis (`memory/indice/`), `recall_memoria.py` (UserPromptSubmit, ≤ 600 B, não bloqueia) e `rodizio_partida.py` (MAPA 2 blocos por seção; INDEX só viva) — tudo **move, nunca apaga**, dry-run por padrão, conservação byte a byte. Rejeitado: subir o teto pra 60 KB (adia; 15 mil tokens por janela) e índice gerado só do frontmatter (não resolve tamanho; fica pra depois, se a fila de `gatilho:` zerar).
```

- [ ] **Step 4: `docs/EVALS.md`** — nova linha na tabela, após F-023:

```markdown
| F-024 | 2026-09-14 | quando um teto/limite copiado de outro contexto mandar PODAR conteúdo | premissa não verificada virou prescrição | topo 6 KB = orçamento, "não carrega" só na nativa, conserto = mover (`dividir`/`rodizio`) · `test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega` + `test_doctor_aponta_o_conserto_mecanico` | fechado |
```

- [ ] **Step 5: INDEX e MAPA do kit**

Em `docs/superpowers/INDEX.md`, acrescente em "Em andamento": `- [orçamento de partida e recall determinístico](../specs/2026-09-15-orcamento-de-partida-e-recall-deterministico-design.md) — índice em dois níveis · hook de recall · rodízio MAPA/INDEX — fechada` (fechada, porque este é o commit de fecho; o `rodizio index` a leva ao histórico na próxima rodada). Em `docs/superpowers/MAPA.md`, atualize "Onde estamos" (1 parágrafo: 0.27.0 na branch, push pendente, ato do owner) e "Próximo passo" (aplicar no Whats em janela própria: `dividir` → `rodizio mapa` → `rodizio index` → `doctor`, cada um com dry-run e OK). Rode `python templates/rodizio_partida.py mapa --proj .` em dry-run e, se mover algo, aplique — o MAPA do kit tem de continuar ≤ 6 KB (`test_mapa_carrega_um_estado_anterior`).

- [ ] **Step 6: Suíte inteira + commit**

Run: `python -m pytest tests -q`
Expected: tudo verde.

```bash
git add CHANGELOG.md .claude-plugin/plugin.json docs/decisoes.md docs/EVALS.md docs/superpowers/INDEX.md docs/superpowers/MAPA.md docs/superpowers/MAPA-historico.md
git commit -m "chore(release): 0.27.0 -- orcamento de partida por script + recall por hook (F-024)"
```

Sem `git push` e sem merge na `main`: publicar é ato do owner (o hook `git_publicacao.py` nega de qualquer jeito). Entregue ao owner os comandos de merge e push e o comando de volta (`git checkout main` continua intocada; tag não é necessária porque a `main` não foi alterada).

---

## Fora deste plano (registrado para a janela do Whats)

1. `python <kit>/templates/memoria_indice.py dividir --proj <Whats>` → tabela → OK → `--aplicar` → commit.
2. `rodizio_partida.py mapa --proj <Whats>` → dry-run → OK → `--aplicar` → commit. Aviso "ainda acima do teto" esperado: o bloco atual do MAPA é conteúdo do owner.
3. `rodizio_partida.py index --proj <Whats>` (move 13 `fechada`) → OK → `--aplicar` → commit. Os 24 `aberta` são decisão do owner.
4. `/mss-spec:doctor` para medir o total novo (meta ~33 KB ≈ 8 mil tokens por janela).
5. Fila de conteúdo, sem prazo: 77 `gatilho:`; `CLAUDE.md` 27 KB → 8 KB; reagrupar famílias por gatilho.
