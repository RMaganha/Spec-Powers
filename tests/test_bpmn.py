"""Comportamento do gerador do desenho BPMN (templates/bpmn.py).

O gerador lê o código Python do projeto por `ast` e monta UM processo por porta de entrada
(rota Flask/FastAPI, ou `main()`/`if __name__` da raiz quando o projeto não expõe rota). Regra
dura: nada de caixa que não está no código — o que não é derivável fica declarado como não
derivável, e arquivo que não parseia vai pra "não lido" (falha ABERTA), nunca derruba a geração.

Camadas (2026-11-18, `docs/decisoes.md`): o extrator lê o projeto por um objeto de disco; aqui ele é um dicionário
{caminho: texto} (`Disco`). A gravação das saídas (`gerar`: `bpmn.md`, `bpmn.html` e um `.bpmn` por diagrama) e a
leitura de verdade ficam num teste só, numa pasta montada uma vez; o processo python, num teste só. O `node` compila o
JS do desenho lido da entrada padrão, sem arquivo.
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "bpmn.py"
BASE = REPO.parent / "bpmn-que-nao-existe"          # absoluto, nunca criado


@pytest.fixture(scope="module")
def bpmn():
    spec = importlib.util.spec_from_file_location("bpmn", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Disco:
    """O projeto em memória, com os métodos do `DiscoReal`: {caminho relativo: texto}; pasta = prefixo de arquivo."""

    def __init__(self, arquivos, raiz=BASE / "proj"):
        self.raiz = raiz
        self.arquivos = {raiz / rel: texto for rel, texto in arquivos.items()}
        self.pastas = {raiz} | {a for p in self.arquivos for a in p.parents if raiz in a.parents}

    def listar(self, d):
        if Path(d) not in self.pastas:
            raise NotADirectoryError(str(d))
        return [p for p in (*self.arquivos, *self.pastas) if p.parent == Path(d)]

    def eh_pasta(self, p):
        return Path(p) in self.pastas

    def ler(self, p):
        try:
            return self.arquivos[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None


def _extrair(bpmn, arquivos, **kw):
    d = arquivos if isinstance(arquivos, Disco) else Disco(arquivos)
    return bpmn.extrair(d.raiz, disco=d, **kw)


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


WEB = {"apis/cotacao.py": COTACAO, "servicos/regras.py": REGRAS, "persistencia/db.py": DB,
       "quebrado.py": "def x(:\n    pass\n", "tests/test_nada.py": "def test_ignorado():\n    assert True\n"}


@pytest.fixture(scope="module")
def proj_web():
    """Projeto com rota Flask: guarda, gateway, subprocesso, banco, HTTP, try/except."""
    return Disco(WEB, BASE / "proj_web")


@pytest.fixture(scope="module")
def proj_script():
    """Projeto SEM rota: as portas de entrada sao o main()/if __name__ da raiz."""
    return Disco({"carga.py": CARGA}, BASE / "proj_script")


@pytest.fixture(scope="module")
def modelo_web(bpmn, proj_web):
    return _extrair(bpmn, proj_web)


@pytest.fixture(scope="module")
def modelo_script(bpmn, proj_script):
    return _extrair(bpmn, proj_script)


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
    p = _proc(_extrair(bpmn, proj_web, profundidade=1), "POST /cotacao")
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
    m = _extrair(bpmn, proj_script, entradas_extra=["paralelo"])
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


@pytest.mark.parametrize("render", ["render_texto", "render_html"])
def test_corte_deixa_rastro(bpmn, proj_web, render):
    """AC7 — DADO teto menor que o processo ENTÃO o corte deixa rastro '… (+N)' (F-009), no texto e no desenho."""
    assert "… (+" in getattr(bpmn, render)(_extrair(bpmn, proj_web, limite=3)), "corte silencioso"


# ----------------------------------------------------------- T3 — o DESENHO (o humano olha este)

@pytest.fixture(scope="module")
def html_web(bpmn, modelo_web):
    return bpmn.render_html(modelo_web, gerado_em="2026-09-02")


def test_html_self_contained(html_web):
    """AC9 — zero CDN (proxy MSIG derruba recurso externo): as libs do bpmn.io vêm VENDORIZADAS
    inline, igual ao vis-network do mapa-neural. Namespace XML (`http://www.omg.org/...`) é
    identificador, não recurso — o que não pode existir é carga externa."""
    assert "<script src=" not in html_web, "script externo — tem que ser self-contained"
    assert "<link " not in html_web, "stylesheet/font externo — tem que ser self-contained"
    assert not re.search(r"url\(['\"]?https?://", html_web), "recurso externo em url()"
    assert "BpmnJS" in html_web, "o viewer do bpmn-js não foi embutido"
    assert "BpmnAutoLayout" in html_web, "o bpmn-auto-layout não foi embutido"
    assert "@font-face" in html_web, "a fonte do bpmn-js não foi embutida"


def test_html_tem_uma_secao_por_diagrama(html_web, bpmn, modelo_web):
    """Formato em NÍVEIS: uma seção por diagrama (rota + drill-down de cada subprocesso)."""
    esperado = sum(len(bpmn.diagramas(p)) for p in modelo_web["processos"])
    assert html_web.count('class="diagrama"') == esperado, esperado
    for p in modelo_web["processos"]:
        assert p["nome"] in html_web, f"processo {p['nome']} não está no HTML"


def _xmls_embutidos(html: str) -> str:
    """Só os blocos <script type="application/xml">: o bundle minificado do bpmn-js cita as
    tags do BPMN por dentro e casaria com qualquer busca feita na página inteira."""
    return "\n".join(re.findall(r'<script type="application/xml"[^>]*>(.*?)</script>', html, re.S))


def test_xml_embutido_carrega_os_elementos(html_web):
    """Quem desenha é o bpmn-js a partir do XML embutido — então é o XML que tem de estar certo."""
    assert 'type="application/xml"' in html_web, "o XML não foi embutido como dado"
    xml = _xmls_embutidos(html_web)
    for tag in ("<bpmn:startEvent", "<bpmn:sequenceFlow", "<bpmn:exclusiveGateway",
                "<bpmn:endEvent", "<bpmn:boundaryEvent"):
        assert tag in xml, f"{tag} ausente no XML embutido"
    assert "errorEventDefinition" in xml, "fim de erro sem definição de erro"
    assert "bpmndi:BPMNShape" not in xml, \
        "o XML embutido não deveria trazer coordenadas — quem posiciona é o auto-layout"


def test_html_declara_o_que_nao_desenha(html_web):
    """Duas listas de buraco, e nenhuma pode ficar implícita: o que a leitura estática não deriva
    do código, e o que o auto-layout do bpmn.io NÃO posiciona (raia, piscina, fluxo de mensagem,
    anotação, associação) — foi a troca que a escolha do renderizador profissional custou."""
    assert "gateway inclusivo" in html_web, "não-derivável do código não declarado"
    for perdido in ("raia", "piscina", "fluxo de mensagem"):
        assert perdido in html_web.lower(), f"limitação do auto-layout não declarada: {perdido}"
    assert "pro humano" in html_web, "o HTML não declara que o visual é pro humano"
    assert "bpmn.md" in html_web, "o HTML não aponta a camada de texto que o assistente lê"


def test_js_do_desenho_passa_no_node_check(html_web):
    """AC10 / F-007 — substring verde não pega erro de parse; o node compilando o JS pega a tela branca.
    O node lê o JS da entrada padrão, sem rodar e sem arquivo (pula se node não estiver no PATH)."""
    if not shutil.which("node"):
        pytest.skip("node não disponível — guarda de sintaxe pulada")
    scripts = re.findall(r"<script>(.*?)</script>", html_web, re.S)
    assert scripts, "o desenho tem JS inline (seletor + pan/zoom)"
    compila = ("let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',d=>s+=d)"
               ".on('end',()=>{new (require('vm').Script)(s)})")
    r = subprocess.run(["node", "-e", compila], input="\n".join(scripts), capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, f"JS do desenho com erro de sintaxe:\n{r.stderr}"


def test_main_fora_da_raiz_tambem_e_porta_de_entrada(bpmn):
    """Achado do dogfood no próprio kit: projeto sem rota cujos scripts NÃO ficam na raiz (aqui,
    em templates/) ficava com ZERO processo. A cascata é: rota → main() da raiz → main() em
    qualquer módulo. Fixture não vê isso; o projeto real vê (regra do dogfood com diff)."""
    nomes = [p["nome"] for p in _extrair(bpmn, {"scripts/job.py": CARGA})["processos"]]
    assert any("main" in n for n in nomes), nomes
    assert any("scripts/job.py" in n for n in nomes), nomes


def test_nome_do_projeto_com_caminho_relativo(bpmn, monkeypatch):
    """Achado do dogfood: `--proj .` (o jeito que o comando roda) saía com o título vazio, porque
    `Path('.').name` é string vazia. O nome sai do caminho resolvido (a pasta atual é o próprio kit,
    lido do dicionário)."""
    monkeypatch.chdir(REPO)
    m = bpmn.extrair(".", disco=Disco({"carga.py": CARGA}, REPO))
    assert m["projeto"] == REPO.name, m["projeto"]


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


def test_gateway_aninhado_nao_reusa_linha_de_ramo_irmao(bpmn):
    """O caso que a fixture web não tem: `if` dentro do ramo de outro `if`, os dois com desfecho.
    Sem alocação global de linha, o ramo interno cairia sobre o ramo externo."""
    m = _extrair(bpmn, {"app.py": (
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
        "        return 'ax'\n")})
    caixas, _, _ = bpmn._posicionar(m["processos"][0]["nos"])
    chaves = [(c["col"], c["linha"]) for c in caixas]
    assert len(chaves) == len(set(chaves)), f"caixas empilhadas: {chaves}"


def test_chamada_resolve_no_modulo_do_chamador(bpmn):
    """Achado do dogfood: `templates/mapa_neural.py` e `templates/anatomia.py` têm cada um uma
    função `gerar`. A resolução por nome simples pegava a PRIMEIRA em ordem de arquivo, e o
    processo do mapa-neural saía desenhando as caixas internas do anatomia — desenho errado com
    cara de certo, que é pior que buraco. Ordem de resolução: mesmo arquivo → import declarado →
    qualquer arquivo (fallback heurístico)."""
    m = _extrair(bpmn, {
        "aaa.py": "def _passo_aaa():\n    return 1\n\n\n"
                  "def gerar():\n    '''Gera o aaa.'''\n    _passo_aaa()\n    return 'aaa'\n",
        "zzz.py": "def _passo_zzz():\n    return 2\n\n\n"
                  "def gerar():\n    '''Gera o zzz.'''\n    _passo_zzz()\n    return 'zzz'\n\n\n"
                  "def main():\n    gerar()\n"})
    p = [x for x in m["processos"] if "zzz.py" in x["nome"]][0]
    ger = [n for n in bpmn.achatar(p["nos"]) if n["fn"] == "gerar"]
    assert ger, [n["fn"] for n in bpmn.achatar(p["nos"])]
    assert ger[0]["arquivo"] == "zzz.py", f"resolveu no módulo errado: {ger[0]['arquivo']}"
    filhos = [n["fn"] for n in bpmn.achatar(ger[0]["filhos"])]
    assert "_passo_zzz" in filhos and "_passo_aaa" not in filhos, filhos


def test_chamada_resolve_pelo_import_declarado(bpmn):
    """`from servicos.regras import aprovar` é o sinal honesto de qual módulo é o dono — vence o
    homônimo de outro arquivo."""
    m = _extrair(bpmn, {
        "aaa.py": "def aprovar():\n    return 'errado'\n",
        "servicos/regras.py": "def _checar():\n    return True\n\n\n"
                              "def aprovar():\n    '''Aprova de verdade.'''\n    _checar()\n    return 'certo'\n",
        "web.py": "from servicos.regras import aprovar\n\n\n"
                  "def main():\n    aprovar()\n    return 1\n"})
    p = [x for x in m["processos"] if "web.py" in x["nome"]][0]
    ap = [n for n in bpmn.achatar(p["nos"]) if n["fn"] == "aprovar"]
    assert ap and ap[0]["arquivo"] == "servicos/regras.py", ap and ap[0]["arquivo"]
    assert ap[0]["raia"] == "servicos", ap[0]["raia"]


def test_codigo_com_html_nao_quebra_o_desenho(bpmn):
    """Todo rótulo nasce do código do projeto e vai para dentro de um ATRIBUTO XML: condição com
    `<`/`>`/`&` ou docstring com `<script>` entrando cru quebraria o parse e a página ficaria em
    branco. Os dois caminhos que de fato chegam ao XML são a pergunta do gateway e o nome da
    tarefa — o docstring do entrypoint não chega (vira anotação, que o XML não emite)."""
    m = _extrair(bpmn, {"app.py": (
        "def _perigoso(a):\n"
        '    """Compara <script> & "aspas" no rotulo."""\n'
        "    return a\n\n\n"
        "def main(a, b):\n"
        "    if a < 3 and b > 4:\n"
        "        _perigoso(1)\n"
        "        return 'ok'\n"
        "    return 'nao'\n")})
    html = bpmn.render_html(m)
    xml = _xmls_embutidos(html)
    assert "&lt;" in xml and "&amp;" in xml, "condição/rótulo com < e & não foram escapados"
    assert "&lt;script&gt;" in xml, "docstring com <script> entrou cru no rótulo da tarefa"
    assert not re.search(r'name="[^"]*<', xml), "sobrou `<` cru dentro de atributo XML"
    for bloco in re.findall(r'<script type="application/xml"[^>]*>(.*?)</script>', html, re.S):
        ET.fromstring(bloco)          # parse de verdade: substring verde não prova XML válido


# ----------------------------------- regressao: "abri o html e nao havia desenho nenhum" (owner)

def test_sem_js_a_pagina_explica_em_vez_de_ficar_branca(html_web):
    """F-017 mudou de forma, não de lição. Com o renderizador do bpmn.io o desenho PASSA a exigir
    JS (é ele que monta o SVG), então a garantia "aparece sem JS" ficou impossível. A troca: se o
    script não rodar, cada moldura já traz texto explicando e apontando o `.bpmn` e o `bpmn.md` —
    página que falha tem de falhar LEGÍVEL, nunca em branco (foi o que custou a 0.24.x)."""
    assert "<noscript>" in html_web, "sem <noscript>: página em branco se o script não rodar"
    assert html_web.count('class="espera"') >= 1, \
        "moldura sem texto de espera — se o viewer não subir, sobra retângulo vazio"
    assert ".bpmn" in html_web and "bpmn.md" in html_web, \
        "o texto de falha não aponta a saída alternativa (.bpmn / bpmn.md)"


def test_indice_navega_por_ancora(html_web, bpmn, modelo_web):
    """O índice é âncora, não botão: funciona mesmo se o JS falhar. E TODO diagrama — inclusive a
    expansão de subprocesso, que não entra no índice — tem âncora própria pra link direto."""
    for p in modelo_web["processos"]:
        diags = bpmn.diagramas(p)
        assert f'href="#{diags[0]["slug"]}"' in html_web, f"índice sem âncora {p['nome']}"
        for d in diags:
            assert f'id="{d["slug"]}"' in html_web, f"diagrama sem âncora própria: {d['nome']}"


def test_processos_do_mais_rico_pro_mais_pobre(bpmn, modelo_web):
    """A página abria em `GET /` (2 nós: início + fim) porque a ordem era alfabética, enquanto
    `POST /endosso` (41 nós) ficava enterrado — parecia que a ferramenta não achou nada.
    Ordem passa a ser nº de nós desc, nome asc como desempate (determinística)."""
    tamanhos = [len(bpmn.achatar(p["nos"])) for p in modelo_web["processos"]]
    assert tamanhos == sorted(tamanhos, reverse=True), \
        f"processos fora de ordem (rico → pobre): {[(p['nome'], len(bpmn.achatar(p['nos']))) for p in modelo_web['processos']]}"
    assert modelo_web["processos"][0]["nome"] == "POST /cotacao", modelo_web["processos"][0]["nome"]


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



def test_cliente_de_llm_vira_piscina_externa(bpmn):
    """Rodando no MSS-SSC (24 rotas, 56 armazenamentos de dados) saíram ZERO fluxos de mensagem —
    num app cuja razão de existir é chamar o Gemini. Duas causas: `google.generativeai` fora da
    tabela de libs, e a chamada de verdade ser método de instância (`self.model.generate_content`),
    que nenhuma heurística de nome de import resolve. O sinal honesto é o **import do SDK** no
    arquivo (mesmo tardio, dentro do método): com ele, construtor de cliente e método de geração
    contam como fluxo de mensagem (11) pra piscina (13) nomeada pelo SDK."""
    m = _extrair(bpmn, {"routers/api.py": ROTA_LLM, "services/gemini.py": GEMINI_SVC,
                        "services/resumo.py": OPENAI_SVC})
    assert "Gemini" in m["piscinas"], m["piscinas"]
    assert "OpenAI" in m["piscinas"], m["piscinas"]
    p = m["processos"][0]
    msgs = {x for n in bpmn.achatar(p["nos"]) for x in n["mensagens"]}
    assert "Gemini" in msgs, f"o subprocesso do Gemini não carrega o fluxo de mensagem: {msgs}"
    assert "OpenAI" in msgs, msgs


def test_sem_import_de_sdk_nao_inventa_piscina(bpmn):
    """A contrapartida: sem import de SDK no arquivo, um método chamado `generate_content` ou uma
    função `create` NÃO viram piscina — o gerador não inventa integração."""
    m = _extrair(bpmn, {"app.py": "class Coisa:\n    def generate_content(self, x):\n        return x\n\n\n"
                                  "def main():\n    Coisa().generate_content(1)\n    return 2\n"})
    assert m["piscinas"] == [], m["piscinas"]


def test_fluxo_de_mensagem_dentro_do_subprocesso_e_desenhado(bpmn):
    """Reconferindo o MSS-SSC: `Gemini` estava no texto e na lista de piscinas, a caixa da piscina
    era desenhada — e NENHUMA seta apontava pra ela. O nó do Gemini fica 2 níveis fundo (dentro da
    expansão do subprocesso), e o SVG da expansão era gerado com a lista de piscinas VAZIA. O
    teste antigo não pegou porque procurava a substring "msg", que casa com o CSS."""
    m = _extrair(bpmn, {
        "routers/api.py": ("from fastapi import FastAPI\n"
                           "from services.fluxo import orquestrar\n\n"
                           "app = FastAPI()\n\n\n"
                           '@app.post("/extrair")\n'
                           "def extrair(pdf):\n"
                           '    """Extrai o consolidado."""\n'
                           "    return orquestrar(pdf)\n"),
        "services/fluxo.py": ("from services.llm import chamar_modelo\n\n\n"
                              "def orquestrar(pdf):\n"
                              '    """Orquestra a extracao."""\n'
                              "    if not pdf:\n"
                              "        raise ValueError('sem pdf')\n"
                              "    return chamar_modelo(pdf)\n"),
        "services/llm.py": ("def chamar_modelo(pdf):\n"
                            '    """Envia o PDF ao Gemini."""\n'
                            "    import google.generativeai as genai\n"
                            "    m = genai.GenerativeModel('x')\n"
                            "    return m.generate_content([pdf])\n")})
    h = bpmn.render_html(m)
    assert "Gemini" in m["piscinas"], m["piscinas"]
    # o auto-layout do bpmn.io NAO posiciona fluxo de mensagem: a integração vive no texto e na
    # ficha do diagrama, e a limitação é declarada na página (nunca some em silêncio)
    assert "Gemini" in bpmn.render_texto(m), "a piscina sumiu da camada de texto"
    assert "Gemini" in h, "a piscina não aparece nem na ficha do diagrama"
    # o subprocesso colapsado tem de carregar a mensagem: quem fala com o Gemini, na leitura BPMN,
    # é a caixa visível no nível de cima
    topo = m["processos"][0]["nos"]
    assert any("Gemini" in n["mensagens"] for n in topo), \
        [(n["rotulo"], n["mensagens"]) for n in topo]


def test_chamada_dentro_do_return_vira_tarefa(bpmn):
    """`return servico(x)` — o padrão do router fino — perdia a tarefa: o statement caía no ramo
    do `ast.Return` e saía só o evento de fim. Achado montando o teste do fluxo de mensagem em 3
    níveis; no MSS-SSC escapou porque as rotas fazem `dados = gen(...)` antes do `return`."""
    m = _extrair(bpmn, {
        "servicos/calc.py": ("def _somar(a):\n    return a\n\n\n"
                             "def calcular(x):\n"
                             '    """Calcula o premio."""\n'
                             "    if x < 0:\n"
                             "        raise ValueError('negativo')\n"
                             "    return _somar(x)\n"),
        "web.py": ("from fastapi import FastAPI\n"
                   "from servicos.calc import calcular\n\n"
                   "app = FastAPI()\n\n\n"
                   '@app.get("/premio")\n'
                   "def premio(x):\n"
                   "    return calcular(x)\n")})
    p = [x for x in m["processos"] if x["nome"] == "GET /premio"][0]
    fns = [n["fn"] for n in bpmn.achatar(p["nos"])]
    assert "calcular" in fns, f"a tarefa do `return calcular(x)` sumiu: {fns}"
    assert "_somar" in fns, f"a tarefa do `return _somar(x)` dentro do serviço sumiu: {fns}"


# ------------------------------------- rotulo de DESENHO em pt-BR (o modelo segue verbatim)

def test_gateway_vira_pergunta_em_pt_br(bpmn):
    """Owner: "trazer o conteúdo em pt-br, inglês só no que for texto de programação". O gateway
    saía rotulado com o nome da variável solto (`anexos`, `row`) — não dizia nada. Agora é
    pergunta em pt-BR com o identificador do código dentro."""
    m = _extrair(bpmn, {"app.py": (
        "def _f(x):\n    return x\n\n\n"
        "def main(dados, linha, valor, anexos):\n"
        "    if not dados:\n"
        "        raise ValueError('vazio')\n"
        "    if linha is None:\n"
        "        raise ValueError('sem linha')\n"
        "    if valor > 100000:\n"
        "        _f(1)\n"
        "        return 'alta'\n"
        "    if anexos:\n"
        "        _f(2)\n"
        "        return 'com anexo'\n"
        "    return 'ok'\n")})
    gws = [n for n in bpmn.achatar(m["processos"][0]["nos"]) if n["tipo"] == "gateway"]
    perguntas = [bpmn.rotulo_desenho(g) for g in gws]
    assert "Falta dados?" in perguntas, perguntas
    assert "linha está vazio?" in perguntas, perguntas
    assert "valor maior que 100000?" in perguntas, perguntas
    assert "Tem anexos?" in perguntas, perguntas
    # e os ramos viram sim/não no desenho (a condição inteira fica no bpmn.md)
    assert bpmn.rotulo_ramo(gws[0], 0) == "sim" and bpmn.rotulo_ramo(gws[0], 1) == "não"


@pytest.mark.parametrize("codigo,quais,esperados", [
    # `JSONResponse({...})` cru no evento de fim não diz o desfecho; `raise X` idem
    ("def main(x):\n    if not x:\n        raise ValidacaoError('ruim')\n    return JSONResponse({'ok': True})\n",
     lambda n: n["tipo"] in ("fim", "fim_erro"), ["Retorna JSONResponse", "Erro: ValidacaoError"]),
    # `cur.execute` como nome de tarefa é texto de programação onde cabia pt-BR: o verbo sai do próprio SQL
    ("import pyodbc\n\n\ndef main(cur):\n"
     '    cur.execute("SELECT id FROM apolice WHERE id = ?", 1)\n'
     '    cur.execute("INSERT INTO endosso (n) VALUES (?)", 2)\n'
     '    cur.execute("UPDATE apolice SET n = ?", 3)\n'
     "    return 1\n",
     lambda n: n["tipo"] == "tarefa", ["Consulta o banco", "Grava no banco", "Atualiza o banco"]),
    # `genai.GenerativeModel` como nome de tarefa não diz nada; "Chama Gemini" diz
    ("def main():\n    import google.generativeai as genai\n    m = genai.GenerativeModel('x')\n    return 1\n",
     lambda n: n["mensagens"], ["Chama Gemini"]),
], ids=["fim-e-erro", "verbo-do-sql", "servico-externo"])
def test_rotulo_de_desenho_em_pt_br(bpmn, codigo, quais, esperados):
    m = _extrair(bpmn, {"app.py": codigo})
    rot = [bpmn.rotulo_desenho(n) for n in bpmn.achatar(m["processos"][0]["nos"]) if quais(n)]
    for esperado in esperados:
        assert esperado in rot, rot


def test_rotulo_de_tarefa_cabe_na_caixa(bpmn, modelo_web):
    """Rótulo de atividade BPMN é frase curta: docstring inteiro estourava a caixa desenhada.
    Corta na 1ª fronteira de sentença e limita — o texto completo fica na anotação e no .md."""
    for n in bpmn.achatar(_proc(modelo_web, "POST /cotacao")["nos"]):
        assert len(bpmn.rotulo_desenho(n)) <= 40, (n["tipo"], bpmn.rotulo_desenho(n))


# ------------------------------------------------- T2: BPMN 2.0 XML (o que o bpmn-js/Bizagi leem)

@pytest.fixture(scope="module")
def diags_web(bpmn, modelo_web):
    return bpmn.diagramas(_proc(modelo_web, "POST /cotacao"))


def test_diagramas_em_niveis(diags_web):
    """Formato escolhido pelo owner: a rota (subprocessos colapsados) + um diagrama por
    subprocesso expandido. Cada figura fica limpa; navega-se entre elas."""
    assert diags_web, "nenhum diagrama"
    assert diags_web[0]["nome"] == "POST /cotacao", diags_web[0]["nome"]
    assert len(diags_web) >= 2, [d["nome"] for d in diags_web]
    assert all(d["elementos"] >= 2 for d in diags_web[1:]), \
        "drill-down com menos de 2 elementos não é diagrama (era um círculo solto na tela)"
    assert all(d["slug"] and "/" not in d["slug"] for d in diags_web), \
        [d["slug"] for d in diags_web]


def test_xml_parseia_e_tem_os_elementos_bpmn(bpmn, diags_web):
    raiz = ET.fromstring(bpmn.render_bpmn(diags_web[0]))
    tags = {e.tag.split("}")[-1] for e in raiz.iter()}
    assert "process" in tags and "startEvent" in tags and "sequenceFlow" in tags, tags
    assert {"task", "subProcess"} & tags, tags
    assert "endEvent" in tags, tags


def test_todo_no_declara_incoming_e_outgoing(bpmn, diags_web):
    """Regressão do spike: o auto-layout monta o grafo pelos <incoming>/<outgoing> do NÓ, não
    pelo sourceRef do fluxo. Sem eles o DI saía com shapes e ZERO edges — setas invisíveis."""
    B = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
    for d in diags_web:
        proc = ET.fromstring(bpmn.render_bpmn(d)).find(f"{B}process")
        fluxos = {f.get("id") for f in proc.findall(f"{B}sequenceFlow")}
        citados = set()
        for e in proc:
            citados |= {x.text for x in e.findall(f"{B}incoming")}
            citados |= {x.text for x in e.findall(f"{B}outgoing")}
        assert fluxos <= citados, f"{d['nome']}: fluxos sem incoming/outgoing: {fluxos - citados}"


def test_xml_usa_rotulo_em_pt_br_e_contrai_o_segue(bpmn, diags_web):
    xml = "".join(bpmn.render_bpmn(d) for d in diags_web)
    assert "Segue o fluxo" not in xml, \
        "o placeholder 'segue' virou caixa no XML — em BPMN o ramo do guarda liga direto no próximo"
    assert "Erro:" in xml, "evento de fim de erro sem rótulo em pt-BR"
    assert 'name="sim"' in xml and 'name="não"' in xml, "ramos do gateway não saíram sim/não"


def test_subprocesso_sem_conteudo_sai_como_tarefa(bpmn):
    """O `+` de subprocesso colapsado prometia um drill-down que não existia."""
    d = Disco({"app.py": ("def _vazio(x):\n    return x\n\n\n"
                          "def _cheio(x):\n"
                          "    if not x:\n"
                          "        raise ValueError('x')\n"
                          "    return _vazio(x)\n\n\n"
                          "def main(x):\n    _cheio(x)\n    return 1\n")})
    xml = bpmn.render_bpmn(bpmn.diagramas(_extrair(bpmn, d)["processos"][0])[0])
    assert "<bpmn:subProcess" in xml, xml[:400]
    xml2 = bpmn.render_bpmn(bpmn.diagramas(_extrair(bpmn, d, profundidade=1)["processos"][0])[0])
    assert "<bpmn:subProcess" not in xml2, "colapsado sem conteúdo lido continua prometendo '+'"


def test_rotulo_do_evento_de_borda_e_so_a_excecao(bpmn):
    """Visto na tela do MSS-SSC: o rótulo saía `mssc_service.ValidacaoError` e estourava a marca
    do evento de borda ("mssc_service.V alidacaoEr…"). Só a exceção, sem o prefixo do módulo."""
    m = _extrair(bpmn, {"app.py": ("def _grava(x):\n"
                                   "    try:\n"
                                   "        return x.save()\n"
                                   "    except mssc_service.ValidacaoError:\n"
                                   "        raise\n\n\n"
                                   "def main(x):\n    _grava(x)\n    return 1\n")})
    xml = "".join(bpmn.render_bpmn(d) for d in bpmn.diagramas(m["processos"][0]))
    bordas = re.findall(r'<bpmn:boundaryEvent[^>]*name="([^"]*)"', xml)
    assert bordas, xml[:400]
    assert "ValidacaoError" in bordas[0], bordas
    assert "mssc_service" not in bordas[0], f"prefixo do módulo estourou a marca: {bordas[0]!r}"


def test_indice_lista_so_as_portas_de_entrada(bpmn, modelo_web):
    """Na tela do MSS-SSC o índice com 36 pílulas comia a primeira tela inteira antes de qualquer
    desenho. Índice = as portas de entrada; a expansão de cada subprocesso já vem logo abaixo do
    diagrama pai (e mantém âncora própria pra link direto)."""
    h = bpmn.render_html(modelo_web)
    nav = h[h.index("<nav>"):h.index("</nav>")]
    assert nav.count("<a ") == len(modelo_web["processos"]), \
        f"índice deveria ter {len(modelo_web['processos'])} entradas, tem {nav.count('<a ')}"
    for p in modelo_web["processos"]:
        d0 = bpmn.diagramas(p)[0]
        assert f'href="#{d0["slug"]}"' in nav, f"porta de entrada fora do índice: {p['nome']}"


def test_slug_de_diagrama_e_unico_no_documento(bpmn):
    """O BUG que o owner viu: três processos deste repo têm um subprocesso chamado `gerar`, e o
    slug do drill-down era `1-gerar` para os três. `getElementById` devolve o PRIMEIRO, então a
    seção do `mapa_neural` renderizava o XML do `anatomia` — cabeçalho de um, desenho de outro.
    No MSS-SSC duas seções estavam trocadas do mesmo jeito. Slug tem de ser único no documento."""
    arquivos = {f"{pasta}/svc.py": (f"def _passo{sufixo}(x):\n    return x\n\n\n"
                                    "def gerar(x):\n"          # SEM docstring, como os três `gerar` deste repo: o
                                    "    if not x:\n"          # rótulo fica igual nos dois e os slugs colidem
                                    f"        raise ValueError('{sufixo}')\n"
                                    f"    return _passo{sufixo}(x)\n")
                for pasta, sufixo in (("a", "A"), ("b", "B"))}
    arquivos["web.py"] = ("from fastapi import FastAPI\n"
                          "from a.svc import gerar as gerar_a\n"
                          "from b.svc import gerar as gerar_b\n\n"
                          "app = FastAPI()\n\n\n"
                          '@app.get("/a")\n'
                          "def rota_a(x):\n    return gerar_a(x)\n\n\n"
                          '@app.get("/b")\n'
                          "def rota_b(x):\n    return gerar_b(x)\n")
    m = _extrair(bpmn, arquivos)
    slugs = [d["slug"] for p in m["processos"] for d in bpmn.diagramas(p)]
    assert len(slugs) == len(set(slugs)), f"slug repetido no modelo: {slugs}"

    h = bpmn.render_html(m)
    ids = re.findall(r'id="(xml-[^"]+)"', h)
    assert len(ids) == len(set(ids)), f"id de XML repetido no HTML: {ids}"
    secoes = re.findall(r'<section class="diagrama" id="([^"]+)"', h)
    assert len(secoes) == len(set(secoes)), f"id de seção repetido: {secoes}"


def test_slug_transliteta_acento_em_vez_de_apagar(bpmn):
    """`Gerador de etapas da extração` virava `gerador-de-etapas-da-extra-o` — o `ç` e o `ã`
    sumiam e o nome do arquivo .bpmn ficava ilegível."""
    assert bpmn._slug("Gerador de etapas da extração") == "gerador-de-etapas-da-extracao"
    assert bpmn._slug("Apólice — validação") == "apolice-validacao"


def test_import_com_apelido_resolve(bpmn):
    """`from servicos.regras import aprovar as aprovar_cotacao` e depois `aprovar_cotacao(x)`:
    eu guardava só o nome LOCAL do import, então procurava `aprovar_cotacao` no módulo destino,
    não achava e a tarefa **desaparecia** — o processo saía início → fim. Apelido é comum."""
    m = _extrair(bpmn, {
        "servicos/regras.py": ("def _checar(x):\n    return x\n\n\n"
                               "def aprovar(x):\n"
                               '    """Aprova a cotacao."""\n'
                               "    return _checar(x)\n"),
        "web.py": ("from fastapi import FastAPI\n"
                   "from servicos.regras import aprovar as aprovar_cotacao\n\n"
                   "app = FastAPI()\n\n\n"
                   '@app.get("/x")\n'
                   "def rota(x):\n    return aprovar_cotacao(x)\n")})
    nos = bpmn.achatar(m["processos"][0]["nos"])
    achado = [n for n in nos if n["fn"] == "aprovar"]
    assert achado, f"a tarefa do apelido sumiu: {[(n['tipo'], n['fn']) for n in nos]}"
    assert achado[0]["arquivo"] == "servicos/regras.py", achado[0]["arquivo"]
    assert achado[0]["raia"] == "servicos", achado[0]["raia"]


def test_montagem_espera_a_moldura_ter_tamanho(html_web):
    """Com o painel estreito, os 36 desenhos do MSS-SSC falharam TODOS em
    `SVGMatrix scale: non-finite` — o `fit-viewport` do bpmn-js divide pela dimensão do container,
    e ele ainda não tinha tamanho quando o script rodou. Guardas: monta sob demanda (moldura
    entrando na tela), espera o quadro seguinte enquanto o tamanho for zero, e nunca aplica
    altura não-finita."""
    js = "\n".join(re.findall(r"<script>(.*?)</script>", html_web, re.S)[-1:])
    assert "IntersectionObserver" in js, "não monta sob demanda: 36 visualizadores de uma vez"
    assert "clientWidth" in js and "requestAnimationFrame" in js, \
        "não espera a moldura ter tamanho antes do fit-viewport"
    assert js.count("isFinite") >= 2, "aplica altura/escala sem checar se é finita"
    assert "data-montado" in js, "sem marca de montado, a moldura pode ser montada duas vezes"


# ---- o disco de verdade e o processo (pasta montada uma vez) ------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("bpmn") / "proj_web"
    for rel, texto in WEB.items():
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_text(texto, encoding="utf-8")
    return raiz


def test_gerar_escreve_as_duas_saidas(bpmn, pasta):
    """AC9 — `gerar()` lê o projeto do disco e escreve as saídas: `bpmn.md` (texto, o assistente lê), `bpmn.html`
    (desenho, o humano vê) e um `.bpmn` por diagrama em `bpmn/` — o que abre no Bizagi, onde raia e piscina ganham a
    posição que o auto-layout não dá. Sem `out_dir`, a saída vai pra `docs/` (como mapa-neural e anatomia)."""
    out = pasta / "_out"
    md, html = bpmn.gerar(proj_dir=pasta, out_dir=out)
    assert md.name == "bpmn.md" and html.name == "bpmn.html", (md, html)
    assert "POST /cotacao" in md.read_text(encoding="utf-8") and "quebrado.py" in md.read_text(encoding="utf-8")
    assert "<svg" in html.read_text(encoding="utf-8")
    esperados = sum(len(bpmn.diagramas(p)) for p in bpmn.extrair(pasta)["processos"])
    arquivos = sorted((out / "bpmn").glob("*.bpmn"))
    assert len(arquivos) == esperados, ([x.name for x in arquivos], esperados)
    for x in arquivos:
        ET.parse(x)          # cada arquivo tem de ser XML válido de verdade
    md, html = bpmn.gerar(proj_dir=pasta)
    assert md.parent == pasta / "docs" and html.parent == pasta / "docs", (md, html)


def test_processo_gera_o_desenho(pasta):
    r = subprocess.run([sys.executable, str(SCRIPT), "--proj", str(pasta), "--out", str(pasta / "_cli")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert r.returncode == 0, r.stderr
    assert "processo(s) desenhado(s)" in r.stdout
    assert (pasta / "_cli" / "bpmn.md").is_file() and (pasta / "_cli" / "bpmn.html").is_file()
