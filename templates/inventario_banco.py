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
       OBJECTPROPERTY(o.object_id, 'IsEncrypted') AS criptografado, m.definition AS corpo
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


def main(argv=None):
    raise SystemExit("inventario_banco: em construção (docs/superpowers/plans/2026-09-22-inventario-banco.md)")


if __name__ == "__main__":
    sys.exit(main())
