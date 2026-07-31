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
        "- [Motor Gemini migrado](m1.md) — migrou o motor\n- [Banco como canal](m2.md) — decisão\n"
        # gancho REAL que cita um caminho com `<proj>` — não é placeholder de molde
        "- [Memória no repo](m3.md) — nunca em ~/.claude/projects/<proj>/memory/\n",
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


def test_render_html_layout_tidy_tree_horizontal(mn, proj):
    """F2.3 — layout horizontal tidy-tree (conexões curvas cubicBezier + balões arredondados),
    no lugar do radial antigo."""
    html = mn.render_html(mn.construir_arvore(proj))
    assert "cubicBezier" in html, "as conexões não são curvas horizontais (cubicBezier)"
    assert "boxH" in html, "não há o layout tidy-tree com faixa proporcional à altura do balão"
    assert "borderRadius:14" in html, "os balões não têm o arredondamento moderno"
    assert "dragNodes:true" in html, "os nós deveriam ser arrastáveis (mover uma caixa)"
    assert "doubleClick" in html, "abrir o .md deveria ser por duplo clique"


def test_html_js_tem_sintaxe_valida(mn, proj, tmp_path):
    """Guarda anti-tela-branca: o JS inline do HTML precisa PARSEAR. Substrings verdes não pegam
    erro de sintaxe (parse-time), e foi assim que um `})` a mais deixou o mapa branco. Valida com
    `node --check` (pula se node não estiver no PATH)."""
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node não disponível — guarda de sintaxe pulada")
    html = mn.render_html(mn.construir_arvore(proj), assoc=mn.extrair_associacoes(proj))
    m = re.findall(r"<script>(.*?)</script>", html, re.S)
    js = m[-1]  # o bloco principal (o 1º é a lib vis-network embutida)
    stub = "var vis={Network:function(){},DataSet:function(){}},document={getElementById:function(){}},window={};\n"
    f = tmp_path / "inline.js"
    f.write_text(stub + js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, "JS inline do HTML tem erro de sintaxe:\n" + r.stderr


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


# ---- F2.4: o mapa é DESCRITIVO (retrata o projeto, não o molde) -------------
# Os 4 achados vieram de rodar o gerador num projeto real de outro time (Flask, pastas com nome
# próprio, worktree de projeto vizinho dentro de .claude/): o mapa saiu com 18 rotas de OUTRO
# projeto, 0 das 17 reais, as camadas principais invisíveis e placeholders do molde como se
# fossem decisões. Este fixture reproduz aquele projeto.

@pytest.fixture()
def proj_alt(tmp_path):
    """Projeto que NÃO segue o molde: Flask, camadas batizadas pelo time (`apis/`,
    `persistencia/`), dois entrypoints na raiz (nenhum é `main.py`), um worktree de projeto
    vizinho em `.claude/` e os arquivos de memória recém-copiados do molde (só placeholder)."""
    p = tmp_path
    (p / "docs" / "superpowers").mkdir(parents=True)
    (p / "docs" / "superpowers" / "MAPA.md").write_text(
        "# Mapa de contexto — proj-flask\n\n## Conexões\n- nenhuma\n", encoding="utf-8")
    # entrypoints da raiz — dois, e nenhum se chama main.py (renomear está fora de escopo lá)
    (p / "app_web.py").write_text(
        '"""Entrypoint web (Flask)."""\n'
        'from flask import Flask\napp = Flask(__name__)\n'
        '@app.route("/chat", methods=["POST"])\ndef chat(): ...\n'
        '@app.route("/health")\ndef health(): ...\n', encoding="utf-8")
    (p / "worker.py").write_text('"""Entrypoint do worker de fila."""\n', encoding="utf-8")
    # camadas com nome PRÓPRIO do projeto (decisão registrada lá) — não estão na lista do molde
    (p / "apis").mkdir()
    (p / "apis" / "openapi.py").write_text(
        '"""Contrato OpenAPI do projeto."""\n'
        '@bp.route("/api/v1/itens", methods=["GET", "PUT"])\ndef itens(): ...\n', encoding="utf-8")
    (p / "persistencia").mkdir()
    (p / "persistencia" / "repo_itens.py").write_text(
        '"""Acesso a dados dos itens."""\nimport psycopg2\n', encoding="utf-8")
    # camadas do molde SEM .py — não podem sumir com a detecção nova
    (p / "sql").mkdir()
    (p / "sql" / "01_schema.sql").write_text("-- ddl\n", encoding="utf-8")
    (p / "templates").mkdir()
    (p / "templates" / "index.html").write_text("<html></html>\n", encoding="utf-8")
    # pastas de ferramenta — nunca são camada do projeto
    for lixo in (".venv", "node_modules"):
        (p / lixo).mkdir()
        (p / lixo / "mod.py").write_text("x = 1\n", encoding="utf-8")
    # worktree de PROJETO VIZINHO dentro de .claude/ — a origem das rotas fantasma
    viz = p / ".claude" / "worktrees" / "vizinho" / "routers"
    viz.mkdir(parents=True)
    (viz / "fantasma.py").write_text(
        "@router.get('/api/fantasma')\ndef f(): ...\n", encoding="utf-8")
    # decisões e diário recém-copiados do molde: só placeholder, nenhum fato do projeto
    (p / "docs" / "decisoes.md").write_text(
        "<!-- MODELO — copie para docs/decisoes.md. Formato:\n"
        "       - <data> — decidimos <X> em vez de <Y> — porque <Z>. -->\n\n"
        "# Decisões — proj-flask\n\n_(ainda sem decisões registradas)_\n", encoding="utf-8")
    (p / "memory").mkdir()
    (p / "memory" / "DIARIO.md").write_text(
        "# Diário de sessão\n\n## <data>\n"
        "- [<assunto>] <gist de 1 linha — o pivô da sessão> → sessions/<data>-<assunto>.md\n",
        encoding="utf-8")
    (p / "memory" / "MEMORY.md").write_text(
        "<!-- MODELO de índice de memória.\n"
        "     - Só ponteiros de 1 linha, NUNCA o conteúdo da memória em si.\n"
        "     - Organize por tópico, não por data. -->\n\n# Memória do projeto — índice\n",
        encoding="utf-8")
    return p


def test_ignora_worktree_de_projeto_vizinho(mn, proj_alt):
    """CA1 — `.claude/` (onde vivem os worktrees) é território de OUTRO projeto: nada de lá pode
    entrar no mapa deste. Sem isso, o `rglob` desce em `.claude/worktrees/` e o mapa afirma rotas
    que não existem aqui — a mesma fronteira 'um projeto por janela', na leitura automática."""
    txt = mn.render_texto(mn.construir_arvore(proj_alt))
    assert "/api/fantasma" not in txt, "trouxe rota de um projeto vizinho (worktree em .claude/)"
    assert ".claude" not in txt, "citou caminho dentro de .claude/ (projeto alheio)"


def test_extrai_rota_flask(mn, proj_alt):
    """CA2 — em Flask o método vai como argumento (`methods=[...]`), não no nome do decorator;
    sem `methods=`, o default do framework é GET."""
    ids = " | ".join(_ids(mn.extrair_apis(proj_alt)))
    assert "POST /chat" in ids, "não extraiu a rota Flask com methods=['POST']"
    assert "GET /health" in ids, "rota Flask sem methods= deveria virar GET (default do framework)"
    assert "GET /api/v1/itens" in ids and "PUT /api/v1/itens" in ids, \
        "não expandiu os múltiplos métodos de uma mesma rota Flask"


def test_arquitetura_detecta_camadas_com_nome_proprio(mn, proj_alt):
    """CA3 — `_CAMADAS` é ORDEM PREFERENCIAL, não filtro: pasta com `.py` entra mesmo com nome
    fora do molde, e TODO `.py` da raiz é entrypoint (não só `main.py`). O mapa é descritivo —
    quem prescreve nome de pasta é o `ESTRUTURA.md`."""
    ids = _ids(mn.extrair_arquitetura(proj_alt))
    assert "apis/" in ids and "persistencia/" in ids, \
        "camada com nome próprio do projeto ficou invisível (mapa prescritivo)"
    assert "app_web.py" in ids and "worker.py" in ids, \
        "entrypoints da raiz sumiram (a lista só esperava main.py)"
    assert "openapi.py" in ids and "repo_itens.py" in ids, "não desceu nos arquivos da camada nova"


def test_arquitetura_mantem_pasta_do_molde_sem_py(mn, proj_alt):
    """CA3b — sem regressão: pasta da lista preferencial que não tem `.py` (`sql/`, `templates/`)
    continua no mapa."""
    ids = _ids(mn.extrair_arquitetura(proj_alt))
    assert "sql/" in ids and "templates/" in ids


def test_arquitetura_ignora_pastas_de_ferramenta(mn, proj_alt):
    """CA3c — `.venv`, `node_modules` e `.claude` nunca são camada do projeto."""
    ids = " | ".join(_ids(mn.extrair_arquitetura(proj_alt)))
    for lixo in (".venv", "node_modules", ".claude"):
        assert lixo not in ids, "%s não pode virar camada" % lixo


def test_arquitetura_ordem_preferencial_primeiro(mn, proj_alt):
    """CA3d — a lista do molde vira ORDEM: entrypoints, depois as camadas conhecidas na ordem
    canônica, depois as demais em ordem alfabética."""
    filhos = [f["id"] for f in mn.extrair_arquitetura(proj_alt)["filhos"]]
    assert filhos.index("app_web.py") < filhos.index("templates/"), "entrypoint vem primeiro"
    assert filhos.index("templates/") < filhos.index("sql/"), "ordem canônica do molde"
    assert filhos.index("sql/") < filhos.index("apis/"), "camada conhecida antes da detectada"
    assert filhos.index("apis/") < filhos.index("persistencia/"), "detectadas em ordem alfabética"


def test_placeholder_do_molde_nao_vira_fato(mn, proj_alt):
    """CA4 — arquivo recém-copiado do molde só tem placeholder; nem o texto dentro de comentário
    HTML nem a linha `- [<assunto>] <gist>` podem virar decisão/entrada de diário/memória.
    Mapa que inventa fato é pior que mapa vazio."""
    ids = _ids(mn.extrair_memorias(proj_alt))
    junto = " | ".join(ids)
    assert not any(i.startswith("decisões") for i in ids), "placeholder do molde virou decisão"
    assert not any(i.startswith("diário") for i in ids), "placeholder do molde virou entrada de diário"
    assert not any(i.startswith("memórias") for i in ids), "comentário-guia do molde virou memória"
    assert "decidimos" not in junto and "<assunto>" not in junto and "ponteiros" not in junto


def test_decisao_e_memoria_reais_continuam_aparecendo(mn, proj):
    """CA4b — sem regressão: no projeto com conteúdo de verdade, decisão e memória seguem no mapa —
    **inclusive** a memória cujo texto real cita `<algo>` (o primeiro filtro, aplicado à linha
    inteira, engoliu a memória que fala de `~/.claude/projects/<proj>/memory/` — pego rodando o
    gerador no próprio kit). Por isso o filtro só vale pra campo curto/estruturado."""
    no = mn.extrair_memorias(proj)
    junto = " | ".join(_ids(no))
    assert "banco = canal" in junto, "a decisão real sumiu junto com o filtro de placeholder"
    assert "Gemini" in junto, "a memória real sumiu junto com o filtro de placeholder"
    assert "Memória no repo" in junto, "memória real com `<proj>` no gancho foi tratada como molde"


# ---- F2.5: nada de corte silencioso · se está no repo, está no mapa ---------
# Segunda rodada do mesmo projeto real: o índice mostrava 25 de 36 memórias **sem avisar**
# (as 4 gravadas naquele dia ficaram fora), e a dimensão de arquitetura só enxergava o 1º nível
# de pastas com `.py` — `web/` (só .html), `prompts/` (só .md) e `n8n/` (só .json) invisíveis,
# e subpasta com código idem.

@pytest.fixture()
def proj_pastas(tmp_path):
    """Projeto com pastas de todo tipo: código aninhado, pasta só de UI, só de prompt, só de
    fluxo, uma vazia e uma de backup."""
    p = tmp_path
    (p / "docs" / "superpowers").mkdir(parents=True)
    (p / "docs" / "superpowers" / "MAPA.md").write_text(
        "# Mapa de contexto — proj-pastas\n", encoding="utf-8")
    (p / "docs" / "nota.md").write_text("# doc solto\n", encoding="utf-8")
    (p / "memory").mkdir()
    (p / "memory" / "MEMORY.md").write_text("# índice\n", encoding="utf-8")
    (p / "apis").mkdir()
    (p / "apis" / "openapi.py").write_text('"""Contrato OpenAPI."""\n', encoding="utf-8")
    (p / "apis" / "v1").mkdir()
    (p / "apis" / "v1" / "rotas.py").write_text('"""Rotas da v1."""\n', encoding="utf-8")
    (p / "apis" / "v1" / "esquemas").mkdir()
    (p / "apis" / "v1" / "esquemas" / "item.py").write_text('"""Esquema do item."""\n', encoding="utf-8")
    (p / "web").mkdir()
    (p / "web" / "chat_v2.html").write_text("<html></html>\n", encoding="utf-8")
    (p / "prompts").mkdir()
    (p / "prompts" / "system_prompt.md").write_text("# prompt do agente\n", encoding="utf-8")
    (p / "n8n").mkdir()
    (p / "n8n" / "fluxo_cotacao.json").write_text("{}\n", encoding="utf-8")
    (p / "backup").mkdir()
    (p / "backup" / "velho.py").write_text("x = 1\n", encoding="utf-8")
    (p / "vazia").mkdir()
    return p


def _filhos(no, id_):
    """Ids dos filhos diretos do nó com o id dado."""
    alvo = _acha(no, id_)
    return [f["id"] for f in (alvo or {}).get("filhos", [])]


def test_camada_entra_por_conteudo_nao_por_extensao(mn, proj_pastas):
    """CA29 — se está no repo, está no mapa: pasta é camada por **ter conteúdo**, não por ter
    `.py`. `web/` (só HTML), `prompts/` (só Markdown) e `n8n/` (só JSON de fluxo) são peças do
    projeto. `docs/` e `memory/` ficam fora porque já têm ramo próprio; pasta vazia não é camada."""
    ids = [f["id"] for f in mn.extrair_arquitetura(proj_pastas)["filhos"]]
    for camada in ("web/", "prompts/", "n8n/", "apis/"):
        assert camada in ids, "%s deveria ser camada (tem conteúdo)" % camada
    assert "docs/" not in ids and "memory/" not in ids, "dimensão própria não se repete na arquitetura"
    assert "vazia/" not in ids, "pasta sem conteúdo não é camada"


def test_camada_desce_nas_subpastas(mn, proj_pastas):
    """CA30 — código dentro de subpasta é código do projeto: a árvore desce (`apis/v1/esquemas/`),
    cada nível com os seus arquivos."""
    arv = mn.extrair_arquitetura(proj_pastas)
    assert "v1/" in _filhos(arv, "apis/"), "não desceu na subpasta com código"
    assert "rotas.py" in _filhos(arv, "v1/"), "a subpasta não trouxe os arquivos dela"
    assert "esquemas/" in _filhos(arv, "v1/"), "não desceu no 2º nível"
    assert "item.py" in _filhos(arv, "esquemas/")


def test_camada_ignorada_por_parametro(mn, proj_pastas):
    """CA31 (parte 2) — `--ignorar` tira uma pasta versionada que só faz ruído."""
    com = [f["id"] for f in mn.extrair_arquitetura(proj_pastas)["filhos"]]
    sem = [f["id"] for f in mn.extrair_arquitetura(proj_pastas, ignorar=["backup"])["filhos"]]
    assert "backup/" in com, "sem declarar nada, pasta versionada aparece (regra: está no repo, está no mapa)"
    assert "backup/" not in sem


def test_camada_no_gitignore_fica_fora(mn, proj_pastas):
    """CA31 — o que o próprio projeto manda o git ignorar não é o projeto: fica fora do mapa,
    sem o gerador precisar adivinhar intenção em prosa."""
    import shutil
    import subprocess
    if not shutil.which("git"):
        pytest.skip("git não disponível")
    (proj_pastas / ".gitignore").write_text("backup/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=proj_pastas, capture_output=True)
    ids = [f["id"] for f in mn.extrair_arquitetura(proj_pastas)["filhos"]]
    assert "backup/" not in ids, "pasta no .gitignore não pode entrar no mapa"
    assert "apis/" in ids, "as demais camadas continuam"


def test_rota_de_pasta_ignorada_nao_conta(mn, proj_pastas):
    """CA31 (coerência) — pasta fora do mapa também não pode gerar endpoint: cópia velha em
    `backup/` não é a API do projeto."""
    (proj_pastas / "backup" / "rotas_velhas.py").write_text(
        '@app.route("/rota-morta")\ndef v(): ...\n', encoding="utf-8")
    ids = " | ".join(_ids(mn.extrair_apis(proj_pastas, ignorar=["backup"])))
    assert "/rota-morta" not in ids


def test_resumo_de_modulo_com_docstring_longa(mn, tmp_path):
    """Regressão pega no dogfood: o resumo saía da 1ª linha da docstring **entre** as aspas de
    abertura e fecho — módulo de docstring longa (o próprio `mapa_neural.py`) ficava sem resumo
    no índice, calado. Agora basta a abertura."""
    (tmp_path / "servico.py").write_text(
        '"""Faz a coisa importante do módulo.\n\n' + ("prosa longa. " * 400) + '\n"""\nx = 1\n',
        encoding="utf-8")
    assert mn._resumo(tmp_path / "servico.py").startswith("Faz a coisa importante")


def test_limite_corta_com_marcador(mn, tmp_path):
    """CA27 — corte **sempre** deixa rastro `… (+N)`. Um `[:25]` mudo faz o índice afirmar um
    todo que não é o todo: foi assim que 11 memórias (entre elas as do dia) sumiram sem aviso."""
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "MEMORY.md").write_text(
        "".join("- [Memória %02d](m%02d.md) — gancho %02d\n" % (i, i, i) for i in range(30)),
        encoding="utf-8")
    no = mn.extrair_memorias(tmp_path, limite=25)
    filhos = _filhos(no, "memórias")
    assert len(filhos) == 26, "deveria haver 25 itens + 1 marcador"
    assert filhos[-1] == "… (+5)", "cortou sem deixar rastro do que ficou de fora"


def test_limite_padrao_nao_corta_projeto_real(mn, tmp_path):
    """CA28 — com o limite padrão, um índice de 36 memórias (o caso real) aparece inteiro."""
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "MEMORY.md").write_text(
        "".join("- [Memória %02d](m%02d.md) — gancho %02d\n" % (i, i, i) for i in range(36)),
        encoding="utf-8")
    filhos = _filhos(mn.extrair_memorias(tmp_path), "memórias")
    assert len(filhos) == 36, "o limite padrão não pode esconder memória de um projeto real"
    assert not any(f.startswith("…") for f in filhos)


def test_decorator_citado_em_comentario_nao_e_rota(mn, tmp_path):
    """CA2c — rota só conta quando o decorator está no início da linha: `@app.route(...)` citado
    dentro de comentário/docstring é documentação, não API (o próprio gerador cita um)."""
    (tmp_path / "doc_mod.py").write_text(
        '"""Exemplo na docstring: @app.route("/na-docstring")."""\n'
        '# comentário citando @app.get("/no-comentario")\n'
        '@app.route("/de-verdade")\ndef v(): ...\n', encoding="utf-8")
    ids = " | ".join(_ids(mn.extrair_apis(tmp_path)))
    assert "GET /de-verdade" in ids
    assert "na-docstring" not in ids and "no-comentario" not in ids
