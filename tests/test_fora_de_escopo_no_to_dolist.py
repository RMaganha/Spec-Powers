"""Fora de escopo = "não agora", uma linha por item no to-dolist com a tag #fora-de-escopo (0.47.0).

Spec: docs/specs/fora-de-escopo-no-to-dolist.md · decisão: docs/decisoes.md (2026-10-28).
O formato antigo (seção no INDEX, FORA-DE-ESCOPO.md) segue aceito só nos scripts que leem outros
projetos — provisório até o upgrade converter cada um.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TODO_KIT = REPO / "to-dolist.md"
RE_ITEM = re.compile(r"^- .+ #fora-de-escopo \(decidido: \d{4}-\d{2}-\d{2}, .+\)$")
# textos vivos (o que o assistente lê ou o kickoff copia); história — CHANGELOG, specs/planos antigos,
# diários — registra o que era verdade na época e fica como está
VIVOS = [*(REPO / "commands").glob("*.md"), *(REPO / "hooks").glob("*.py"), REPO / "hooks" / "README.md",
         *(REPO / "templates").glob("*.py"), *(REPO / "templates").glob("*.md"), REPO / "templates" / "gitignore",
         REPO / "docs" / "LEIA-ME.md", REPO / "docs" / "COMO-FUNCIONA.html"]


def _ler(p):
    return p.read_text(encoding="utf-8")


def _ignora_todolist(gitignore: str) -> bool:
    return any(l.strip() in ("/to-dolist.md", "to-dolist.md") for l in gitignore.splitlines())


def _secao_fora_de_escopo(texto: str) -> bool:
    return any(l.startswith("#") and "fora de escopo" in l.lower() for l in texto.splitlines())


def test_todolist_vai_pro_git_no_molde_e_no_kit():
    assert not _ignora_todolist(_ler(REPO / "templates" / "gitignore")), "molde ainda ignora o to-dolist"
    assert not _ignora_todolist(_ler(REPO / ".gitignore")), "o kit ainda ignora o próprio to-dolist"
    assert "/to-dolist.md" not in _ler(REPO / "commands" / "compliance.md"), \
        "compliance ainda exige o to-dolist ignorado"


def test_comando_todolist_fala_do_formato_novo():
    todo = _ler(REPO / "commands" / "to-dolist.md")
    assert "#fora-de-escopo" in todo
    assert "listar #fora-de-escopo" in todo, "falta o filtro pedido pelo owner"
    assert "(decidido: AAAA-MM-DD, " in todo, "falta o formato da linha"
    assert "depois do merge" in todo, "falta o custo: item de uma branch só chega na main depois do merge"
    assert "Nunca commite" not in todo and "fora do git" not in todo


def test_captura_roteia_nao_agora_pro_todolist():
    mem = _ler(REPO / "commands" / "memory.md")
    assert "#fora-de-escopo" in mem and "to-dolist.md" in mem
    assert "decidido NÃO fazer" not in mem and "decidiu-se NÃO fazer" not in mem


def test_molde_do_index_sem_secao_fora_de_escopo():
    assert "fora de escopo" not in _ler(REPO / "templates" / "INDEX.md").lower()


def test_nenhum_texto_vivo_diz_que_fora_de_escopo_e_proibicao():
    """O erro de origem: "NÃO fazer" sem "naquele momento" virou proibição (docs/decisoes.md, 2026-10-28)."""
    proibicao = re.compile(r"fora de escopo[^\n]{0,40}n[ãa]o fazer|decis[õo]es de n[ãa]o fazer", re.I)
    achados = [f"{p.relative_to(REPO)}: {m.group(0)}" for p in VIVOS if p.is_file()
               for m in proibicao.finditer(_ler(p))]
    assert not achados, achados


def test_kit_converteu_o_proprio_fora_de_escopo():
    assert not (REPO / "docs" / "superpowers" / "FORA-DE-ESCOPO.md").exists()
    assert not _secao_fora_de_escopo(_ler(REPO / "docs" / "superpowers" / "INDEX.md"))
    itens = [l for l in _ler(TODO_KIT).splitlines() if "#fora-de-escopo" in l]
    assert len(itens) >= 50, f"só {len(itens)} itens convertidos"
    fora_do_formato = [l for l in itens if not RE_ITEM.match(l)]
    assert not fora_do_formato, fora_do_formato
