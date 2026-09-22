"""Comportamento do inventário do banco vivo (templates/inventario_banco.py).

Regra dura: SOMENTE-LEITURA e SÓ CATÁLOGO — nenhuma query escreve e nenhuma lê dado de negócio;
credencial reaproveitada por leitura ESTÁTICA (o get_connection.py de outro projeto nunca é
importado); segredo nunca sai; "sem citação" nunca vira "pode apagar"; só mexe em arquivo que tem a
marca do inventário. Testável sem banco: o cursor é falso. Spec: docs/specs/inventario-banco.md
"""
import datetime as dt
import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "inventario_banco.py"


def _carregar():
    spec = importlib.util.spec_from_file_location("inventario_banco", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # @dataclass no Python 3.14 resolve o módulo por aqui
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def inv():
    return _carregar()


def test_importavel_sem_pyodbc_nem_cryptography(monkeypatch):
    """Driver e cripto entram por import tardio: a suíte roda em máquina sem ODBC."""
    monkeypatch.setitem(sys.modules, "pyodbc", None)  # None em sys.modules = o import falha
    monkeypatch.setitem(sys.modules, "cryptography", None)
    monkeypatch.setitem(sys.modules, "cryptography.fernet", None)
    mod = _carregar()
    assert callable(mod.main)


PROIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|EXEC|EXECUTE|SP_EXECUTESQL|GRANT|DENY|REVOKE)\b",
    re.I)
ALVO = re.compile(r"\b(?:FROM|JOIN|APPLY)\s+([\w.\[\]]+)", re.I)


def test_queries_sao_somente_leitura(inv):
    """'O script não escreve' é fato verificável, não promessa de prosa."""
    sujas = {n: PROIBIDAS.findall(q) for n, q in inv.QUERIES.items() if PROIBIDAS.search(q)}
    assert not sujas, f"query com verbo de escrita: {sujas}"
    for nome, q in inv.QUERIES.items():
        assert q.lstrip().upper().startswith("SELECT"), f"{nome} não começa com SELECT"


def test_queries_so_leem_catalogo(inv):
    """Nenhum dado de negócio: todo FROM/JOIN é sys.*, INFORMATION_SCHEMA.* ou msdb.dbo.sys*."""
    fora = []
    for nome, q in inv.QUERIES.items():
        for alvo in ALVO.findall(q):
            a = alvo.lower()
            if not a.startswith(("sys.", "msdb.dbo.sys", "information_schema.")):
                fora.append(f"{nome}: {alvo}")
    assert not fora, f"query fora do catálogo: {fora}"
    assert "SELECT *" not in " ".join(inv.QUERIES.values()).upper()


def test_so_existe_um_execute_no_modulo():
    """Guarda do guarda: SQL executado fora de QUERIES escaparia dos dois testes acima."""
    assert SCRIPT.read_text(encoding="utf-8").count(".execute(") == 1


def test_opcionais_sao_queries_conhecidas(inv):
    assert set(inv.OPCIONAIS) <= set(inv.QUERIES)
    assert set(inv.OPCIONAIS) == set(inv.DESCRICAO_OPCIONAL)


def test_mask_password(inv):
    assert inv.mask_password("Server=a;UID=u;PWD=s3nh4") == "Server=a;UID=u;PWD=***HIDDEN***"
    assert "x9" not in inv.mask_password("Data Source=a;User ID=u;Password=x9;")


def test_mask_password_respeita_chaves(inv):
    assert (inv.mask_password("Server=a;UID=u;PWD={s3n;ha};Database=x")
            == "Server=a;UID=u;PWD=***HIDDEN***;Database=x")


@pytest.mark.parametrize("antes, depois", [
    ("Server=a;Database=Velha;UID=u", "Server=a;Database=Nova;UID=u"),
    ("Data Source=a;Initial Catalog=Velha;", "Data Source=a;Initial Catalog=Nova;"),
    ("Server=a;UID=u", "Server=a;UID=u;Database=Nova"),
    ("Server=a;Database=Old1;Initial Catalog=Old2;UID=u",
     "Server=a;Database=Nova;Initial Catalog=Nova;UID=u"),
])
def test_trocar_base(inv, antes, depois):
    assert inv.trocar_base(antes, "Nova") == depois


@pytest.mark.parametrize("antes, depois", [
    ("Server=h,1435;Database=x", "Server=h,1500;Database=x"),
    ("Server=h;Database=x", "Server=h,1500;Database=x"),
    ("Server = h,1435;Database=x", "Server = h,1500;Database=x"),
])
def test_trocar_porta(inv, antes, depois):
    assert inv.trocar_porta(antes, "1500") == depois


def test_le_servidor_e_base(inv):
    conn = "Server=srv,1435;Initial Catalog=Legado;UID=u"
    assert inv.servidor_da_conn(conn) == "srv,1435"
    assert inv.base_da_conn(conn) == "Legado"
    assert inv.base_da_conn("Server=srv") is None


FONTE = '''
raise SystemExit("importou o get_connection.py do outro projeto!")
DEV_SSC_KEY = b"chave-ssc-dev"
DEV_SSC_CIPHERTEXT = b"cifra-ssc-dev"
DEV_MS10_KEY = b"chave-ms10-dev"
DEV_MS10_CIPHERTEXT = b"cifra-ms10-dev"
PROD_SSC_KEY: bytes = b"chave-ssc-prd"
PROD_SSC_CIPHERTEXT: bytes = b"cifra-ssc-prd"
DEV_SOZINHA_KEY = b"sem-par"
OUTRA_COISA = 42
'''


@pytest.fixture
def fonte(tmp_path):
    p = tmp_path / "get_connection.py"
    p.write_text(FONTE, encoding="utf-8")
    return p


def test_le_pares_por_ast_sem_importar(inv, fonte):
    """O `raise` no topo prova: se o módulo fosse importado, o teste explodiria."""
    pares = inv.ler_pares_fernet(fonte)
    assert pares[("DEV", "SSC")] == {"KEY": b"chave-ssc-dev", "CIPHERTEXT": b"cifra-ssc-dev"}
    assert set(pares) == {("DEV", "SSC"), ("DEV", "MS10"), ("PROD", "SSC")}  # SOZINHA sem par sai


def test_escolhe_sozinho_quando_so_ha_um(inv, fonte):
    assert inv.escolher_par(inv.ler_pares_fernet(fonte), "PRD") == (b"chave-ssc-prd", b"cifra-ssc-prd")


def test_mais_de_um_par_para_e_lista_nomes_sem_valores(inv, fonte):
    with pytest.raises(inv.ErroCredencial) as e:
        inv.escolher_par(inv.ler_pares_fernet(fonte), "D0")
    msg = str(e.value)
    assert "MS10" in msg and "SSC" in msg and "--par" in msg
    assert "chave-" not in msg and "cifra-" not in msg


def test_par_ignora_caixa_e_recusa_inexistente(inv, fonte):
    pares = inv.ler_pares_fernet(fonte)
    assert inv.escolher_par(pares, "d0", par="ms10") == (b"chave-ms10-dev", b"cifra-ms10-dev")
    with pytest.raises(inv.ErroCredencial, match="TRP"):
        inv.escolher_par(pares, "D0", par="TRP")
    with pytest.raises(inv.ErroCredencial, match="D0, HML ou PRD"):
        inv.escolher_par(pares, "XPTO")
