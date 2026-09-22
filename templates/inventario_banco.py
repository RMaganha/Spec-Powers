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
def mask_password(conn_str):
    """Mascara a senha na conn string. Cópia do templates/get_connection.py — aquele arquivo é MOLDE
    com placeholders (`DEV_<BASE>_KEY`), não é Python importável."""
    partes = []
    for parte in conn_str.split(";"):
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
        return _RE_BASE.sub(lambda m: f"{m.group(1)}={base}", conn_str, count=1)
    return conn_str.rstrip(";") + f";Database={base}"


def trocar_porta(conn_str, porta):
    """Sobrescreve a porta do servidor (host,porta), mantendo o host — mesma regra do molde."""
    return re.sub(r"(?i)((?:Server|Data Source)=[^;,]+)(?:,\d+)?", rf"\g<1>,{porta}", conn_str, count=1)


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


def main(argv=None):
    raise SystemExit("inventario_banco: em construção (docs/superpowers/plans/2026-09-22-inventario-banco.md)")


if __name__ == "__main__":
    sys.exit(main())
