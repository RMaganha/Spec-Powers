"""Os hooks leem o evento em UTF-8, seja qual for a página de código do console.

Causa medida em 2026-11-16 (conversa d23210d6): os hooks liam a entrada com `json.load(sys.stdin)`. Sem
`PYTHONIOENCODING`, o Python filho no Windows lê o pipe como cp1252 e "Já decidido — não reabrir:" chega como
`J\\xc3\\xa1 decidido \\xe2\\u20ac\\u201d n\\xc3\\xa3o…`: o `RE_TITULO_DECIDIDO` não casa e o hook devolve "falta
`Já decidido`" num bloco que tem o título. O mesmo vale pra todo gatilho com acento dos outros hooks.

Conserto: `hooks/_entrada.py` (`ler_evento`) lê os bytes e decodifica em UTF-8; texto que não é UTF-8 → o hook
falha aberto, como antes.

Os testes de processo mandam bytes UTF-8 CRUS (não o `json.dumps` em ASCII dos outros testes, que nunca viu o
problema) com o ambiente SEM `PYTHONIOENCODING`/`PYTHONUTF8` — a condição real. No Linux do CI o pipe já é UTF-8
e eles só passam; quem discrimina é o Windows.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PASTA_HOOKS = REPO / "hooks"
PASSAGEM = PASTA_HOOKS / "passagem_de_conversa.py"

BLOCO = (
    "/mss-spec:tarefa consertar o acento dos hooks\n"           # 1ª linha com a porta do kit (0.67.0, F-077)
    "Já decidido — não reabrir:\n"
    "1. A entrada é lida em UTF-8.\n"
    "2. Texto que não é UTF-8 faz o hook falhar aberto.\n"
    "Falta decidir:\n"
    "1. nada\n"
    "Regras desta conversa: o que está decidido não se reabre.\n"
)


def _ambiente(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    env.update({"TEMP": str(tmp_path), "TMP": str(tmp_path),
                "MSS_REGISTRO_ARQUIVO": str(tmp_path / "registro.jsonl")})
    return env


def _rodar(hook, dados: bytes, tmp_path):
    return subprocess.run([sys.executable, str(hook)], input=dados, capture_output=True, env=_ambiente(tmp_path),
                          cwd=str(tmp_path))


def _bytes(evento) -> bytes:
    return json.dumps(evento, ensure_ascii=False).encode("utf-8")


def test_pedido_com_titulo_acentuado_e_reconhecido(tmp_path):
    evento = {"hook_event_name": "UserPromptSubmit", "session_id": "s-utf8-pedido", "prompt": BLOCO}
    proc = _rodar(PASSAGEM, _bytes(evento), tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip(), "o hook não reconheceu o título `Já decidido` (entrada lida fora de UTF-8)"
    contexto = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "2 item(ns) do owner como DECIDIDOS" in contexto


def test_bloco_entregue_com_titulo_acentuado_nao_e_devolvido(tmp_path):
    """O sintoma medido: no `Stop`, o bloco completo voltava com "falta no bloco `Já decidido`"."""
    resposta = "Abra uma conversa nova e cole o texto pronto abaixo:\n\n```\n" + BLOCO + "```\n"
    evento = {"hook_event_name": "Stop", "session_id": "s-utf8-fim", "last_assistant_message": resposta}
    proc = _rodar(PASSAGEM, _bytes(evento), tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == b"", proc.stdout.decode("utf-8", "replace")


def test_entrada_que_nao_e_utf8_falha_aberto(tmp_path):
    evento = {"hook_event_name": "UserPromptSubmit", "session_id": "s-utf8-ruim", "prompt": BLOCO}
    proc = _rodar(PASSAGEM, json.dumps(evento, ensure_ascii=False).encode("cp1252"), tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == b""


def _hooks_registrados():
    comandos = json.loads((PASTA_HOOKS / "hooks.json").read_text(encoding="utf-8"))
    nomes = set()
    for grupos in comandos["hooks"].values():
        for grupo in grupos:
            for h in grupo["hooks"]:
                nomes.update(re.findall(r"hooks/(\w+\.py)", h["command"]))
    return sorted(nomes)


def test_os_18_hooks_registrados():
    assert len(_hooks_registrados()) == 18, _hooks_registrados()


@pytest.mark.parametrize("nome", _hooks_registrados())
def test_hook_le_o_evento_pela_funcao_comum(nome):
    fonte = (PASTA_HOOKS / nome).read_text(encoding="utf-8")
    assert not re.search(r"sys\.stdin(?!\.buffer)", fonte), f"{nome} lê `sys.stdin` em texto"
    assert "ler_evento(" in fonte, f"{nome} não lê o evento por `_entrada.ler_evento`"


def test_funcao_comum_le_bytes_em_utf8():
    fonte = (PASTA_HOOKS / "_entrada.py").read_text(encoding="utf-8")
    assert "sys.stdin.buffer.read()" in fonte and '.decode("utf-8")' in fonte
