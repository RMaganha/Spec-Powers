"""Comportamento de `templates/mapa_neural.py` (F2 — o mapa mental do projeto).

O gerador monta o **mapa mental do projeto atual**: uma árvore com o projeto no centro e
4 dimensões (arquitetura interna · APIs & integrações · memórias & conhecimento · conexões
entre projetos), cada uma preenchida por um extrator que lê o repo. Produz duas saídas do
mesmo modelo: (a) `mapa-neural.md` (índice em texto que o assistente consulta) e (b)
`mapa-neural.html` (mapa radial full-screen, expansível/arrastável, self-contained).

Camadas (2026-11-18, `docs/decisoes.md`): os extratores leem o projeto por um objeto de disco; aqui ele é um
dicionário {caminho: texto} (`Disco`), com a varredura, o glob, a data e o `git check-ignore` em memória. O disco
de verdade (mtime, `git check-ignore` num repositório com `git init --template=`, a gravação do `gerar`) fica num
teste só, numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "templates" / "mapa_neural.py"
RAIZ = REPO.parent / "projeto-que-nao-existe-mapa"          # absoluto, nunca criado
DATA = "2026-11-18"


@pytest.fixture(scope="module")
def mn():
    spec = importlib.util.spec_from_file_location("mss_mapa_neural", TEMPLATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Disco:
    """O projeto em memória: {caminho relativo: texto}; caminho terminado em `/` é pasta vazia. Os métodos do
    `DiscoReal`: a varredura respeita a poda de quem chama (como o `os.walk`), o glob entende `*` e `**/`, toda
    folha tem a data `DATA`, e `ignorados` são as pastas que o git do projeto ignora."""

    def __init__(self, arquivos, ignorados=(), raiz=RAIZ):
        self.raiz, self.ignorados = raiz, set(ignorados)
        self.arquivos = {raiz / rel: texto for rel, texto in arquivos.items() if not rel.endswith("/")}
        self.pastas = {raiz} | {raiz / rel.rstrip("/") for rel in arquivos if rel.endswith("/")}
        for p in list(self.arquivos) + list(self.pastas):
            self.pastas.update(a for a in p.parents if a == raiz or raiz in a.parents)

    def existe(self, p):
        return self.eh_arquivo(p) or self.eh_pasta(p)

    def eh_arquivo(self, p):
        return Path(p) in self.arquivos

    def eh_pasta(self, p):
        return Path(p) in self.pastas

    def ler(self, p, estrito=False):
        try:
            return self.arquivos[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None

    def data(self, p):
        return DATA if self.eh_arquivo(p) else ""

    def listar(self, d):
        d = Path(d)
        if not self.eh_pasta(d):
            raise NotADirectoryError(str(d))
        return sorted({p for p in list(self.arquivos) + list(self.pastas) if p.parent == d and p != d})

    def percorrer(self, d):
        d = Path(d)
        if not self.eh_pasta(d):
            return
        filhos = self.listar(d)
        dirs = [f.name for f in filhos if self.eh_pasta(f)]
        yield d, dirs, [f.name for f in filhos if self.eh_arquivo(f)]
        for nome in dirs:                                  # depois da poda de quem chamou
            yield from self.percorrer(d / nome)

    def glob(self, base, padrao):
        rx = re.compile("^" + re.escape(padrao).replace(r"\*\*/", "(?:.*/)?").replace(r"\*", "[^/]*") + "$")
        base = Path(base)
        return [p for p in self.arquivos if base in p.parents and rx.match(p.relative_to(base).as_posix())]

    def git_ignorados(self, proj, nomes):
        return {n for n in nomes if n in self.ignorados}


PROJ = {   # um projeto no padrão do kit, com as 4 dimensões representadas
    "docs/superpowers/MAPA.md": (
        "# Mapa de contexto — meu-proj\n\n## Onde estamos\nx\n\n## Próximo passo\ny\n\n"
        "## Conexões\n- → IA Jeday Cosseguro: manda o PDF (banco TKGS_CORP)\n"
        "- ← n8n: expõe a fila (GET /api/queue_processar)\n- nenhuma\n"),
    "docs/superpowers/specs/2026-01-01-emissao-design.md": (
        "# emissão cosseguro — design\n\n"
        "Primeira linha de corpo (vira o lead/resumo).\n"
        "Segunda linha com MARCADOR_SO_NO_CORPO que não é lead.\n\n"
        "## Arquivos tocados\n"
        "- `services/emissao.py` (regra)\n"
        "- `services/nao_existe.py` (arquivo inexistente — não pode virar aresta)\n"),
    "docs/decisoes.md": "# Decisões\n- 2026 — banco = canal\n",
    "main.py": '"""Ponto de entrada da API do meu-proj."""\nprint("ok")\n',
    "routers/processar.py": ("import pyodbc\nfrom fastapi import APIRouter\nrouter = APIRouter()\n"
                             "@router.get('/api/queue_processar')\ndef q(): ...\n"
                             "@router.post('/api/processar')\ndef p(): ...\n"),
    "services/emissao.py": "# regra de emissão\n",
    "memory/MEMORY.md": (
        "- [Motor Gemini migrado](m1.md) — migrou o motor\n- [Banco como canal](m2.md) — decisão\n"
        # gancho REAL que cita um caminho com `<proj>` — não é placeholder de molde
        "- [Memória no repo](m3.md) — nunca em ~/.claude/projects/<proj>/memory/\n"),
    # memórias reais com [[links]] cruzados (camada associativa): slug com hífen no link vs. arquivo com
    # underscore + prefixo (normalização), e um link órfão que não resolve.
    "memory/feedback_rel_a.md": "# Rel A\nCorpo. Relacionado a [[rel-b]] e a [[nao-existe-xyz]].\n",
    "memory/rel_b.md": "# Rel B\nCorpo sem links de volta.\n",
    "memory/DIARIO.md": (
        "# Diário de sessão — meu-proj\n\n## 2026-01-02\n"
        "- [emissao-retry] discutimos o retry no envio → backoff exponencial → sessions/2026-01-02-emissao-retry.md\n"),
}


@pytest.fixture(scope="module")
def proj():
    return Disco(PROJ)


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


def _arvore(mn, d, **kw):
    return mn.construir_arvore(d.raiz, disco=d, **kw)


# ---- extratores ----------------------------------------------------------

def test_extrair_conexoes(mn, proj):
    no = mn.extrair_conexoes(RAIZ, proj)
    assert no["dim"] == "conn"
    ids = _ids(no)
    assert "IA Jeday Cosseguro" in ids, "não trouxe o projeto vizinho declarado (nome completo)"
    assert "n8n" in ids
    assert not any("nenhuma" in i.lower() for i in ids), "não pode incluir a linha 'nenhuma'"


def test_conexoes_movidas_pro_conexoes_md_seguem_no_mapa_neural(mn):
    """Com o detalhe em CONEXOES.md e só os nomes no MAPA, o mapa neural não pode perder as conexões."""
    d = Disco({
        "docs/superpowers/MAPA.md": (
            "# Mapa\n\n## Onde estamos\nx\n\n## Conexões\n\n"
            "- Detalhe em [CONEXOES.md](CONEXOES.md) (contratos, tokens, topologia). Conexões: CRM MSIG · n8n.\n"),
        "docs/superpowers/CONEXOES.md": (
            "# Conexões — o detalhe de cada integração\n\n<!-- movido em 2026-09-23 -->\n\n"
            "- → CRM MSIG: parcelas e boleto (`www4.msig.com.br`)\n"
            "- ← n8n: recebe o anexo (`POST /whatsapp/anexo`)\n")})
    ids = _ids(mn.extrair_conexoes(RAIZ, d))
    assert "CRM MSIG" in ids and "n8n" in ids, f"conexões do CONEXOES.md sumiram do mapa neural: {ids}"


def test_conexao_no_mapa_e_no_conexoes_md_aparece_uma_vez(mn):
    d = Disco({"docs/superpowers/MAPA.md": "# Mapa\n\n## Conexões\n- → CRM MSIG: parcelas (`x`)\n",
               "docs/superpowers/CONEXOES.md": "# Conexões\n\n- → CRM MSIG: parcelas (`x`)\n"})
    assert [f["id"] for f in mn.extrair_conexoes(RAIZ, d)["filhos"]].count("CRM MSIG") == 1


def test_extrair_arquitetura(mn, proj):
    no = mn.extrair_arquitetura(RAIZ, disco=proj)
    assert no["dim"] == "arq"
    ids = " | ".join(_ids(no))
    assert "main.py" in ids and "routers" in ids and "services" in ids


def test_arquitetura_traz_resumo_da_peca(mn, proj):
    """O índice deve trazer o resumo de 1 linha por peça (docstring) — pra servir de consulta
    e o assistente não reabrir a fonte a cada pergunta."""
    assert "Ponto de entrada da API" in mn.render_texto(_arvore(mn, proj)), \
        "o resumo (docstring) da peça não aparece no índice"


def test_extrair_apis_endpoints_e_integracoes(mn, proj):
    no = mn.extrair_apis(RAIZ, disco=proj)
    assert no["dim"] == "api"
    ids = " | ".join(_ids(no))
    assert "GET /api/queue_processar" in ids, "não extraiu o endpoint GET"
    assert "POST /api/processar" in ids, "não extraiu o endpoint POST"
    assert "SQL" in ids or "banco" in ids.lower(), "não detectou a integração de banco (pyodbc)"


def test_extrair_memorias(mn, proj):
    no = mn.extrair_memorias(RAIZ, disco=proj)
    assert no["dim"] == "mem"
    ids = " | ".join(_ids(no))
    assert "emissão cosseguro" in ids, "não trouxe a spec"
    assert "Gemini" in ids, "não trouxe a memória do índice"


def test_extrair_diario(mn, proj):
    """A dimensão de memórias traz também o diário de sessão (memory/DIARIO.md → memory/sessions/)."""
    assert "emissao-retry" in " | ".join(_ids(mn.extrair_memorias(RAIZ, disco=proj))), \
        "o mapa mental não trouxe a entrada do diário (memory/DIARIO.md)"


# ---- F2.2: datas nas folhas -----------------------------------------------

def test_folha_com_arquivo_ganha_data(mn, proj):
    """CA15 — nó-folha ancorado num arquivo tem `data`; agrupador/raiz/endpoint (sem arquivo) não tem.
    (O mtime de verdade, em `YYYY-MM-DD`, é provado no teste de disco.)"""
    arv = _arvore(mn, proj)
    assert _acha(arv, "main.py").get("data") == DATA, "a folha main.py não ganhou a data"
    assert "data" not in arv, "a raiz não pode ter data"
    assert "data" not in _acha(arv, "Arquitetura interna"), "a dimensão (agrupador) não pode ter data"
    ep = _acha(arv, "GET /api/queue_processar")
    assert ep is not None and "data" not in ep, "endpoint não é arquivo — não pode ter data"
    assert "data" not in _acha(arv, "Motor Gemini migrado"), "memória apontando pra arquivo ausente não tem data"


# ---- F2.2: camada associativa ---------------------------------------------

def _pares(assoc):
    """Conjunto de pares não-ordenados {frozenset({a,b})} das arestas."""
    return {frozenset((e["a"], e["b"])) for e in assoc}


def test_associacoes_memoria_memoria_por_links(mn, proj):
    """CA17 — [[link]] que resolve a um arquivo real vira aresta (com normalização de slug);
    link órfão (não resolve) é descartado — nunca inventa nó/aresta."""
    assoc = mn.extrair_associacoes(RAIZ, proj)
    assert frozenset(("memory/feedback_rel_a.md", "memory/rel_b.md")) in _pares(assoc), \
        "não ligou feedback_rel_a ↔ rel_b (normalização do slug [[rel-b]] falhou)"
    assert not any("nao-existe" in x or "nao_existe" in x for e in assoc for x in (e["a"], e["b"])), \
        "link órfão [[nao-existe-xyz]] não pode virar aresta"


def test_associacoes_spec_codigo_por_arquivos_tocados(mn, proj):
    """CA18 — caminho citado em `## Arquivos tocados` que existe vira aresta spec↔código;
    caminho inexistente é descartado."""
    assoc = mn.extrair_associacoes(RAIZ, proj)
    assert frozenset(("docs/superpowers/specs/2026-01-01-emissao-design.md", "services/emissao.py")) in _pares(assoc), \
        "não ligou a spec ao services/emissao.py citado em Arquivos tocados"
    assert not any("nao_existe" in x for e in assoc for x in (e["a"], e["b"])), \
        "caminho inexistente (services/nao_existe.py) não pode virar aresta"


def test_construir_arvore_projeto_no_centro_com_4_dimensoes(mn, proj):
    arv = _arvore(mn, proj)
    assert arv["dim"] == "projeto" and arv["id"] == "meu-proj"
    assert {f["dim"] for f in arv["filhos"]} == {"arq", "api", "mem", "conn"}, \
        "a raiz deve ter exatamente as 4 dimensões"


# ---- render --------------------------------------------------------------

def test_render_html_full_screen_e_self_contained(mn, proj):
    html = mn.render_html(_arvore(mn, proj))
    low = html.lower()
    assert "<script src=" not in low, "HTML referencia script externo (não é self-contained)"
    assert "100vw" in low or "100vh" in low, "o SVG/página não ocupa a tela toda (full-screen)"
    assert "var tree" in low or "const tree" in low, "a árvore não foi embutida como dado no HTML"
    assert "meu-proj" in html, "o nome do projeto não aparece no HTML"
    assert "IA Jeday Cosseguro" in html, "uma conexão real não aparece no HTML"
    assert "vis.Network" in html and "vis.DataSet" in html, "não usa a lib vis-network (grafo com física/zoom/pan)"
    assert "vis-network" in html, "a lib vis-network não está embutida inline (self-contained)"
    assert 'id="pop"' in html, "sem o pop-up de detalhes"
    assert "routers/processar.py" in html, "o local (caminho) da peça não foi embutido pro pop-up"


def test_coletar_docs_embute_conteudo_dos_md(mn, proj):
    """Coleta o conteúdo dos .md referenciados por algum nó (via `local`), pra embutir no HTML.
    Chave = caminho relativo; valor = conteúdo do arquivo (inclui o corpo, não só o título)."""
    docs = mn.coletar_docs(RAIZ, _arvore(mn, proj), proj)
    chave_spec = next((k for k in docs if k.endswith("2026-01-01-emissao-design.md")), None)
    assert chave_spec is not None, "não coletou o .md da spec referenciada por um nó"
    assert "MARCADOR_SO_NO_CORPO" in docs[chave_spec], "coletou só o título, não o conteúdo do arquivo"
    assert not any(k.endswith("m1.md") for k in docs), "não deve coletar caminho de .md inexistente"


def test_render_html_clique_abre_md_em_nova_aba(mn, proj):
    """CA14 — o HTML embute o conteúdo dos .md (__DOCS__) e traz o handler que abre
    nova aba (window.open) + o renderizador markdown vanilla inline."""
    arv = _arvore(mn, proj)
    html = mn.render_html(arv, docs=mn.coletar_docs(RAIZ, arv, proj))
    assert "MARCADOR_SO_NO_CORPO" in html, "o conteúdo do .md não foi embutido inline no HTML"
    assert "window.open" in html, "não há handler que abre o .md em nova aba"
    assert "mdToHtml" in html, "não há o renderizador markdown vanilla inline"
    assert "<script src=" not in html.lower(), "deixou de ser self-contained"


def test_render_html_popup_mostra_data(mn, proj):
    """CA16 — o pop-up injeta a data (n.data) quando presente."""
    assert "n.data" in mn.render_html(_arvore(mn, proj)), "o HTML não injeta a data (n.data) no pop-up"


def test_render_html_embute_associacoes_e_destaque(mn, proj):
    """CA19 — HTML embute as associações (__ASSOC__ → dado) + hook que acende as arestas
    ao focar um nó; segue self-contained/full-screen."""
    html = mn.render_html(_arvore(mn, proj), assoc=mn.extrair_associacoes(RAIZ, proj))
    assert "__ASSOC__" not in html, "o placeholder __ASSOC__ não foi substituído"
    assert "var ASSOC" in html or "const ASSOC" in html, "as associações não foram embutidas como dado"
    assert "acenderAssoc" in html, "não há o hook que acende as arestas associativas no hover"
    assert "services/emissao.py" in html, "a associação spec↔código não chegou ao HTML"
    assert "<script src=" not in html.lower(), "deixou de ser self-contained"


def test_render_html_layout_tidy_tree_horizontal(mn, proj):
    """F2.3 — layout horizontal tidy-tree (conexões curvas cubicBezier + balões arredondados),
    no lugar do radial antigo."""
    html = mn.render_html(_arvore(mn, proj))
    assert "cubicBezier" in html, "as conexões não são curvas horizontais (cubicBezier)"
    assert "boxH" in html, "não há o layout tidy-tree com faixa proporcional à altura do balão"
    assert "borderRadius:14" in html, "os balões não têm o arredondamento moderno"
    assert "dragNodes:true" in html, "os nós deveriam ser arrastáveis (mover uma caixa)"
    assert "doubleClick" in html, "abrir o .md deveria ser por duplo clique"


def test_html_js_tem_sintaxe_valida(mn, proj):
    """Guarda anti-tela-branca: o JS inline do HTML precisa PARSEAR. Substrings verdes não pegam
    erro de sintaxe (parse-time), e foi assim que um `})` a mais deixou o mapa branco. O node compila
    o JS lido da entrada padrão, sem rodar e sem arquivo (pula se node não estiver no PATH)."""
    if not shutil.which("node"):
        pytest.skip("node não disponível — guarda de sintaxe pulada")
    html = mn.render_html(_arvore(mn, proj), assoc=mn.extrair_associacoes(RAIZ, proj))
    js = re.findall(r"<script>(.*?)</script>", html, re.S)[-1]  # o bloco principal (o 1º é a lib vis-network)
    compila = ("let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',d=>s+=d)"
               ".on('end',()=>{new (require('vm').Script)(s)})")
    r = subprocess.run(["node", "-e", compila], input=js, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, "JS inline do HTML tem erro de sintaxe:\n" + r.stderr


def test_render_texto_tem_secao_relacoes(mn, proj):
    """CA19 (texto) — o índice .md ganha a seção Relações (associativa)."""
    txt = mn.render_texto(_arvore(mn, proj), assoc=mn.extrair_associacoes(RAIZ, proj))
    assert "Relações" in txt, "o índice de texto não traz a seção Relações"
    assert "services/emissao.py" in txt, "a relação spec↔código não aparece no índice de texto"


def test_render_texto_lista_as_dimensoes(mn, proj):
    txt = mn.render_texto(_arvore(mn, proj))
    for marca in ("Arquitetura", "APIs", "Memórias", "Conexões"):
        assert marca in txt, f"o índice de texto não lista a dimensão {marca}"


# ---- F2.4: o mapa é DESCRITIVO (retrata o projeto, não o molde) -------------
# Os 4 achados vieram de rodar o gerador num projeto real de outro time (Flask, pastas com nome
# próprio, worktree de projeto vizinho dentro de .claude/): o mapa saiu com 18 rotas de OUTRO
# projeto, 0 das 17 reais, as camadas principais invisíveis e placeholders do molde como se
# fossem decisões. Este projeto reproduz aquele.

ALT = {
    "docs/superpowers/MAPA.md": "# Mapa de contexto — proj-flask\n\n## Conexões\n- nenhuma\n",
    # entrypoints da raiz — dois, e nenhum se chama main.py (renomear está fora de escopo lá)
    "app_web.py": ('"""Entrypoint web (Flask)."""\nfrom flask import Flask\napp = Flask(__name__)\n'
                   '@app.route("/chat", methods=["POST"])\ndef chat(): ...\n'
                   '@app.route("/health")\ndef health(): ...\n'),
    "worker.py": '"""Entrypoint do worker de fila."""\n',
    # camadas com nome PRÓPRIO do projeto (decisão registrada lá) — não estão na lista do molde
    "apis/openapi.py": ('"""Contrato OpenAPI do projeto."""\n'
                        '@bp.route("/api/v1/itens", methods=["GET", "PUT"])\ndef itens(): ...\n'),
    "persistencia/repo_itens.py": '"""Acesso a dados dos itens."""\nimport psycopg2\n',
    # camadas do molde SEM .py — não podem sumir com a detecção nova
    "sql/01_schema.sql": "-- ddl\n",
    "templates/index.html": "<html></html>\n",
    # pastas de ferramenta — nunca são camada do projeto
    ".venv/mod.py": "x = 1\n",
    "node_modules/mod.py": "x = 1\n",
    # worktree de PROJETO VIZINHO dentro de .claude/ — a origem das rotas fantasma
    ".claude/worktrees/vizinho/routers/fantasma.py": "@router.get('/api/fantasma')\ndef f(): ...\n",
    # decisões e diário recém-copiados do molde: só placeholder, nenhum fato do projeto
    "docs/decisoes.md": ("<!-- MODELO — copie para docs/decisoes.md. Formato:\n"
                         "       - <data> — decidimos <X> em vez de <Y> — porque <Z>. -->\n\n"
                         "# Decisões — proj-flask\n\n_(ainda sem decisões registradas)_\n"),
    "memory/DIARIO.md": ("# Diário de sessão\n\n## <data>\n"
                         "- [<assunto>] <gist de 1 linha — o pivô da sessão> → sessions/<data>-<assunto>.md\n"),
    "memory/MEMORY.md": ("<!-- MODELO de índice de memória.\n"
                         "     - Só ponteiros de 1 linha, NUNCA o conteúdo da memória em si.\n"
                         "     - Organize por tópico, não por data. -->\n\n# Memória do projeto — índice\n"),
}


@pytest.fixture(scope="module")
def proj_alt():
    """Projeto que NÃO segue o molde: Flask, camadas batizadas pelo time (`apis/`, `persistencia/`), dois
    entrypoints na raiz (nenhum é `main.py`), um worktree de projeto vizinho em `.claude/` e os arquivos de
    memória recém-copiados do molde (só placeholder)."""
    return Disco(ALT)


def test_ignora_worktree_de_projeto_vizinho(mn, proj_alt):
    """CA1 — `.claude/` (onde vivem os worktrees) é território de OUTRO projeto: nada de lá pode
    entrar no mapa deste. Sem isso, a varredura desce em `.claude/worktrees/` e o mapa afirma rotas
    que não existem aqui — a mesma fronteira 'um projeto por janela', na leitura automática."""
    txt = mn.render_texto(_arvore(mn, proj_alt))
    assert "/api/fantasma" not in txt, "trouxe rota de um projeto vizinho (worktree em .claude/)"
    assert ".claude" not in txt, "citou caminho dentro de .claude/ (projeto alheio)"


def test_extrai_rota_flask(mn, proj_alt):
    """CA2 — em Flask o método vai como argumento (`methods=[...]`), não no nome do decorator;
    sem `methods=`, o default do framework é GET."""
    ids = " | ".join(_ids(mn.extrair_apis(RAIZ, disco=proj_alt)))
    assert "POST /chat" in ids, "não extraiu a rota Flask com methods=['POST']"
    assert "GET /health" in ids, "rota Flask sem methods= deveria virar GET (default do framework)"
    assert "GET /api/v1/itens" in ids and "PUT /api/v1/itens" in ids, \
        "não expandiu os múltiplos métodos de uma mesma rota Flask"


def test_arquitetura_detecta_camadas_com_nome_proprio(mn, proj_alt):
    """CA3 — `_CAMADAS` é ORDEM PREFERENCIAL, não filtro: pasta com `.py` entra mesmo com nome
    fora do molde, e TODO `.py` da raiz é entrypoint (não só `main.py`). O mapa é descritivo —
    quem prescreve nome de pasta é o `ESTRUTURA.md`."""
    ids = _ids(mn.extrair_arquitetura(RAIZ, disco=proj_alt))
    assert "apis/" in ids and "persistencia/" in ids, "camada com nome próprio do projeto ficou invisível"
    assert "app_web.py" in ids and "worker.py" in ids, "entrypoints da raiz sumiram (a lista só esperava main.py)"
    assert "openapi.py" in ids and "repo_itens.py" in ids, "não desceu nos arquivos da camada nova"


def test_arquitetura_mantem_pasta_do_molde_sem_py(mn, proj_alt):
    """CA3b — sem regressão: pasta da lista preferencial que não tem `.py` (`sql/`, `templates/`)
    continua no mapa."""
    ids = _ids(mn.extrair_arquitetura(RAIZ, disco=proj_alt))
    assert "sql/" in ids and "templates/" in ids


def test_arquitetura_ignora_pastas_de_ferramenta(mn, proj_alt):
    """CA3c — `.venv`, `node_modules` e `.claude` nunca são camada do projeto."""
    ids = " | ".join(_ids(mn.extrair_arquitetura(RAIZ, disco=proj_alt)))
    for lixo in (".venv", "node_modules", ".claude"):
        assert lixo not in ids, "%s não pode virar camada" % lixo


def test_arquitetura_ordem_preferencial_primeiro(mn, proj_alt):
    """CA3d — a lista do molde vira ORDEM: entrypoints, depois as camadas conhecidas na ordem
    canônica, depois as demais em ordem alfabética."""
    filhos = [f["id"] for f in mn.extrair_arquitetura(RAIZ, disco=proj_alt)["filhos"]]
    assert filhos.index("app_web.py") < filhos.index("templates/"), "entrypoint vem primeiro"
    assert filhos.index("templates/") < filhos.index("sql/"), "ordem canônica do molde"
    assert filhos.index("sql/") < filhos.index("apis/"), "camada conhecida antes da detectada"
    assert filhos.index("apis/") < filhos.index("persistencia/"), "detectadas em ordem alfabética"


def test_placeholder_do_molde_nao_vira_fato(mn, proj_alt):
    """CA4 — arquivo recém-copiado do molde só tem placeholder; nem o texto dentro de comentário
    HTML nem a linha `- [<assunto>] <gist>` podem virar decisão/entrada de diário/memória.
    Mapa que inventa fato é pior que mapa vazio."""
    ids = _ids(mn.extrair_memorias(RAIZ, disco=proj_alt))
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
    junto = " | ".join(_ids(mn.extrair_memorias(RAIZ, disco=proj)))
    assert "banco = canal" in junto, "a decisão real sumiu junto com o filtro de placeholder"
    assert "Gemini" in junto, "a memória real sumiu junto com o filtro de placeholder"
    assert "Memória no repo" in junto, "memória real com `<proj>` no gancho foi tratada como molde"


# ---- F2.5: nada de corte silencioso · se está no repo, está no mapa ---------
# Segunda rodada do mesmo projeto real: o índice mostrava 25 de 36 memórias **sem avisar**
# (as 4 gravadas naquele dia ficaram fora), e a dimensão de arquitetura só enxergava o 1º nível
# de pastas com `.py` — `web/` (só .html), `prompts/` (só .md) e `n8n/` (só .json) invisíveis,
# e subpasta com código idem.

PASTAS = {   # pastas de todo tipo: código aninhado, só de UI, só de prompt, só de fluxo, vazia e de backup
    "docs/superpowers/MAPA.md": "# Mapa de contexto — proj-pastas\n",
    "docs/nota.md": "# doc solto\n",
    "memory/MEMORY.md": "# índice\n",
    "apis/openapi.py": '"""Contrato OpenAPI."""\n',
    "apis/v1/rotas.py": '"""Rotas da v1."""\n',
    "apis/v1/esquemas/item.py": '"""Esquema do item."""\n',
    "web/chat_v2.html": "<html></html>\n",
    "prompts/system_prompt.md": "# prompt do agente\n",
    "n8n/fluxo_cotacao.json": "{}\n",
    "backup/velho.py": "x = 1\n",
    "vazia/": "",
}


def _pastas():
    return Disco(PASTAS)


def _filhos(no, id_):
    """Ids dos filhos diretos do nó com o id dado."""
    return [f["id"] for f in (_acha(no, id_) or {}).get("filhos", [])]


def _camadas(mn, d, **kw):
    return [f["id"] for f in mn.extrair_arquitetura(RAIZ, disco=d, **kw)["filhos"]]


def test_camada_entra_por_conteudo_nao_por_extensao(mn):
    """CA29 — se está no repo, está no mapa: pasta é camada por **ter conteúdo**, não por ter
    `.py`. `web/` (só HTML), `prompts/` (só Markdown) e `n8n/` (só JSON de fluxo) são peças do
    projeto. `docs/` e `memory/` ficam fora porque já têm ramo próprio; pasta vazia não é camada."""
    ids = _camadas(mn, _pastas())
    for camada in ("web/", "prompts/", "n8n/", "apis/"):
        assert camada in ids, "%s deveria ser camada (tem conteúdo)" % camada
    assert "docs/" not in ids and "memory/" not in ids, "dimensão própria não se repete na arquitetura"
    assert "vazia/" not in ids, "pasta sem conteúdo não é camada"


def test_camada_desce_nas_subpastas(mn):
    """CA30 — código dentro de subpasta é código do projeto: a árvore desce (`apis/v1/esquemas/`),
    cada nível com os seus arquivos."""
    arv = mn.extrair_arquitetura(RAIZ, disco=_pastas())
    assert "v1/" in _filhos(arv, "apis/"), "não desceu na subpasta com código"
    assert "rotas.py" in _filhos(arv, "v1/"), "a subpasta não trouxe os arquivos dela"
    assert "esquemas/" in _filhos(arv, "v1/"), "não desceu no 2º nível"
    assert "item.py" in _filhos(arv, "esquemas/")


def test_arquivo_morto_e_certificado_ficam_fora(mn):
    """CA32 — `backup/` e `certs/` saem por default: arquivo morto **não é o sistema** e material
    de certificado é insumo de build. O caso concreto: `backup/v1/chat.html` aparecia como **par**
    de `web/chat_v2.html` — duas UIs de aparência equivalente no mapa, sendo que só uma existe
    (e "reviver a UI v1" está declarado fora de escopo lá). Ambiguidade dessas já custou caro."""
    d = Disco({**PASTAS, "certs/corp-ca.pem": "-----BEGIN-----\n", "backup/v1/chat.html": "<html>v1</html>\n"})
    ids = " | ".join(_ids(mn.extrair_arquitetura(RAIZ, disco=d)))
    assert "backup/" not in ids and "chat.html" not in ids, "arquivo morto não é camada"
    assert "certs/" not in ids, "material de certificado não é camada"
    assert "web/" in ids, "a UI viva continua no mapa"


def test_n8n_continua_sendo_camada(mn):
    """CA32 (limite da exceção) — a exclusão é só de arquivo morto/insumo. `n8n/` guarda os
    **fluxos de trabalho do projeto** (decisão do owner: "n8n com certeza") e continua camada,
    mesmo sem `.py`."""
    arv = mn.extrair_arquitetura(RAIZ, disco=_pastas())
    assert "n8n/" in [f["id"] for f in arv["filhos"]]
    assert "fluxo_cotacao.json" in _filhos(arv, "n8n/")


def test_camada_ignorada_por_parametro(mn):
    """CA31 (parte 2) — `--ignorar` tira uma pasta versionada que o **projeto** sabe não ser
    runtime (nome próprio, ex.: `_investigacao/`): é por aqui que a leitura de prosa feita pelo
    assistente chega ao gerador, sem o gerador adivinhar nada."""
    d = Disco({**PASTAS, "_investigacao/teste.py": "x = 1\n"})
    assert "_investigacao/" in _camadas(mn, d), "sem declarar nada, pasta versionada aparece"
    assert "_investigacao/" not in _camadas(mn, d, ignorar=["_investigacao"])


def test_camada_que_o_git_ignora_fica_fora_da_arquitetura(mn):
    """CA31 — o que o próprio projeto manda o git ignorar não é o projeto: fica fora do mapa,
    sem o gerador precisar adivinhar intenção em prosa. (O `git check-ignore` de verdade é provado
    em `test_camada_no_gitignore_fica_fora`, no disco.)"""
    ids = _camadas(mn, Disco({**PASTAS, "relatorios/saida.html": "<html></html>\n"}, ignorados={"relatorios"}))
    assert "relatorios/" not in ids, "pasta no .gitignore não pode entrar no mapa"
    assert "apis/" in ids, "as demais camadas continuam"


def test_rota_de_pasta_ignorada_nao_conta(mn):
    """CA31 (coerência) — pasta fora do mapa também não pode gerar endpoint: cópia velha não é a
    API do projeto. Vale tanto pelo `--ignorar` quanto pelo default (`backup/`)."""
    d = Disco({**PASTAS, "sobras/rotas_velhas.py": '@app.route("/rota-morta")\ndef v(): ...\n',
               "backup/rotas_arquivadas.py": '@app.route("/rota-arquivada")\ndef a(): ...\n'})
    ids = " | ".join(_ids(mn.extrair_apis(RAIZ, ignorar=["sobras"], disco=d)))
    assert "/rota-morta" not in ids, "pasta em --ignorar não pode expor endpoint"
    assert "/rota-arquivada" not in ids, "pasta de arquivo morto não pode expor endpoint"


def test_resumo_de_modulo_com_docstring_longa(mn):
    """Regressão pega no dogfood: o resumo saía da 1ª linha da docstring **entre** as aspas de
    abertura e fecho — módulo de docstring longa (o próprio `mapa_neural.py`) ficava sem resumo
    no índice, calado. Agora basta a abertura."""
    d = Disco({"servico.py": '"""Faz a coisa importante do módulo.\n\n' + ("prosa longa. " * 400) + '\n"""\nx = 1\n'})
    assert mn._resumo(RAIZ / "servico.py", d).startswith("Faz a coisa importante")


def _indice_de(n):
    return Disco({"memory/MEMORY.md": "".join("- [Memória %02d](m%02d.md) — gancho %02d\n" % (i, i, i)
                                               for i in range(n))})


def test_limite_corta_com_marcador(mn):
    """CA27 — corte **sempre** deixa rastro `… (+N)`. Um `[:25]` mudo faz o índice afirmar um
    todo que não é o todo: foi assim que 11 memórias (entre elas as do dia) sumiram sem aviso."""
    filhos = _filhos(mn.extrair_memorias(RAIZ, limite=25, disco=_indice_de(30)), "memórias")
    assert len(filhos) == 26, "deveria haver 25 itens + 1 marcador"
    assert filhos[-1] == "… (+5)", "cortou sem deixar rastro do que ficou de fora"


def test_limite_padrao_nao_corta_projeto_real(mn):
    """CA28 — com o limite padrão, um índice de 36 memórias (o caso real) aparece inteiro."""
    filhos = _filhos(mn.extrair_memorias(RAIZ, disco=_indice_de(36)), "memórias")
    assert len(filhos) == 36, "o limite padrão não pode esconder memória de um projeto real"
    assert not any(f.startswith("…") for f in filhos)


def test_decorator_citado_em_comentario_nao_e_rota(mn):
    """CA2c — rota só conta quando o decorator está no início da linha: `@app.route(...)` citado
    dentro de comentário/docstring é documentação, não API (o próprio gerador cita um)."""
    d = Disco({"doc_mod.py": ('"""Exemplo na docstring: @app.route("/na-docstring")."""\n'
                              '# comentário citando @app.get("/no-comentario")\n'
                              '@app.route("/de-verdade")\ndef v(): ...\n')})
    ids = " | ".join(_ids(mn.extrair_apis(RAIZ, disco=d)))
    assert "GET /de-verdade" in ids
    assert "na-docstring" not in ids and "no-comentario" not in ids


# ---- o disco de verdade e o processo (pasta montada uma vez) ------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("mapa_neural") / "meu-proj"
    for rel, texto in {**PROJ, "relatorios/saida.html": "<html></html>\n", ".gitignore": "relatorios/\n"}.items():
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_text(texto, encoding="utf-8")
    if shutil.which("git"):
        subprocess.run(["git", "init", "-q", "--template="], cwd=raiz, capture_output=True)
    return raiz


def test_camada_no_gitignore_fica_fora(mn, pasta):
    """O disco de verdade: o `git check-ignore` real (F-005: bytes + `-z`, senão o Windows manda `\\r` e o filtro
    vira pó em silêncio), o mtime das folhas, a varredura e a gravação do `gerar`."""
    if not shutil.which("git"):
        pytest.skip("git não disponível")
    arv = mn.construir_arvore(pasta)
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", _acha(arv, "main.py").get("data", "")), \
        "a folha main.py não ganhou a data (mtime YYYY-MM-DD)"
    assert _acha(arv, "GET /api/queue_processar") is not None and _acha(arv, "routers/") is not None
    camadas = [f["id"] for f in _acha(arv, "Arquitetura interna")["filhos"]]
    assert "relatorios/" not in camadas, "pasta no .gitignore não pode entrar no mapa"
    assert "services/" in camadas
    assert frozenset(("memory/feedback_rel_a.md", "memory/rel_b.md")) in _pares(mn.extrair_associacoes(pasta))
    assert "MARCADOR_SO_NO_CORPO" in "".join(mn.coletar_docs(pasta, arv).values())
    md, html = mn.gerar(proj_dir=pasta, out_dir=pasta / "_out")
    assert Path(md).suffix == ".md" and "Arquitetura" in Path(md).read_text(encoding="utf-8")
    assert Path(html).suffix == ".html" and "meu-proj" in Path(html).read_text(encoding="utf-8")


def test_processo_gera_o_mapa(pasta):
    r = subprocess.run([sys.executable, str(TEMPLATE), "--proj", str(pasta), "--out", str(pasta / "_out_cli")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    assert "mapa mental gerado" in r.stdout
    assert (pasta / "_out_cli" / "mapa-neural.md").is_file() and (pasta / "_out_cli" / "mapa-neural.html").is_file()
