"""Comportamento do inventário do banco vivo (templates/inventario_banco.py).

Regra dura: SOMENTE-LEITURA e SÓ CATÁLOGO — nenhuma query escreve e nenhuma lê dado de negócio;
credencial reaproveitada por leitura ESTÁTICA (o get_connection.py de outro projeto nunca é
importado); segredo nunca sai; "sem citação" nunca vira "pode apagar"; só mexe em arquivo que tem a
marca do inventário. Testável sem banco: o cursor é falso. Spec: docs/specs/inventario-banco.md

Camadas (2026-11-18, `docs/decisoes.md`): a regra é testada em memória — o texto da fonte entra pelo `ler` do
`resolver_conn`, o código do projeto como pares (caminho, texto) no `indexar_textos`, e a pasta dos .sql como
{nome: é do inventário?} no `plano_dos_corpos`. O disco de verdade (varredura, BOM, renomear só a caixa, não
sobrescrever, o teto que não grava nada, `--proj .`) fica num teste só, numa pasta montada uma vez.
"""
import datetime as dt
import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "inventario_banco.py"
FALSA = REPO.parent / "pasta-que-nao-existe-inventario"          # absoluta, nunca criada


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


@pytest.mark.parametrize("conn, mascarada", [
    ("Server=a;UID=u;PWD=s3nh4", "Server=a;UID=u;PWD=***HIDDEN***"),
    ("Data Source=a;User ID=u;Password=x9;", None),
    ("Server=a;UID=u;PWD={s3n;ha};Database=x", "Server=a;UID=u;PWD=***HIDDEN***;Database=x"),
])
def test_mask_password(inv, conn, mascarada):
    saida = inv.mask_password(conn)
    assert saida == mascarada if mascarada else "x9" not in saida


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


# --------------------------------------------------------------- a credencial: o texto da fonte entra como dado

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
CAMINHO_FONTE = FALSA / "get_connection.py"


def _ler(texto):
    """O `ler` do resolver_conn: a fonte em memória."""
    return lambda caminho: texto


def test_le_pares_por_ast_sem_importar(inv):
    """O `raise` no topo prova: se o texto fosse executado, o teste explodiria."""
    pares = inv.pares_fernet_do_texto(FONTE)
    assert pares[("DEV", "SSC")] == {"KEY": b"chave-ssc-dev", "CIPHERTEXT": b"cifra-ssc-dev"}
    assert set(pares) == {("DEV", "SSC"), ("DEV", "MS10"), ("PROD", "SSC")}  # SOZINHA sem par sai


def test_escolhe_sozinho_quando_so_ha_um(inv):
    assert inv.escolher_par(inv.pares_fernet_do_texto(FONTE), "PRD") == (b"chave-ssc-prd", b"cifra-ssc-prd")


def test_mais_de_um_par_para_e_lista_nomes_sem_valores(inv):
    with pytest.raises(inv.ErroCredencial) as e:
        inv.escolher_par(inv.pares_fernet_do_texto(FONTE), "D0")
    msg = str(e.value)
    assert "MS10" in msg and "SSC" in msg and "--par" in msg
    assert "chave-" not in msg and "cifra-" not in msg


def test_par_ignora_caixa_e_recusa_inexistente(inv):
    pares = inv.pares_fernet_do_texto(FONTE)
    assert inv.escolher_par(pares, "d0", par="ms10") == (b"chave-ms10-dev", b"cifra-ms10-dev")
    with pytest.raises(inv.ErroCredencial, match="TRP"):
        inv.escolher_par(pares, "D0", par="TRP")
    with pytest.raises(inv.ErroCredencial, match="D0, HML ou PRD"):
        inv.escolher_par(pares, "XPTO")


CONN_SSC = "Server=srv-ssc,1435;Database=SSC;UID=leitor;PWD=s3nh4"


def _decriptar_falso(chave, cifra):
    return {b"chave-ssc-dev": CONN_SSC}[chave]


def test_fonte_com_base_nova(inv):
    c = inv.resolver_conn({}, CAMINHO_FONTE, "D0", "SSC", "LegadoCS", None, decriptar=_decriptar_falso,
                          ler=_ler(FONTE))
    assert "Database=LegadoCS" in c.conn_str and "Server=srv-ssc,1435" in c.conn_str
    assert "Encrypt=yes" in c.conn_str and "timeout=30" in c.conn_str
    assert "srv-ssc,1435" in c.origem and "LegadoCS" in c.origem
    assert "s3nh4" not in c.origem


def test_fonte_ganha_da_variavel_e_avisa(inv):
    env = {"MSS_INVENTARIO_CONN": "Server=outro;PWD=x"}
    c = inv.resolver_conn(env, CAMINHO_FONTE, "D0", "SSC", None, None, decriptar=_decriptar_falso, ler=_ler(FONTE))
    assert "srv-ssc" in c.conn_str
    assert any("MSS_INVENTARIO_CONN ignorada" in a for a in c.avisos)


def test_variavel_quando_sem_fonte(inv):
    c = inv.resolver_conn({"MSS_INVENTARIO_CONN": "Server=h;Trusted_Connection=yes"}, base="Legado")
    assert "Database=Legado" in c.conn_str and "variável MSS_INVENTARIO_CONN" in c.origem


def test_sem_nada_para_sem_inventar(inv):
    with pytest.raises(inv.ErroCredencial) as e:
        inv.resolver_conn({})
    msg = str(e.value)
    assert "--fonte" in msg and "MSS_INVENTARIO_CONN" in msg
    assert not re.search(r"\d+\.\d+\.\d+\.\d+", msg), "erro sugeriu um IP"
    assert "MSSQLD0" not in msg and "1433" not in msg


def test_porta(inv):
    c = inv.resolver_conn({}, CAMINHO_FONTE, "D0", "SSC", None, "1500", decriptar=_decriptar_falso, ler=_ler(FONTE))
    assert "Server=srv-ssc,1500" in c.conn_str


def test_fonte_placeholder(inv):
    texto = 'DEV_X_KEY = b"<par gerado/copiado>"\nDEV_X_CIPHERTEXT = b"<par gerado/copiado>"\n'
    with pytest.raises(inv.ErroCredencial, match="placeholder"):
        inv.resolver_conn({}, CAMINHO_FONTE, ler=_ler(texto))


def test_molde_do_kit_nao_e_python_e_erro_e_claro(inv):
    """O próprio templates/get_connection.py tem `DEV_<BASE>_KEY` — não parseia (lido do kit, só leitura)."""
    with pytest.raises(inv.ErroCredencial, match="não consegui ler"):
        inv.resolver_conn({}, REPO / "templates" / "get_connection.py")


def test_fonte_inexistente(inv):
    with pytest.raises(inv.ErroCredencial, match="não encontrado"):
        inv.resolver_conn({}, CAMINHO_FONTE, ler=_ler(None))


def test_fernet_de_verdade(inv):
    fernet = pytest.importorskip("cryptography.fernet")
    chave = fernet.Fernet.generate_key()
    cifra = fernet.Fernet(chave).encrypt(CONN_SSC.encode())
    texto = f"DEV_SSC_KEY = {chave!r}\nDEV_SSC_CIPHERTEXT = {cifra!r}\n"
    c = inv.resolver_conn({}, CAMINHO_FONTE, "D0", None, "LegadoCS", ler=_ler(texto))
    assert "Database=LegadoCS" in c.conn_str and "PWD=s3nh4" in c.conn_str


def test_par_fernet_errado_da_erro_claro(inv):
    fernet = pytest.importorskip("cryptography.fernet")
    chave_certa = fernet.Fernet.generate_key()
    cifra = fernet.Fernet(fernet.Fernet.generate_key()).encrypt(CONN_SSC.encode())
    texto = f"DEV_SSC_KEY = {chave_certa!r}\nDEV_SSC_CIPHERTEXT = {cifra!r}\n"
    with pytest.raises(inv.ErroCredencial, match="não consegui decriptar"):
        inv.resolver_conn({}, CAMINHO_FONTE, ler=_ler(texto))


def test_fonte_nao_utf8_da_erro_claro(inv):
    def ilegivel(_caminho):
        return b"DEV_X_KEY = b'a'\n\xff\xfe".decode("utf-8-sig")
    with pytest.raises(inv.ErroCredencial, match="não consegui ler"):
        inv.resolver_conn({}, CAMINHO_FONTE, ler=ilegivel)


def test_sem_cryptography_nao_culpa_o_par(inv):
    """Revisão final M4: ImportError virava 'chave e cifra não conferem'."""
    def sem_lib(chave, cifra):
        raise ImportError("No module named 'cryptography'")
    with pytest.raises(inv.ErroCredencial, match="cryptography"):
        inv.resolver_conn({}, CAMINHO_FONTE, "D0", "SSC", decriptar=sem_lib, ler=_ler(FONTE))


@pytest.mark.parametrize("mensagem, esperado", [
    ('[42000] [SQL Server]Cannot open database "LegadoCS" requested by the login. The login failed. (4060)',
     "PERMISSÃO"),
    ("[28000] [SQL Server]Login failed for user 'leitor'. (18456)", "CREDENCIAL"),
    ("[08001] [Microsoft][ODBC Driver 17 for SQL Server]Named Pipes Provider: Could not open a connection [53].",
     "REDE"),
    ("[HYT00] [Microsoft][ODBC Driver 17 for SQL Server]Login timeout expired", "REDE"),
    ("[08001] [Microsoft][ODBC Driver 17 for SQL Server]SSL Provider: The client and server cannot communicate, "
     "because they do not possess a common algorithm.", "TLS"),
    ("[08001] [Microsoft][ODBC Driver 18 for SQL Server]SSL Provider: [error:0A000086:SSL routines::certificate "
     "verify failed]", "TLS"),
    ("algo que ninguém previu", "não classificada"),
    ("[42000] The SELECT permission was denied on the object 'sysjobs'", "PERMISSÃO"),
])
def test_explicar_erro(inv, mensagem, esperado):
    assert esperado in inv.explicar_erro(RuntimeError(mensagem))


def test_permissao_negada_no_catalogo_e_permissao(inv):
    msg = inv.explicar_erro(RuntimeError("[42000] The SELECT permission was denied on the object 'sysjobs'"))
    assert msg.startswith("PERMISSÃO")


# --------------------------------------------------------------- a coleta, com o cursor falso

D1, D2 = dt.datetime(2014, 3, 1), dt.datetime(2019, 11, 20)


class CursorFalso:
    """Cursor pyodbc de mentira: responde cada QUERIES[nome] com (colunas, linhas). Nome em `falhas`
    levanta — simula falta de permissão. Query sem resposta devolve vazio."""

    def __init__(self, mod, respostas, falhas=()):
        self._por_sql = {mod.QUERIES[n]: r for n, r in respostas.items()}
        self._falhas = {mod.QUERIES[n] for n in falhas}
        self.executadas = []
        self.description = None
        self._linhas = []

    def execute(self, sql):
        self.executadas.append(sql)
        if sql in self._falhas:
            raise RuntimeError("[42000] The SELECT permission was denied")
        colunas, linhas = self._por_sql.get(sql, (["vazio"], []))
        self.description = [(c,) for c in colunas]
        self._linhas = list(linhas)
        return self

    def fetchall(self):
        return self._linhas


COLS_MODULOS = ["esquema", "nome", "tipo", "criado", "modificado", "criptografado", "corpo", "pai"]


def respostas_base():
    """2 tabelas + 4 módulos: um citado no código (quando o teste traz o .cs), um chamado só por outra
    procedure, um chamado só por job, um criptografado."""
    return {
        "contagem": (["total"], [(6,)]),
        "tabelas": (["esquema", "nome", "criado", "modificado"],
                    [("dbo", "Apolice", D1, D2), ("dbo", "Log", D1, D1)]),
        "colunas": (["esquema", "tabela", "coluna", "tipo", "tamanho", "nulo", "identidade", "padrao"],
                    [("dbo", "Apolice", "Id", "int", 4, False, True, None),
                     ("dbo", "Apolice", "Numero", "varchar", 20, False, False, None),
                     ("dbo", "Log", "Id", "int", 4, False, True, None)]),
        "chaves": (["esquema", "tabela", "chave", "tipo", "coluna"],
                   [("dbo", "Apolice", "PK_Apolice", "PRIMARY_KEY_CONSTRAINT", "Id")]),
        "fks": (["fk", "esquema", "tabela", "coluna", "esquema_ref", "tabela_ref", "coluna_ref"], []),
        "indices": (["esquema", "tabela", "indice", "tipo", "unico", "coluna"],
                    [("dbo", "Apolice", "IX_Apolice_Numero", "NONCLUSTERED", True, "Numero")]),
        "linhas": (["esquema", "tabela", "linhas"], [("dbo", "Apolice", 18234), ("dbo", "Log", 0)]),
        "modulos": (COLS_MODULOS, [
            ("dbo", "ConsultaApolice", "SQL_STORED_PROCEDURE", D1, D2, 0,
             "CREATE PROCEDURE dbo.ConsultaApolice @Numero varchar(20) AS\r\n"
             "SELECT Id FROM dbo.Apolice WHERE Numero = @Numero", None),
            ("dbo", "FechamentoMensal", "SQL_STORED_PROCEDURE", D1, D2, 0,
             "CREATE PROCEDURE dbo.FechamentoMensal AS EXEC dbo.RecalculaPremio", None),
            ("dbo", "RecalculaPremio", "SQL_STORED_PROCEDURE", D1, D1, 0,
             "CREATE PROCEDURE dbo.RecalculaPremio AS SELECT 1", None),
            ("dbo", "Cifrada", "SQL_STORED_PROCEDURE", D1, D1, 1, None, None)]),
        "parametros": (["esquema", "objeto", "parametro", "tipo", "saida"],
                       [("dbo", "ConsultaApolice", "@Numero", "varchar", False)]),
        "dependencias": (["esquema", "objeto", "esquema_ref", "referencia"],
                         [("dbo", "ConsultaApolice", "dbo", "Apolice"),
                          ("dbo", "FechamentoMensal", "dbo", "RecalculaPremio")]),
        "servidores": (["nome", "produto", "provedor", "origem"],
                       [("SRV_SINISTRO", "", "SQLNCLI", "Server=sin;UID=u;PWD=zzz-linked")]),
        "jobs": (["job", "ativo", "passo", "comando"],
                 [("Fechamento", True, "roda", "EXEC dbo.FechamentoMensal -- PWD=zzz-job")]),
    }


def _catalogo(inv, respostas=None, falhas=()):
    return inv.coletar(CursorFalso(inv, respostas or respostas_base(), falhas))


def test_coleta_base(inv):
    cat = _catalogo(inv)
    assert [t["nome"] for t in cat.dados["tabelas"]] == ["Apolice", "Log"]
    assert any("`dbo.Cifrada` — corpo criptografado" in l for l in cat.lacunas)


def test_teto_para_antes_de_ler_qualquer_coisa(inv):
    cur = CursorFalso(inv, respostas_base())
    with pytest.raises(inv.ErroTeto, match="6 objetos"):
        inv.coletar(cur, max_objetos=5)
    assert cur.executadas == [inv.QUERIES["contagem"]]


def test_opcional_sem_permissao_vira_lacuna(inv):
    cat = _catalogo(inv, falhas=("jobs", "linhas"))
    assert cat.dados["jobs"] == [] and cat.dados["linhas"] == []
    texto = " ".join(cat.lacunas)
    assert "jobs do SQL Agent" in texto and "VIEW DATABASE STATE" in texto


def test_obrigatoria_sem_permissao_derruba(inv):
    with pytest.raises(RuntimeError):
        _catalogo(inv, falhas=("modulos",))


def test_corpo_nulo_sem_criptografia_e_falta_de_view_definition(inv):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Escondida", "SQL_STORED_PROCEDURE", D1, D1, 0, None)])
    assert any("`dbo.Escondida`" in l and "VIEW DEFINITION" in l for l in _catalogo(inv, r).lacunas)


# --------------------------------------------------------------- segredo no corpo

@pytest.mark.parametrize("linha, tipo", [
    ("SELECT a FROM OPENROWSET('SQLNCLI', 'Server=x;UID=u;PWD=Abc123;', 'SELECT 1')", "senha em conn string"),
    ("CREATE LOGIN app WITH PASSWORD = 'Abc123'", "senha de LOGIN"),
    ("ALTER LOGIN app WITH PASSWORD = N'Abc123'", "senha de LOGIN"),
    ("EXEC sp_addlinkedsrvlogin @rmtsrvname='SRV', @useself='false', @rmtuser='u', @rmtpassword='Abc123'",
     "senha de linked server (sp_addlinkedsrvlogin)"),
    ("EXEC sp_addlinkedsrvlogin 'SRV', 'false', NULL, 'u', 'Abc123'", "senha de linked server (sp_addlinkedsrvlogin)"),
    ("CREATE DATABASE SCOPED CREDENTIAL c WITH IDENTITY = 'u', SECRET = 'Abc123'", "SECRET de credencial"),
    ("SELECT a FROM OPENROWSET('Microsoft.Jet.OLEDB.4.0', 'C:\\x.mdb';'admin';'Abc123', 'SELECT 1')",
     "senha em OPENROWSET"),
    ("EXEC sp_addlinkedsrvlogin\n    'SRV', 'false', NULL, 'user', 'Abc123'", "senha de linked server (sp_addlinkedsrvlogin)"),
    ("CREATE LOGIN app WITH\nPASSWORD = 'Abc123'", "senha de LOGIN"),
    ("CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Abc123'", "senha (PASSWORD = '...')"),
    ("ALTER LOGIN app WITH PASSWORD = 'New123' OLD_PASSWORD = 'Abc123'", "senha (PASSWORD = '...')"),
    ("DECLARE @pwd varchar(20) = 'Abc123'", "senha em variável"),
    ("SET @senha = N'Abc123'", "senha em variável"),
    ("EXEC master..xp_cmdshell 'bcp db..t out x.txt -S srv -U u -P Abc123'", "senha em linha de comando (-P)"),
    ("EXEC sp_addlogin 'user', 'Abc123'", "senha de sp_addlogin"),
    ("EXEC sp_password 'Old999', 'Abc123', 'user'", "senha de sp_password"),
])
def test_mascara_segredo(inv, linha, tipo):
    corpo, achados = inv.mascarar_segredos(linha)
    assert "Abc123" not in corpo
    assert inv.MASCARA in corpo
    assert tipo in [t for _, t in achados]


def test_corpo_sem_segredo_intacto_e_linha_do_original(inv):
    limpo = "CREATE PROCEDURE p AS\r\nSELECT 1"
    assert inv.mascarar_segredos(limpo) == (limpo, [])
    corpo, achados = inv.mascarar_segredos("a\r\nconn = 'PWD=x9;'\r\nc")
    assert achados == [(2, "senha em conn string")]
    assert corpo.count("\r\n") == 2 and "x9" not in corpo


def test_cabecalho_de_segredo(inv):
    cab = inv.cabecalho_segredo([(12, "senha de LOGIN")], "\n")
    assert "linha 12 do corpo original (senha de LOGIN)" in cab
    assert "não script executável" in cab


def test_sp_password_mascara_as_duas_senhas(inv):
    corpo, _ = inv.mascarar_segredos("EXEC sp_password 'Old999', 'Abc123', 'user'")
    assert "Old999" not in corpo and "Abc123" not in corpo and "'user'" in corpo


@pytest.mark.parametrize("corpo", [
    "SET @pwd = @parametro",                                                     # variável recebendo variável
    "EXEC sp_addlinkedsrvlogin 'SRV', 'false', NULL\nINSERT INTO t VALUES ('a','b','c','d')",   # não invade a seguinte
    "SELECT 'Relatorio -Produto Especial' AS titulo",                            # -P fora de linha de comando
    "PRINT 'Consulta -Padrao nao encontrada'",
])
def test_o_que_nao_e_segredo_fica_intacto(inv, corpo):
    assert inv.mascarar_segredos(corpo) == (corpo, [])


def test_linha_reportada_quando_o_segredo_quebra_linha(inv):
    _, achados = inv.mascarar_segredos("a\nEXEC sp_addlinkedsrvlogin\n 'S', 'false', NULL, 'u', 'Abc123'")
    assert achados == [(3, "senha de linked server (sp_addlinkedsrvlogin)")]


def test_menos_p_com_bcp_montado_em_duas_linhas(inv):
    corpo, achados = inv.mascarar_segredos("SET @cmd = 'bcp db..t out x.txt -S srv -U u ' +\n'-P Abc123'")
    assert "Abc123" not in corpo and achados == [(2, "senha em linha de comando (-P)")]


# --------------------------------------------------------------- cruzamento: o código do projeto entra como dado

def _cruzar(inv, arquivos, respostas=None):
    """`arquivos` = {caminho relativo: texto} — o projeto, em memória."""
    return inv.cruzar(_catalogo(inv, respostas), inv.indexar_textos(arquivos.items(), excluir="docs/banco"))


def test_tres_classes(inv):
    c = _cruzar(inv, {"src/ApoliceRepo.cs": 'var cmd = new SqlCommand("[dbo].[ConsultaApolice]", conn);'})
    assert c["dbo.ConsultaApolice"].classe == inv.CITADO_CODIGO
    assert c["dbo.ConsultaApolice"].ocorrencias == ["src/ApoliceRepo.cs:1"]
    assert c["dbo.RecalculaPremio"].classe == inv.CITADO_BANCO   # só FechamentoMensal chama
    assert c["dbo.FechamentoMensal"].classe == inv.CITADO_BANCO  # só o job chama
    assert c["dbo.Apolice"].classe == inv.CITADO_BANCO           # só a procedure lê
    assert c["dbo.Cifrada"].classe == inv.SEM_CITACAO


@pytest.mark.parametrize("forma", ["ConsultaApolice", "dbo.ConsultaApolice", "[dbo].[ConsultaApolice]",
                                   "exec DBO.CONSULTAAPOLICE"])
def test_formas_do_nome(inv, forma):
    assert _cruzar(inv, {"Dados.vb": f'cmd.CommandText = "{forma}"'})["dbo.ConsultaApolice"].classe == inv.CITADO_CODIGO


@pytest.mark.parametrize("arquivos", [
    # a saída do próprio inventário não autoconfirma: os .sql e o banco.md contêm todos os nomes
    {"docs/banco/dbo.Cifrada.sql": "CREATE PROCEDURE dbo.Cifrada AS SELECT 1", "docs/banco.md": "`dbo.Cifrada`",
     "README.md": "dbo.Cifrada"},
    {"bin/Debug/App.exe.config": "Cifrada", "obj/x.cs": "Cifrada"},
    {"Bin/Debug/x.config": "Cifrada"}, {"OBJ/x.config": "Cifrada"}, {"venv/lib/x.config": "Cifrada"},
    {"TestResults/x.config": "Cifrada"},
    # saídas de outros geradores do kit
    {"docs/bpmn.html": "Cifrada", "docs/mapa-neural.html": "Cifrada", "docs/anatomia.html": "Cifrada",
     "docs/bpmn/p.bpmn": "Cifrada"},
])
def test_o_que_nao_e_codigo_do_projeto_nao_cita(inv, arquivos):
    assert _cruzar(inv, arquivos)["dbo.Cifrada"].classe == inv.SEM_CITACAO


def test_nome_generico_e_casamento_fraco(inv):
    c = _cruzar(inv, {"Util.cs": "Log.Write(x);"})["dbo.Log"]
    assert c.classe == inv.CITADO_CODIGO and c.fraco


def test_nome_fora_do_padrao_nao_e_cruzado(inv):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Minha Proc", "SQL_STORED_PROCEDURE", D1, D1, 0, "SELECT 1")])
    assert _cruzar(inv, {}, r)["dbo.Minha Proc"].classe == inv.NAO_CRUZADO


def test_trigger_dispara_com_a_tabela_nao_vira_sem_citacao(inv):
    """Revisão final I3: ninguém 'chama' trigger — ela dispara com a tabela. Sem isso, toda trigger caía
    em 'sem citação', justo onde legado esconde regra de negócio."""
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "TR_Apolice_Audit", "SQL_TRIGGER", D1, D1, 0,
                                    "CREATE TRIGGER dbo.TR_Apolice_Audit ON dbo.Apolice ...", "Apolice")])
    c = _cruzar(inv, {}, r)["dbo.TR_Apolice_Audit"]
    assert c.classe == inv.DISPARA_COM_TABELA and c.ocorrencias == ["dbo.Apolice"]


def test_arquivo_utf16_do_ssms_e_lido(inv):
    """Revisão final I4: 'Generate Scripts' do SSMS salva em UTF-16; lido como UTF-8 vira ruído e o objeto
    sai 'sem citação' — a direção perigosa."""
    texto = inv.texto_de_bytes("EXEC dbo.Cifrada\r\n".encode("utf-16"))
    assert _cruzar(inv, {"scripts/rotina.sql": texto})["dbo.Cifrada"].classe == inv.CITADO_CODIGO
    assert inv.texto_de_bytes("ação".encode("cp1252")).startswith("a"), "cp1252 cai no replace, sem estourar"


def test_indice_guarda_so_os_nomes_pedidos_e_no_maximo_tres(inv):
    """Revisão final I5: o índice guardava todo token do repo (~1,2 GB num monólito de 2M linhas)."""
    indice = inv.indexar_textos(((f"src/A{i}.cs", "Cifrada(); outraCoisa();") for i in range(5)), nomes={"cifrada"})
    assert set(indice) == {"cifrada"} and len(indice["cifrada"]) == 3


# --------------------------------------------------------------- os .sql: a pasta entra como {nome: é nosso?}

def _plano(inv, respostas=None, existentes=None):
    return inv.plano_dos_corpos(_catalogo(inv, respostas), existentes or {})


def test_corpos_com_marca_e_crlf_preservado(inv):
    plano = _plano(inv)
    escritos = dict(plano.escrever)
    assert plano.gravacao.gravados == list(escritos) and "dbo.Cifrada.sql" not in escritos
    texto = escritos["dbo.ConsultaApolice.sql"]
    assert texto.startswith(inv.MARCA_SQL) and "WHERE Numero = @Numero" in texto
    assert "AS\r\nSELECT" in texto  # CRLF do SQL Server preservado
    assert plano.renomear == [] and plano.remover == []


def test_segredo_mascarado_no_arquivo(inv):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Importa", "SQL_STORED_PROCEDURE", D1, D1, 0,
                                    "CREATE PROCEDURE dbo.Importa AS\nSELECT * FROM OPENROWSET('SQLNCLI','Server=x;PWD=Abc123;','SELECT 1')")])
    plano = _plano(inv, r)
    texto = dict(plano.escrever)["dbo.Importa.sql"]
    assert "Abc123" not in texto and inv.MASCARA in texto and "Segredo removido" in texto
    assert plano.gravacao.segredos == [("dbo.Importa", 2, "senha em conn string")]


def test_remove_so_o_que_e_do_inventario(inv):
    plano = _plano(inv, existentes={"dbo.Sumiu.sql": True, "script_do_time.sql": False})
    assert plano.remover == ["dbo.Sumiu.sql"] and plano.gravacao.removidos == ["dbo.Sumiu.sql"]
    assert plano.gravacao.preservados == ["script_do_time.sql"]


def test_nao_escreve_por_cima_de_sql_do_time_com_o_mesmo_nome(inv):
    """Revisão final C1: a marca guardava só a remoção; a escrita passava por cima."""
    plano = _plano(inv, existentes={"dbo.ConsultaApolice.sql": False})
    g = plano.gravacao
    assert "dbo.ConsultaApolice.sql" not in dict(plano.escrever)
    assert g.conflitos == ["dbo.ConsultaApolice.sql"] and "dbo.ConsultaApolice.sql" not in g.gravados
    assert "dbo.ConsultaApolice.sql" not in g.preservados  # listado uma vez só, como conflito


def test_rodada_sem_view_definition_nao_apaga_os_corpos_versionados(inv):
    """Revisão final I1: objeto que existe mas veio sem corpo nesta rodada mantém o .sql anterior."""
    r = respostas_base()
    colunas, linhas = r["modulos"]
    r["modulos"] = (colunas, [l[:6] + (None,) + l[7:] for l in linhas])  # login mais fraco: todo corpo NULL
    plano = _plano(inv, r, existentes={"dbo.ConsultaApolice.sql": True})
    assert plano.remover == [] and plano.gravacao.mantidos == ["dbo.ConsultaApolice.sql"]


def test_renomear_so_na_caixa_nao_perde_o_corpo(inv):
    """Revisão final I2: no NTFS `dbo.X.sql` e `dbo.x.sql` são o mesmo arquivo."""
    r = respostas_base()
    colunas, linhas = r["modulos"]
    r["modulos"] = (colunas, [(l[0], "CONSULTAAPOLICE") + l[2:] if l[1] == "ConsultaApolice" else l for l in linhas])
    plano = _plano(inv, r, existentes={"dbo.ConsultaApolice.sql": True})
    assert plano.renomear == [("dbo.ConsultaApolice.sql", "dbo.CONSULTAAPOLICE.sql")]
    assert "dbo.CONSULTAAPOLICE.sql" in dict(plano.escrever) and plano.remover == []


def test_colisao_de_caixa_marca_so_o_objeto_nao_gravado(inv):
    """Re-revisão N2: com dbo.X e dbo.x no catálogo, as duas linhas diziam 'não gravado'."""
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "ConsultaApolice", "SQL_STORED_PROCEDURE", D1, D1, 0, "SELECT 1", None),
                                   ("dbo", "CONSULTAAPOLICE", "SQL_STORED_PROCEDURE", D1, D1, 0, "SELECT 2", None)])
    cat = _catalogo(inv, r)
    g = inv.plano_dos_corpos(cat, {}).gravacao
    assert g.conflitos == ["dbo.CONSULTAAPOLICE.sql"]
    md = inv.renderizar_md("P", "o", "2026-09-22", cat, inv.cruzar(cat, {}), g.segredos, g.objetos_em_conflito)
    assert "`banco/dbo.ConsultaApolice.sql`" in md
    linha_2 = next(l for l in md.splitlines() if l.startswith("| `dbo.CONSULTAAPOLICE` | sql_stored_procedure"))
    assert "não gravado" in linha_2 and "time" not in linha_2


def test_nome_de_arquivo_seguro(inv):
    assert inv.nome_arquivo("dbo", "a/b c") == "dbo.a_b_c.sql"


# --------------------------------------------------------------- o banco.md

def _md(inv, respostas=None, segredos=()):
    cat = _catalogo(inv, respostas)
    cit = inv.cruzar(cat, inv.indexar_textos([("src/Repo.cs", 'Exec("dbo.ConsultaApolice");')]))
    return inv.renderizar_md("LegadoCS", "variável MSS_INVENTARIO_CONN → servidor srv, base Legado",
                             "2026-09-22", cat, cit, list(segredos))


def test_md_marca_e_frase_de_guarda_no_topo_do_cruzamento(inv):
    md = _md(inv)
    assert md.startswith(inv.MARCA_MD)
    secao = md.split("## Cruzamento com o código", 1)[1]
    assert secao.lstrip().startswith(f"> {inv.FRASE_GUARDA}")
    assert '"pode apagar"' in md


def test_md_nunca_traz_corpo_nem_segredo(inv):
    md = _md(inv, segredos=[("dbo.Importa", 2, "senha em conn string")])
    assert "WHERE Numero = @Numero" not in md          # corpo fica só no .sql
    assert "zzz-linked" not in md and "zzz-job" not in md  # origem do linked server e texto do job
    assert "`dbo.Importa` | 2 | senha em conn string" in md


def test_md_conteudo(inv):
    md = _md(inv)
    assert "# Banco do projeto LegadoCS" in md
    assert "18.234" in md or "18234" in md
    assert "`dbo.ConsultaApolice` | citado no código | `src/Repo.cs:1`" in md
    assert "Fechamento" in md and "`dbo.FechamentoMensal`" in md  # job → objeto que ele chama
    assert "`dbo.Cifrada` — corpo criptografado" in md
    assert "Não coberto por desenho" in md
    assert "`banco/dbo.ConsultaApolice.sql`" in md


def test_md_sem_linhas_quando_opcional_falhou(inv):
    cat = _catalogo(inv, falhas=("linhas",))
    md = inv.renderizar_md("P", "o", "2026-09-22", cat, inv.cruzar(cat, {}), [])
    assert "`dbo.Apolice` — — linhas" in md


def test_nome_com_barra_vertical_nao_quebra_a_tabela(inv):
    """Revisão final M1: nome entre colchetes pode ter `|` (justo o caso 'não cruzado') e quebrava a tabela."""
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Proc|Velha", "SQL_STORED_PROCEDURE", D1, D1, 0, "SELECT 1")])
    cat = _catalogo(inv, r)
    md = inv.renderizar_md("P", "o", "2026-09-22", cat, inv.cruzar(cat, {}), [])
    linhas = [l for l in md.splitlines() if "Proc" in l and l.startswith("|")]
    assert linhas and all(r"Proc\|Velha" in l for l in linhas)


def test_tipo_da_coluna_traz_o_tamanho(inv):
    """Revisão final M6: varchar(20) aparecia como varchar; nvarchar guarda bytes (divide por 2)."""
    r = respostas_base()
    r["colunas"] = (r["colunas"][0], [("dbo", "Apolice", "Numero", "varchar", 20, False, False, None),
                                      ("dbo", "Apolice", "Nome", "nvarchar", 200, True, False, None),
                                      ("dbo", "Apolice", "Obs", "varchar", -1, True, False, None)])
    cat = _catalogo(inv, r)
    md = inv.renderizar_md("P", "o", "2026-09-22", cat, inv.cruzar(cat, {}), [])
    assert "varchar(20)" in md and "nvarchar(100)" in md and "varchar(max)" in md


@pytest.mark.parametrize("gitignore, falta", [
    (None, "/docs/banco.md"), ("node_modules/\n", "/docs/banco.md"),
    ("/docs/banco.md\n", ""), ("docs/banco.md\n", ""),              # com ou sem a barra inicial
])
def test_linha_do_gitignore(inv, gitignore, falta):
    assert inv.linha_gitignore(gitignore) == falta


def test_banco_md_do_projeto_e_alheio(inv):
    assert inv.md_alheio("# Anotações do time\n")
    assert not inv.md_alheio(inv.MARCA_MD + "\n# Banco do projeto X\n") and not inv.md_alheio(None)


def test_relatorio_sugere_o_gitignore_sem_editar(inv):
    rel = inv.Relatorio(FALSA / "docs" / "banco.md", FALSA / "docs" / "banco", 6, ["a.sql"], [], [], [], [],
                        [("dbo.Importa", 2, "senha em conn string")], [], "/docs/banco.md")
    texto = inv.relatorio_texto(rel)
    assert "/docs/banco.md" in texto and "pergunte ao owner" in texto
    assert "dbo.Importa linha 2 (senha em conn string)" in texto


# --------------------------------------------------------------- o main, sem chegar a gravar

class ConexaoFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.fechada = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.fechada = True


ENV_OK = {"MSS_INVENTARIO_CONN": "Server=srv;Database=x;UID=u;PWD=segredo123"}
EXISTENTE = str(REPO)          # pasta que existe; nenhum destes testes chega a gravar nela


def test_main_sem_credencial(inv, capsys):
    assert inv.main(["--proj", EXISTENTE], env={}, conectar_fn=lambda s: pytest.fail("conectou")) == 2
    assert "--fonte" in capsys.readouterr().err


def test_main_conexao_recusada(inv, capsys):
    def recusa(_):
        raise RuntimeError("[28000] Login failed for user 'u'. (18456)")
    assert inv.main(["--proj", EXISTENTE], env=ENV_OK, conectar_fn=recusa) == 3
    err = capsys.readouterr().err
    assert "CREDENCIAL" in err and "segredo123" not in err


def test_main_query_obrigatoria_negada_sai_limpo(inv, capsys):
    """Revisão final I6: falha fora de ErroTeto/ErroSaida escapava como traceback. A query cai antes de gravar."""
    conn = ConexaoFalsa(CursorFalso(inv, respostas_base(), falhas=("modulos",)))
    assert inv.main(["--proj", EXISTENTE, "--out", str(FALSA)], env=ENV_OK, conectar_fn=lambda s: conn) == 5
    err = capsys.readouterr().err
    assert "PERMISSÃO" in err and "Traceback" not in err and conn.fechada
    assert not FALSA.exists()


def test_main_proj_inexistente_nao_cria_pasta(inv, capsys):
    """Revisão final I8: --proj digitado errado criava a árvore e saía 0."""
    alvo = FALSA / "typo" / "proj"
    assert inv.main(["--proj", str(alvo)], env=ENV_OK, conectar_fn=lambda s: pytest.fail("conectou")) == 2
    assert not alvo.exists() and "--proj" in capsys.readouterr().err


def test_porta_nao_numerica_e_recusada(inv):
    with pytest.raises(SystemExit):
        inv.main(["--proj", EXISTENTE, "--porta", "abc"], env=ENV_OK, conectar_fn=lambda s: pytest.fail("conectou"))


def test_erro_de_disco_nao_vira_permissao_do_banco(inv, monkeypatch, capsys):
    """Re-revisão N1: PermissionError do disco ('Permission denied') caía no ramo de permissão do banco e
    mandava o owner pedir VIEW DEFINITION — ação errada."""
    def disco_bloqueado(*a, **k):
        raise PermissionError(13, "Permission denied", str(FALSA / "docs" / "banco.md"))
    monkeypatch.setattr(inv, "gerar", disco_bloqueado)
    conn = ConexaoFalsa(CursorFalso(inv, respostas_base()))
    assert inv.main(["--proj", EXISTENTE], env=ENV_OK, conectar_fn=lambda s: conn) == 5
    err = capsys.readouterr().err
    assert "DISCO" in err and "VIEW DEFINITION" not in err and conn.fechada


# --------------------------------------------------------------- o disco de verdade (pasta montada uma vez)

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("inventario_banco")
    legado = base / "LegadoCS"
    (legado / "src").mkdir(parents=True)
    (legado / "src" / "Repo.cs").write_text('cmd.CommandText = "dbo.ConsultaApolice";', encoding="utf-8")
    (legado / "scripts").mkdir()
    (legado / "scripts" / "rotina.sql").write_text("EXEC dbo.RecalculaPremio\r\n", encoding="utf-16")
    (legado / "bin").mkdir()
    (legado / "bin" / "App.config").write_text("dbo.Cifrada", encoding="utf-8")
    (legado / ".gitignore").write_bytes("# configuração\n/docs/banco.md\n".encode("cp1252"))
    alheio = base / "alheio"
    (alheio / "docs").mkdir(parents=True)
    (alheio / "docs" / "banco.md").write_text("# Anotações do time\n", encoding="utf-8")
    (base / "get_connection.py").write_text(FONTE, encoding="utf-8")
    return base


def test_disco_de_ponta_a_ponta(inv, pasta, monkeypatch, capsys):
    legado, alheio = pasta / "LegadoCS", pasta / "alheio"
    # a fonte lida do disco, e a que não existe
    c = inv.resolver_conn({}, pasta / "get_connection.py", "D0", "SSC", decriptar=_decriptar_falso)
    assert "srv-ssc" in c.conn_str
    with pytest.raises(inv.ErroCredencial, match="não encontrado"):
        inv.resolver_conn({}, pasta / "nao_existe.py")
    # 1ª rodada pelo main, com `--proj .` (caso F-016: Path('.').name é vazio)
    monkeypatch.chdir(legado)
    conn = ConexaoFalsa(CursorFalso(inv, respostas_base()))
    vistas = []
    assert inv.main(["--proj", ".", "--base", "Legado"], env=ENV_OK,
                    conectar_fn=lambda s: vistas.append(s) or conn) == 0
    assert conn.fechada and "Database=Legado" in vistas[0]
    saida = capsys.readouterr()
    assert "segredo123" not in saida.out + saida.err
    assert "falta no .gitignore" not in saida.out, "o .gitignore em cp1252 já ancora a saída"
    md = (legado / "docs" / "banco.md").read_text(encoding="utf-8")
    assert md.startswith(inv.MARCA_MD) and "# Banco do projeto LegadoCS" in md
    assert "`dbo.ConsultaApolice` | citado no código | `src/Repo.cs:1`" in md
    assert "`dbo.RecalculaPremio` | citado no código | `scripts/rotina.sql:1`" in md, "UTF-16 do SSMS não foi lido"
    assert "`dbo.Cifrada` | sem citação" in md, "a pasta bin/ entrou na varredura"
    sql = legado / "docs" / "banco" / "dbo.ConsultaApolice.sql"
    assert sql.read_bytes().startswith(b"\xef\xbb\xbf") and b"AS\r\nSELECT" in sql.read_bytes()
    # 2ª rodada: renomeado só na caixa, um .sql nosso que sumiu e um do time
    banco = legado / "docs" / "banco"
    (banco / "dbo.Sumiu.sql").write_text(inv.MARCA_SQL + "\nSELECT 1", encoding="utf-8-sig")
    (banco / "script_do_time.sql").write_text("-- script nosso\nSELECT 1", encoding="utf-8")
    r = respostas_base()
    colunas, linhas = r["modulos"]
    r["modulos"] = (colunas, [(l[0], "CONSULTAAPOLICE") + l[2:] if l[1] == "ConsultaApolice" else l for l in linhas])
    rel = inv.gerar(legado, CursorFalso(inv, r), "o")
    nomes = sorted(p.name for p in banco.iterdir())
    assert [n for n in nomes if n.casefold() == "dbo.consultaapolice.sql"] == ["dbo.CONSULTAAPOLICE.sql"]
    assert "dbo.Sumiu.sql" not in nomes and "script_do_time.sql" in nomes
    assert rel.linha_gitignore == "" and rel.total_objetos == 6 and len(rel.gravados) == 3
    # o banco.md do projeto não é sobrescrito; o teto não grava nada
    with pytest.raises(inv.ErroSaida, match="não sobrescrevo"):
        inv.gerar(alheio, CursorFalso(inv, respostas_base()), "o")
    assert (alheio / "docs" / "banco.md").read_text(encoding="utf-8") == "# Anotações do time\n"
    assert not (alheio / "docs" / "banco").exists()
    with pytest.raises(inv.ErroTeto):
        inv.gerar(alheio, CursorFalso(inv, respostas_base()), "o", out=pasta / "teto", max_objetos=1)
    assert not (pasta / "teto").exists()
