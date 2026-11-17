"""O evento do hook, lido em UTF-8 — seja qual for a página de código do console.

Por que existe (medido em 2026-11-16, spec `docs/specs/sono-da-memoria.md`): os hooks liam a entrada com
`json.load(sys.stdin)`. Sem `PYTHONIOENCODING`, o Python filho no Windows lê o pipe como cp1252, e
"Já decidido — não reabrir:" chegava como `J\\xc3\\xa1 decidido \\xe2\\u20ac\\u201d n\\xc3\\xa3o…` — nenhum gatilho com
acento casava (o `passagem_de_conversa.py` devolvia "falta `Já decidido`" num bloco que tinha o título).

Lê os BYTES e decodifica em UTF-8. Texto que não é UTF-8 levanta exceção; quem chama já trata qualquer exceção da
leitura saindo calado (falha aberta), como antes. A saída dos hooks não muda.

Os hooks importam este módulo de dentro do `try` do `main()`: rodando como script (`python hooks/<hook>.py`), a
pasta `hooks/` é o `sys.path[0]`.
"""
import json
import sys


def ler_evento():
    """O JSON do evento que o Claude Code manda no stdin do hook, decodificado em UTF-8."""
    return json.loads(sys.stdin.buffer.read().decode("utf-8"))
