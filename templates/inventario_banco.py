"""Inventário do banco vivo (SQL Server) — o que a `analise` não alcança lendo o repositório.

Gerador do kit mss-spec (irmão de mapa_neural.py, anatomia.py e bpmn.py). Conecta SOMENTE-LEITURA,
lê o CATÁLOGO (nunca dado de negócio), cruza os nomes dos objetos com o código do projeto e grava:

- docs/banco.md                      retrato em texto, pro assistente — FORA do git (/docs/banco.md)
- docs/banco/<esquema>.<objeto>.sql  corpo de cada procedure/function/view/trigger — VERSIONADO,
                                     UTF-8 com BOM, segredo mascarado antes de gravar

Credencial (para no primeiro que resolver): --fonte <get_connection.py de projeto MSIG>, lido por
`ast` — o módulo NÃO é importado nem executado — + --ambiente/--par/--base/--porta; senão a variável
MSS_INVENTARIO_CONN; senão erro que diz o que faltou. Nunca inventa host, porta ou base.

Só mexe em arquivo com a marca do inventário (brownfield). Spec: docs/specs/inventario-banco.md
"""
import argparse
import ast
import bisect
import datetime as dt
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

VARIAVEL_CONN = "MSS_INVENTARIO_CONN"
AMBIENTES = {"D0": "DEV", "HML": "HML", "PRD": "PROD"}
MAX_OBJETOS_PADRAO = 2000
MASCARA = "***REMOVIDO PELO INVENTARIO***"
MARCA_MD = "<!-- [inventario-banco] retrato gerado — regenerável, fora do git. Não edite à mão. -->"
MARCA_SQL = "-- [inventario-banco] corpo extraído do catálogo — regenerável; não edite à mão."
FRASE_GUARDA = ('**"Sem citação" não significa "pode apagar"** — significa "não encontrei citação '
                'textual". Nome montado em runtime não aparece nesta busca.')


# ------------------------------------------------------------------------------------ queries
# SOMENTE catálogo. Testes travam: nenhuma escrita, nenhum FROM fora de sys./msdb.dbo.sys/INFORMATION_SCHEMA.
QUERIES = {
    "contagem": """
SELECT COUNT(*) AS total FROM sys.objects
WHERE type IN ('U', 'V', 'P', 'FN', 'IF', 'TF', 'TR') AND is_ms_shipped = 0""",
    "tabelas": """
SELECT s.name AS esquema, t.name AS nome, t.create_date AS criado, t.modify_date AS modificado
FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
ORDER BY s.name, t.name""",
    "colunas": """
SELECT s.name AS esquema, t.name AS tabela, c.name AS coluna, ty.name AS tipo,
       c.max_length AS tamanho, c.is_nullable AS nulo, c.is_identity AS identidade,
       dc.definition AS padrao
FROM sys.columns c
JOIN sys.tables t ON t.object_id = c.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints dc ON dc.object_id = c.default_object_id
ORDER BY s.name, t.name, c.column_id""",
    "chaves": """
SELECT s.name AS esquema, t.name AS tabela, k.name AS chave, k.type_desc AS tipo, c.name AS coluna
FROM sys.key_constraints k
JOIN sys.tables t ON t.object_id = k.parent_object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.index_columns ic ON ic.object_id = k.parent_object_id AND ic.index_id = k.unique_index_id
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
ORDER BY s.name, t.name, k.name, ic.key_ordinal""",
    "fks": """
SELECT fk.name AS fk, sp.name AS esquema, tp.name AS tabela, cp.name AS coluna,
       sr.name AS esquema_ref, tr.name AS tabela_ref, cr.name AS coluna_ref
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
JOIN sys.schemas sp ON sp.schema_id = tp.schema_id
JOIN sys.columns cp ON cp.object_id = fkc.parent_object_id AND cp.column_id = fkc.parent_column_id
JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
JOIN sys.schemas sr ON sr.schema_id = tr.schema_id
JOIN sys.columns cr ON cr.object_id = fkc.referenced_object_id AND cr.column_id = fkc.referenced_column_id
ORDER BY sp.name, tp.name, fk.name""",
    "indices": """
SELECT s.name AS esquema, t.name AS tabela, i.name AS indice, i.type_desc AS tipo,
       i.is_unique AS unico, c.name AS coluna
FROM sys.indexes i
JOIN sys.tables t ON t.object_id = i.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE i.name IS NOT NULL AND ic.is_included_column = 0
ORDER BY s.name, t.name, i.name, ic.key_ordinal""",
    "linhas": """
SELECT s.name AS esquema, t.name AS tabela, SUM(p.row_count) AS linhas
FROM sys.dm_db_partition_stats p
JOIN sys.tables t ON t.object_id = p.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE p.index_id IN (0, 1)
GROUP BY s.name, t.name""",
    "modulos": """
SELECT s.name AS esquema, o.name AS nome, o.type_desc AS tipo,
       o.create_date AS criado, o.modify_date AS modificado,
       OBJECTPROPERTY(o.object_id, 'IsEncrypted') AS criptografado, m.definition AS corpo,
       OBJECT_NAME(o.parent_object_id) AS pai
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
LEFT JOIN sys.sql_modules m ON m.object_id = o.object_id
WHERE o.type IN ('P', 'FN', 'IF', 'TF', 'V', 'TR') AND o.is_ms_shipped = 0
ORDER BY o.type_desc, s.name, o.name""",
    "parametros": """
SELECT s.name AS esquema, o.name AS objeto, p.name AS parametro, ty.name AS tipo,
       p.is_output AS saida
FROM sys.parameters p
JOIN sys.objects o ON o.object_id = p.object_id
JOIN sys.schemas s ON s.schema_id = o.schema_id
JOIN sys.types ty ON ty.user_type_id = p.user_type_id
WHERE o.is_ms_shipped = 0 AND p.parameter_id > 0
ORDER BY s.name, o.name, p.parameter_id""",
    "dependencias": """
SELECT DISTINCT sr.name AS esquema, o.name AS objeto, d.referenced_schema_name AS esquema_ref,
       d.referenced_entity_name AS referencia
FROM sys.sql_expression_dependencies d
JOIN sys.objects o ON o.object_id = d.referencing_id
JOIN sys.schemas sr ON sr.schema_id = o.schema_id
WHERE d.referenced_entity_name IS NOT NULL
ORDER BY esquema, objeto""",
    "servidores": """
SELECT name AS nome, product AS produto, provider AS provedor, data_source AS origem
FROM sys.servers WHERE is_linked = 1""",
    "jobs": """
SELECT j.name AS job, j.enabled AS ativo, st.step_name AS passo, st.command AS comando
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps st ON st.job_id = j.job_id
WHERE st.database_name = DB_NAME()
ORDER BY j.name, st.step_id""",
}

# Falha nestas (permissão) vira LACUNA nomeada, não derruba a geração (falha aberta).
OPCIONAIS = ("linhas", "servidores", "jobs")
DESCRICAO_OPCIONAL = {
    "linhas": "contagem de linhas (sys.dm_db_partition_stats exige VIEW DATABASE STATE)",
    "servidores": "linked servers (sys.servers)",
    "jobs": "jobs do SQL Agent (msdb)",
}


def _executar(cursor, sql):
    """Único ponto que executa SQL no módulo (teste trava) — devolve list[dict] pelos aliases."""
    cursor.execute(sql)
    nomes = [d[0] for d in cursor.description]
    return [dict(zip(nomes, linha)) for linha in cursor.fetchall()]


# --------------------------------------------------------------------------------- conn string
def _partes_conn(conn_str):
    """Divide a conn string em ';', mas ignora ';' dentro de chaves `{...}` (valor ODBC quotado)."""
    partes = []
    atual = []
    profundidade = 0
    for ch in conn_str:
        if ch == "{":
            profundidade += 1
            atual.append(ch)
        elif ch == "}":
            profundidade = max(0, profundidade - 1)
            atual.append(ch)
        elif ch == ";" and profundidade == 0:
            partes.append("".join(atual))
            atual = []
        else:
            atual.append(ch)
    partes.append("".join(atual))
    return partes


def mask_password(conn_str):
    """Mascara a senha na conn string. Cópia do templates/get_connection.py — aquele arquivo é MOLDE
    com placeholders (`DEV_<BASE>_KEY`), não é Python importável."""
    partes = []
    for parte in _partes_conn(conn_str):
        if "=" in parte:
            chave, _ = parte.split("=", 1)
            if chave.strip().lower() in ("pwd", "password"):
                partes.append(f"{chave}=***HIDDEN***")
            else:
                partes.append(parte)
        elif parte.strip():
            partes.append(parte)
    return ";".join(partes)


_RE_BASE = re.compile(r"(?i)\b(Database|Initial Catalog)\s*=\s*[^;]*")


def trocar_base(conn_str, base):
    """Troca a base (Database= ou Initial Catalog=); acrescenta Database= se não houver."""
    if _RE_BASE.search(conn_str):
        return _RE_BASE.sub(lambda m: f"{m.group(1)}={base}", conn_str)
    return conn_str.rstrip(";") + f";Database={base}"


def trocar_porta(conn_str, porta):
    """Sobrescreve a porta do servidor (host,porta), mantendo o host — mesma regra do molde."""
    return re.sub(r"(?i)((?:Server|Data Source)\s*=\s*[^;,]+)(?:,\d+)?", rf"\g<1>,{porta}", conn_str, count=1)


def servidor_da_conn(conn_str):
    m = re.search(r"(?i)\b(?:Server|Data Source)\s*=\s*([^;]*)", conn_str)
    return m.group(1).strip() if m else None


def base_da_conn(conn_str):
    m = re.search(r"(?i)\b(?:Database|Initial Catalog)\s*=\s*([^;]*)", conn_str)
    return m.group(1).strip() if m else None


def _completar(conn_str):
    """Mesmo acabamento do _build_conn_str do molde: TLS e timeout — o que já conecta, conecta igual."""
    conn_str = conn_str.rstrip(";")
    if "encrypt" not in conn_str.lower():
        conn_str += ";Encrypt=yes;TrustServerCertificate=yes"
    if "timeout" not in conn_str.lower():
        conn_str += ";timeout=30"
    return conn_str


# ---------------------------------------------------------------------------------- credencial
class ErroCredencial(Exception):
    """Credencial não resolvida — a mensagem diz o que faltou, nunca contém segredo."""


# Convenção do molde templates/get_connection.py: <DEV|HML|PROD>_<BASE>_<KEY|CIPHERTEXT>.
_RE_PAR = re.compile(r"^(DEV|HML|PROD)_(\w+?)_(KEY|CIPHERTEXT)$")


def ler_pares_fernet(fonte):
    """{(PREFIXO, BASE): {"KEY": b"..", "CIPHERTEXT": b".."}} lidos por `ast`.

    O arquivo é PARSEADO, nunca importado: o get_connection.py de outro projeto não roda aqui. Só
    atribuições de topo com literal str/bytes entram; par incompleto (sem KEY ou sem CIPHERTEXT) sai."""
    arvore = ast.parse(Path(fonte).read_text(encoding="utf-8-sig"))
    pares = {}
    for no in arvore.body:
        if isinstance(no, ast.Assign) and len(no.targets) == 1:
            alvo, valor_no = no.targets[0], no.value
        elif isinstance(no, ast.AnnAssign) and no.value is not None:
            alvo, valor_no = no.target, no.value
        else:
            continue
        if not isinstance(alvo, ast.Name):
            continue
        m = _RE_PAR.match(alvo.id)
        if not m:
            continue
        try:
            valor = ast.literal_eval(valor_no)
        except (ValueError, SyntaxError):
            continue
        if isinstance(valor, str):
            valor = valor.encode()
        if isinstance(valor, bytes):
            pares.setdefault((m.group(1), m.group(2)), {})[m.group(3)] = valor
    return {k: v for k, v in pares.items() if "KEY" in v and "CIPHERTEXT" in v}


def escolher_par(pares, ambiente, par=None):
    """(KEY, CIPHERTEXT) do ambiente. Mais de uma base e sem --par → para e lista os NOMES."""
    prefixo = AMBIENTES.get(ambiente.strip().upper())
    if prefixo is None:
        raise ErroCredencial(f"--ambiente inválido: {ambiente!r} — use D0, HML ou PRD.")
    bases = sorted(b for (p, b) in pares if p == prefixo)
    if not bases:
        raise ErroCredencial(f"a fonte não tem par {prefixo}_<BASE>_KEY/CIPHERTEXT para o ambiente {ambiente}.")
    if par is None:
        if len(bases) > 1:
            raise ErroCredencial(
                f"a fonte tem mais de um par para {ambiente}: {', '.join(bases)} — diga qual com "
                "--par <BASE> (a base nova está no mesmo servidor de qual delas?).")
        escolhida = bases[0]
    else:
        escolhida = {b.upper(): b for b in bases}.get(par.strip().upper())
        if escolhida is None:
            raise ErroCredencial(f"--par {par!r} não existe na fonte para {ambiente}; disponíveis: {', '.join(bases)}.")
    entrada = pares[(prefixo, escolhida)]
    return entrada["KEY"], entrada["CIPHERTEXT"]


@dataclass
class Conexao:
    conn_str: str
    origem: str  # pro relatório: de onde veio + servidor + base — NUNCA senha
    avisos: list = field(default_factory=list)


def decriptar_fernet(chave, cifra):
    from cryptography.fernet import Fernet  # import tardio: o módulo carrega sem cryptography
    return Fernet(chave).decrypt(cifra).decode()


def resolver_conn(env, fonte=None, ambiente="D0", par=None, base=None, porta=None, decriptar=decriptar_fernet):
    """--fonte (par Fernet reaproveitado) > MSS_INVENTARIO_CONN > erro que diz o que faltou."""
    avisos = []
    if fonte:
        caminho = Path(fonte)
        if env.get(VARIAVEL_CONN):
            avisos.append(f"{VARIAVEL_CONN} ignorada: --fonte foi passado (a flag é a intenção mais específica).")
        if not caminho.is_file():
            raise ErroCredencial(f"--fonte não encontrado: {caminho}")
        try:
            pares = ler_pares_fernet(caminho)
        except SyntaxError as e:
            raise ErroCredencial(
                f"não consegui ler {caminho} como Python ({e.msg}, linha {e.lineno}) — aponte o "
                "get_connection.py de um projeto que conecta de verdade, não o molde do kit.") from None
        except (UnicodeDecodeError, OSError) as e:
            raise ErroCredencial(f"não consegui ler {caminho} como Python ({type(e).__name__}) — aponte o "
                                  "get_connection.py de um projeto que conecta de verdade.") from None
        chave, cifra = escolher_par(pares, ambiente, par)
        if b"<" in chave or b"<" in cifra:
            raise ErroCredencial(f"o par em {caminho} ainda é placeholder — aponte um projeto que conecta de verdade.")
        try:
            conn = decriptar(chave, cifra)
        except ImportError:
            raise ErroCredencial("falta o pacote `cryptography` pra decriptar o par "
                                 "(pip install cryptography) — o par em si não foi testado.") from None
        except Exception:
            raise ErroCredencial(f"não consegui decriptar o par em {caminho} — chave e cifra não conferem "
                                  "(par copiado pela metade ou de ambientes diferentes?).") from None
        origem = f"par Fernet {AMBIENTES[ambiente.strip().upper()]} de {caminho}"
    elif env.get(VARIAVEL_CONN):
        conn = env[VARIAVEL_CONN]
        origem = f"variável {VARIAVEL_CONN}"
    else:
        raise ErroCredencial(
            "sem credencial. Passe --fonte <get_connection.py de um projeto MSIG que alcança o servidor> "
            f"--ambiente D0 --base <nome da base>, ou defina {VARIAVEL_CONN} com a conn string. "
            "O inventário não chuta host, porta nem base.")
    if base:
        conn = trocar_base(conn, base)
    if porta:
        conn = trocar_porta(conn, porta)
    conn = _completar(conn)
    servidor = servidor_da_conn(conn) or "(servidor não declarado na conn string)"
    nome_base = base_da_conn(conn) or "(base padrão do login)"
    return Conexao(conn, f"{origem} → servidor {servidor}, base {nome_base}", avisos)


# --------------------------------------------------------------------------------------- erro
def explicar_erro(exc):
    """Traduz a falha de conexão pro owner. Ordem importa: o 4060 também diz 'login failed'."""
    msg = str(exc)
    baixo = msg.lower()
    if "4060" in msg or "cannot open database" in baixo:
        return ("PERMISSÃO: o login entrou no servidor mas não abre esta base — falta acesso do login à "
                "base (usuário/GRANT). Conserto do owner, não do kit.")
    if "18456" in msg or "login failed" in baixo:
        return "CREDENCIAL: o servidor recusou o login (usuário/senha). Confira o par ou a variável usada."
    if "permission" in baixo and "denied" in baixo:
        return ("PERMISSÃO: o login não pode ler parte do catálogo desta base (falta VIEW DEFINITION ou "
                "leitura nas views de sistema). Peça a permissão ou use outro login — conserto do owner.")
    if "ssl provider" in baixo or "certificate" in baixo or "certificado" in baixo:
        return ("TLS: o servidor respondeu, mas a negociação de criptografia falhou (SQL Server antigo sem "
                "TLS 1.2, ou certificado não confiável). Não é host/porta nem senha — é a criptografia da "
                "conexão (Encrypt/TrustServerCertificate, ou o TLS do servidor).")
    if any(s in baixo for s in ("08001", "hyt00", "timeout", "timed out", "[53]", "(53)",
                                "network-related", "tcp provider")):
        return ("REDE: o servidor não respondeu (erro 53/timeout). Fora da rede corporativa nada responde; "
                "confira host e porta (--porta). Isso não é credencial.")
    return f"falha não classificada ({type(exc).__name__}): {mask_password(msg)[:200]}"


# -------------------------------------------------------------------------------------- coleta
class ErroTeto(Exception):
    """Catálogo acima de --max-objetos: para antes de ler corpo e antes de gravar qualquer coisa."""


@dataclass
class Catalogo:
    dados: dict  # nome da query -> list[dict]
    lacunas: list


def coletar(cursor, max_objetos=MAX_OBJETOS_PADRAO):
    total = _executar(cursor, QUERIES["contagem"])[0]["total"]
    if total > max_objetos:
        raise ErroTeto(f"a base tem {total} objetos (teto --max-objetos {max_objetos}). Nada foi gravado. "
                       "Se é isso mesmo, rode de novo com --max-objetos maior.")
    dados, lacunas = {}, []
    for nome, sql in QUERIES.items():
        if nome == "contagem":
            continue
        try:
            dados[nome] = _executar(cursor, sql)
        except Exception as e:
            if nome not in OPCIONAIS:
                raise
            dados[nome] = []
            lacunas.append(f"{DESCRICAO_OPCIONAL[nome]} — não lido ({type(e).__name__}: sem permissão ou indisponível)")
    for m in dados["modulos"]:
        if m["corpo"] is None:
            motivo = ("corpo criptografado (WITH ENCRYPTION), não extraído" if m["criptografado"]
                      else "corpo invisível ao login (falta VIEW DEFINITION), não extraído")
            lacunas.append(f"`{m['esquema']}.{m['nome']}` — {motivo}")
    return Catalogo(dados, lacunas)


# ------------------------------------------------------------------------------------- segredo
# Varre o corpo INTEIRO, não linha a linha: o prefixo pode quebrar linha (`EXEC sp_addlinkedsrvlogin`
# e os argumentos embaixo). O VALOR nunca atravessa linha, então mascarar não muda a contagem de
# linhas. Ordem importa: os padrões específicos vêm primeiro (dão o tipo certo); os genéricos pulam
# valor já mascarado. Falso positivo é aceitável; falso negativo vai pro git pra sempre.
# Os genéricos têm que ficar DEPOIS dos específicos: a checagem de "já mascarado" depende dessa ordem.
_V = r"N?'[^'\n]*'"
_ARG = r"(?:N?'[^'\n]*'|NULL|\w+)"  # argumento posicional: literal, NULL ou identificador
_RE_LINHA_DE_COMANDO = re.compile(r"(?i)\b(?:bcp|sqlcmd|osql|isql|xp_cmdshell)\b")
_JANELA_CONTEXTO = 400  # chars antes do -P onde o comando tem que aparecer (comando montado em 2+ linhas)
_PADROES_SEGREDO = (
    (re.compile(rf"(?i)(\bwith\s+password\s*=\s*)({_V})"), "senha de LOGIN", None),
    (re.compile(rf"(?i)(@rmtpassword\s*=\s*)({_V})"), "senha de linked server (sp_addlinkedsrvlogin)", None),
    (re.compile(rf"(?i)(\bsp_addlinkedsrvlogin\s+(?:{_ARG}\s*,\s*){{4}})({_V})"),
     "senha de linked server (sp_addlinkedsrvlogin)", None),
    (re.compile(rf"(?i)(\bsp_addlogin\b\s*{_V}\s*,\s*)({_V})"), "senha de sp_addlogin", None),
    (re.compile(rf"(?i)(\bsp_password\b\s*)({_V})"), "senha de sp_password", None),
    (re.compile(rf"(?i)(\bsp_password\b\s*(?:{_V}|NULL)\s*,\s*)({_V})"), "senha de sp_password", None),
    (re.compile(rf"(?i)(\bsecret\s*=\s*)({_V})"), "SECRET de credencial", None),
    (re.compile(rf"(?i)(\bidentity\s*=\s*)({_V})"), "IDENTITY de credencial", None),
    (re.compile(rf"(?i)(\bopenrowset\s*\(\s*{_V}\s*,\s*{_V}\s*;\s*{_V}\s*;\s*)({_V})"), "senha em OPENROWSET", None),
    (re.compile(rf"(?i)(@(?:senha|pwd|passwd|password|psw)\w*[^=\n']*=\s*)({_V})"), "senha em variável", None),
    (re.compile(rf"(?i)(password\s*=\s*)({_V})"), "senha (PASSWORD = '...')", None),
    (re.compile(r"""(?m)((?:^|[\s'"])-P\s*)("[^"\n]*"|[^\s'";]+)"""),
     "senha em linha de comando (-P)", _RE_LINHA_DE_COMANDO),
    (re.compile(r"(?i)(\b(?:pwd|password)\s*=\s*)(?!N?'|@)([^;'\"\s]+)"), "senha em conn string", None),
)


def _mascarado(valor):
    v = valor.lstrip("Nn")
    if v.startswith("'"):
        return f"'{MASCARA}'"
    if v.startswith('"'):
        return f'"{MASCARA}"'
    return MASCARA


def mascarar_segredos(corpo):
    """(corpo com segredo mascarado, [(linha do corpo original, tipo)]) — nunca devolve o valor."""
    achados = []
    texto = corpo
    for regex, tipo, contexto in _PADROES_SEGREDO:
        # Índice das quebras de linha calculado 1x por padrão (não por match): achar a linha de um
        # match por contagem ingênua (`texto.count("\n", 0, pos)`) é O(posição) — com muitos matches
        # num corpo grande isso vira O(n²). Com `bisect` sobre a lista pré-calculada fica O(log n).
        quebras = [q.start() for q in re.finditer("\n", texto)]

        def troca(m, texto=texto, tipo=tipo, contexto=contexto, quebras=quebras):
            if "***REMOVIDO" in m.group(2):  # já mascarado por um padrão mais específico
                return m.group(0)
            if contexto is not None and not contexto.search(texto, max(0, m.start() - _JANELA_CONTEXTO), m.start()):
                return m.group(0)
            achados.append((bisect.bisect_left(quebras, m.start(2)) + 1, tipo))
            return m.group(1) + _mascarado(m.group(2))
        texto = regex.sub(troca, texto)
    return texto, sorted(achados, key=lambda a: a[0])


def cabecalho_segredo(achados, nl):
    detalhes = "; ".join(f"linha {n} do corpo original ({tipo})" for n, tipo in achados)
    return (f"-- [inventario-banco] Segredo removido antes de versionar: {detalhes}.{nl}"
            f"-- Este arquivo é DOCUMENTAÇÃO do objeto, não script executável.{nl}")


# ---------------------------------------------------------------------------------- cruzamento
# Comparadas em minúsculas: projeto .NET antigo tem `Bin`/`Obj`.
DIRS_IGNORADOS = {"bin", "obj", "packages", ".vs", ".git", ".svn", "$tf", ".idea", "node_modules", ".venv",
                  "venv", "__pycache__", "dist", "build", "testresults"}
# Saídas dos outros geradores do kit: repetem nomes e, ordenadas antes de src/, roubariam o "onde".
SAIDAS_DO_KIT = {"docs/bpmn.html", "docs/mapa-neural.html", "docs/anatomia.html"}
PASTAS_SAIDA_DO_KIT = ("docs/bpmn/",)
# Código, de qualquer linguagem. `.md` fica FORA: doc não é código, e ARQUITETURA.md/banco.md repetem os nomes.
EXT_CODIGO = {".cs", ".vb", ".aspx", ".ascx", ".asmx", ".ashx", ".master", ".cshtml", ".vbhtml",
              ".config", ".xml", ".xsd", ".edmx", ".dbml", ".resx", ".settings", ".json", ".sql",
              ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".htm", ".ini", ".yml", ".yaml", ".txt",
              ".csproj", ".vbproj", ".ps1", ".bat", ".cmd"}
GENERICOS = {"cliente", "clientes", "status", "log", "logs", "usuario", "usuarios", "user", "users",
             "config", "parametro", "parametros", "tipo", "tipos", "dados", "data", "item", "itens",
             "nome", "valor", "produto", "produtos", "pessoa", "pessoas", "endereco", "historico",
             "arquivo", "arquivos", "erro", "erros", "evento", "eventos", "sessao", "perfil", "menu", "teste"}
CITADO_CODIGO = "citado no código"
CITADO_BANCO = "citado só no banco"
SEM_CITACAO = "sem citação"
NAO_CRUZADO = "não cruzado (nome fora do padrão de identificador)"
DISPARA_COM_TABELA = "dispara com a tabela (trigger)"
MAX_OCORRENCIAS = 3
_RE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_RE_NOME_CRUZAVEL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class Citacao:
    classe: str
    ocorrencias: list
    fraco: bool = False


def _ler_texto(arq):
    """UTF-16 com BOM (o "Unicode" do Generate Scripts do SSMS) ou UTF-8; cp1252 cai no replace — os
    identificadores são ASCII, então o caractere trocado só vira fronteira de token."""
    bruto = arq.read_bytes()
    codificacao = "utf-16" if bruto[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return bruto.decode(codificacao, errors="replace")


def indexar_codigo(proj, excluir=None, nomes=None):
    """{token minúsculo: ["arquivo:linha", ...]} (no máximo MAX_OCORRENCIAS por token) dos arquivos de
    código. Busca por TOKEN: `Nome`, `dbo.Nome` e `[dbo].[Nome]` caem no mesmo token. `excluir` é a pasta
    de saída (anti-autoconfirmação); `nomes` (minúsculos) limita o índice aos objetos do inventário —
    sem isso, um monólito de 2M linhas guardaria todo token do repo."""
    proj = Path(proj).resolve()
    excluir = Path(excluir).resolve() if excluir else None
    indice = {}
    for raiz, dirs, arquivos in os.walk(proj):
        raiz = Path(raiz)
        dirs[:] = sorted(d for d in dirs if d.lower() not in DIRS_IGNORADOS and raiz / d != excluir)
        for nome in sorted(arquivos):
            arq = raiz / nome
            rel = arq.relative_to(proj).as_posix()
            if (arq.suffix.lower() not in EXT_CODIGO or rel in SAIDAS_DO_KIT
                    or rel.startswith(PASTAS_SAIDA_DO_KIT)):
                continue
            try:
                texto = _ler_texto(arq)
            except OSError:
                continue
            for n, linha in enumerate(texto.splitlines(), 1):
                for tok in {t.lower() for t in _RE_IDENT.findall(linha)}:
                    if nomes is not None and tok not in nomes:
                        continue
                    lugares = indice.setdefault(tok, [])
                    if len(lugares) < MAX_OCORRENCIAS:
                        lugares.append(f"{rel}:{n}")
    return indice


def objetos(catalogo):
    """[(esquema, nome, tipo)] de tabelas + módulos, na ordem do catálogo."""
    tabs = [(t["esquema"], t["nome"], "USER_TABLE") for t in catalogo.dados["tabelas"]]
    mods = [(m["esquema"], m["nome"], m["tipo"]) for m in catalogo.dados["modulos"]]
    return tabs + mods


def chamados_no_banco(catalogo):
    """Nomes (minúsculos) que outro objeto do banco ou um passo de job referencia."""
    nomes = set()
    for d in catalogo.dados.get("dependencias", []):
        if d["referencia"] and d["referencia"].lower() != d["objeto"].lower():
            nomes.add(d["referencia"].lower())
    for j in catalogo.dados.get("jobs", []):
        nomes.update(t.lower() for t in _RE_IDENT.findall(j["comando"] or ""))
    return nomes


def cruzar(catalogo, indice):
    no_banco = chamados_no_banco(catalogo)
    pais = {(m["esquema"], m["nome"]): m.get("pai") for m in catalogo.dados["modulos"]
            if m["tipo"] == "SQL_TRIGGER" and m.get("pai")}
    citacoes = {}
    for esquema, nome, _tipo in objetos(catalogo):
        chave = f"{esquema}.{nome}"
        if (esquema, nome) in pais:  # trigger não é chamada: dispara com a tabela
            citacoes[chave] = Citacao(DISPARA_COM_TABELA, [f"{esquema}.{pais[(esquema, nome)]}"])
            continue
        if not _RE_NOME_CRUZAVEL.match(nome):
            citacoes[chave] = Citacao(NAO_CRUZADO, [])
            continue
        baixo = nome.lower()
        fraco = baixo in GENERICOS or len(nome) <= 4
        if baixo in indice:
            citacoes[chave] = Citacao(CITADO_CODIGO, indice[baixo][:3], fraco)
        elif baixo in no_banco:
            citacoes[chave] = Citacao(CITADO_BANCO, [], fraco)
        else:
            citacoes[chave] = Citacao(SEM_CITACAO, [], fraco)
    return citacoes


# -------------------------------------------------------------------------------------- escrita
_RE_ARQ_INSEGURO = re.compile(r"[^\w.-]")


def nome_arquivo(esquema, nome):
    return _RE_ARQ_INSEGURO.sub("_", f"{esquema}.{nome}") + ".sql"


def _e_do_inventario(arq):
    """Brownfield: só arquivo que começa com a marca é nosso pra sobrescrever/remover."""
    try:
        with open(arq, encoding="utf-8-sig", errors="replace") as f:
            return f.readline().startswith(MARCA_SQL)
    except OSError:
        return False


@dataclass
class Gravacao:
    gravados: list     # .sql escritos nesta rodada
    removidos: list    # .sql NOSSOS de objeto que sumiu do catálogo
    preservados: list  # .sql alheios (sem a marca) que já estavam na pasta — intocados
    mantidos: list     # .sql nossos de objeto que existe mas veio sem corpo nesta rodada
    conflitos: list    # corpo NÃO gravado: arquivo do time com o mesmo nome, ou nome que só difere na caixa
    segredos: list     # [(objeto, linha, tipo)] — nunca o valor
    objetos_em_conflito: list = field(default_factory=list)  # "esquema.nome" de quem ficou sem corpo gravado


def gravar_corpos(catalogo, pasta):
    """1 .sql por módulo com corpo (UTF-8 com BOM, marca na 1ª linha, segredo mascarado).

    Brownfield: só escreve por cima e só remove arquivo que começa com a marca. Remove o .sql nosso
    SÓ de objeto que sumiu do catálogo — objeto que existe mas veio sem corpo nesta rodada (login sem
    VIEW DEFINITION, virou WITH ENCRYPTION) mantém o .sql anterior, que pode ser a única cópia. Nomes
    comparados sem caixa: no NTFS `dbo.X.sql` e `dbo.x.sql` são o mesmo arquivo."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    existentes = {p.name.casefold(): p for p in pasta.glob("*.sql")}
    no_catalogo = {nome_arquivo(m["esquema"], m["nome"]).casefold() for m in catalogo.dados["modulos"]}
    g = Gravacao([], [], [], [], [], [])
    usados = set()
    for m in catalogo.dados["modulos"]:
        if m["corpo"] is None:
            continue
        arq = nome_arquivo(m["esquema"], m["nome"])
        chave = arq.casefold()
        alvo = existentes.get(chave)
        objeto = f"{m['esquema']}.{m['nome']}"
        if chave in usados or (alvo is not None and not _e_do_inventario(alvo)):
            g.conflitos.append(arq)
            g.objetos_em_conflito.append(objeto)
            continue
        nl = "\r\n" if "\r\n" in m["corpo"] else "\n"
        corpo, achados = mascarar_segredos(m["corpo"])
        cabecalho = MARCA_SQL + nl
        if achados:
            cabecalho += cabecalho_segredo(achados, nl)
            g.segredos.extend((objeto, n, tipo) for n, tipo in achados)
        if alvo is not None and alvo.name != arq:  # renomeado só na caixa: renomeia (sem janela sem cópia)
            alvo.rename(pasta / arq)
        (pasta / arq).write_text(cabecalho + corpo, encoding="utf-8-sig", newline="")
        usados.add(chave)
        g.gravados.append(arq)
    em_conflito = {c.casefold() for c in g.conflitos}
    for chave, velho in sorted(existentes.items()):
        if chave in usados or chave in em_conflito:
            continue
        if not _e_do_inventario(velho):
            g.preservados.append(velho.name)
        elif chave in no_catalogo:
            g.mantidos.append(velho.name)
        else:
            velho.unlink()
            g.removidos.append(velho.name)
    return g


# ---------------------------------------------------------------------------------------- render
def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "sim" if v else "não"
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _cod(v):
    """Nome como código dentro de célula de tabela GFM: `|` escapado (vale até dentro de crase), crase
    trocada e quebra de linha achatada — nome entre colchetes pode ter qualquer um dos três."""
    return "`" + _fmt(v).replace("`", "'") + "`"


def _tipo_coluna(c):
    """Tipo com tamanho: varchar(20), nvarchar(100) (max_length é em bytes: nchar/nvarchar dividem por 2), (max)."""
    tipo, n = c["tipo"], c.get("tamanho")
    if tipo in ("varchar", "char", "varbinary", "binary", "nvarchar", "nchar") and isinstance(n, int):
        return f"{tipo}(max)" if n == -1 else f"{tipo}({n // 2 if tipo.startswith('n') else n})"
    return _fmt(tipo)


def _agrupar(linhas, *chaves):
    grupos = {}
    for l in linhas:
        grupos.setdefault(tuple(l[k] for k in chaves), []).append(l)
    return grupos


def renderizar_md(projeto, origem, hoje, catalogo, citacoes, segredos, objetos_em_conflito=()):
    """Retrato em texto pro assistente. NUNCA corpo de objeto, nunca valor de segredo, nunca texto de job."""
    em_conflito = set(objetos_em_conflito)
    d = catalogo.dados
    mods = d["modulos"]
    por_tipo = {}
    for m in mods:
        por_tipo[m["tipo"]] = por_tipo.get(m["tipo"], 0) + 1
    sem = sum(1 for c in citacoes.values() if c.classe == SEM_CITACAO)
    nao_extraidos = sum(1 for m in mods if m["corpo"] is None)
    out = [MARCA_MD, "", f"# Banco do projeto {projeto}", "",
           f"Gerado em {hoje} por `templates/inventario_banco.py` · {origem} · "
           "**só catálogo — nenhum dado de negócio foi lido.**", "",
           "## Resumo", "", "| o quê | quantos |", "|---|---|", f"| tabelas | {len(d['tabelas'])} |"]
    out += [f"| {tipo.lower()} | {n} |" for tipo, n in sorted(por_tipo.items())]
    out += [f"| sem citação no código | {sem} |", f"| corpo não extraído | {nao_extraidos} |",
            f"| segredos mascarados | {len(segredos)} |", f"| lacunas | {len(catalogo.lacunas)} |", ""]

    out += ["## Cruzamento com o código", "", f"> {FRASE_GUARDA}", "",
            "| objeto | classificação | onde |", "|---|---|---|"]
    for chave, c in citacoes.items():
        rotulo = c.classe + (" · casamento fraco, conferir" if c.fraco and c.classe == CITADO_CODIGO else "")
        onde = ", ".join(_cod(o) for o in c.ocorrencias) or "—"
        out.append(f"| {_cod(chave)} | {rotulo} | {onde} |")
    out.append("")

    linhas_tab = {(l["esquema"], l["tabela"]): l["linhas"] for l in d.get("linhas", [])}
    cols = _agrupar(d.get("colunas", []), "esquema", "tabela")
    chaves = _agrupar(d.get("chaves", []), "esquema", "tabela")
    fks = _agrupar(d.get("fks", []), "esquema", "tabela")
    idx = _agrupar(d.get("indices", []), "esquema", "tabela")
    out += ["## Tabelas", ""]
    for t in d["tabelas"]:
        k = (t["esquema"], t["nome"])
        out += [f"### {_cod(t['esquema'] + '.' + t['nome'])} — {_fmt(linhas_tab.get(k))} linhas (estimativa) · "
                f"criada {_fmt(t['criado'])} · modificada {_fmt(t['modificado'])}", "",
                "| coluna | tipo | nulo | identidade | padrão |", "|---|---|---|---|---|"]
        for c in cols.get(k, []):
            out.append(f"| {_fmt(c['coluna'])} | {_tipo_coluna(c)} | {_fmt(c['nulo'])} | "
                       f"{_fmt(c['identidade'])} | {_fmt(c['padrao'])} |")
        for (nome_k,), g in _agrupar(chaves.get(k, []), "chave").items():
            out.append(f"- **{_fmt(g[0]['tipo'])}** {_cod(nome_k)} ({', '.join(_fmt(x['coluna']) for x in g)})")
        for (nome_fk,), g in _agrupar(fks.get(k, []), "fk").items():
            out.append(f"- **FK** {_cod(nome_fk)}: ({', '.join(_fmt(x['coluna']) for x in g)}) → "
                       f"{_cod(g[0]['esquema_ref'] + '.' + g[0]['tabela_ref'])} "
                       f"({', '.join(_fmt(x['coluna_ref']) for x in g)})")
        for (nome_i,), g in _agrupar(idx.get(k, []), "indice").items():
            unico = " único" if g[0]["unico"] else ""
            out.append(f"- índice{unico} {_cod(nome_i)} {_fmt(g[0]['tipo']).lower()} "
                       f"({', '.join(_fmt(x['coluna']) for x in g)})")
        out.append("")

    params = _agrupar(d.get("parametros", []), "esquema", "objeto")
    deps = _agrupar(d.get("dependencias", []), "esquema", "objeto")
    out += ["## Procedures, functions, views e triggers", "",
            "| objeto | tipo | parâmetros | referencia | criado | modificado | corpo |",
            "|---|---|---|---|---|---|---|"]
    for m in mods:
        k = (m["esquema"], m["nome"])
        ps = ", ".join(f"{_fmt(p['parametro'])} {_fmt(p['tipo'])}" + (" OUTPUT" if p["saida"] else "")
                       for p in params.get(k, [])) or "—"
        rs = ", ".join(sorted({_fmt(f"{x['esquema_ref'] or m['esquema']}.{x['referencia']}")
                               for x in deps.get(k, [])})) or "—"
        arq = nome_arquivo(m["esquema"], m["nome"])
        if m["corpo"] is None:
            corpo = "não extraído (ver Lacunas)"
        elif f"{m['esquema']}.{m['nome']}" in em_conflito:
            corpo = "não gravado (conflito de nome de arquivo — ver o relatório)"
        else:
            corpo = _cod(f"banco/{arq}")
        out.append(f"| {_cod(m['esquema'] + '.' + m['nome'])} | {_fmt(m['tipo']).lower()} | {ps} | {rs} | "
                   f"{_fmt(m['criado'])} | {_fmt(m['modificado'])} | {corpo} |")
    out.append("")

    nomes_inv = {nome.lower(): f"{esq}.{nome}" for esq, nome, _ in objetos(catalogo)}
    out += ["## Fronteira do sistema", "", "### Linked servers", ""]
    servidores = d.get("servidores", [])
    if servidores:
        out += ["| nome | provedor | origem |", "|---|---|---|"]
        out += [f"| `{_fmt(s['nome'])}` | {_fmt(s['provedor'])} | {mask_password(_fmt(s['origem']))} |"
                for s in servidores]
    else:
        out.append("Nenhum linked server visível (ou sem permissão — ver Lacunas).")
    out += ["", "### Jobs do SQL Agent que tocam esta base", "",
            "O texto do passo não é transcrito (pode ter segredo): só o job, o passo e os objetos do inventário que ele chama.", ""]
    jobs = d.get("jobs", [])
    if jobs:
        out += ["| job | ativo | passo | chama |", "|---|---|---|---|"]
        for j in jobs:
            chamados = sorted({nomes_inv[t.lower()] for t in _RE_IDENT.findall(j["comando"] or "")
                               if t.lower() in nomes_inv})
            out.append(f"| `{_fmt(j['job'])}` | {_fmt(j['ativo'])} | {_fmt(j['passo'])} | "
                       f"{', '.join(_cod(c) for c in chamados) or '—'} |")
    else:
        out.append("Nenhum job visível para esta base (ou sem permissão em `msdb` — ver Lacunas).")
    out.append("")

    out += ["## Segredos mascarados", "",
            f"Valor nunca exibido nem gravado — o `.sql` versionado leva `{MASCARA}` no lugar.", ""]
    if segredos:
        out += ["| objeto | linha do corpo original | tipo |", "|---|---|---|"]
        out += [f"| {_cod(o)} | {n} | {t} |" for o, n, t in segredos]
    else:
        out.append("Nenhum encontrado pelos padrões da varredura (PWD=/Password=, WITH PASSWORD, "
                   "sp_addlinkedsrvlogin, SECRET=/IDENTITY=, OPENROWSET).")
    out += ["", "## Lacunas", ""]
    out += [f"- {l}" for l in catalogo.lacunas]
    out.append("- **Não coberto por desenho:** triggers de DDL do banco (não pertencem a esquema) · SQL montado "
               "em runtime (ver o aviso do cruzamento) · dado de negócio (o inventário não lê linha de tabela).")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------------- orquestração
class ErroSaida(Exception):
    """Arquivo de saída existe e não é nosso (brownfield) — para sem gravar."""


@dataclass
class Relatorio:
    md: Path
    pasta_sql: Path
    total_objetos: int
    gravados: list
    removidos: list
    preservados: list
    mantidos: list
    conflitos: list
    segredos: list
    lacunas: list
    linha_gitignore: str  # "" quando já está ancorada ou a saída não é a padrão


def gerar(proj, cursor, origem, out=None, max_objetos=MAX_OBJETOS_PADRAO, hoje=None):
    proj = Path(proj).resolve()
    destino = Path(out).resolve() if out else proj / "docs"
    md = destino / "banco.md"
    if md.exists() and not md.read_text(encoding="utf-8-sig", errors="replace").startswith(MARCA_MD):
        raise ErroSaida(f"{md} já existe e não foi gerado pelo inventário — não sobrescrevo. "
                        "Renomeie o arquivo do projeto ou use --out.")
    catalogo = coletar(cursor, max_objetos)  # o teto estoura aqui, antes de gravar qualquer coisa
    nomes = {nome.lower() for _, nome, _ in objetos(catalogo)}
    citacoes = cruzar(catalogo, indexar_codigo(proj, excluir=destino / "banco", nomes=nomes))
    g = gravar_corpos(catalogo, destino / "banco")
    md.write_text(renderizar_md(proj.name, origem, hoje or dt.date.today().isoformat(),
                                catalogo, citacoes, g.segredos, g.objetos_em_conflito), encoding="utf-8")
    linha = ""
    if out is None:
        gi = proj / ".gitignore"
        ancoradas = ({l.strip() for l in gi.read_text(encoding="utf-8-sig", errors="replace").splitlines()}
                     if gi.exists() else set())
        linha = "" if ancoradas & {"/docs/banco.md", "docs/banco.md"} else "/docs/banco.md"
    return Relatorio(md, destino / "banco", len(objetos(catalogo)), g.gravados, g.removidos, g.preservados,
                     g.mantidos, g.conflitos, g.segredos, catalogo.lacunas, linha)


def relatorio_texto(rel):
    out = [f"inventário gerado: {rel.md}",
           f"objetos: {rel.total_objetos} · corpos gravados: {len(rel.gravados)} em {rel.pasta_sql}"]
    if rel.removidos:
        out.append("removidos (sumiram do banco): " + ", ".join(rel.removidos))
    if rel.mantidos:
        out.append("mantidos (o objeto existe, mas o corpo não veio nesta rodada — login sem VIEW DEFINITION?): "
                   + ", ".join(rel.mantidos))
    if rel.conflitos:
        out.append(f"NÃO documentados (já há arquivo do time com o mesmo nome em {rel.pasta_sql}, ou dois objetos "
                   "que só diferem na caixa): " + ", ".join(rel.conflitos))
    if rel.preservados:
        out.append(f"em {rel.pasta_sql} mas NÃO são do inventário (não mexi): " + ", ".join(rel.preservados))
    if rel.segredos:
        out.append("segredos mascarados (valor nunca exibido): "
                   + "; ".join(f"{o} linha {n} ({t})" for o, n, t in rel.segredos))
    out.append(f"lacunas: {len(rel.lacunas)} (seção Lacunas do banco.md)")
    if rel.linha_gitignore:
        out.append(f"falta no .gitignore (pergunte ao owner antes de acrescentar): {rel.linha_gitignore}")
    return "\n".join(out)


def conectar(conn_str):
    import pyodbc  # import tardio: o módulo (e os testes) não precisam do driver ODBC
    return pyodbc.connect(conn_str, timeout=30, autocommit=True)


def main(argv=None, env=None, conectar_fn=None):
    for fluxo in (sys.stdout, sys.stderr):  # console Windows em cp1252 embaralha acento (padrão do kit)
        try:
            fluxo.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(description="Inventário somente-leitura do banco vivo (SQL Server).")
    ap.add_argument("--proj", help="diretório do projeto (default: diretório atual)")
    ap.add_argument("--out", help="pasta de saída (default: <proj>/docs)")
    ap.add_argument("--fonte", help="get_connection.py de um projeto MSIG que alcança o servidor (lido por ast)")
    ap.add_argument("--ambiente", default="D0", help="D0 | HML | PRD (default: D0)")
    ap.add_argument("--par", help="base da fonte cujo par reaproveitar, quando a fonte tem mais de uma")
    ap.add_argument("--base", help="base a inventariar (sobrescreve o Database= da conn string)")
    ap.add_argument("--porta", type=int, help="sobrescreve a porta do servidor")
    ap.add_argument("--max-objetos", type=int, default=MAX_OBJETOS_PADRAO)
    args = ap.parse_args(argv)
    env = os.environ if env is None else env
    conectar_fn = conectar_fn or conectar
    proj = Path(args.proj) if args.proj else Path.cwd()
    if not proj.is_dir():
        print(f"[inventario-banco] --proj não é uma pasta existente: {proj}", file=sys.stderr)
        return 2
    try:
        conexao = resolver_conn(env, args.fonte, args.ambiente, args.par, args.base, args.porta)
    except ErroCredencial as e:
        print(f"[inventario-banco] {e}", file=sys.stderr)
        return 2
    for aviso in conexao.avisos:
        print(f"[inventario-banco] aviso: {aviso}")
    print(f"[inventario-banco] conectando: {conexao.origem}")
    try:
        conn = conectar_fn(conexao.conn_str)
    except Exception as e:
        print(f"[inventario-banco] {explicar_erro(e)}", file=sys.stderr)
        return 3
    try:
        rel = gerar(proj, conn.cursor(), conexao.origem, out=args.out, max_objetos=args.max_objetos)
    except (ErroTeto, ErroSaida) as e:
        print(f"[inventario-banco] {e}", file=sys.stderr)
        return 4
    except OSError as e:  # disco — antes do genérico: "Permission denied" do Windows não é permissão do banco
        print(f"[inventario-banco] DISCO: não consegui gravar {e.filename or ''} ({e.strerror or e}) — arquivo "
              "aberto/bloqueado ou pasta sem permissão. Não é o banco.", file=sys.stderr)
        return 5
    except Exception as e:  # noqa: BLE001 — query negada, queda de rede no meio, disco: mensagem, nunca traceback
        print(f"[inventario-banco] {explicar_erro(e)}", file=sys.stderr)
        return 5
    finally:
        conn.close()
    print(relatorio_texto(rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
