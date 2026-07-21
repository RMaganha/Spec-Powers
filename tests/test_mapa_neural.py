"""Comportamento de `templates/mapa_neural.py` (F2 — o mapa mental do projeto).

O gerador monta o **mapa mental do projeto atual**: uma árvore com o projeto no centro e
4 dimensões (arquitetura interna · APIs & integrações · memórias & conhecimento · conexões
entre projetos), cada uma preenchida por um extrator que lê o repo. Produz duas saídas do
mesmo modelo: (a) `mapa-neural.md` (índice em texto que o assistente consulta) e (b)
`mapa-neural.html` (mapa radial full-screen, expansível/arrastável, self-contained).
Aqui exercitamos cada extrator + o render com fixtures; o wiring fica no smoke.
"""
import importlib.util
import re
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
        "# emissão cosseguro — design\n\n"
        "Primeira linha de corpo (vira o lead/resumo).\n"
        "Segunda linha com MARCADOR_SO_NO_CORPO que não é lead.\n\n"
        "## Arquivos tocados\n"
        "- `services/emissao.py` (regra)\n"
        "- `services/nao_existe.py` (arquivo inexistente — não pode virar aresta)\n",
        encoding="utf-8",
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
    # memórias reais com [[links]] cruzados (pra testar a camada associativa): slug com hífen no
    # link vs. arquivo com underscore + prefixo (normalização), e um link órfão que não resolve.
    (tmp_path / "memory" / "feedback_rel_a.md").write_text(
        "# Rel A\nCorpo. Relacionado a [[rel-b]] e a [[nao-existe-xyz]].\n", encoding="utf-8")
    (tmp_path / "memory" / "rel_b.md").write_text(
        "# Rel B\nCorpo sem links de volta.\n", encoding="utf-8")
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


def _walk(no):
    """Itera todos os nós da subárvore (o próprio + descendentes)."""
    yield no
    for f in no.get("filhos", []):
        yield from _walk(f)


def _acha(no, id_):
    """1º nó (BFS/DFS) com o id dado, ou None."""
    return next((n for n in _walk(no) if n["id"] == id_), None)


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


# ---- F2.2: datas nas folhas -----------------------------------------------

def test_folha_com_arquivo_ganha_data_mtime(mn, proj):
    """CA15 — nó-folha ancorado num arquivo em disco tem `data` = mtime (YYYY-MM-DD);
    agrupador/raiz/endpoint (sem arquivo) não tem `data`."""
    arv = mn.construir_arvore(proj)
    main = _acha(arv, "main.py")
    assert main is not None and re.match(r"^\d{4}-\d{2}-\d{2}$", main.get("data", "")), \
        "a folha main.py não ganhou a data (mtime YYYY-MM-DD)"
    # a raiz (projeto) e uma dimensão são agrupadores — não têm data
    assert "data" not in arv, "a raiz não pode ter data"
    dim_arq = _acha(arv, "Arquitetura interna")
    assert "data" not in dim_arq, "a dimensão (agrupador) não pode ter data"
    # o endpoint (não é arquivo) não tem data
    ep = _acha(arv, "GET /api/queue_processar")
    assert ep is not None and "data" not in ep, "endpoint não é arquivo — não pode ter data"


# ---- F2.2: camada associativa ---------------------------------------------

def _pares(assoc):
    """Conjunto de pares não-ordenados {frozenset({a,b})} das arestas."""
    return {frozenset((e["a"], e["b"])) for e in assoc}


def test_associacoes_memoria_memoria_por_links(mn, proj):
    """CA17 — [[link]] que resolve a um arquivo real vira aresta (com normalização de slug);
    link órfão (não resolve) é descartado — nunca inventa nó/aresta."""
    assoc = mn.extrair_associacoes(proj)
    pares = _pares(assoc)
    assert frozenset(("memory/feedback_rel_a.md", "memory/rel_b.md")) in pares, \
        "não ligou feedback_rel_a ↔ rel_b (normalização do slug [[rel-b]] falhou)"
    # nenhum lado de aresta pode citar o link órfão
    assert not any("nao-existe" in x or "nao_existe" in x for e in assoc for x in (e["a"], e["b"])), \
        "link órfão [[nao-existe-xyz]] não pode virar aresta"


def test_associacoes_spec_codigo_por_arquivos_tocados(mn, proj):
    """CA18 — caminho citado em `## Arquivos tocados` que existe em disco vira aresta spec↔código;
    caminho inexistente é descartado."""
    assoc = mn.extrair_associacoes(proj)
    spec_local = "docs/superpowers/specs/2026-01-01-emissao-design.md"
    pares = _pares(assoc)
    assert frozenset((spec_local, "services/emissao.py")) in pares, \
        "não ligou a spec ao services/emissao.py citado em Arquivos tocados"
    assert not any("nao_existe" in x for e in assoc for x in (e["a"], e["b"])), \
        "caminho inexistente (services/nao_existe.py) não pode virar aresta"


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


def test_coletar_docs_embute_conteudo_dos_md(mn, proj):
    """Coleta o conteúdo dos .md referenciados por algum nó (via `local`), pra embutir no HTML.
    Chave = caminho relativo; valor = conteúdo do arquivo (inclui o corpo, não só o título)."""
    arv = mn.construir_arvore(proj)
    docs = mn.coletar_docs(proj, arv)
    chave_spec = next((k for k in docs if k.endswith("2026-01-01-emissao-design.md")), None)
    assert chave_spec is not None, "não coletou o .md da spec referenciada por um nó"
    assert "MARCADOR_SO_NO_CORPO" in docs[chave_spec], "coletou só o título, não o conteúdo do arquivo"
    # arquivo inexistente citado no índice de memória (m1.md/m2.md não existem) não pode virar chave
    assert not any(k.endswith("m1.md") for k in docs), "não deve coletar caminho de .md inexistente"


def test_render_html_clique_abre_md_em_nova_aba(mn, proj):
    """CA14 — o HTML embute o conteúdo dos .md (__DOCS__) e traz o handler que abre
    nova aba (window.open) + o renderizador markdown vanilla inline."""
    arv = mn.construir_arvore(proj)
    docs = mn.coletar_docs(proj, arv)
    html = mn.render_html(arv, docs=docs)
    assert "MARCADOR_SO_NO_CORPO" in html, "o conteúdo do .md não foi embutido inline no HTML"
    assert "window.open" in html, "não há handler que abre o .md em nova aba"
    assert "mdToHtml" in html, "não há o renderizador markdown vanilla inline"
    # continua self-contained (sem CDN/script externo)
    assert "<script src=" not in html.lower(), "deixou de ser self-contained"


def test_render_html_popup_mostra_data(mn, proj):
    """CA16 — o pop-up injeta a data (n.data) quando presente."""
    html = mn.render_html(mn.construir_arvore(proj))
    assert "n.data" in html, "o HTML não injeta a data (n.data) no pop-up"


def test_render_html_embute_associacoes_e_destaque(mn, proj):
    """CA19 — HTML embute as associações (__ASSOC__ → dado) + hook que acende as arestas
    ao focar um nó; segue self-contained/full-screen."""
    arv = mn.construir_arvore(proj)
    assoc = mn.extrair_associacoes(proj)
    html = mn.render_html(arv, assoc=assoc)
    assert "__ASSOC__" not in html, "o placeholder __ASSOC__ não foi substituído"
    assert "var ASSOC" in html or "const ASSOC" in html, "as associações não foram embutidas como dado"
    assert "acenderAssoc" in html, "não há o hook que acende as arestas associativas no hover"
    assert "services/emissao.py" in html, "a associação spec↔código não chegou ao HTML"
    assert "<script src=" not in html.lower(), "deixou de ser self-contained"


def test_render_texto_tem_secao_relacoes(mn, proj):
    """CA19 (texto) — o índice .md ganha a seção Relações (associativa)."""
    assoc = mn.extrair_associacoes(proj)
    txt = mn.render_texto(mn.construir_arvore(proj), assoc=assoc)
    assert "Relações" in txt, "o índice de texto não traz a seção Relações"
    assert "services/emissao.py" in txt, "a relação spec↔código não aparece no índice de texto"


def test_render_texto_lista_as_dimensoes(mn, proj):
    txt = mn.render_texto(mn.construir_arvore(proj))
    for marca in ("Arquitetura", "APIs", "Memórias", "Conexões"):
        assert marca in txt, f"o índice de texto não lista a dimensão {marca}"


def test_gerar_cria_md_e_html(mn, proj, tmp_path):
    out = tmp_path / "_out"
    md, html = mn.gerar(proj_dir=proj, out_dir=out)
    assert Path(md).exists() and Path(md).suffix == ".md"
    assert Path(html).exists() and Path(html).suffix == ".html"
