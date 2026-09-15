"""memoria_indice.py — índice de memória em dois níveis (topo por família + memory/indice/).

Por que existe: o índice plano do Whats chegou a 25.421 bytes (~6.355 tokens em TODA janela) e o kit
mandou PODAR — contra a própria decisão "mover, nunca apagar". O topo passa a ter 1 linha por família
(teto 6 KB) e as memórias vivem em subíndices lidos só quando a família bate.
"""
import importlib.util
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_indice.py"
FIXTURE = REPO / "tests" / "fixtures" / "memoria_whats_2026-09-14" / "MEMORY.md"

FRONT_COM_GATILHO = "---\nname: {name}\ndescription: {desc}\ngatilho: quando {gat}\nmetadata:\n  type: project\n---\n\ncorpo\n"
FRONT_SEM_GATILHO = "---\nname: {name}\ndescription: {desc}\nmetadata:\n  type: project\n---\n\ncorpo\n"


def _mod():
    spec = importlib.util.spec_from_file_location("memoria_indice", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses (3.14) resolve anotações via sys.modules
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
