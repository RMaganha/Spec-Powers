# Inventário do banco vivo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao `/mss-spec:analise` um inventário somente-leitura do banco SQL Server vivo (catálogo + corpo das procedures + cruzamento com o código), disparado sozinho por evidência no código.

**Architecture:** 4º gerador determinístico do kit (`templates/inventario_banco.py`), no padrão de `mapa_neural.py`/`anatomia.py`/`bpmn.py`: funções puras testadas com **cursor falso** + camada fina de conexão (`pyodbc`, import tardio). Credencial reaproveita o par Fernet de outro projeto MSIG lido por `ast` (nunca importado). O comando `/mss-spec:inventario-banco` é fino (regenerar); a entrada real é um passo novo na fase 2 do `commands/analise.md`.

**Tech Stack:** Python 3.14 (stdlib: `ast`, `re`, `argparse`, `dataclasses`, `pathlib`) · `pyodbc` e `cryptography` só em runtime, por import tardio · pytest.

**Spec:** `docs/specs/inventario-banco.md` · **Branch:** `feature/inventario-do-banco-vivo` (já existe, a partir da `main`).

**Regras do repositório que valem em todas as tarefas:**
- Rode o pytest **em passo próprio**, nunca encadeado em pipe com `git commit` (caso F-025: `pytest | tail -1 && git commit` commitou com 2 vermelhos).
- Commits terminam com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Nunca** `git push`/`merge`/`rebase` — publicar é ato do owner; `hooks/git_publicacao.py` nega de qualquer jeito.
- No gerador: **sem** `from __future__ import annotations` (quebra `@dataclass` carregada por `importlib` no Python 3.14 — memória `project_importlib_dataclass_precisa_de_sys_modules`).

---

## Mapa de arquivos

| arquivo | ação | responsabilidade |
|---|---|---|
| `templates/inventario_banco.py` | criar | o gerador inteiro (seções: queries · credencial · erro · coleta · segredo · cruzamento · escrita · render · CLI) |
| `tests/test_inventario_banco.py` | criar | comportamento do gerador, sem banco |
| `commands/inventario-banco.md` | criar | comando fino pra regenerar |
| `commands/analise.md` | modificar | passo *Dados — banco vivo* + exceção dos `.sql` gerados na regra dura |
| `templates/ARQUITETURA.md` | modificar | seção 5 (Dados) ganha as linhas do inventário |
| `.gitignore`, `templates/gitignore` | modificar | `/docs/banco.md` ancorado (os `.sql` **não** entram) |
| `docs/LEIA-ME.md` | modificar | linha do comando novo |
| `docs/COMO-FUNCIONA.html` | modificar | 5 cards faltantes (`anatomia`, `bpmn`, `diagnostico`, `divergir`, `inventario-banco`), "Os 25 atalhos", renumeração C1..C25 |
| `tests/test_smoke_kit.py` | modificar | wiring do comando, disparo pela `analise`, contagem do COMO-FUNCIONA |
| `docs/specs/inventario-banco.md` | modificar | Task 0 (detalhes do planejamento) e Task 16 (Estado atual) |
| `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/decisoes.md`, `docs/superpowers/INDEX.md`, `docs/superpowers/MAPA.md` | modificar | fecho (Task 16) |

---

### Task 0: Alinhar a spec com o que o planejamento fechou

A spec foi aprovada com 7 pontos que só apareceram ao planejar. Um é contradição interna (§ 2 × § 6 sobre precedência).

**Files:**
- Modify: `docs/specs/inventario-banco.md`

- [ ] **Step 1: `--par` no caminho padrão (§ 2)**

Edit — old:
```
+ `--base <nome>` + `--porta` (opcional). O caso que
```
new:
```
+ `--base <nome>` + `--porta` (opcional) + `--par <BASE>` quando a fonte
   tem mais de uma base (sem ele, o script **para e lista os nomes** — nunca escolhe sozinho). O caso que
```

- [ ] **Step 2: precedência flag > variável (§ 2 e § 6)**

Edit — old:
```
Cadeia de resolução, para no primeiro caminho que resolver:
```
new:
```
Cadeia de resolução, para no primeiro caminho que resolver (`--fonte` passado **ganha** da variável — a
flag é a intenção mais específica; a variável ignorada é avisada):
```
Edit — old:
```
- **credencial**: variável ganha da fonte quando as duas existem · `--fonte` + `--base` troca o
```
new:
```
- **credencial**: `--fonte` ganha da variável quando os dois existem, com aviso · `--fonte` + `--base` troca o
```

- [ ] **Step 3: contagem de linhas é opcional (§ 3)**

Edit — old:
```
`sys.dm_db_partition_stats` (estimativa de partição, custo ~zero — não `COUNT(*)`), que responde "o
```
new:
```
`sys.dm_db_partition_stats` (estimativa de partição, custo ~zero — não `COUNT(*)`; exige `VIEW
  DATABASE STATE` e, sem ela, degrada pra lacuna), que responde "o
```

- [ ] **Step 4: jobs sem o texto do passo (§ 3)**

Edit — old:
```
  do Agent**; em legado, metade do sistema costuma ser job agendado que ninguém lembra).
```
new:
```
  do Agent**; em legado, metade do sistema costuma ser job agendado que ninguém lembra — o texto do
  passo **não** vai pra saída, pode ter segredo: só job, passo e objetos do inventário que ele chama).
```

- [ ] **Step 5: criptografado × falta de `VIEW DEFINITION` (§ 3)**

Edit — old:
```
como lacuna nomeada (`<objeto> — corpo criptografado, não extraído`); objeto invisível por permissão
idem.
```
new:
```
como lacuna nomeada (`<objeto> — corpo criptografado, não extraído`); corpo `NULL` **sem** criptografia
é falta de `VIEW DEFINITION` e vira lacuna com esse nome (`OBJECTPROPERTY(..., 'IsEncrypted')` separa
os dois casos).
```

- [ ] **Step 6: `.md` fora do cruzamento e classe *não cruzado* (§ 4)**

Edit — old:
```
`ConsultaApolice`, `dbo.ConsultaApolice`, `[dbo].[ConsultaApolice]`. Procura em todo arquivo de texto
do projeto, menos
```
new:
```
`ConsultaApolice`, `dbo.ConsultaApolice`, `[dbo].[ConsultaApolice]` (a busca é por **token**, então as
três caem no mesmo nome). Procura nos arquivos de **código** do projeto (`.md` fica fora: doc não é
código, e `ARQUITETURA.md`/`banco.md` repetem os nomes), menos
```
Edit — old:
```
- **sem citação** — não apareceu em lugar nenhum
```
new:
```
- **sem citação** — não apareceu em lugar nenhum
- **não cruzado** — nome fora do padrão de identificador (`[Minha Proc]`, com espaço ou acento): a
  busca por token não o enxerga, e isso é dito em vez de virar *sem citação*
```

- [ ] **Step 7: marca de autoria — brownfield (§ 5)**

Edit — old:
```
**O que o script não faz:**
```
new:
```
**Brownfield — só mexe no que é seu.** Todo `.sql` gerado começa com a marca
`-- [inventario-banco]` e o `banco.md` com `<!-- [inventario-banco] ... -->`. Só arquivo com a marca é
sobrescrito ou removido: um `docs/banco.md` que o time já tinha faz o script **parar sem gravar**
(use `--out`), e `.sql` alheio em `docs/banco/` fica intocado e listado no relatório.

**O que o script não faz:**
```

- [ ] **Step 8: testes novos na lista (§ 6)**

Edit — old:
```
- **teto e regeneração**: acima de `--max-objetos` para sem gravar nada · objeto sumido tem o `.sql`
  removido e reportado
```
new:
```
- **teto e regeneração**: acima de `--max-objetos` para sem gravar nada · objeto sumido tem o `.sql`
  removido e reportado
- **marca de autoria**: `banco.md` alheio → para sem gravar · `.sql` alheio preservado e listado ·
  `--proj .` sai com o nome do projeto no título (`Path(".").name` é vazio — caso F-016)
```

- [ ] **Step 9: linha no Histórico**

Acrescente ao fim do arquivo:
```
- 2026-09-22 — plano de implementação (`docs/superpowers/plans/2026-09-22-inventario-banco.md`)
  fechou 7 detalhes que o desenho deixou abertos: `--par`, precedência flag > variável (o § 6 dizia
  o contrário do § 2), linhas como opcional, `.md` fora do cruzamento, classe *não cruzado*,
  criptografado × falta de `VIEW DEFINITION`, marca de autoria nos arquivos gerados (brownfield).
```

- [ ] **Step 10: Commit**

```bash
git add docs/specs/inventario-banco.md docs/superpowers/plans/2026-09-22-inventario-banco.md
git commit -m "docs(spec): inventario do banco -- detalhes fechados no planejamento + plano de implementacao

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Esqueleto do gerador, importável sem `pyodbc` nem `cryptography`

**Files:**
- Create: `templates/inventario_banco.py`
- Create: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing test**

Crie `tests/test_inventario_banco.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `FileNotFoundError` (o script não existe).

- [ ] **Step 3: Write minimal implementation**

Crie `templates/inventario_banco.py`:
```python
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


def main(argv=None):
    raise SystemExit("inventario_banco: em construção (docs/superpowers/plans/2026-09-22-inventario-banco.md)")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): esqueleto do gerador, importavel sem pyodbc/cryptography

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Queries de catálogo — somente-leitura e só catálogo, travados por teste

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim de `tests/test_inventario_banco.py`:
```python
PROIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|EXEC|EXECUTE|GRANT|DENY|REVOKE)\b", re.I)
ALVO = re.compile(r"\b(?:FROM|JOIN)\s+([\w.\[\]]+)", re.I)


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: module 'inventario_banco' has no attribute 'QUERIES'` (e `count` == 0 no terceiro).

- [ ] **Step 3: Write minimal implementation**

Em `templates/inventario_banco.py`, acrescente **antes** de `def main`:
```python
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
WHERE i.name IS NOT NULL
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
SELECT sr.name AS esquema, o.name AS objeto, d.referenced_schema_name AS esquema_ref,
       d.referenced_entity_name AS referencia
FROM sys.sql_expression_dependencies d
JOIN sys.objects o ON o.object_id = d.referencing_id
JOIN sys.schemas sr ON sr.schema_id = o.schema_id
WHERE d.referenced_entity_name IS NOT NULL
ORDER BY sr.name, o.name""",
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): queries de catalogo, somente-leitura travado por teste

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Utilitários de conn string (máscara, base, porta)

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
def test_mask_password(inv):
    assert inv.mask_password("Server=a;UID=u;PWD=s3nh4") == "Server=a;UID=u;PWD=***HIDDEN***"
    assert "x9" not in inv.mask_password("Data Source=a;User ID=u;Password=x9;")


@pytest.mark.parametrize("antes, depois", [
    ("Server=a;Database=Velha;UID=u", "Server=a;Database=Nova;UID=u"),
    ("Data Source=a;Initial Catalog=Velha;", "Data Source=a;Initial Catalog=Nova;"),
    ("Server=a;UID=u", "Server=a;UID=u;Database=Nova"),
])
def test_trocar_base(inv, antes, depois):
    assert inv.trocar_base(antes, "Nova") == depois


@pytest.mark.parametrize("antes, depois", [
    ("Server=h,1435;Database=x", "Server=h,1500;Database=x"),
    ("Server=h;Database=x", "Server=h,1500;Database=x"),
])
def test_trocar_porta(inv, antes, depois):
    assert inv.trocar_porta(antes, "1500") == depois


def test_le_servidor_e_base(inv):
    conn = "Server=srv,1435;Initial Catalog=Legado;UID=u"
    assert inv.servidor_da_conn(conn) == "srv,1435"
    assert inv.base_da_conn(conn) == "Legado"
    assert inv.base_da_conn("Server=srv") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'mask_password'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (12 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): mascara, troca de base e de porta na conn string

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Ler o par Fernet por `ast` e escolher o par certo

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'ler_pares_fernet'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (16 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): par Fernet lido por ast (nunca importado) e escolha por --par

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Cadeia de resolução da credencial

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'resolver_conn'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
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
        chave, cifra = escolher_par(pares, ambiente, par)
        if b"<" in chave or b"<" in cifra:
            raise ErroCredencial(f"o par em {caminho} ainda é placeholder — aponte um projeto que conecta de verdade.")
        conn = decriptar(chave, cifra)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (25 passed; `test_fernet_de_verdade` roda porque `cryptography` 48.0.1 está instalado nesta máquina)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): cadeia de credencial --fonte > MSS_INVENTARIO_CONN > erro claro

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Erro de conexão classificado (rede × credencial × permissão)

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing test**

Acrescente ao fim do arquivo de teste:
```python
@pytest.mark.parametrize("mensagem, esperado", [
    ('[42000] [SQL Server]Cannot open database "LegadoCS" requested by the login. The login failed. (4060)',
     "PERMISSÃO"),
    ("[28000] [SQL Server]Login failed for user 'leitor'. (18456)", "CREDENCIAL"),
    ("[08001] [Microsoft][ODBC Driver 17 for SQL Server]Named Pipes Provider: Could not open a connection [53].",
     "REDE"),
    ("[HYT00] [Microsoft][ODBC Driver 17 for SQL Server]Login timeout expired", "REDE"),
    ("algo que ninguém previu", "não classificada"),
])
def test_explicar_erro(inv, mensagem, esperado):
    assert esperado in inv.explicar_erro(RuntimeError(mensagem))
```
(O 1º caso tem "login failed" **e** 4060 — o teste trava que permissão na base é checada antes de credencial.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_inventario_banco.py -k explicar_erro -v`
Expected: FAIL — `AttributeError: ... no attribute 'explicar_erro'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
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
    if any(s in baixo for s in ("08001", "hyt00", "timeout", "timed out", "[53]", "(53)",
                                "network-related", "tcp provider")):
        return ("REDE: o servidor não respondeu (erro 53/timeout). Fora da rede corporativa nada responde; "
                "confira host e porta (--porta). Isso não é credencial.")
    return f"falha de conexão não classificada ({type(exc).__name__}): {mask_password(msg)[:200]}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (30 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): erro de conexao classificado em rede/credencial/permissao

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Coleta com cursor falso — teto, opcionais que degradam, lacunas de corpo

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests (e os auxiliares que as tarefas seguintes reusam)**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'coletar'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (35 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): coleta do catalogo com teto e lacunas nomeadas

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Varredura de segredo

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'mascarar_segredos'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
# ------------------------------------------------------------------------------------- segredo
# Ordem importa: as formas entre aspas vêm antes da genérica; a genérica recusa valor que começa com
# aspas (senão mascararia só o "N" de N'...'). Grupo 1 = prefixo mantido; grupo 2 = valor mascarado.
_PADROES_SEGREDO = (
    (re.compile(r"(?i)(\bwith\s+password\s*=\s*)(N?'[^']*')"), "senha de LOGIN"),
    (re.compile(r"(?i)(@rmtpassword\s*=\s*)(N?'[^']*')"), "senha de linked server (sp_addlinkedsrvlogin)"),
    (re.compile(r"(?i)(\bsp_addlinkedsrvlogin\b[^;\n]*?,[^,\n]*,[^,\n]*,[^,\n]*,\s*)(N?'[^']*')"),
     "senha de linked server (sp_addlinkedsrvlogin)"),
    (re.compile(r"(?i)(\bsecret\s*=\s*)(N?'[^']*')"), "SECRET de credencial"),
    (re.compile(r"(?i)(\bidentity\s*=\s*)(N?'[^']*')"), "IDENTITY de credencial"),
    (re.compile(r"(?i)(\bopenrowset\s*\(\s*N?'[^']*'\s*,\s*N?'[^']*'\s*;\s*N?'[^']*'\s*;\s*)(N?'[^']*')"),
     "senha em OPENROWSET"),
    (re.compile(r"(?i)(\b(?:pwd|password)\s*=\s*)(?!N?')([^;'\"\s]+)"), "senha em conn string"),
)


def _substituto(m):
    valor = m.group(2)
    return m.group(1) + (f"'{MASCARA}'" if valor.lstrip("Nn").startswith("'") else MASCARA)


def mascarar_segredos(corpo):
    """(corpo com segredo mascarado, [(linha do corpo original, tipo)]). Nunca devolve o valor."""
    achados = []
    linhas = corpo.split("\n")
    for i, linha in enumerate(linhas, 1):
        for regex, tipo in _PADROES_SEGREDO:
            linha, n = regex.subn(_substituto, linha)
            if n:
                achados.append((i, tipo))
        linhas[i - 1] = linha
    return "\n".join(linhas), achados


def cabecalho_segredo(achados, nl):
    detalhes = "; ".join(f"linha {n} do corpo original ({tipo})" for n, tipo in achados)
    return (f"-- [inventario-banco] Segredo removido antes de versionar: {detalhes}.{nl}"
            f"-- Este arquivo é DOCUMENTAÇÃO do objeto, não script executável.{nl}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (44 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): varredura de segredo antes de versionar o corpo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Cruzamento com o código

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'cruzar'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
# ---------------------------------------------------------------------------------- cruzamento
DIRS_IGNORADOS = {"bin", "obj", "packages", ".vs", ".git", "node_modules", ".venv", "__pycache__"}
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
_RE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_RE_NOME_CRUZAVEL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class Citacao:
    classe: str
    ocorrencias: list
    fraco: bool = False


def indexar_codigo(proj, excluir=None):
    """{token minúsculo: ["arquivo:linha", ...]} dos arquivos de código. Busca por TOKEN: `Nome`,
    `dbo.Nome` e `[dbo].[Nome]` caem no mesmo token. `excluir` é a pasta de saída (anti-autoconfirmação)."""
    proj = Path(proj)
    excluir = Path(excluir).resolve() if excluir else None
    indice = {}
    for raiz, dirs, arquivos in os.walk(proj):
        dirs[:] = sorted(d for d in dirs
                         if d not in DIRS_IGNORADOS and (excluir is None or Path(raiz, d).resolve() != excluir))
        for nome in sorted(arquivos):
            arq = Path(raiz, nome)
            if arq.suffix.lower() not in EXT_CODIGO:
                continue
            try:
                texto = arq.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            rel = arq.relative_to(proj).as_posix()
            for n, linha in enumerate(texto.splitlines(), 1):
                for tok in {t.lower() for t in _RE_IDENT.findall(linha)}:
                    indice.setdefault(tok, []).append(f"{rel}:{n}")
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
    citacoes = {}
    for esquema, nome, _tipo in objetos(catalogo):
        chave = f"{esquema}.{nome}"
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (53 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): cruzamento por token - citado no codigo, so no banco, sem citacao

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Gravar os corpos (UTF-8 com BOM, marca, segredo mascarado, brownfield)

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
def _gravar(inv, pasta, respostas=None):
    return inv.gravar_corpos(inv.coletar(CursorFalso(inv, respostas or respostas_base())), pasta)


def test_corpos_utf8_bom_com_marca(inv, tmp_path):
    gravados, removidos, preservados, segredos = _gravar(inv, tmp_path / "banco")
    arq = tmp_path / "banco" / "dbo.ConsultaApolice.sql"
    assert "dbo.ConsultaApolice.sql" in gravados and "dbo.Cifrada.sql" not in gravados
    assert arq.read_bytes().startswith(b"\xef\xbb\xbf")
    texto = arq.read_text(encoding="utf-8-sig")
    assert texto.startswith(inv.MARCA_SQL)
    assert "WHERE Numero = @Numero" in texto
    assert b"AS\r\nSELECT" in arq.read_bytes()  # CRLF do SQL Server preservado


def test_segredo_mascarado_no_arquivo(inv, tmp_path):
    r = respostas_base()
    r["modulos"] = (COLS_MODULOS, [("dbo", "Importa", "SQL_STORED_PROCEDURE", D1, D1, 0,
                                    "CREATE PROCEDURE dbo.Importa AS\nSELECT * FROM OPENROWSET('SQLNCLI','Server=x;PWD=Abc123;','SELECT 1')")])
    _, _, _, segredos = _gravar(inv, tmp_path / "banco", r)
    texto = (tmp_path / "banco" / "dbo.Importa.sql").read_text(encoding="utf-8-sig")
    assert "Abc123" not in texto and inv.MASCARA in texto and "Segredo removido" in texto
    assert segredos == [("dbo.Importa", 2, "senha em conn string")]


def test_remove_so_o_que_e_do_inventario(inv, tmp_path):
    pasta = tmp_path / "banco"
    pasta.mkdir()
    (pasta / "dbo.Sumiu.sql").write_text(inv.MARCA_SQL + "\nSELECT 1", encoding="utf-8-sig")
    (pasta / "script_do_time.sql").write_text("-- script nosso\nSELECT 1", encoding="utf-8")
    _, removidos, preservados, _ = _gravar(inv, pasta)
    assert removidos == ["dbo.Sumiu.sql"] and not (pasta / "dbo.Sumiu.sql").exists()
    assert preservados == ["script_do_time.sql"] and (pasta / "script_do_time.sql").exists()


def test_nome_de_arquivo_seguro(inv):
    assert inv.nome_arquivo("dbo", "a/b c") == "dbo.a_b_c.sql"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'gravar_corpos'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
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


def gravar_corpos(catalogo, pasta):
    """1 .sql por módulo com corpo (UTF-8 com BOM, marca na 1ª linha, segredo mascarado). Remove o
    .sql NOSSO de objeto que sumiu do catálogo; .sql alheio fica e é listado.
    Devolve (gravados, removidos, preservados, segredos[(objeto, linha, tipo)])."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    gravados, segredos = [], []
    for m in catalogo.dados["modulos"]:
        if m["corpo"] is None:
            continue
        objeto = f"{m['esquema']}.{m['nome']}"
        nl = "\r\n" if "\r\n" in m["corpo"] else "\n"
        corpo, achados = mascarar_segredos(m["corpo"])
        cabecalho = MARCA_SQL + nl
        if achados:
            cabecalho += cabecalho_segredo(achados, nl)
            segredos.extend((objeto, n, tipo) for n, tipo in achados)
        arq = nome_arquivo(m["esquema"], m["nome"])
        (pasta / arq).write_text(cabecalho + corpo, encoding="utf-8-sig", newline="")
        gravados.append(arq)
    atuais = set(gravados)
    removidos, preservados = [], []
    for velho in sorted(pasta.glob("*.sql")):
        if velho.name in atuais:
            continue
        if _e_do_inventario(velho):
            velho.unlink()
            removidos.append(velho.name)
        else:
            preservados.append(velho.name)
    return gravados, removidos, preservados, segredos
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (57 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): corpos .sql com BOM, marca de autoria e segredo mascarado

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Renderizar o `banco.md`

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main`)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `AttributeError: ... no attribute 'renderizar_md'`.

- [ ] **Step 3: Write minimal implementation**

Acrescente antes de `def main`:
```python
# ---------------------------------------------------------------------------------------- render
def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "sim" if v else "não"
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _agrupar(linhas, *chaves):
    grupos = {}
    for l in linhas:
        grupos.setdefault(tuple(l[k] for k in chaves), []).append(l)
    return grupos


def renderizar_md(projeto, origem, hoje, catalogo, citacoes, segredos):
    """Retrato em texto pro assistente. NUNCA corpo de objeto, nunca valor de segredo, nunca texto de job."""
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
        onde = ", ".join(f"`{o}`" for o in c.ocorrencias) or "—"
        out.append(f"| `{chave}` | {rotulo} | {onde} |")
    out.append("")

    linhas_tab = {(l["esquema"], l["tabela"]): l["linhas"] for l in d.get("linhas", [])}
    cols = _agrupar(d.get("colunas", []), "esquema", "tabela")
    chaves = _agrupar(d.get("chaves", []), "esquema", "tabela")
    fks = _agrupar(d.get("fks", []), "esquema", "tabela")
    idx = _agrupar(d.get("indices", []), "esquema", "tabela")
    out += ["## Tabelas", ""]
    for t in d["tabelas"]:
        k = (t["esquema"], t["nome"])
        out += [f"### `{t['esquema']}.{t['nome']}` — {_fmt(linhas_tab.get(k))} linhas (estimativa) · "
                f"criada {_fmt(t['criado'])} · modificada {_fmt(t['modificado'])}", "",
                "| coluna | tipo | nulo | identidade | padrão |", "|---|---|---|---|---|"]
        for c in cols.get(k, []):
            out.append(f"| {_fmt(c['coluna'])} | {_fmt(c['tipo'])} | {_fmt(c['nulo'])} | "
                       f"{_fmt(c['identidade'])} | {_fmt(c['padrao'])} |")
        for (nome_k,), g in _agrupar(chaves.get(k, []), "chave").items():
            out.append(f"- **{_fmt(g[0]['tipo'])}** `{nome_k}` ({', '.join(x['coluna'] for x in g)})")
        for (nome_fk,), g in _agrupar(fks.get(k, []), "fk").items():
            out.append(f"- **FK** `{nome_fk}`: ({', '.join(x['coluna'] for x in g)}) → "
                       f"`{g[0]['esquema_ref']}.{g[0]['tabela_ref']}` ({', '.join(x['coluna_ref'] for x in g)})")
        for (nome_i,), g in _agrupar(idx.get(k, []), "indice").items():
            unico = " único" if g[0]["unico"] else ""
            out.append(f"- índice{unico} `{nome_i}` {_fmt(g[0]['tipo']).lower()} "
                       f"({', '.join(x['coluna'] for x in g)})")
        out.append("")

    params = _agrupar(d.get("parametros", []), "esquema", "objeto")
    deps = _agrupar(d.get("dependencias", []), "esquema", "objeto")
    out += ["## Procedures, functions, views e triggers", "",
            "| objeto | tipo | parâmetros | referencia | criado | modificado | corpo |",
            "|---|---|---|---|---|---|---|"]
    for m in mods:
        k = (m["esquema"], m["nome"])
        ps = ", ".join(f"{p['parametro']} {p['tipo']}" + (" OUTPUT" if p["saida"] else "")
                       for p in params.get(k, [])) or "—"
        rs = ", ".join(sorted({f"{x['esquema_ref'] or m['esquema']}.{x['referencia']}"
                               for x in deps.get(k, [])})) or "—"
        corpo = (f"`banco/{nome_arquivo(m['esquema'], m['nome'])}`" if m["corpo"] is not None
                 else "não extraído (ver Lacunas)")
        out.append(f"| `{m['esquema']}.{m['nome']}` | {_fmt(m['tipo']).lower()} | {ps} | {rs} | "
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
                       f"{', '.join(f'`{c}`' for c in chamados) or '—'} |")
    else:
        out.append("Nenhum job visível para esta base (ou sem permissão em `msdb` — ver Lacunas).")
    out.append("")

    out += ["## Segredos mascarados", "",
            f"Valor nunca exibido nem gravado — o `.sql` versionado leva `{MASCARA}` no lugar.", ""]
    if segredos:
        out += ["| objeto | linha do corpo original | tipo |", "|---|---|---|"]
        out += [f"| `{o}` | {n} | {t} |" for o, n, t in segredos]
    else:
        out.append("Nenhum encontrado pelos padrões da varredura (PWD=/Password=, WITH PASSWORD, "
                   "sp_addlinkedsrvlogin, SECRET=/IDENTITY=, OPENROWSET).")
    out += ["", "## Lacunas", ""]
    out += [f"- {l}" for l in catalogo.lacunas]
    out.append("- **Não coberto por desenho:** triggers de DDL do banco (não pertencem a esquema) · SQL montado "
               "em runtime (ver o aviso do cruzamento) · dado de negócio (o inventário não lê linha de tabela).")
    return "\n".join(out) + "\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (61 passed)

- [ ] **Step 5: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): banco.md - retrato sem corpo nem segredo, frase de guarda no cruzamento

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: `gerar()` + CLI `main()` — ponta a ponta com conexão falsa

**Files:**
- Modify: `templates/inventario_banco.py` (acrescentar antes de `def main` e **substituir** o `main` provisório)
- Test: `tests/test_inventario_banco.py`

- [ ] **Step 1: Write the failing tests**

Acrescente ao fim do arquivo de teste:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: FAIL — `TypeError: main() got an unexpected keyword argument 'env'` / `AttributeError: ... 'ErroSaida'`.

- [ ] **Step 3: Write the implementation**

Acrescente antes de `def main`:
```python
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
    citacoes = cruzar(catalogo, indexar_codigo(proj, excluir=destino / "banco"))
    gravados, removidos, preservados, segredos = gravar_corpos(catalogo, destino / "banco")
    md.write_text(renderizar_md(proj.name, origem, hoje or dt.date.today().isoformat(),
                                catalogo, citacoes, segredos), encoding="utf-8")
    linha = ""
    if out is None:
        gi = proj / ".gitignore"
        ancoradas = {l.strip() for l in gi.read_text(encoding="utf-8-sig").splitlines()} if gi.exists() else set()
        linha = "" if "/docs/banco.md" in ancoradas else "/docs/banco.md"
    return Relatorio(md, destino / "banco", len(objetos(catalogo)), gravados, removidos, preservados,
                     segredos, catalogo.lacunas, linha)


def relatorio_texto(rel):
    out = [f"inventário gerado: {rel.md}",
           f"objetos: {rel.total_objetos} · corpos gravados: {len(rel.gravados)} em {rel.pasta_sql}"]
    if rel.removidos:
        out.append("removidos (sumiram do banco): " + ", ".join(rel.removidos))
    if rel.preservados:
        out.append("em docs/banco/ mas NÃO são do inventário (não mexi): " + ", ".join(rel.preservados))
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
```

**Substitua** o `main` provisório (as 2 linhas `def main(argv=None):` / `raise SystemExit(...)`) por:
```python
def main(argv=None, env=None, conectar_fn=None):
    ap = argparse.ArgumentParser(description="Inventário somente-leitura do banco vivo (SQL Server).")
    ap.add_argument("--proj", help="diretório do projeto (default: diretório atual)")
    ap.add_argument("--out", help="pasta de saída (default: <proj>/docs)")
    ap.add_argument("--fonte", help="get_connection.py de um projeto MSIG que alcança o servidor (lido por ast)")
    ap.add_argument("--ambiente", default="D0", help="D0 | HML | PRD (default: D0)")
    ap.add_argument("--par", help="base da fonte cujo par reaproveitar, quando a fonte tem mais de uma")
    ap.add_argument("--base", help="base a inventariar (sobrescreve o Database= da conn string)")
    ap.add_argument("--porta", help="sobrescreve a porta do servidor")
    ap.add_argument("--max-objetos", type=int, default=MAX_OBJETOS_PADRAO)
    args = ap.parse_args(argv)
    env = os.environ if env is None else env
    conectar_fn = conectar_fn or conectar
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
        rel = gerar(args.proj or Path.cwd(), conn.cursor(), conexao.origem,
                    out=args.out, max_objetos=args.max_objetos)
    except (ErroTeto, ErroSaida) as e:
        print(f"[inventario-banco] {e}", file=sys.stderr)
        return 4
    finally:
        conn.close()
    print(relatorio_texto(rel))
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inventario_banco.py -v`
Expected: PASS (68 passed)

- [ ] **Step 5: Rodar a suíte inteira (passo próprio)**

Run: `python -m pytest -q`
Expected: `404 passed` (336 anteriores + 68 novos)

- [ ] **Step 6: Commit**

```bash
git add templates/inventario_banco.py tests/test_inventario_banco.py
git commit -m "feat(inventario-banco): gerar() e CLI ponta a ponta, sem sobrescrever o que nao e nosso

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Comando `/mss-spec:inventario-banco`, `.gitignore` e LEIA-ME

**Files:**
- Create: `commands/inventario-banco.md`
- Modify: `.gitignore` (depois da linha `/docs/bpmn/`), `templates/gitignore` (idem), `docs/LEIA-ME.md` (depois da linha do `/mss-spec:bpmn`)
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Write the failing test**

Acrescente ao fim de `tests/test_smoke_kit.py`:
```python
def test_inventario_banco_wiring():
    """4º gerador determinístico: script testável + comando fino + retrato fora do git ANCORADO em
    /docs/ — 'banco.md' SOLTO no .gitignore ignoraria o commands/banco.md que já existe (mesma armadilha
    do bpmn). Os corpos .sql são versionados de propósito: docs/banco/ NÃO entra no .gitignore.
    O comportamento do gerador vive em tests/test_inventario_banco.py."""
    assert (REPO / "templates" / "inventario_banco.py").exists(), "falta templates/inventario_banco.py"
    cmd = (REPO / "commands" / "inventario-banco.md").read_text(encoding="utf-8")
    low = cmd.lower()
    assert "templates/inventario_banco.py" in cmd, "comando não aponta o gerador"
    assert "fora do git" in low and "versionado" in low, "comando não declara o que vai e o que não vai pro git"
    assert "pro assistente" in low, "comando não carrega 'visual é pro humano; dados pro assistente'"
    assert "nunca peça senha digitada" in low, "comando não carrega 'reusar o que já conecta'"
    assert "pode apagar" in low, "comando não carrega a frase de guarda contra DROP"
    assert "nunca o valor" in low, "comando não proíbe exibir o valor do segredo"
    for gi_path in ("templates/gitignore", ".gitignore"):
        linhas = [l.strip() for l in (REPO / gi_path).read_text(encoding="utf-8").splitlines()]
        assert "/docs/banco.md" in linhas, f"{gi_path} não ancora /docs/banco.md"
        assert "banco.md" not in linhas, f"{gi_path}: 'banco.md' solto ignoraria commands/banco.md"
        assert "/docs/banco/" not in linhas, f"{gi_path}: os .sql são versionados — não ignore docs/banco/"
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    assert "/mss-spec:inventario-banco" in leiame, "LEIA-ME não lista o comando"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke_kit.py -k inventario_banco -v`
Expected: FAIL — `FileNotFoundError: ... commands\inventario-banco.md`

- [ ] **Step 3: Criar o comando**

Crie `commands/inventario-banco.md`:
````markdown
---
description: Inventário somente-leitura do banco vivo (SQL Server) — catálogo, corpo das procedures/functions/views/triggers, jobs e linked servers, cruzado com o código; o /mss-spec:analise dispara sozinho, este comando regenera
argument-hint: "[base] (vazio: usa o ponteiro da seção Dados do docs/ARQUITETURA.md)"
---

**Responda sempre em português (pt-BR).**

Regenera o **inventário do banco vivo** deste projeto. Na primeira vez quem dispara é o `/mss-spec:analise` (passo *Dados — banco vivo*); aqui é o atalho pra rodar de novo quando o banco mudou, sem reanalisar o código.

1. **Credencial — nunca peça senha digitada.** Leia o ponteiro na seção *Dados* do `docs/ARQUITETURA.md` (servidor · base · ambiente · qual `get_connection.py` emprestou o par). Sem ponteiro, pergunte **qual base** e **qual projeto MSIG já alcança esse servidor**. Alternativa: a variável `MSS_INVENTARIO_CONN` com a conn string (serve `Trusted_Connection=yes`).

2. **Rode o gerador** (somente-leitura, só catálogo):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/templates/inventario_banco.py" --proj . --fonte <get_connection.py> --ambiente D0 --base <base>
   ```

   `--par <BASE>` quando a fonte tem mais de um par (sem ele o script para e lista os nomes) · `--porta N` · `--max-objetos N` (default 2000) · `--out <dir>`. Se `${CLAUDE_PLUGIN_ROOT}` não resolver, ache o script nos locais padrão (`~/.claude/plugins/cache/.../mss-spec/templates/inventario_banco.py` ou o clone apontado pelo junction/skills-dir). Não achou → **PARE com erro claro**; nunca invente caminho. O `--fonte` é **lido por `ast`**, nunca importado: o código do outro projeto não roda.

3. **Saídas:**
   - `docs/banco.md` — retrato em texto, **pro assistente**; **fora do git** (linha ancorada `/docs/banco.md`). O script avisa se ela falta no `.gitignore`: **pergunte** antes de acrescentar (em projeto que já existia o `.gitignore` é do projeto).
   - `docs/banco/<esquema>.<objeto>.sql` — corpo de cada objeto, **versionado**, UTF-8 com BOM, segredo mascarado antes de gravar. É documentação, não script executável.
   - O script só sobrescreve ou remove arquivo com a marca `[inventario-banco]`: um `docs/banco.md` do time faz ele parar; `.sql` alheio em `docs/banco/` fica e é listado.

4. **Reporte** o que o script imprimiu: objetos, segredos mascarados (objeto + tipo — **nunca o valor**), lacunas (corpo criptografado, falta de `VIEW DEFINITION`, `msdb`), arquivos removidos. Atualize as contagens na seção *Dados* do `docs/ARQUITETURA.md`.

**"Sem citação" não significa "pode apagar"** — significa "não encontrei citação textual"; SQL montado em runtime não aparece na busca. Nunca proponha `DROP` a partir deste inventário.

Erro de conexão vem classificado: **REDE** (53/timeout — fora da rede corporativa nada responde), **CREDENCIAL** (login recusado) ou **PERMISSÃO** (o login não abre a base — conserto do owner).
````

- [ ] **Step 4: Âncora nos dois `.gitignore`**

Em `.gitignore` **e** em `templates/gitignore`, logo depois da linha `/docs/bpmn/`, acrescente:
```
# Inventario do banco vivo (/mss-spec:inventario-banco) - o RETRATO docs/banco.md e derivado e fica
# fora do git, ANCORADO em /docs/ (solto, 'banco.md' ignoraria o commands/banco.md). Os corpos
# docs/banco/*.sql sao VERSIONADOS de proposito: unica copia da regra de negocio fora do servidor.
/docs/banco.md
```

- [ ] **Step 5: Linha no LEIA-ME**

Em `docs/LEIA-ME.md`, logo depois da linha que começa com `` | `/mss-spec:bpmn` ``, acrescente:
```
| `/mss-spec:inventario-banco` | **Inventário somente-leitura do banco vivo (SQL Server):** catálogo, corpo de procedure/function/view/trigger, jobs e linked servers; cruza cada nome com o código (*citado no código* × *só no banco* × *sem citação* — que **não** significa "pode apagar"). O `/mss-spec:analise` dispara sozinho; este comando regenera. `docs/banco.md` fora do git + `docs/banco/*.sql` versionados, segredo mascarado |
```
Depois confira se o LEIA-ME escreve a quantidade de comandos em algum lugar:

Run: `grep -n -i "[0-9][0-9] comandos\|[0-9][0-9] atalhos" docs/LEIA-ME.md`
Expected: nenhuma linha. Se aparecer, atualize o número para 25.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_smoke_kit.py -v`
Expected: PASS (inclusive `test_plugin_root_refs_existem` e `test_templates_citados_existem`, que agora validam o caminho novo)

- [ ] **Step 7: Commit**

```bash
git add commands/inventario-banco.md .gitignore templates/gitignore docs/LEIA-ME.md tests/test_smoke_kit.py
git commit -m "feat(inventario-banco): comando fino, /docs/banco.md ancorado nos gitignores, LEIA-ME

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 14: A `analise` dispara sozinha

**Files:**
- Modify: `commands/analise.md` (regra dura + fase 2 + passo 4)
- Modify: `templates/ARQUITETURA.md` (seção 5)
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Write the failing test**

Acrescente ao fim de `tests/test_smoke_kit.py`:
```python
def test_analise_dispara_inventario_do_banco():
    """O owner não sabe o nome do comando ('eu vou usar o analise, ele vai ter que ser inteligente o
    suficiente') — a analise dispara o inventário por EVIDÊNCIA no código, pergunta só a credencial, e a
    regra dura abre exceção pros .sql gerados (senão proibiria a própria saída do inventário)."""
    an = (REPO / "commands" / "analise.md").read_text(encoding="utf-8")
    low = an.lower()
    assert "templates/inventario_banco.py" in an, "analise.md não roda o gerador do inventário"
    for evidencia in ("connectionStrings", "SqlConnection", "get_connection.py"):
        assert evidencia in an, f"analise.md não dispara o inventário pela evidência {evidencia}"
    assert "MSS_INVENTARIO_CONN" in an
    assert "nunca peça senha digitada" in low
    assert "pode apagar" in low
    assert "docs/banco/" in an, "analise.md não abre a exceção dos .sql gerados pelo inventário"
    tpl = (REPO / "templates" / "ARQUITETURA.md").read_text(encoding="utf-8")
    assert "Banco vivo (inventário)" in tpl, "ARQUITETURA.md não tem onde destilar o inventário"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke_kit.py -k dispara_inventario -v`
Expected: FAIL — `analise.md não roda o gerador do inventário`

- [ ] **Step 3: Exceção na regra dura**

Em `commands/analise.md`, Edit — old:
```
- **código**: qualquer `.py`/`.ts`/`.tsx`/`.js`/`.sql`, `config/logging.py`, `utils/get_connection.py`, `requirements.txt`/`package.json`;
```
new:
```
- **código**: qualquer `.py`/`.ts`/`.tsx`/`.js`/`.sql`, `config/logging.py`, `utils/get_connection.py`, `requirements.txt`/`package.json` — **exceção única:** os `docs/banco/*.sql` que o inventário do banco grava são documentação (corpo extraído do catálogo, com marca `[inventario-banco]`), não código do projeto;
```

- [ ] **Step 4: Passo novo na fase 2**

Em `commands/analise.md`, Edit — old:
```
- **Config**: `config/`, `settings.*`, `.env.example` — **quais chaves o código realmente lê**.
```
new:
```
- **Dados — banco vivo** (disparo automático, não é menu). Achou evidência de banco — `<connectionStrings>` em `web.config`/`app.config`, `SqlConnection`/`SqlCommand`/`SqlDataAdapter`/`.edmx`/Dapper/EF nos `.cs`, `utils/get_connection.py`, `pyodbc`, `psycopg`, SQLAlchemy — **diga a evidência e inventarie**: o `.sql` do repo não traz a regra de negócio que mora em procedure, trigger e job.
  - Pergunte **só** qual base e de onde vem a credencial — é o portão da conexão. **Nunca peça senha digitada**: reuse o `get_connection.py` de um projeto MSIG que alcança o servidor, ou a variável `MSS_INVENTARIO_CONN`. Detectar ≠ usar: da `<connectionStrings>` leia só `Server=`/`Initial Catalog=`, nunca a senha.
  - Rode `python "${CLAUDE_PLUGIN_ROOT}/templates/inventario_banco.py" --proj . --fonte <get_connection.py> --ambiente D0 --base <base>` (`--par <BASE>` quando a fonte tem mais de uma base). Erro vem classificado em REDE/CREDENCIAL/PERMISSÃO — repasse ao owner como veio.
  - Destile o `docs/banco.md` na seção *Dados* do dossiê (contagens, modelo, e o **ponteiro**: servidor, base, ambiente, qual projeto emprestou o par — caminho, nunca valor) e os linked servers/jobs nas *Conexões* do MAPA, levando junto a frase **"sem citação" não significa "pode apagar"**.
  - O script avisa se falta `/docs/banco.md` no `.gitignore`: **pergunte** antes de acrescentar. Owner disse "pula" → linha em *Lacunas*. Regenerar depois: `/mss-spec:inventario-banco`.
- **Config**: `config/`, `settings.*`, `.env.example` — **quais chaves o código realmente lê**.
```

- [ ] **Step 5: Seção 5 do dossiê**

Em `templates/ARQUITETURA.md`, Edit — old:
```
- **DDL versionada?** <sim (`sql/NN_*.sql`) | não — como o esquema é criado hoje>
```
new:
```
- **DDL versionada?** <sim (`sql/NN_*.sql`) | não — como o esquema é criado hoje>
- **Banco vivo (inventário):** <`docs/banco.md` gerado em <data> · N tabelas · N procedures · N sem citação no código · N corpo não extraído — ou "não inventariado: <motivo>", repetido em Lacunas>
- **Credencial do inventário:** <servidor · base · ambiente · `get_connection.py` de qual projeto (caminho, nunca valor) | variável `MSS_INVENTARIO_CONN`>
- > "Sem citação" não significa "pode apagar" — significa "não encontrei citação textual".
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_smoke_kit.py -v`
Expected: PASS (inclusive o `test_analise_wiring` que já existia)

- [ ] **Step 7: Commit**

```bash
git add commands/analise.md templates/ARQUITETURA.md tests/test_smoke_kit.py
git commit -m "feat(analise): dispara o inventario do banco por evidencia no codigo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 15: `COMO-FUNCIONA.html` — 5 cards, "Os 25 atalhos", contagem travada

Hoje o HTML diz **"Os 20 atalhos"** e tem 20 cards, mas `commands/` tem 24 arquivos (25 depois da Task 13). Faltam `anatomia`, `bpmn`, `diagnostico`, `divergir` e `inventario-banco`.

**Files:**
- Modify: `docs/COMO-FUNCIONA.html`
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Write the failing test**

Acrescente ao fim de `tests/test_smoke_kit.py`:
```python
def test_como_funciona_lista_todos_os_comandos():
    """Contagem travada: o COMO-FUNCIONA.html já ficou 4 comandos defasado (consertado à mão) e estava de
    novo em 20 × 24. Todo arquivo de commands/ tem card id="c-<nome>" (hífen ignorado: to-dolist ↔
    c-todolist), o número em 'Os N atalhos' bate com a pasta e a numeração C1..CN é contínua."""
    html = (REPO / "docs" / "COMO-FUNCIONA.html").read_text(encoding="utf-8")
    comandos = {p.stem.replace("-", "") for p in _command_files()}
    cards = {c.replace("-", "") for c in re.findall(r'<div class="node" id="c-([a-z-]+)"', html)}
    assert not comandos - cards, f"comando sem card no COMO-FUNCIONA.html: {sorted(comandos - cards)}"
    assert not cards - comandos, f"card sem comando: {sorted(cards - comandos)}"
    m = re.search(r"Os (\d+) atalhos", html)
    assert m, "COMO-FUNCIONA.html perdeu a frase 'Os N atalhos'"
    assert int(m.group(1)) == len(comandos), f"'Os {m.group(1)} atalhos', mas há {len(comandos)} comandos"
    idx = [int(n) for n in re.findall(r'<span class="node-idx">C(\d+)</span>', html)]
    assert idx == list(range(1, len(comandos) + 1)), "numeração C1..CN dos cards fora de ordem"
    # a nav lateral tem 1 link por card, na mesma ordem e com a mesma numeração
    nav = re.findall(r'<a href="#c-([a-z-]+)"><span class="nav-num">C(\d+)</span>', html)
    ordem_cards = re.findall(r'<div class="node" id="c-([a-z-]+)"', html)
    assert [c for c, _ in nav] == ordem_cards, "nav lateral fora da ordem dos cards (ou card sem link)"
    assert [int(n) for _, n in nav] == list(range(1, len(comandos) + 1)), "numeração C1..CN da nav lateral"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke_kit.py -k como_funciona_lista -v`
Expected: FAIL — `comando sem card no COMO-FUNCIONA.html: ['anatomia', 'bpmn', 'diagnostico', 'divergir', 'inventariobanco']`

- [ ] **Step 3: Card `inventario-banco` (seção "Começar", depois do card `c-analise`)**

Insira imediatamente **antes** da linha `  <div class="node" id="c-doctor">`:
```html
  <div class="node" id="c-inventario-banco">
    <div class="node-head"><span class="node-idx">C3</span><span class="node-name">inventario-banco</span><span class="node-type">o que mora no banco</span></div>
    <div class="node-body">
      <p class="plain">Lê o banco de dados de verdade — tabelas, procedures, triggers e jobs — sem tocar em nenhum dado.</p>
      <p>Num sistema antigo, a regra de negócio costuma estar <strong>dentro do banco</strong>, não no código. O <code>/mss-spec:analise</code> dispara este inventário sozinho quando acha sinal de banco no projeto; o comando existe para <strong>regenerar</strong> quando o banco mudar. Reaproveita a credencial de um projeto MSIG que já conecta no mesmo servidor — ninguém digita senha — e só lê o <em>catálogo</em>: estrutura e código, nunca linha de tabela.</p>
      <p>Cruza cada nome com os arquivos do projeto e marca <strong>citado no código</strong>, <strong>citado só no banco</strong> (chamado por outra procedure ou job) ou <strong>sem citação</strong>. E avisa: <em>"sem citação" não significa "pode apagar"</em> — SQL montado em tempo de execução não aparece na busca.</p>
      <div class="subhead">Exemplo</div>
      <pre><code>/mss-spec:inventario-banco
  → docs/banco.md      (retrato pro assistente, fora do git)
  → docs/banco/*.sql   (corpo de cada procedure, versionado, segredo mascarado)</code></pre>
      <div class="label-row"><span class="pill ok">somente-leitura</span><span class="pill graph">só catálogo</span></div>
    </div>
  </div>

```

- [ ] **Step 4: Card `divergir` (seção "Construir", depois de `c-precedentes`)**

Insira imediatamente **antes** da linha `  <h3>Apoio no dia a dia</h3>`:
```html
  <div class="node" id="c-divergir">
    <div class="node-head"><span class="node-idx">C11</span><span class="node-name">divergir</span><span class="node-type">antes de escolher</span></div>
    <div class="node-body">
      <p class="plain">Quando a decisão é aberta e cara de desfazer, gera abordagens de verdade diferentes antes de escolher uma.</p>
      <p>Cada abordagem nasce num assistente separado, com um ponto de partida próprio, para ninguém ser puxado pela primeira ideia. Depois a janela principal critica, dá nota e marca as armadilhas. Custa cerca de dez chamadas, e isso é anunciado antes; se já existe precedente na MSIG, reaproveitar vence divergir.</p>
      <div class="subhead">Exemplo</div>
      <pre><code>/mss-spec:divergir "fila de reprocessamento: tabela, Service Bus ou job?"
  → abordagens independentes · crítica e nota · armadilha sedutora marcada</code></pre>
      <div class="label-row"><span class="pill graph">anti-ancoragem</span><span class="pill ok">só em decisão aberta e cara</span></div>
    </div>
  </div>

```

- [ ] **Step 5: Card `diagnostico` (seção "Apoio no dia a dia", depois de `c-todolist`)**

Insira imediatamente **antes** da linha `  <h3>Verificar &amp; publicar</h3>`:
```html
  <div class="node" id="c-diagnostico">
    <div class="node-head"><span class="node-idx">C15</span><span class="node-name">diagnostico</span><span class="node-type">quando trava</span></div>
    <div class="node-body">
      <p class="plain">Um trilho para investigar problema sem ficar chutando hipótese atrás de hipótese.</p>
      <p>Antes de pedir mais evidência a você, compara o que quebrou com o precedente que funciona (outro projeto, outra versão, outro ambiente). O que você já afirmou como fato não é rediscutido.</p>
      <div class="subhead">Exemplo</div>
      <pre><code>/mss-spec:diagnostico "503 na nuvem, local funciona"
  → diff contra o que funciona → causa → conserto</code></pre>
      <div class="label-row"><span class="pill ok">corta o loop</span><span class="pill graph">precedente antes de pergunta</span></div>
    </div>
  </div>

```

- [ ] **Step 6: Card `bpmn` (seção "Manter & compartilhar", depois de `c-documentacao`)**

Insira imediatamente **antes** da linha `  <h3>Contexto &amp; memória (anti-amnésia)</h3>`:
```html
  <div class="node" id="c-bpmn">
    <div class="node-head"><span class="node-idx">C22</span><span class="node-name">bpmn</span><span class="node-type">processo desenhado</span></div>
    <div class="node-body">
      <p class="plain">Desenha os processos do sistema em BPMN, lendo o código.</p>
      <p>Um diagrama por porta de entrada (cada rota, ou cada <code>main()</code>), com os subprocessos abrindo em diagramas próprios. Sai em três formas: a página com o desenho, os arquivos <code>.bpmn</code> que abrem no Bizagi, e um texto que o assistente consulta. Hoje lê só código Python.</p>
      <div class="subhead">Exemplo</div>
      <pre><code>/mss-spec:bpmn
  → docs/bpmn.html · docs/bpmn/*.bpmn · docs/bpmn.md   (fora do git)</code></pre>
      <div class="label-row"><span class="pill graph">derivado do código</span><span class="pill ok">abre no Bizagi</span></div>
    </div>
  </div>

```

- [ ] **Step 7: Card `anatomia` (seção "Contexto & memória", depois de `c-mapa-neural`)**

O card `c-mapa-neural` é o último da seção `comandos`, que fecha com `</section>` na linha seguinte ao `</div>` dele. Insira o card entre o `</div>` que fecha `c-mapa-neural` e esse `</section>` — ou seja, imediatamente antes da **primeira** linha `</section>` que aparece **depois** de `id="c-mapa-neural"`:
```html

  <div class="node" id="c-anatomia">
    <div class="node-head"><span class="node-idx">C25</span><span class="node-name">anatomia</span><span class="node-type">raio-x do kit</span></div>
    <div class="node-body">
      <p class="plain">Um painel que mostra quando cada peça do kit entra em ação e quem lê ou escreve cada arquivo.</p>
      <p>Quatro visões: o momento em que cada peça dispara (partida, evento, sob demanda, fecho), a matriz de quem lê × quem escreve, os riscos e a fila de trabalho. Os números são medidos na hora; o painel é para você — o assistente continua lendo os arquivos de contexto.</p>
      <div class="subhead">Exemplo</div>
      <pre><code>/mss-spec:anatomia
  → docs/anatomia.html   (fora do git)</code></pre>
      <div class="label-row"><span class="pill graph">números medidos</span><span class="pill ok">visual é pro humano</span></div>
    </div>
  </div>
```

- [ ] **Step 8: Os 5 links na navegação lateral**

A nav (bloco `<div class="nav-group">…`, perto da linha 124) tem um `<li>` por comando, na ordem dos cards. Insira cada linha abaixo **logo depois** do `<li>` indicado (os números são provisórios — o Step 9 renumera):

depois de `<li><a href="#c-analise">…analise</a></li>`:
```html
      <li><a href="#c-inventario-banco"><span class="nav-num">C3</span>inventario-banco</a></li>
```
depois de `<li><a href="#c-precedentes">…precedentes</a></li>`:
```html
      <li><a href="#c-divergir"><span class="nav-num">C11</span>divergir</a></li>
```
depois de `<li><a href="#c-todolist">…to-dolist</a></li>`:
```html
      <li><a href="#c-diagnostico"><span class="nav-num">C15</span>diagnostico</a></li>
```
depois de `<li><a href="#c-documentacao">…documentacao</a></li>`:
```html
      <li><a href="#c-bpmn"><span class="nav-num">C22</span>bpmn</a></li>
```
depois de `<li><a href="#c-mapa-neural">…mapa-neural</a></li>`:
```html
      <li><a href="#c-anatomia"><span class="nav-num">C25</span>anatomia</a></li>
```

- [ ] **Step 9: "Os 25 atalhos" e renumeração C1..C25 (cards e nav)**

Edit em `docs/COMO-FUNCIONA.html` — old: `Os 20 atalhos` → new: `Os 25 atalhos`.

Depois renumere cards e nav, cada um pela ordem em que aparece (contadores separados):

Run:
```bash
python -c "import re,pathlib,itertools; p=pathlib.Path('docs/COMO-FUNCIONA.html'); h=p.read_text(encoding='utf-8'); a=itertools.count(1); h=re.sub(r'<span class=\"node-idx\">C\d+</span>', lambda m: f'<span class=\"node-idx\">C{next(a)}</span>', h); b=itertools.count(1); h=re.sub(r'<span class=\"nav-num\">C\d+</span>', lambda m: f'<span class=\"nav-num\">C{next(b)}</span>', h); p.write_text(h, encoding='utf-8')"
```

- [ ] **Step 10: Run tests to verify they pass**

Run: `python -m pytest tests/test_smoke_kit.py -v`
Expected: PASS (inclusive `test_redes_de_seguranca_documentadas`, que lê o mesmo HTML)

- [ ] **Step 11: Conferência visual**

Abra `docs/COMO-FUNCIONA.html` no navegador (Browser pane ou duplo clique) e confira: os 5 cards novos renderizam com o mesmo estilo dos vizinhos, a sequência C1..C25 aparece nas seções certas, e nenhum card quebrou o layout.

- [ ] **Step 12: Commit**

```bash
git add docs/COMO-FUNCIONA.html tests/test_smoke_kit.py
git commit -m "docs(como-funciona): 5 cards faltantes, 'Os 25 atalhos' e contagem travada por teste

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 16: Fecho — spec viva, decisões, CHANGELOG, versão, INDEX, MAPA

**Files:**
- Modify: `docs/specs/inventario-banco.md`, `docs/decisoes.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/superpowers/INDEX.md`, `docs/superpowers/MAPA.md`
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Write the failing test**

No fim de `test_inventario_banco_wiring` (em `tests/test_smoke_kit.py`), acrescente:
```python
    spec = (REPO / "docs" / "specs" / "inventario-banco.md").read_text(encoding="utf-8")
    assert "## Estado atual" in spec and "## Histórico" in spec, "spec viva sem as seções fixas"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke_kit.py -k inventario_banco_wiring -v`
Expected: FAIL — `spec viva sem as seções fixas`

- [ ] **Step 3: Spec viva vira "Estado atual"**

Em `docs/specs/inventario-banco.md`, Edit — old:
```
## Estado alvo (desenho aprovado em 2026-09-22 — **ainda não implementado**)
```
new:
```
## Estado atual (implementado na 0.28.0 — **não validado contra banco real**; ver Histórico)
```
E acrescente ao fim do arquivo:
```
- 2026-09-22 — implementado (0.28.0): `templates/inventario_banco.py` + `tests/test_inventario_banco.py`
  (68 testes, cursor falso), `/mss-spec:inventario-banco`, passo *Dados — banco vivo* na `analise`,
  `COMO-FUNCIONA.html` com os 5 cards que faltavam e contagem travada. **Falta o dogfood** no projeto
  C# contra o D0 — em especial conferir o regex do par (`<DEV|HML|PROD>_<BASE>_<KEY|CIPHERTEXT>`, tirado
  do molde do kit) contra o `get_connection.py` real usado como `--fonte`.
```

- [ ] **Step 4: Registro de decisão**

Em `docs/decisoes.md`, acrescente depois da linha que começa com `- 2026-09-15 — **o teto do índice de memória do repo é ORÇAMENTO`:
```
- 2026-09-22 — **inventário do banco vivo = 4º gerador determinístico com entrada automática pela `analise`** (`templates/inventario_banco.py` + `/mss-spec:inventario-banco` pra regenerar) em vez de **fase em prosa dentro da `analise`** (não-determinística, podia inventar query, e engordava o 2º maior comando já na fila de poda) ou **subcomando do `/mss-spec:banco`** (o `banco` é prescritivo; inventário é descritivo — a fronteira `ESTRUTURA.md` × `ARQUITETURA.md`). Credencial: **reusar o que já conecta** (par Fernet de outro projeto MSIG, lido por `ast`, `--base` por cima), sem arquivo de configuração novo — o ponteiro vive no `ARQUITETURA.md`. Só catálogo, nunca dado de negócio; corpos versionados com segredo mascarado; só mexe em arquivo com a marca `[inventario-banco]`; "sem citação" nunca vira "pode apagar". Spec: `docs/specs/inventario-banco.md`.
```

- [ ] **Step 5: CHANGELOG e versão**

Em `CHANGELOG.md`, insira logo **antes** da linha `## 0.27.0 — 2026-09-15 (orçamento de partida por script · recall por hook)`:
```
## 0.28.0 — 2026-09-22 (inventário do banco vivo)
- **o que motivou:** documentar um sistema C# parado há 6 anos com os dados num SQL Server D0. A `analise` lia só o `.sql` do repositório; num legado a regra de negócio mora **dentro do banco** (procedure, trigger, job). O kit tinha o conector (`get_connection.py`), mas nenhum comando mandava a análise usá-lo.
- feat(**`templates/inventario_banco.py`**, 4º gerador determinístico): somente-leitura e **só catálogo** (nenhuma linha de tabela lida — teste varre as queries); credencial reaproveitando o par Fernet de um projeto MSIG que já alcança o servidor, lido por `ast` (nunca importado), com `--base` sobrescrevendo o `Database=` e `--par` quando a fonte tem várias bases; ou `MSS_INVENTARIO_CONN`; senão erro que diz o que faltou. Cruza os nomes com o código de qualquer linguagem: *citado no código* × *citado só no banco* × *sem citação* — com a frase "sem citação não significa pode apagar". Corpos em `docs/banco/*.sql` **versionados** (UTF-8 com BOM, segredo mascarado); retrato `docs/banco.md` fora do git; só mexe em arquivo com a marca `[inventario-banco]`.
- feat(**`/mss-spec:analise` dispara sozinho**): passo *Dados — banco vivo* acionado por evidência (`<connectionStrings>`, `SqlConnection`, `get_connection.py`, `pyodbc`…) — o owner não precisa saber o nome do comando. `/mss-spec:inventario-banco` fica pra regenerar.
- test(**contagem do `COMO-FUNCIONA.html` travada**): estava em 20 cards × 24 comandos; ganhou `anatomia`, `bpmn`, `diagnostico`, `divergir` e `inventario-banco`, e um teste que prende cards, "Os N atalhos" e a numeração à pasta `commands/`.

```
Em `.claude-plugin/plugin.json` **e** `.claude-plugin/marketplace.json`, troque `"version": "0.27.0"` por `"version": "0.28.0"` (o `test_manifestos_validos_e_coerentes` exige os dois iguais).

- [ ] **Step 6: INDEX**

Em `docs/superpowers/INDEX.md`, logo depois da linha `5. upgrade — sincroniza projeto existente com a evolução dos templates — **em andamento** (sem commit)`, acrescente:
```
6. inventário do banco vivo — `/mss-spec:analise` inventaria o SQL Server sozinho (spec `docs/specs/inventario-banco.md`) — **em andamento** (implementado na 0.28.0; falta dogfood no projeto C# real)
7. cobertura C#/.NET na análise — `Program`/`Startup`, controllers, `.csproj`, rotas (o `bpmn` e o `mapa-neural` seguem só Python) — pausada: nasce depois do dogfood do item 6
```

- [ ] **Step 7: MAPA**

Em `docs/superpowers/MAPA.md`, na seção `## Onde estamos`, insira logo depois do título (antes do bloco atual) este parágrafo e uma linha em branco, e troque o comentário que já existe abaixo por nada (o bloco que era atual passa a ficar sob ele):
```
`feature/inventario-do-banco-vivo` — **v0.28.0 pronta na branch; merge/push são do owner.** Suíte **N verde** (N = o que o `pytest -q` do Step 8 imprimir; era 336). Entregue: `templates/inventario_banco.py` (4º gerador: somente-leitura, só catálogo, par Fernet reaproveitado lido por `ast` + `--base`/`--par`, cruzamento citado/só-no-banco/sem citação, corpos versionados com segredo mascarado, marca de autoria) · `/mss-spec:inventario-banco` · passo automático na `analise` · `COMO-FUNCIONA.html` com 25 cards e contagem travada. **Não validado contra banco real.** Spec: `docs/specs/inventario-banco.md`; plano em `plans/2026-09-22-inventario-banco.md`.

<!-- histórico do estado anterior -->
```
Na seção `## Próximo passo`, faça o mesmo com:
```
**Dogfood no projeto C# (janela própria, aberta no projeto — não aqui):** `/mss-spec:analise` tem que disparar o inventário sozinho pela `<connectionStrings>`; conferir o regex do par contra o `get_connection.py` real usado como `--fonte`; rodar duas vezes e ver o `git diff` dos `docs/banco/*.sql` vazio. Depois: item 7 do INDEX (C#/.NET), e o item 6 vira `fechada` no `INDEX-historico.md`.

<!-- histórico do próximo passo anterior -->
```
Remova os comentários `<!-- histórico do estado anterior -->` e `<!-- histórico do próximo passo anterior -->` **antigos** (fica um de cada, o que você acabou de inserir). Depois aplique o rodízio (o MAPA tem teto de 6.000 bytes travado por teste):

Run: `python templates/rodizio_partida.py mapa --proj .`
Expected: relatório de dry-run. Se ele listar blocos a mover, rode `python templates/rodizio_partida.py mapa --proj . --aplicar`.

- [ ] **Step 8: Suíte inteira (passo próprio)**

Run: `python -m pytest -q`
Expected: tudo verde — `407 passed` (336 + 68 do gerador + 3 do smoke). Troque o `N` do MAPA pelo número impresso.

- [ ] **Step 9: Commit**

```bash
git add docs/specs/inventario-banco.md docs/decisoes.md CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json docs/superpowers/INDEX.md docs/superpowers/MAPA.md docs/superpowers/MAPA-historico.md tests/test_smoke_kit.py
git commit -m "chore(release): 0.28.0 -- inventario do banco vivo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
(Se o rodízio não criou/alterou `docs/superpowers/MAPA-historico.md`, tire-o do `git add`.)

- [ ] **Step 10: Gate de pré-publicação**

Rode `/mss-spec:release` e cole o veredito. Verde → apresente ao owner as opções de integração (merge/PR/push são **ato dele**, do terminal dele). O item 6 do INDEX continua `em andamento` até o dogfood.

---

### Task 17 (fora desta janela): Dogfood no projeto C# real

Não é executável nesta janela: o owner determinou que esta sessão **não lê o projeto C#**. Registrado aqui pra não se perder (memória `project_dogfood_gerador_diff_antes_depois`: "fixture só contém o que eu imaginei").

- [ ] Abrir o Claude Code **na pasta do projeto C#** e rodar `/mss-spec:analise`.
- [ ] Conferir que o passo *Dados — banco vivo* disparou pela evidência, sem o owner citar o comando.
- [ ] Conferir que o `--fonte` real parseia (regex `<DEV|HML|PROD>_<BASE>_<KEY|CIPHERTEXT>`). Se a convenção do arquivo real for outra, o ajuste é **só** o `_RE_PAR` + um caso novo em `test_le_pares_por_ast_sem_importar` — de volta nesta janela do kit.
- [ ] Rodar o inventário duas vezes seguidas: `git diff docs/banco/` tem que sair vazio (a marca não tem data, o corpo é o mesmo).
- [ ] Abrir 2-3 `.sql` no SSMS/Visual Studio e conferir acento nos comentários (UTF-8 com BOM).
- [ ] Voltar ao kit: item 6 do INDEX vira `fechada` no `INDEX-historico.md`, e o que o dogfood destampou vira caso no `docs/EVALS.md` ou linha no Histórico da spec.
