"""Recall da memória: gatilho no frontmatter, índice agrupado por gatilho, corpus de falhas.

Por que estes testes existem: 27 das 33 memórias duráveis nunca entravam na sessão sozinhas —
o índice que o Claude Code auto-carrega é o da pasta nativa (volátil), e o índice do repo dizia
*o que a memória é* em vez de *quando abrir*. Gatilho + teto + corpus de falhas são o conserto.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# tetos que o próprio Claude Code aplica ao índice de auto-memory (docs: Memory)
TETO_LINHAS = 200
TETO_BYTES = 25 * 1024

INDICES = {"MEMORY.md", "DIARIO.md"}


def _memorias():
    arqs = [p for p in sorted((REPO / "memory").glob("*.md")) if p.name not in INDICES]
    assert arqs, "nenhuma memória encontrada em memory/"
    return arqs


def _frontmatter(md: Path) -> str:
    txt = md.read_text(encoding="utf-8")
    assert txt.startswith("---"), f"{md.name}: sem frontmatter"
    return txt.split("---")[1]


def test_toda_memoria_tem_gatilho():
    """CA5 — memória sem gatilho é memória que ninguém sabe quando abrir."""
    sem = [md.name for md in _memorias() if not re.search(r"^gatilho:\s*\S", _frontmatter(md), re.M)]
    assert not sem, "memórias sem `gatilho:` no frontmatter:\n" + "\n".join(sem)


def test_gatilho_e_condicao_observavel():
    """O gatilho descreve QUANDO abrir ('quando ...'), não o que a memória é."""
    fora = []
    for md in _memorias():
        m = re.search(r"^gatilho:\s*(.+)$", _frontmatter(md), re.M)
        if not m or not m.group(1).strip().lower().startswith("quando "):
            fora.append(md.name)
    assert not fora, "gatilho tem que começar por 'quando ' (condição observável):\n" + "\n".join(fora)


def test_indice_memoria_dentro_do_teto():
    """CA6 — acima de 200 linhas / 25 KB o excedente nem carrega."""
    idx = REPO / "memory" / "MEMORY.md"
    txt = idx.read_text(encoding="utf-8")
    linhas = len(txt.splitlines())
    tamanho = len(txt.encode("utf-8"))
    assert linhas <= TETO_LINHAS, f"memory/MEMORY.md tem {linhas} linhas (teto {TETO_LINHAS})"
    assert tamanho <= TETO_BYTES, f"memory/MEMORY.md tem {tamanho} bytes (teto {TETO_BYTES})"


def test_indice_agrupado_por_gatilho():
    """CA6 — o índice é agrupado por família de gatilho e cada linha começa pelo gatilho."""
    txt = (REPO / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert re.search(r"^## ", txt, re.M), "memory/MEMORY.md não tem grupos (## <família de gatilho>)"
    ruins = [l for l in txt.splitlines()
             if l.startswith("- ") and not l.lower().startswith("- **quando ")]
    assert not ruins, "linhas do índice que não começam pelo gatilho:\n" + "\n".join(ruins)


def test_toda_memoria_esta_no_indice():
    """Memória fora do índice é memória invisível — exceto a marcada `obsoleta:` (podada de propósito)."""
    txt = (REPO / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    faltando = [md.name for md in _memorias()
                if md.name not in txt and not re.search(r"^obsoleta:", _frontmatter(md), re.M)]
    assert not faltando, "memórias fora do índice:\n" + "\n".join(faltando)


def test_template_memory_documenta_gatilho_e_teto():
    """O molde que vai pros outros projetos carrega a mesma regra."""
    txt = (REPO / "templates" / "MEMORY.md").read_text(encoding="utf-8")
    assert "gatilho:" in txt, "templates/MEMORY.md não documenta o campo gatilho:"
    assert "200" in txt and "25" in txt, "templates/MEMORY.md não documenta o teto (200 linhas / 25 KB)"


# ---------------------------------------------------------------- corpus de falhas (docs/EVALS.md)

CASO = re.compile(r"^\| (F-\d{3}) \|", re.M)


def _evals() -> str:
    p = REPO / "docs" / "EVALS.md"
    assert p.exists(), "falta docs/EVALS.md (a memória só de falhas)"
    return p.read_text(encoding="utf-8")


def test_evals_tem_tabela_indice():
    """CA4 — colunas fixas: id, gatilho, classe, status."""
    txt = _evals()
    cab = next((l for l in txt.splitlines() if l.startswith("| id ")), "")
    for col in ("gatilho", "classe", "guardrail", "status"):
        assert col in cab, f"docs/EVALS.md: tabela-índice sem a coluna {col} (cabeçalho: {cab!r})"


def test_evals_ids_unicos_e_status_valido():
    """CA4 — id único F-NNN e status ∈ {aberto, fechado}."""
    txt = _evals()
    ids = CASO.findall(txt)
    assert ids, "docs/EVALS.md: nenhum caso F-NNN na tabela"
    assert len(ids) == len(set(ids)), f"ids repetidos em docs/EVALS.md: {ids}"
    for linha in [l for l in txt.splitlines() if CASO.match(l)]:
        status = linha.rstrip("| ").rsplit("|", 1)[-1].strip().strip("*`")
        assert status in ("aberto", "fechado"), f"status inválido em docs/EVALS.md: {linha!r}"


def test_evals_caso_fechado_tem_guardrail():
    """CA4 — caso sem guardrail NÃO pode estar fechado (é o que impede o corpus de virar teatro)."""
    ruins = []
    for linha in [l for l in _evals().splitlines() if CASO.match(l)]:
        celulas = [c.strip() for c in linha.strip("|").split("|")]
        guardrail, status = celulas[-2], celulas[-1]
        if status == "fechado" and (not guardrail or guardrail == "—"):
            ruins.append(linha)
    assert not ruins, "casos fechados sem guardrail:\n" + "\n".join(ruins)


def test_template_evals_existe():
    """O corpus de falhas é molde: todo projeto do kit nasce com ele."""
    p = REPO / "templates" / "EVALS.md"
    assert p.exists(), "falta templates/EVALS.md"
    txt = p.read_text(encoding="utf-8")
    assert "F-001" in txt or "F-NNN" in txt, "templates/EVALS.md não mostra o formato do id"
    assert "aberto" in txt, "templates/EVALS.md não documenta o status aberto (caso sem guardrail)"


def test_evals_so_cita_teste_que_existe():
    """Corpus que cita teste fantasma é teatro: todo `test_*` citado tem que existir em tests/."""
    citados = set(re.findall(r"`(test_[a-z0-9_]+)`", _evals()))
    existentes = set()
    for py in (REPO / "tests").glob("test_*.py"):
        existentes.update(re.findall(r"^def (test_[a-z0-9_]+)", py.read_text(encoding="utf-8"), re.M))
    fantasmas = sorted(citados - existentes)
    assert not fantasmas, "docs/EVALS.md cita teste que não existe:\n" + "\n".join(fantasmas)
