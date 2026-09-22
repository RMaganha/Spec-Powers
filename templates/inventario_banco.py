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
