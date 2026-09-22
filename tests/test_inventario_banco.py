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


CONN_SSC = "Server=srv-ssc,1435;Database=SSC;UID=leitor;PWD=s3nh4"


def _decriptar_falso(chave, cifra):
    return {b"chave-ssc-dev": CONN_SSC}[chave]


def test_fonte_com_base_nova(inv, fonte):
    c = inv.resolver_conn({}, fonte, "D0", "SSC", "LegadoCS", None, decriptar=_decriptar_falso)
    assert "Database=LegadoCS" in c.conn_str and "Server=srv-ssc,1435" in c.conn_str
    assert "Encrypt=yes" in c.conn_str and "timeout=30" in c.conn_str
    assert "srv-ssc,1435" in c.origem and "LegadoCS" in c.origem
    assert "s3nh4" not in c.origem


def test_fonte_ganha_da_variavel_e_avisa(inv, fonte):
    env = {"MSS_INVENTARIO_CONN": "Server=outro;PWD=x"}
    c = inv.resolver_conn(env, fonte, "D0", "SSC", None, None, decriptar=_decriptar_falso)
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


def test_porta(inv, fonte):
    c = inv.resolver_conn({}, fonte, "D0", "SSC", None, "1500", decriptar=_decriptar_falso)
    assert "Server=srv-ssc,1500" in c.conn_str


def test_fonte_placeholder(inv, tmp_path):
    p = tmp_path / "get_connection.py"
    p.write_text('DEV_X_KEY = b"<par gerado/copiado>"\nDEV_X_CIPHERTEXT = b"<par gerado/copiado>"\n',
                 encoding="utf-8")
    with pytest.raises(inv.ErroCredencial, match="placeholder"):
        inv.resolver_conn({}, p)


def test_molde_do_kit_nao_e_python_e_erro_e_claro(inv):
    """O próprio templates/get_connection.py tem `DEV_<BASE>_KEY` — não parseia."""
    with pytest.raises(inv.ErroCredencial, match="não consegui ler"):
        inv.resolver_conn({}, REPO / "templates" / "get_connection.py")


def test_fonte_inexistente(inv, tmp_path):
    with pytest.raises(inv.ErroCredencial, match="não encontrado"):
        inv.resolver_conn({}, tmp_path / "nao_existe.py")


def test_fernet_de_verdade(inv, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    chave = fernet.Fernet.generate_key()
    cifra = fernet.Fernet(chave).encrypt(CONN_SSC.encode())
    p = tmp_path / "get_connection.py"
    p.write_text(f"DEV_SSC_KEY = {chave!r}\nDEV_SSC_CIPHERTEXT = {cifra!r}\n", encoding="utf-8")
    c = inv.resolver_conn({}, p, "D0", None, "LegadoCS")
    assert "Database=LegadoCS" in c.conn_str and "PWD=s3nh4" in c.conn_str


def test_par_fernet_errado_da_erro_claro(inv, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    chave_certa = fernet.Fernet.generate_key()
    chave_errada = fernet.Fernet.generate_key()
    cifra = fernet.Fernet(chave_errada).encrypt(CONN_SSC.encode())
    p = tmp_path / "get_connection.py"
    p.write_text(f"DEV_SSC_KEY = {chave_certa!r}\nDEV_SSC_CIPHERTEXT = {cifra!r}\n", encoding="utf-8")
    with pytest.raises(inv.ErroCredencial, match="não consegui decriptar"):
        inv.resolver_conn({}, p)


def test_fonte_nao_utf8_da_erro_claro(inv, tmp_path):
    p = tmp_path / "get_connection.py"
    p.write_bytes(b"DEV_X_KEY = b'a'\n\xff\xfe")
    with pytest.raises(inv.ErroCredencial, match="não consegui ler"):
        inv.resolver_conn({}, p)


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
])
def test_explicar_erro(inv, mensagem, esperado):
    assert esperado in inv.explicar_erro(RuntimeError(mensagem))


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


COLS_MODULOS = ["esquema", "nome", "tipo", "criado", "modificado", "criptografado", "corpo"]


def respostas_base():
    """2 tabelas + 4 módulos: um citado no código (quando o teste cria o .cs), um chamado só por outra
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
             "SELECT Id FROM dbo.Apolice WHERE Numero = @Numero"),
            ("dbo", "FechamentoMensal", "SQL_STORED_PROCEDURE", D1, D2, 0,
             "CREATE PROCEDURE dbo.FechamentoMensal AS EXEC dbo.RecalculaPremio"),
            ("dbo", "RecalculaPremio", "SQL_STORED_PROCEDURE", D1, D1, 0,
             "CREATE PROCEDURE dbo.RecalculaPremio AS SELECT 1"),
            ("dbo", "Cifrada", "SQL_STORED_PROCEDURE", D1, D1, 1, None)]),
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


def test_coleta_base(inv):
    cat = inv.coletar(CursorFalso(inv, respostas_base()))
    assert [t["nome"] for t in cat.dados["tabelas"]] == ["Apolice", "Log"]
    assert any("`dbo.Cifrada` — corpo criptografado" in l for l in cat.lacunas)


def test_teto_para_antes_de_ler_qualquer_coisa(inv):
    cur = CursorFalso(inv, respostas_base())
    with pytest.raises(inv.ErroTeto, match="6 objetos"):
        inv.coletar(cur, max_objetos=5)
    assert cur.executadas == [inv.QUERIES["contagem"]]


def test_opcional_sem_permissao_vira_lacuna(inv):
    cat = inv.coletar(CursorFalso(inv, respostas_base(), falhas=("jobs", "linhas")))
    assert cat.dados["jobs"] == [] and cat.dados["linhas"] == []
    texto = " ".join(cat.lacunas)
    assert "jobs do SQL Agent" in texto and "VIEW DATABASE STATE" in texto


def test_obrigatoria_sem_permissao_derruba(inv):
    with pytest.raises(RuntimeError):
        inv.coletar(CursorFalso(inv, respostas_base(), falhas=("modulos",)))


def test_corpo_nulo_sem_criptografia_e_falta_de_view_definition(inv):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Escondida", "SQL_STORED_PROCEDURE", D1, D1, 0, None)])
    cat = inv.coletar(CursorFalso(inv, r))
    assert any("`dbo.Escondida`" in l and "VIEW DEFINITION" in l for l in cat.lacunas)


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


def test_variavel_recebendo_variavel_nao_e_segredo(inv):
    assert inv.mascarar_segredos("SET @pwd = @parametro") == ("SET @pwd = @parametro", [])


def test_linha_reportada_quando_o_segredo_quebra_linha(inv):
    _, achados = inv.mascarar_segredos("a\nEXEC sp_addlinkedsrvlogin\n 'S', 'false', NULL, 'u', 'Abc123'")
    assert achados == [(3, "senha de linked server (sp_addlinkedsrvlogin)")]


def test_linked_server_posicional_nao_invade_a_instrucao_seguinte(inv):
    corpo = "EXEC sp_addlinkedsrvlogin 'SRV', 'false', NULL\nINSERT INTO t VALUES ('a','b','c','d')"
    assert inv.mascarar_segredos(corpo) == (corpo, [])


@pytest.mark.parametrize("corpo", ["SELECT 'Relatorio -Produto Especial' AS titulo",
                                   "PRINT 'Consulta -Padrao nao encontrada'"])
def test_menos_p_fora_de_linha_de_comando_nao_e_segredo(inv, corpo):
    assert inv.mascarar_segredos(corpo) == (corpo, [])


def test_menos_p_com_bcp_montado_em_duas_linhas(inv):
    corpo, achados = inv.mascarar_segredos("SET @cmd = 'bcp db..t out x.txt -S srv -U u ' +\n'-P Abc123'")
    assert "Abc123" not in corpo and achados == [(2, "senha em linha de comando (-P)")]


def _projeto(raiz, arquivos):
    for rel, texto in arquivos.items():
        p = raiz / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
    return raiz


def _cruzar(inv, proj, respostas=None):
    cat = inv.coletar(CursorFalso(inv, respostas or respostas_base()))
    return inv.cruzar(cat, inv.indexar_codigo(proj, excluir=proj / "docs" / "banco"))


def test_tres_classes(inv, tmp_path):
    proj = _projeto(tmp_path, {"src/ApoliceRepo.cs": 'var cmd = new SqlCommand("[dbo].[ConsultaApolice]", conn);'})
    c = _cruzar(inv, proj)
    assert c["dbo.ConsultaApolice"].classe == inv.CITADO_CODIGO
    assert c["dbo.ConsultaApolice"].ocorrencias == ["src/ApoliceRepo.cs:1"]
    assert c["dbo.RecalculaPremio"].classe == inv.CITADO_BANCO   # só FechamentoMensal chama
    assert c["dbo.FechamentoMensal"].classe == inv.CITADO_BANCO  # só o job chama
    assert c["dbo.Apolice"].classe == inv.CITADO_BANCO           # só a procedure lê
    assert c["dbo.Cifrada"].classe == inv.SEM_CITACAO


@pytest.mark.parametrize("forma", ["ConsultaApolice", "dbo.ConsultaApolice", "[dbo].[ConsultaApolice]",
                                   "exec DBO.CONSULTAAPOLICE"])
def test_formas_do_nome(inv, tmp_path, forma):
    proj = _projeto(tmp_path, {"Dados.vb": f'cmd.CommandText = "{forma}"'})
    assert _cruzar(inv, proj)["dbo.ConsultaApolice"].classe == inv.CITADO_CODIGO


def test_saida_do_inventario_nao_autoconfirma(inv, tmp_path):
    """Os .sql gerados e o banco.md contêm todos os nomes — sem exclusão, tudo pareceria usado."""
    proj = _projeto(tmp_path, {"docs/banco/dbo.Cifrada.sql": "CREATE PROCEDURE dbo.Cifrada AS SELECT 1",
                               "docs/banco.md": "`dbo.Cifrada`", "README.md": "dbo.Cifrada"})
    assert _cruzar(inv, proj)["dbo.Cifrada"].classe == inv.SEM_CITACAO


def test_bin_obj_ignorados(inv, tmp_path):
    proj = _projeto(tmp_path, {"bin/Debug/App.exe.config": "Cifrada", "obj/x.cs": "Cifrada"})
    assert _cruzar(inv, proj)["dbo.Cifrada"].classe == inv.SEM_CITACAO


def test_nome_generico_e_casamento_fraco(inv, tmp_path):
    proj = _projeto(tmp_path, {"Util.cs": "Log.Write(x);"})
    c = _cruzar(inv, proj)["dbo.Log"]
    assert c.classe == inv.CITADO_CODIGO and c.fraco


def test_nome_fora_do_padrao_nao_e_cruzado(inv, tmp_path):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Minha Proc", "SQL_STORED_PROCEDURE", D1, D1, 0, "SELECT 1")])
    assert _cruzar(inv, tmp_path, r)["dbo.Minha Proc"].classe == inv.NAO_CRUZADO


def _gravar(inv, pasta, respostas=None):
    return inv.gravar_corpos(inv.coletar(CursorFalso(inv, respostas or respostas_base())), pasta)


def test_corpos_utf8_bom_com_marca(inv, tmp_path):
    g = _gravar(inv, tmp_path / "banco")
    arq = tmp_path / "banco" / "dbo.ConsultaApolice.sql"
    assert "dbo.ConsultaApolice.sql" in g.gravados and "dbo.Cifrada.sql" not in g.gravados
    assert arq.read_bytes().startswith(b"\xef\xbb\xbf")
    texto = arq.read_text(encoding="utf-8-sig")
    assert texto.startswith(inv.MARCA_SQL)
    assert "WHERE Numero = @Numero" in texto
    assert b"AS\r\nSELECT" in arq.read_bytes()  # CRLF do SQL Server preservado


def test_segredo_mascarado_no_arquivo(inv, tmp_path):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Importa", "SQL_STORED_PROCEDURE", D1, D1, 0,
                                    "CREATE PROCEDURE dbo.Importa AS\nSELECT * FROM OPENROWSET('SQLNCLI','Server=x;PWD=Abc123;','SELECT 1')")])
    g = _gravar(inv, tmp_path / "banco", r)
    texto = (tmp_path / "banco" / "dbo.Importa.sql").read_text(encoding="utf-8-sig")
    assert "Abc123" not in texto and inv.MASCARA in texto and "Segredo removido" in texto
    assert g.segredos == [("dbo.Importa", 2, "senha em conn string")]


def test_remove_so_o_que_e_do_inventario(inv, tmp_path):
    pasta = tmp_path / "banco"
    pasta.mkdir()
    (pasta / "dbo.Sumiu.sql").write_text(inv.MARCA_SQL + "\nSELECT 1", encoding="utf-8-sig")
    (pasta / "script_do_time.sql").write_text("-- script nosso\nSELECT 1", encoding="utf-8")
    g = _gravar(inv, pasta)
    assert g.removidos == ["dbo.Sumiu.sql"] and not (pasta / "dbo.Sumiu.sql").exists()
    assert g.preservados == ["script_do_time.sql"] and (pasta / "script_do_time.sql").exists()


def test_nao_escreve_por_cima_de_sql_do_time_com_o_mesmo_nome(inv, tmp_path):
    """Revisão final C1: a marca guardava só a remoção; a escrita passava por cima."""
    pasta = tmp_path / "banco"
    pasta.mkdir()
    (pasta / "dbo.ConsultaApolice.sql").write_text("-- script do time\nSELECT 1", encoding="utf-8")
    g = _gravar(inv, pasta)
    assert (pasta / "dbo.ConsultaApolice.sql").read_text(encoding="utf-8") == "-- script do time\nSELECT 1"
    assert g.conflitos == ["dbo.ConsultaApolice.sql"] and "dbo.ConsultaApolice.sql" not in g.gravados
    assert "dbo.ConsultaApolice.sql" not in g.preservados  # listado uma vez só, como conflito


def test_rodada_sem_view_definition_nao_apaga_os_corpos_versionados(inv, tmp_path):
    """Revisão final I1: objeto que existe mas veio sem corpo nesta rodada mantém o .sql anterior."""
    pasta = tmp_path / "banco"
    _gravar(inv, pasta)
    r = respostas_base()
    colunas, linhas = r["modulos"]
    r["modulos"] = (colunas, [l[:6] + (None,) for l in linhas])  # login mais fraco: todo corpo NULL
    g = _gravar(inv, pasta, r)
    assert g.removidos == []
    assert (pasta / "dbo.ConsultaApolice.sql").exists()
    assert "dbo.ConsultaApolice.sql" in g.mantidos


def test_renomear_so_na_caixa_nao_perde_o_corpo(inv, tmp_path):
    """Revisão final I2: no NTFS `dbo.X.sql` e `dbo.x.sql` são o mesmo arquivo."""
    pasta = tmp_path / "banco"
    _gravar(inv, pasta)
    r = respostas_base()
    colunas, linhas = r["modulos"]
    r["modulos"] = (colunas, [(l[0], "CONSULTAAPOLICE") + l[2:] if l[1] == "ConsultaApolice" else l
                              for l in linhas])
    g = _gravar(inv, pasta, r)
    nomes = [p.name for p in pasta.iterdir()]
    assert [n for n in nomes if n.casefold() == "dbo.consultaapolice.sql"] == ["dbo.CONSULTAAPOLICE.sql"]
    assert g.removidos == []


def test_nome_de_arquivo_seguro(inv):
    assert inv.nome_arquivo("dbo", "a/b c") == "dbo.a_b_c.sql"


def _md(inv, tmp_path, respostas=None, segredos=()):
    cat = inv.coletar(CursorFalso(inv, respostas or respostas_base()))
    proj = _projeto(tmp_path, {"src/Repo.cs": 'Exec("dbo.ConsultaApolice");'})
    cit = inv.cruzar(cat, inv.indexar_codigo(proj))
    return inv.renderizar_md("LegadoCS", "variável MSS_INVENTARIO_CONN → servidor srv, base Legado",
                             "2026-09-22", cat, cit, list(segredos))


def test_md_marca_e_frase_de_guarda_no_topo_do_cruzamento(inv, tmp_path):
    md = _md(inv, tmp_path)
    assert md.startswith(inv.MARCA_MD)
    secao = md.split("## Cruzamento com o código", 1)[1]
    assert secao.lstrip().startswith(f"> {inv.FRASE_GUARDA}")
    assert '"pode apagar"' in md


def test_md_nunca_traz_corpo_nem_segredo(inv, tmp_path):
    md = _md(inv, tmp_path, segredos=[("dbo.Importa", 2, "senha em conn string")])
    assert "WHERE Numero = @Numero" not in md          # corpo fica só no .sql
    assert "zzz-linked" not in md and "zzz-job" not in md  # origem do linked server e texto do job
    assert "`dbo.Importa` | 2 | senha em conn string" in md


def test_md_conteudo(inv, tmp_path):
    md = _md(inv, tmp_path)
    assert "# Banco do projeto LegadoCS" in md
    assert "18.234" in md or "18234" in md
    assert "`dbo.ConsultaApolice` | citado no código | `src/Repo.cs:1`" in md
    assert "Fechamento" in md and "`dbo.FechamentoMensal`" in md  # job → objeto que ele chama
    assert "`dbo.Cifrada` — corpo criptografado" in md
    assert "Não coberto por desenho" in md
    assert "`banco/dbo.ConsultaApolice.sql`" in md


def test_md_sem_linhas_quando_opcional_falhou(inv, tmp_path):
    cat = inv.coletar(CursorFalso(inv, respostas_base(), falhas=("linhas",)))
    md = inv.renderizar_md("P", "o", "2026-09-22", cat, inv.cruzar(cat, {}), [])
    assert "`dbo.Apolice` — — linhas" in md


class ConexaoFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.fechada = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.fechada = True


ENV_OK = {"MSS_INVENTARIO_CONN": "Server=srv;Database=x;UID=u;PWD=segredo123"}


def test_main_ponta_a_ponta(inv, tmp_path, capsys):
    proj = _projeto(tmp_path / "LegadoCS", {"src/Repo.cs": 'cmd.CommandText = "dbo.ConsultaApolice";'})
    conn = ConexaoFalsa(CursorFalso(inv, respostas_base()))
    vistas = []
    rc = inv.main(["--proj", str(proj), "--base", "Legado"], env=ENV_OK,
                  conectar_fn=lambda s: vistas.append(s) or conn)
    assert rc == 0 and conn.fechada
    assert "Database=Legado" in vistas[0]
    saida = capsys.readouterr()
    assert "segredo123" not in saida.out + saida.err
    assert (proj / "docs" / "banco.md").read_text(encoding="utf-8").startswith(inv.MARCA_MD)
    assert (proj / "docs" / "banco" / "dbo.ConsultaApolice.sql").exists()
    assert "/docs/banco.md" in saida.out  # sugere a linha do .gitignore (não edita)
    assert not (proj / ".gitignore").exists()


def test_proj_ponto_da_nome_ao_titulo(inv, tmp_path, monkeypatch):
    """Caso F-016: Path('.').name é vazio."""
    proj = tmp_path / "LegadoCS"
    proj.mkdir()
    monkeypatch.chdir(proj)
    assert inv.main(["--proj", "."], env=ENV_OK,
                    conectar_fn=lambda s: ConexaoFalsa(CursorFalso(inv, respostas_base()))) == 0
    assert "# Banco do projeto LegadoCS" in (proj / "docs" / "banco.md").read_text(encoding="utf-8")


def test_nao_sobrescreve_banco_md_do_projeto(inv, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "banco.md").write_text("# Anotações do time\n", encoding="utf-8")
    with pytest.raises(inv.ErroSaida, match="não sobrescrevo"):
        inv.gerar(tmp_path, CursorFalso(inv, respostas_base()), "o")
    assert (tmp_path / "docs" / "banco.md").read_text(encoding="utf-8") == "# Anotações do time\n"
    assert not (tmp_path / "docs" / "banco").exists()


def test_teto_nao_grava_nada(inv, tmp_path):
    with pytest.raises(inv.ErroTeto):
        inv.gerar(tmp_path, CursorFalso(inv, respostas_base()), "o", max_objetos=1)
    assert not (tmp_path / "docs").exists()


def test_regeneracao_e_gitignore_ja_ancorado(inv, tmp_path):
    (tmp_path / ".gitignore").write_text("/docs/banco.md\n", encoding="utf-8")
    inv.gerar(tmp_path, CursorFalso(inv, respostas_base()), "o")
    rel = inv.gerar(tmp_path, CursorFalso(inv, respostas_base()), "o")  # 2ª rodada sobrescreve o nosso
    assert rel.linha_gitignore == ""
    assert rel.total_objetos == 6 and len(rel.gravados) == 3


def test_main_sem_credencial(inv, tmp_path, capsys):
    assert inv.main(["--proj", str(tmp_path)], env={}, conectar_fn=lambda s: pytest.fail("conectou")) == 2
    assert "--fonte" in capsys.readouterr().err


def test_main_conexao_recusada(inv, tmp_path, capsys):
    def recusa(_):
        raise RuntimeError("[28000] Login failed for user 'u'. (18456)")
    assert inv.main(["--proj", str(tmp_path)], env=ENV_OK, conectar_fn=recusa) == 3
    err = capsys.readouterr().err
    assert "CREDENCIAL" in err and "segredo123" not in err


def test_gitignore_em_cp1252_nao_derruba_depois_de_gravar(inv, tmp_path):
    """Revisão final I7: o .gitignore era lido sem errors= e estourava com tudo já no disco."""
    (tmp_path / ".gitignore").write_bytes("# configuração\n/docs/banco.md\n".encode("cp1252"))
    rel = inv.gerar(tmp_path, CursorFalso(inv, respostas_base()), "o")
    assert rel.linha_gitignore == ""


def test_gitignore_sem_barra_inicial_tambem_ancora(inv, tmp_path):
    (tmp_path / ".gitignore").write_text("docs/banco.md\n", encoding="utf-8")
    assert inv.gerar(tmp_path, CursorFalso(inv, respostas_base()), "o").linha_gitignore == ""


def test_trigger_dispara_com_a_tabela_nao_vira_sem_citacao(inv, tmp_path):
    """Revisão final I3: ninguém 'chama' trigger — ela dispara com a tabela. Sem isso, toda trigger caía
    em 'sem citação', justo onde legado esconde regra de negócio."""
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS + ["pai"], [("dbo", "TR_Apolice_Audit", "SQL_TRIGGER", D1, D1, 0,
                                             "CREATE TRIGGER dbo.TR_Apolice_Audit ON dbo.Apolice ...", "Apolice")])
    c = _cruzar(inv, tmp_path, r)["dbo.TR_Apolice_Audit"]
    assert c.classe == inv.DISPARA_COM_TABELA and c.ocorrencias == ["dbo.Apolice"]


def test_arquivo_utf16_do_ssms_e_lido(inv, tmp_path):
    """Revisão final I4: 'Generate Scripts' do SSMS salva em UTF-16; lido como UTF-8 vira ruído e o objeto
    sai 'sem citação' — a direção perigosa."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "rotina.sql").write_text("EXEC dbo.Cifrada\r\n", encoding="utf-16")
    assert _cruzar(inv, tmp_path)["dbo.Cifrada"].classe == inv.CITADO_CODIGO


def test_indice_guarda_so_os_nomes_pedidos_e_no_maximo_tres(inv, tmp_path):
    """Revisão final I5: o índice guardava todo token do repo (~1,2 GB num monólito de 2M linhas)."""
    _projeto(tmp_path, {f"src/A{i}.cs": "Cifrada(); outraCoisa();" for i in range(5)})
    indice = inv.indexar_codigo(tmp_path, nomes={"cifrada"})
    assert set(indice) == {"cifrada"} and len(indice["cifrada"]) == 3


@pytest.mark.parametrize("pasta", ["Bin/Debug", "OBJ", "venv/lib", "TestResults"])
def test_pastas_geradas_ignoradas_sem_diferenciar_caixa(inv, tmp_path, pasta):
    _projeto(tmp_path, {f"{pasta}/x.config": "Cifrada"})
    assert _cruzar(inv, tmp_path)["dbo.Cifrada"].classe == inv.SEM_CITACAO


def test_saidas_de_outros_geradores_do_kit_nao_contam(inv, tmp_path):
    _projeto(tmp_path, {"docs/bpmn.html": "Cifrada", "docs/mapa-neural.html": "Cifrada",
                        "docs/anatomia.html": "Cifrada", "docs/bpmn/p.bpmn": "Cifrada"})
    assert _cruzar(inv, tmp_path)["dbo.Cifrada"].classe == inv.SEM_CITACAO
