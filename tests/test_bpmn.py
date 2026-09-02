"""Comportamento do gerador do desenho BPMN (templates/bpmn.py).

O gerador lê o código Python do projeto por `ast` e monta UM processo por porta de entrada
(rota Flask/FastAPI, ou `main()`/`if __name__` da raiz quando o projeto não expõe rota). Regra
dura: nada de caixa que não está no código — o que não é derivável fica declarado como não
derivável, e arquivo que não parseia vai pra "não lido" (falha ABERTA), nunca derruba a geração.
"""
import importlib.util
import re
import shutil
import subprocess

import pytest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _mod():
    spec = importlib.util.spec_from_file_location("bpmn", REPO / "templates" / "bpmn.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def bpmn():
    return _mod()


# ------------------------------------------------------------------------------------- fixtures

COTACAO = '''
from flask import Flask, request
from servicos.regras import aprovar_cotacao, recusar
from persistencia.db import gravar_protocolo

app = Flask(__name__)


@app.route("/cotacao", methods=["POST"])
def criar_cotacao():
    """Recebe a cotacao do corretor e decide a alcada."""
    dados = request.get_json()
    if not dados:
        raise ValueError("payload vazio")
    if dados["valor"] > 100000:
        parecer = aprovar_cotacao(dados)
        gravar_protocolo(parecer)
        return {"status": "aprovada"}
    else:
        recusar(dados)
        return {"status": "recusada"}


@app.get("/saude")
def saude():
    return {"ok": True}
'''

REGRAS = '''
import requests
from persistencia.db import gravar_protocolo


def aprovar_cotacao(dados):
    """Aprova a cotacao consultando o motor de risco."""
    try:
        risco = requests.post("https://motor.risco/api", json=dados)
    except TimeoutError:
        raise RuntimeError("motor fora")
    if risco.json()["score"] > 700:
        gravar_protocolo(dados)
        return "aprovado"
    return "pendente"


def recusar(dados):
    return "recusado"
'''

DB = '''
import pyodbc


def gravar_protocolo(parecer):
    """Grava o protocolo no SQL Server."""
    conn = pyodbc.connect("dsn")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO protocolo (parecer) VALUES (?)", parecer)
    return cursor.rowcount
'''

CARGA = '''
import asyncio


def _extrair(origem):
    """Extrai as linhas da origem."""
    return [origem]


def _transformar(linhas):
    """Normaliza as linhas."""
    return linhas


async def paralelo(a, b):
    await asyncio.gather(_extrair(a), _transformar(b))


def main():
    """Roda a carga diaria."""
    linhas = _extrair("origem")
    dados = _transformar(linhas)
    return dados


if __name__ == "__main__":
    main()
'''


@pytest.fixture(scope="module")
def proj_web(tmp_path_factory):
    """Projeto com rota Flask: guarda, gateway, subprocesso, banco, HTTP, try/except."""
    p = tmp_path_factory.mktemp("proj_web")
    for pasta in ("apis", "servicos", "persistencia", "tests"):
        (p / pasta).mkdir()
    (p / "apis" / "cotacao.py").write_text(COTACAO, encoding="utf-8")
    (p / "servicos" / "regras.py").write_text(REGRAS, encoding="utf-8")
    (p / "persistencia" / "db.py").write_text(DB, encoding="utf-8")
    (p / "quebrado.py").write_text("def x(:\n    pass\n", encoding="utf-8")
    (p / "tests" / "test_nada.py").write_text("def test_ignorado():\n    assert True\n",
                                              encoding="utf-8")
    return p


@pytest.fixture(scope="module")
def proj_script(tmp_path_factory):
    """Projeto SEM rota: as portas de entrada sao o main()/if __name__ da raiz."""
    p = tmp_path_factory.mktemp("proj_script")
    (p / "carga.py").write_text(CARGA, encoding="utf-8")
    return p


@pytest.fixture(scope="module")
def modelo_web(bpmn, proj_web):
    return bpmn.extrair(proj_web)


@pytest.fixture(scope="module")
def modelo_script(bpmn, proj_script):
    return bpmn.extrair(proj_script)


def _proc(modelo, nome):
    achados = [p for p in modelo["processos"] if p["nome"] == nome]
    assert achados, f"processo {nome!r} não saiu; saíram: {[p['nome'] for p in modelo['processos']]}"
    return achados[0]


def _achatar(nos):
    """Todos os nós, descendo em ramos e filhos de subprocesso."""
    for n in nos:
        yield n
        for r in n.get("ramos") or []:
            yield from _achatar(r["nos"])
        yield from _achatar(n.get("filhos") or [])


# ------------------------------------------------------------------- AC1/AC2 — portas de entrada

def test_rota_vira_processo_com_inicio_e_fim(modelo_web):
    """AC1 — DADO rota @app.route("/cotacao", methods=["POST"]) ENTÃO processo 'POST /cotacao'
    com evento de início e ao menos um evento de fim."""
    p = _proc(modelo_web, "POST /cotacao")
    assert p["nos"][0]["tipo"] == "inicio", p["nos"][0]
    tipos = {n["tipo"] for n in _achatar(p["nos"])}
    assert tipos & {"fim", "fim_erro"}, f"nenhum evento de fim em {tipos}"
    assert _proc(modelo_web, "GET /saude")  # decorator sem methods= é GET


def test_sem_rota_usa_main_da_raiz(modelo_script):
    """AC2 — DADO projeto sem rota alguma ENTÃO a porta de entrada é o main()/if __name__."""
    nomes = [p["nome"] for p in modelo_script["processos"]]
    assert any("main" in n for n in nomes), nomes


def test_tests_nao_entra(modelo_web):
    """tests/ não é processo do sistema — mesma fronteira do mapa_neural."""
    for p in modelo_web["processos"]:
        assert not p["arquivo"].startswith("tests"), p["arquivo"]


# ---------------------------------------------------------------------- AC3 — gateway e guarda

def test_if_com_desfechos_diferentes_vira_gateway(modelo_web):
    """AC3a — if/else com desfechos diferentes → gateway exclusivo, um ramo rotulado por saída."""
    p = _proc(modelo_web, "POST /cotacao")
    gws = [n for n in _achatar(p["nos"]) if n["tipo"] == "gateway"]
    assert gws, "nenhum gateway exclusivo no processo"
    valor = [g for g in gws if "valor" in g["rotulo"]]
    assert valor, [g["rotulo"] for g in gws]
    assert len(valor[0]["ramos"]) == 2, valor[0]["ramos"]
    assert any("100000" in r["rotulo"] for r in valor[0]["ramos"]), valor[0]["ramos"]


def test_guarda_vira_gateway_com_fim_de_erro(modelo_web):
    """AC3b — DADO guarda `if not dados: raise` ENTÃO gateway + evento de fim de ERRO (a guarda
    nunca desaparece do desenho)."""
    p = _proc(modelo_web, "POST /cotacao")
    erros = [n for n in _achatar(p["nos"]) if n["tipo"] == "fim_erro"]
    assert erros, "a guarda sumiu: nenhum fim de erro"
    assert any("ValueError" in n["rotulo"] for n in erros), [n["rotulo"] for n in erros]


# --------------------------------------------------------------- AC4 — tarefa, raia, subprocesso

def test_chamada_do_projeto_vira_tarefa_na_raia_do_modulo(modelo_web):
    """AC4a — chamada a função definida no projeto → tarefa, com a raia do módulo/pasta dela."""
    p = _proc(modelo_web, "POST /cotacao")
    tarefas = [n for n in _achatar(p["nos"]) if n["tipo"] in ("tarefa", "subprocesso")]
    raias = {n["raia"] for n in tarefas}
    assert "servicos" in raias and "persistencia" in raias, raias
    assert not any("get_json" in n["rotulo"] for n in tarefas), \
        "chamada a lib de fora virou tarefa: " + str([n["rotulo"] for n in tarefas])


def test_funcao_com_decisao_vira_subprocesso_expandido(modelo_web):
    """AC4b — a função chamada que por dentro tem decisão/chamadas sai como SUBPROCESSO,
    expandido; a que só retorna sai como tarefa simples."""
    p = _proc(modelo_web, "POST /cotacao")
    nos = list(_achatar(p["nos"]))
    subs = [n for n in nos if n["tipo"] == "subprocesso"]
    assert subs, "nenhum subprocesso"
    aprovar = [n for n in subs if n["fn"] == "aprovar_cotacao"]
    assert aprovar, [(n["fn"], n["rotulo"]) for n in subs]
    assert aprovar[0]["filhos"], "aprovar_cotacao não expandiu"
    # sem docstring o rótulo é o nome da função — e a função que só retorna é tarefa, não subprocesso
    recusar = [n for n in nos if n["fn"] == "recusar"]
    assert recusar and recusar[0]["tipo"] == "tarefa", recusar
    assert recusar[0]["rotulo"] == "recusar", recusar[0]["rotulo"]


def test_profundidade_limita_a_expansao(bpmn, proj_web):
    """profundidade=1 não desce no subprocesso (poda antes de fidelidade)."""
    m = bpmn.extrair(proj_web, profundidade=1)
    p = _proc(m, "POST /cotacao")
    assert not any(n.get("filhos") for n in _achatar(p["nos"])), "expandiu além da profundidade"


# ------------------------------------------------------------- AC5 — dados, mensagem, borda, AC6

def test_banco_vira_armazenamento_de_dados(modelo_web):
    """AC5a — cursor.execute/pyodbc → armazenamento de dados anexado à tarefa."""
    p = _proc(modelo_web, "POST /cotacao")
    com_dados = [n for n in _achatar(p["nos"]) if n.get("dados")]
    assert com_dados, "nenhum armazenamento de dados detectado"
    assert any("INSERT" in d or "protocolo" in d for n in com_dados for d in n["dados"]), \
        [n["dados"] for n in com_dados]


def test_http_vira_fluxo_de_mensagem_para_piscina_externa(modelo_web):
    """AC5b — requests/httpx → fluxo de mensagem pra piscina externa nomeada."""
    p = _proc(modelo_web, "POST /cotacao")
    com_msg = [n for n in _achatar(p["nos"]) if n.get("mensagens")]
    assert com_msg, "nenhum fluxo de mensagem detectado"
    assert any("motor.risco" in m for n in com_msg for m in n["mensagens"]), \
        [n["mensagens"] for n in com_msg]
    assert p["piscinas"], "piscina externa não declarada no processo"


def test_try_except_vira_evento_de_borda(modelo_web):
    """AC5c — try/except em volta da tarefa → evento de borda nela."""
    p = _proc(modelo_web, "POST /cotacao")
    com_borda = [n for n in _achatar(p["nos"]) if n.get("borda")]
    assert com_borda, "nenhum evento de borda"
    assert any("TimeoutError" in n["borda"] for n in com_borda), [n["borda"] for n in com_borda]


def test_rotulo_e_anotacao_vem_do_docstring(modelo_web):
    """AC6 — rótulo = 1ª linha do docstring (senão o nome da função); docstring vira anotação."""
    p = _proc(modelo_web, "POST /cotacao")
    assert "alcada" in (p["nos"][0]["anotacao"] or ""), p["nos"][0]
    rotulos = [n["rotulo"] for n in _achatar(p["nos"])]
    assert any("Grava o protocolo" in r for r in rotulos), rotulos
    assert "recusar" in rotulos, rotulos  # sem docstring → nome da função


def test_gateway_paralelo(bpmn, proj_script):
    """Elemento 7 — asyncio.gather vira gateway PARALELO (não exclusivo)."""
    m = bpmn.extrair(proj_script, entradas_extra=["paralelo"])
    todos = [n for p in m["processos"] for n in _achatar(p["nos"])]
    assert any(n["tipo"] == "gateway_paralelo" for n in todos), [n["tipo"] for n in todos]


def test_reuso_vira_chamada_de_atividade(modelo_web):
    """Elemento 20 — o que é chamado por 2+ fluxos é marcado como reuso."""
    reusados = [n["rotulo"] for p in modelo_web["processos"]
                for n in _achatar(p["nos"]) if n.get("reuso")]
    assert any("protocolo" in r for r in reusados), reusados


# ----------------------------------------------------------------------------- AC8 — falha aberta

def test_arquivo_que_nao_parseia_vai_para_nao_lido(modelo_web):
    """AC8 — .py com erro de sintaxe não derruba a geração: entra em 'não lido', declarado."""
    nao = " ".join(x["arquivo"] for x in modelo_web["nao_lidos"])
    assert "quebrado.py" in nao, modelo_web["nao_lidos"]
    assert modelo_web["processos"], "o arquivo quebrado derrubou a extração"


# ------------------------------------------------------- T2 — saída de TEXTO (o assistente lê esta)

@pytest.fixture(scope="module")
def texto_web(bpmn, modelo_web):
    return bpmn.render_texto(modelo_web)


def test_texto_tem_processo_com_passos_ordenados_e_tipo_do_elemento(texto_web):
    """AC9 (documentação) — o .md descreve cada processo em passos ordenados, com o tipo de
    elemento BPMN, a raia e os desfechos. É a camada que o assistente consulta."""
    assert "POST /cotacao" in texto_web
    for termo in ("início", "gateway exclusivo", "subprocesso", "tarefa", "fim de erro"):
        assert termo in texto_web, f"o texto não nomeia o elemento {termo!r}"
    assert "servicos" in texto_web and "persistencia" in texto_web, "raias ausentes"
    assert "motor.risco" in texto_web, "piscina externa ausente"
    assert "TimeoutError" in texto_web, "evento de borda ausente"


def test_texto_declara_nao_lido_e_nao_derivavel(texto_web):
    """AC8 — 'não lido' declarado; e o que a leitura estática não deriva fica escrito, em vez
    de sumir em silêncio (o desenho não pode parecer completo quando não é)."""
    assert "quebrado.py" in texto_web
    assert "gateway inclusivo" in texto_web, "elemento não-derivável não declarado"


def test_texto_registra_o_corte(bpmn, proj_web):
    """AC7 — DADO teto menor que o processo ENTÃO o corte deixa rastro '… (+N)' (F-009)."""
    m = bpmn.extrair(proj_web, limite=3)
    t = bpmn.render_texto(m)
    assert "… (+" in t, "corte silencioso: nenhum rastro no texto"


# ----------------------------------------------------------- T3 — o DESENHO (o humano olha este)

@pytest.fixture(scope="module")
def html_web(bpmn, modelo_web):
    return bpmn.render_html(modelo_web, gerado_em="2026-09-02")


def test_html_self_contained(html_web):
    """AC9 — zero CDN (proxy MSIG derruba recurso externo): CSS e JS inline, nada de fora."""
    assert "<script src=" not in html_web, "script externo — tem que ser self-contained"
    assert "<link " not in html_web, "stylesheet/font externo — tem que ser self-contained"
    assert "http://" not in html_web.replace("http://www.w3.org", ""), "recurso externo por http"
    assert "<style>" in html_web and "<script>" in html_web
    assert "<svg" in html_web, "sem SVG não há desenho"


def test_html_tem_um_desenho_por_processo_com_seletor(html_web, modelo_web):
    """AC9 — um painel por processo + seletor (o projeto tem N portas de entrada, não uma)."""
    for p in modelo_web["processos"]:
        assert p["nome"] in html_web, f"processo {p['nome']} não está no HTML"
    assert html_web.count('class="processo"') == len(modelo_web["processos"])
    assert 'data-alvo=' in html_web, "sem seletor de processo"


def test_html_desenha_os_elementos_bpmn(html_web):
    """AC1/AC3/AC4/AC5 — os elementos do desenho estão no SVG com a classe do seu tipo, e as
    raias e a piscina externa aparecem rotuladas."""
    for classe in ("e-inicio", "e-fim_erro", "e-tarefa", "e-subprocesso", "e-gateway"):
        assert classe in html_web, f"elemento {classe} não foi desenhado"
    assert "raia" in html_web and "servicos" in html_web, "raias não rotuladas"
    assert "motor.risco" in html_web, "piscina externa não desenhada"
    assert "e-dados" in html_web, "armazenamento de dados não desenhado"
    assert "e-borda" in html_web, "evento de borda não desenhado"
    assert 'class="msg"' in html_web, "fluxo de mensagem não DESENHADO (a substring 'msg' casava com o CSS)"


def test_html_tem_legenda_e_declara_o_nao_derivavel(html_web):
    """O desenho carrega a legenda dos elementos (o modelo que o owner mandou) e declara o que
    a leitura estática não deriva — desenho que parece completo sem ser é pior que buraco visível."""
    assert "Legenda" in html_web
    assert "gateway inclusivo" in html_web, "não-derivável não declarado no desenho"
    assert "pro humano" in html_web, "o HTML não declara que o visual é pro humano"


def test_html_registra_corte(bpmn, proj_web):
    """AC7 — corte com rastro também no desenho."""
    h = bpmn.render_html(bpmn.extrair(proj_web, limite=3))
    assert "… (+" in h, "corte silencioso no desenho"


def test_js_do_desenho_passa_no_node_check(html_web, tmp_path):
    """AC10 / F-007 — substring verde não pega erro de parse; `node --check` pega a tela branca.
    (pula se node não estiver no PATH)"""
    if not shutil.which("node"):
        pytest.skip("node não disponível — guarda de sintaxe pulada")
    scripts = re.findall(r"<script>(.*?)</script>", html_web, re.S)
    assert scripts, "o desenho tem JS inline (seletor + pan/zoom)"
    f = tmp_path / "bpmn.js"
    f.write_text("\n".join(scripts), encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, f"JS do desenho com erro de sintaxe:\n{r.stderr}"


def test_gerar_escreve_as_duas_saidas(bpmn, proj_web, tmp_path):
    """AC9 — `gerar()` escreve as DUAS saídas em docs/: o texto (assistente) e o desenho (humano)."""
    md, html = bpmn.gerar(proj_dir=proj_web, out_dir=tmp_path)
    assert md.name == "bpmn.md" and html.name == "bpmn.html", (md, html)
    assert md.exists() and html.exists()
    assert "POST /cotacao" in md.read_text(encoding="utf-8")
    assert "<svg" in html.read_text(encoding="utf-8")


def test_gerar_default_cai_em_docs(bpmn, proj_script):
    """A saída default vai pra docs/ (isolada da raiz, como mapa-neural e anatomia)."""
    md, html = bpmn.gerar(proj_dir=proj_script)
    assert md.parent.name == "docs" and html.parent.name == "docs", (md, html)


def test_main_fora_da_raiz_tambem_e_porta_de_entrada(bpmn, tmp_path):
    """Achado do dogfood no próprio kit: projeto sem rota cujos scripts NÃO ficam na raiz (aqui,
    em templates/) ficava com ZERO processo. A cascata é: rota → main() da raiz → main() em
    qualquer módulo. Fixture não vê isso; o projeto real vê (regra do dogfood com diff)."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "job.py").write_text(CARGA, encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    nomes = [p["nome"] for p in m["processos"]]
    assert any("main" in n for n in nomes), nomes
    assert any("scripts/job.py" in n for n in nomes), nomes


def test_nome_do_projeto_com_caminho_relativo(bpmn, proj_script, monkeypatch):
    """Achado do dogfood: `--proj .` (o jeito que o comando roda) saía com o título vazio, porque
    `Path('.').name` é string vazia. O nome sai do caminho resolvido."""
    monkeypatch.chdir(proj_script)
    m = bpmn.extrair(".")
    assert m["projeto"] == Path(proj_script).name, m["projeto"]


def test_layout_nao_sobrepoe_caixas(bpmn, modelo_web, modelo_script):
    """Guarda determinística do desenho (a regra do kit é validar tela por DADO, nunca dirigindo
    o browser): duas caixas na mesma (coluna, linha) sairiam empilhadas no SVG. Gateway aninhado
    podia reaproveitar a linha de um ramo irmão — a alocação de linha é global por processo."""
    for modelo in (modelo_web, modelo_script):
        for p in modelo["processos"]:
            caixas, _, _ = bpmn._posicionar(p["nos"])
            vistos = {}
            for c in caixas:
                chave = (c["col"], c["linha"])
                assert chave not in vistos, (
                    f"colisão em {chave} no processo {p['nome']}: "
                    f"{vistos.get(chave)} × {c['no']['rotulo']}")
                vistos[chave] = c["no"]["rotulo"]


def test_gateway_aninhado_nao_reusa_linha_de_ramo_irmao(bpmn, tmp_path):
    """O caso que a fixture web não tem: `if` dentro do ramo de outro `if`, os dois com desfecho.
    Sem alocação global de linha, o ramo interno cairia sobre o ramo externo."""
    (tmp_path / "app.py").write_text(
        "def _a(x):\n    return x\n\n\n"
        "def _b(x):\n    return x\n\n\n"
        "def main():\n"
        "    if x > 1:\n"
        "        if y > 2:\n"
        "            _a(1)\n"
        "            return 'ay'\n"
        "        else:\n"
        "            _b(2)\n"
        "            return 'by'\n"
        "    else:\n"
        "        _a(3)\n"
        "        return 'ax'\n", encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    caixas, _, _ = bpmn._posicionar(m["processos"][0]["nos"])
    chaves = [(c["col"], c["linha"]) for c in caixas]
    assert len(chaves) == len(set(chaves)), f"caixas empilhadas: {chaves}"


def test_chamada_resolve_no_modulo_do_chamador(bpmn, tmp_path):
    """Achado do dogfood: `templates/mapa_neural.py` e `templates/anatomia.py` têm cada um uma
    função `gerar`. A resolução por nome simples pegava a PRIMEIRA em ordem de arquivo, e o
    processo do mapa-neural saía desenhando as caixas internas do anatomia — desenho errado com
    cara de certo, que é pior que buraco. Ordem de resolução: mesmo arquivo → import declarado →
    qualquer arquivo (fallback heurístico)."""
    (tmp_path / "aaa.py").write_text(
        "def _passo_aaa():\n    return 1\n\n\n"
        "def gerar():\n    '''Gera o aaa.'''\n    _passo_aaa()\n    return 'aaa'\n", encoding="utf-8")
    (tmp_path / "zzz.py").write_text(
        "def _passo_zzz():\n    return 2\n\n\n"
        "def gerar():\n    '''Gera o zzz.'''\n    _passo_zzz()\n    return 'zzz'\n\n\n"
        "def main():\n    gerar()\n", encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    p = [x for x in m["processos"] if "zzz.py" in x["nome"]][0]
    ger = [n for n in bpmn.achatar(p["nos"]) if n["fn"] == "gerar"]
    assert ger, [n["fn"] for n in bpmn.achatar(p["nos"])]
    assert ger[0]["arquivo"] == "zzz.py", f"resolveu no módulo errado: {ger[0]['arquivo']}"
    filhos = [n["fn"] for n in bpmn.achatar(ger[0]["filhos"])]
    assert "_passo_zzz" in filhos and "_passo_aaa" not in filhos, filhos


def test_chamada_resolve_pelo_import_declarado(bpmn, tmp_path):
    """`from servicos.regras import aprovar` é o sinal honesto de qual módulo é o dono — vence o
    homônimo de outro arquivo."""
    (tmp_path / "aaa.py").write_text("def aprovar():\n    return 'errado'\n", encoding="utf-8")
    (tmp_path / "servicos").mkdir()
    (tmp_path / "servicos" / "regras.py").write_text(
        "def _checar():\n    return True\n\n\n"
        "def aprovar():\n    '''Aprova de verdade.'''\n    _checar()\n    return 'certo'\n",
        encoding="utf-8")
    (tmp_path / "web.py").write_text(
        "from servicos.regras import aprovar\n\n\n"
        "def main():\n    aprovar()\n    return 1\n", encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    p = [x for x in m["processos"] if "web.py" in x["nome"]][0]
    ap = [n for n in bpmn.achatar(p["nos"]) if n["fn"] == "aprovar"]
    assert ap and ap[0]["arquivo"] == "servicos/regras.py", ap and ap[0]["arquivo"]
    assert ap[0]["raia"] == "servicos", ap[0]["raia"]


def test_codigo_com_html_nao_quebra_o_desenho(bpmn, tmp_path):
    """Rótulo sai do código do projeto: docstring/condição com `<`, `>` ou `&` entraria cru no SVG
    e quebraria o desenho (tela em branco). Tudo que vem do código é escapado."""
    (tmp_path / "app.py").write_text(
        "def _x(a):\n    return a\n\n\n"
        "def main():\n"
        '    """Compara <script> & "aspas" no docstring."""\n'
        "    if a < 3 and b > 4:\n"
        "        _x(1)\n"
        "        return 'ok'\n", encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    h = bpmn.render_html(m)
    assert "<script>Compara" not in h and "<script> &" not in h, "código cru vazou pro HTML"
    assert "&lt;script&gt;" in h, "o docstring não foi escapado"
    assert h.count("<script>") == 1, "sobrou tag script além do JS do desenho"


# ----------------------------------- regressao: "abri o html e nao havia desenho nenhum" (owner)

def test_desenho_visivel_sem_js(html_web):
    """O owner abriu o HTML e viu só a legenda e os nomes das rotas. Causa: as seções nasciam
    `display:none` e só o JS inline revelava uma — script que não roda (viewer que sandboxa, CSP,
    erro em runtime) apagava o desenho inteiro. O precedente que funciona (`anatomia.html`) tem
    ZERO `display:none`. Agora esconder é **enriquecimento** do JS: sem JS, tudo aparece."""
    escondem = [l for l in html_web.split("\n") if "display:none" in l and ".processo" in l]
    assert escondem, "nenhuma regra esconde processo — o seletor com JS deixou de funcionar?"
    assert all("body.js" in l for l in escondem), (
        "esconde processo SEM depender de JS — o desenho desaparece inteiro se o script não roda: "
        + str(escondem))
    assert 'id="p0"' in html_web, "seção sem id — o índice não tem pra onde apontar sem JS"


def test_indice_navega_sem_js(html_web, modelo_web):
    """Sem JS o seletor de botões não faz nada; com âncora, ele pelo menos rola até o processo."""
    for i in range(len(modelo_web["processos"])):
        assert f'href="#p{i}"' in html_web, f"índice não aponta a âncora #p{i}"


def test_processos_do_mais_rico_pro_mais_pobre(bpmn, proj_web):
    """A página abria em `GET /` (2 nós: início + fim) porque a ordem era alfabética, enquanto
    `POST /endosso` (41 nós) ficava enterrado — parecia que a ferramenta não achou nada.
    Ordem passa a ser nº de nós desc, nome asc como desempate (determinística)."""
    m = bpmn.extrair(proj_web)
    tamanhos = [len(bpmn.achatar(p["nos"])) for p in m["processos"]]
    assert tamanhos == sorted(tamanhos, reverse=True), \
        f"processos fora de ordem (rico → pobre): {[(p['nome'], len(bpmn.achatar(p['nos']))) for p in m['processos']]}"
    assert m["processos"][0]["nome"] == "POST /cotacao", m["processos"][0]["nome"]


# --------------------------- gap achado rodando no MSS-SSC: cliente de LLM nao virava piscina

GEMINI_SVC = '''
class GeminiService:
    def __init__(self):
        import google.generativeai as genai  # import tardio: so quando for usar de fato
        genai.configure(api_key="x")
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def extrair_pdf(self, pdf):
        """Envia um PDF + prompt ao Gemini e devolve o JSON extraido."""
        resp = self.model.generate_content(["prompt", pdf])
        return resp.text
'''

OPENAI_SVC = '''
from openai import OpenAI


def resumir(texto):
    """Resume o texto com o modelo."""
    cliente = OpenAI()
    r = cliente.chat.completions.create(model="gpt", messages=[])
    return r.choices[0].message.content
'''

ROTA_LLM = '''
from fastapi import FastAPI
from services.gemini import GeminiService
from services.resumo import resumir

app = FastAPI()


@app.post("/extrair")
def extrair(pdf):
    """Extrai o consolidado da apolice."""
    dados = GeminiService().extrair_pdf(pdf)
    resumir(dados)
    return dados
'''


@pytest.fixture(scope="module")
def proj_llm(tmp_path_factory):
    p = tmp_path_factory.mktemp("proj_llm")
    (p / "routers").mkdir()
    (p / "services").mkdir()
    (p / "routers" / "api.py").write_text(ROTA_LLM, encoding="utf-8")
    (p / "services" / "gemini.py").write_text(GEMINI_SVC, encoding="utf-8")
    (p / "services" / "resumo.py").write_text(OPENAI_SVC, encoding="utf-8")
    return p


def test_cliente_de_llm_vira_piscina_externa(bpmn, proj_llm):
    """Rodando no MSS-SSC (24 rotas, 56 armazenamentos de dados) saíram ZERO fluxos de mensagem —
    num app cuja razão de existir é chamar o Gemini. Duas causas: `google.generativeai` fora da
    tabela de libs, e a chamada de verdade ser método de instância (`self.model.generate_content`),
    que nenhuma heurística de nome de import resolve. O sinal honesto é o **import do SDK** no
    arquivo (mesmo tardio, dentro do método): com ele, construtor de cliente e método de geração
    contam como fluxo de mensagem (11) pra piscina (13) nomeada pelo SDK."""
    m = bpmn.extrair(proj_llm)
    assert "Gemini" in m["piscinas"], m["piscinas"]
    assert "OpenAI" in m["piscinas"], m["piscinas"]
    p = m["processos"][0]
    msgs = {x for n in bpmn.achatar(p["nos"]) for x in n["mensagens"]}
    assert "Gemini" in msgs, f"o subprocesso do Gemini não carrega o fluxo de mensagem: {msgs}"
    assert "OpenAI" in msgs, msgs


def test_sem_import_de_sdk_nao_inventa_piscina(bpmn, tmp_path):
    """A contrapartida: sem import de SDK no arquivo, um método chamado `generate_content` ou uma
    função `create` NÃO viram piscina — o gerador não inventa integração."""
    (tmp_path / "app.py").write_text(
        "class Coisa:\n    def generate_content(self, x):\n        return x\n\n\n"
        "def main():\n    Coisa().generate_content(1)\n    return 2\n", encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    assert m["piscinas"] == [], m["piscinas"]


def test_fluxo_de_mensagem_dentro_do_subprocesso_e_desenhado(bpmn, tmp_path):
    """Reconferindo o MSS-SSC: `Gemini` estava no texto e na lista de piscinas, a caixa da piscina
    era desenhada — e NENHUMA seta apontava pra ela. O nó do Gemini fica 2 níveis fundo (dentro da
    expansão do subprocesso), e o SVG da expansão era gerado com a lista de piscinas VAZIA. O
    teste antigo não pegou porque procurava a substring "msg", que casa com o CSS."""
    (tmp_path / "routers").mkdir()
    (tmp_path / "services").mkdir()
    (tmp_path / "routers" / "api.py").write_text(
        "from fastapi import FastAPI\n"
        "from services.fluxo import orquestrar\n\n"
        "app = FastAPI()\n\n\n"
        '@app.post("/extrair")\n'
        "def extrair(pdf):\n"
        '    """Extrai o consolidado."""\n'
        "    return orquestrar(pdf)\n", encoding="utf-8")
    (tmp_path / "services" / "fluxo.py").write_text(
        "from services.llm import chamar_modelo\n\n\n"
        "def orquestrar(pdf):\n"
        '    """Orquestra a extracao."""\n'
        "    if not pdf:\n"
        "        raise ValueError('sem pdf')\n"
        "    return chamar_modelo(pdf)\n", encoding="utf-8")
    (tmp_path / "services" / "llm.py").write_text(
        "def chamar_modelo(pdf):\n"
        '    """Envia o PDF ao Gemini."""\n'
        "    import google.generativeai as genai\n"
        "    m = genai.GenerativeModel('x')\n"
        "    return m.generate_content([pdf])\n", encoding="utf-8")

    m = bpmn.extrair(tmp_path)
    h = bpmn.render_html(m)
    assert "Gemini" in m["piscinas"], m["piscinas"]
    assert 'class="msg"' in h, \
        "a piscina foi desenhada sem NENHUMA seta de fluxo de mensagem apontando pra ela"
    # o subprocesso colapsado tem de carregar a mensagem: quem fala com o Gemini, na leitura BPMN,
    # é a caixa visível no nível de cima
    topo = m["processos"][0]["nos"]
    assert any("Gemini" in n["mensagens"] for n in topo), \
        [(n["rotulo"], n["mensagens"]) for n in topo]


def test_chamada_dentro_do_return_vira_tarefa(bpmn, tmp_path):
    """`return servico(x)` — o padrão do router fino — perdia a tarefa: o statement caía no ramo
    do `ast.Return` e saía só o evento de fim. Achado montando o teste do fluxo de mensagem em 3
    níveis; no MSS-SSC escapou porque as rotas fazem `dados = gen(...)` antes do `return`."""
    (tmp_path / "servicos").mkdir()
    (tmp_path / "servicos" / "calc.py").write_text(
        "def _somar(a):\n    return a\n\n\n"
        "def calcular(x):\n"
        '    """Calcula o premio."""\n'
        "    if x < 0:\n"
        "        raise ValueError('negativo')\n"
        "    return _somar(x)\n", encoding="utf-8")
    (tmp_path / "web.py").write_text(
        "from fastapi import FastAPI\n"
        "from servicos.calc import calcular\n\n"
        "app = FastAPI()\n\n\n"
        '@app.get("/premio")\n'
        "def premio(x):\n"
        "    return calcular(x)\n", encoding="utf-8")
    m = bpmn.extrair(tmp_path)
    p = [x for x in m["processos"] if x["nome"] == "GET /premio"][0]
    fns = [n["fn"] for n in bpmn.achatar(p["nos"])]
    assert "calcular" in fns, f"a tarefa do `return calcular(x)` sumiu: {fns}"
    assert "_somar" in fns, f"a tarefa do `return _somar(x)` dentro do serviço sumiu: {fns}"
