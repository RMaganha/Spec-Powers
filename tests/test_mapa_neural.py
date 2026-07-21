"""Comportamento de `templates/mapa_neural.py` (F2 — o mapa mental do projeto).

O gerador monta o **mapa mental do projeto atual**: uma árvore com o projeto no centro e
4 dimensões (arquitetura interna · APIs & integrações · memórias & conhecimento · conexões
entre projetos), cada uma preenchida por um extrator que lê o repo. Produz duas saídas do
mesmo modelo: (a) `mapa-neural.md` (índice em texto que o assistente consulta) e (b)
`mapa-neural.html` (mapa radial full-screen, expansível/arrastável, self-contained).
Aqui exercitamos cada extrator + o render com fixtures; o wiring fica no smoke.
"""
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "templates" / "mapa_neural.py"


@pytest.fixture()
def mn():
    spec = importlib.util.spec_from_file_location("mss_mapa_neural", TEMPLATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def proj(tmp_path):
    """Um projeto-fixture no padrão do kit, com as 4 dimensões representadas."""
    (tmp_path / "docs" / "superpowers" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "superpowers" / "MAPA.md").write_text(
        "# Mapa de contexto — meu-proj\n\n## Onde estamos\nx\n\n## Próximo passo\ny\n\n"
        "## Conexões\n- → IA Jeday Cosseguro: manda o PDF (banco TKGS_CORP)\n"
        "- ← n8n: expõe a fila (GET /api/queue_processar)\n- nenhuma\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "superpowers" / "specs" / "2026-01-01-emissao-design.md").write_text(
        "# emissão cosseguro — design\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "decisoes.md").write_text("# Decisões\n- 2026 — banco = canal\n", encoding="utf-8")
    (tmp_path / "main.py").write_text('"""Ponto de entrada da API do meu-proj."""\nprint("ok")\n', encoding="utf-8")
    (tmp_path / "routers").mkdir()
    (tmp_path / "routers" / "processar.py").write_text(
        "import pyodbc\nfrom fastapi import APIRouter\nrouter = APIRouter()\n"
        "@router.get('/api/queue_processar')\ndef q(): ...\n"
        "@router.post('/api/processar')\ndef p(): ...\n",
        encoding="utf-8",
    )
    (tmp_path / "services").mkdir()
    (tmp_path / "services" / "emissao.py").write_text("# regra de emissão\n", encoding="utf-8")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "MEMORY.md").write_text(
        "- [Motor Gemini migrado](m1.md) — migrou o motor\n- [Banco como canal](m2.md) — decisão\n",
        encoding="utf-8",
    )
    (tmp_path / "memory" / "DIARIO.md").write_text(
        "# Diário de sessão — meu-proj\n\n## 2026-01-02\n"
        "- [emissao-retry] discutimos o retry no envio → backoff exponencial → sessions/2026-01-02-emissao-retry.md\n",
        encoding="utf-8",
    )
    return tmp_path


def _ids(no):
    """Todos os ids de uma subárvore (recursivo), pra asserção simples."""
    acc = [no["id"]]
    for f in no.get("filhos", []):
        acc += _ids(f)
    return acc


# ---- extratores ----------------------------------------------------------

def test_extrair_conexoes(mn, proj):
    no = mn.extrair_conexoes(proj)
    assert no["dim"] == "conn"
    ids = _ids(no)
    assert "IA Jeday Cosseguro" in ids, "não trouxe o projeto vizinho declarado (nome completo)"
    assert "n8n" in ids
    assert not any("nenhuma" in i.lower() for i in ids), "não pode incluir a linha 'nenhuma'"


def test_extrair_arquitetura(mn, proj):
    no = mn.extrair_arquitetura(proj)
    assert no["dim"] == "arq"
    ids = " | ".join(_ids(no))
    assert "main.py" in ids and "routers" in ids and "services" in ids


def test_arquitetura_traz_resumo_da_peca(mn, proj):
    """O índice deve trazer o resumo de 1 linha por peça (docstring) — pra servir de consulta
    e o assistente não reabrir a fonte a cada pergunta."""
    txt = mn.render_texto(mn.construir_arvore(proj))
    assert "Ponto de entrada da API" in txt, "o resumo (docstring) da peça não aparece no índice"


def test_extrair_apis_endpoints_e_integracoes(mn, proj):
    no = mn.extrair_apis(proj)
    assert no["dim"] == "api"
    ids = " | ".join(_ids(no))
    assert "GET /api/queue_processar" in ids, "não extraiu o endpoint GET"
    assert "POST /api/processar" in ids, "não extraiu o endpoint POST"
    assert "SQL" in ids or "banco" in ids.lower(), "não detectou a integração de banco (pyodbc)"


def test_extrair_memorias(mn, proj):
    no = mn.extrair_memorias(proj)
    assert no["dim"] == "mem"
    ids = " | ".join(_ids(no))
    assert "emissão cosseguro" in ids, "não trouxe a spec"
    assert "Gemini" in ids, "não trouxe a memória do índice"


def test_extrair_diario(mn, proj):
    """A dimensão de memórias traz também o diário de sessão (memory/DIARIO.md → memory/sessions/)."""
    no = mn.extrair_memorias(proj)
    ids = " | ".join(_ids(no))
    assert "emissao-retry" in ids, "o mapa mental não trouxe a entrada do diário (memory/DIARIO.md)"


def test_construir_arvore_projeto_no_centro_com_4_dimensoes(mn, proj):
    arv = mn.construir_arvore(proj)
    assert arv["dim"] == "projeto" and arv["id"] == "meu-proj"
    dims = {f["dim"] for f in arv["filhos"]}
    assert dims == {"arq", "api", "mem", "conn"}, "a raiz deve ter exatamente as 4 dimensões"


# ---- render --------------------------------------------------------------

def test_render_html_full_screen_e_self_contained(mn, proj):
    html = mn.render_html(mn.construir_arvore(proj))
    low = html.lower()
    assert "<script src=" not in low, "HTML referencia script externo (não é self-contained)"
    assert "100vw" in low or "100vh" in low, "o SVG/página não ocupa a tela toda (full-screen)"
    assert "var tree" in low or "const tree" in low, "a árvore não foi embutida como dado no HTML"
    assert "meu-proj" in html, "o nome do projeto não aparece no HTML"
    assert "IA Jeday Cosseguro" in html, "uma conexão real não aparece no HTML"
    # grafo via vis-network embutido (física/zoom/pan) + pop-up rico com o local
    assert "vis.Network" in html and "vis.DataSet" in html, "não usa a lib vis-network (grafo com física/zoom/pan)"
    assert "vis-network" in html, "a lib vis-network não está embutida inline (self-contained)"
    assert 'id="pop"' in html, "sem o pop-up de detalhes"
    assert "routers/processar.py" in html, "o local (caminho) da peça não foi embutido pro pop-up"


def test_render_texto_lista_as_dimensoes(mn, proj):
    txt = mn.render_texto(mn.construir_arvore(proj))
    for marca in ("Arquitetura", "APIs", "Memórias", "Conexões"):
        assert marca in txt, f"o índice de texto não lista a dimensão {marca}"


def test_gerar_cria_md_e_html(mn, proj, tmp_path):
    out = tmp_path / "_out"
    md, html = mn.gerar(proj_dir=proj, out_dir=out)
    assert Path(md).exists() and Path(md).suffix == ".md"
    assert Path(html).exists() and Path(html).suffix == ".html"
