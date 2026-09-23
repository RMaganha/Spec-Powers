"""Cerca do pipe — o commit não sai quando um pipe esconde o resultado do pytest (caso F-025).

`python -m pytest … | tail -1 && git commit …` commitou com 2 testes vermelhos (`edc0ab9`,
2026-09-15): num pipe, o código de saída é o do ÚLTIMO comando (o `tail`), e o `&&` só olha esse.
A memória `feedback_pipe_mascara_o_exit_do_teste` não bastou — reincidiu em `f9388e5`. Por isso
cerca, não prosa: vive no processo do `git_publicacao.py` (mesmo evento, custo extra ~0 ms), com
modo de falha PRÓPRIO — ABERTA (commit vermelho se reverte; push não).
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "git_publicacao.py"


def _mod():
    spec = importlib.util.spec_from_file_location("git_publicacao", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evento(comando, tool="Bash"):
    return {"hook_event_name": "PreToolUse", "cwd": str(REPO),
            "tool_name": tool, "tool_input": {"command": comando}}


# --- AC1: pytest com pipe + git commit no mesmo comando é negado -------------------------

@pytest.mark.parametrize("comando", [
    # os dois comandos reais do F-025
    "python -m pytest tests/ -q | tail -1 && git commit -m 'feat: x'",
    "python -m pytest -q 2>&1 | tail -1 && git add hooks/x.py tests/test_x.py && git commit -m x",
    "pytest -q | tail -3 && git commit -am x",
    "py.test -x | grep passed && git commit -m x",
    "python3 -m pytest -q | tail -1; git commit -m x",
    "cd /c/proj && python -m pytest -q | tail -1 && git -C /c/proj commit -m x",
    "C:/Python314/python.exe -m pytest -q | tail -1 && git commit -m x",
])
def test_nega_pytest_mascarado_por_pipe_antes_do_commit(comando):
    mod = _mod()
    motivo = mod.decidir(_evento(comando), ambiente={})
    assert motivo is not None, f"passou: {comando!r} — o commit sairia com a suíte vermelha"
    assert "F-025" in motivo, "motivo não cita o caso"
    assert "pipefail" in motivo, "motivo não dá a saída `set -o pipefail`"
    assert "passo próprio" in motivo, "motivo não dá a saída 'pytest num passo próprio'"


def test_nega_tambem_no_powershell():
    mod = _mod()
    comando = "python -m pytest -q | Select-Object -Last 1; git commit -m x"
    assert mod.decidir(_evento(comando, tool="PowerShell"), ambiente={}) is not None


# --- AC2: o resto passa ------------------------------------------------------------------

@pytest.mark.parametrize("comando", [
    "python -m pytest -q && git commit -m x",            # o commit depende do exit real
    "python -m pytest -q 2>&1 | tail -3",                # pipe sem commit: só ler a saída
    "python -m pytest -q",
    "git commit -m 'feat: x'",
    "git add -A && git commit -m x",
    "set -o pipefail; python -m pytest -q | tail -1 && git commit -m x",
    "set -euo pipefail && pytest -q | tail -1 && git commit -m x",
    "git log --oneline | head -5 && git commit -m x",   # pipe sem pytest
    "grep -rn pytest docs/ | head && git commit -m x",  # 'pytest' como texto, não como comando
    "git commit -m x && python -m pytest -q | tail -1",  # teste DEPOIS do commit não mascara o commit
])
def test_libera_o_resto(comando):
    mod = _mod()
    assert mod.decidir(_evento(comando), ambiente={}) is None, f"barrou de graça: {comando!r}"


# --- AC3: escape próprio e falha ABERTA, sem mexer na cerca de publicação ----------------

COMANDO_F025 = "python -m pytest -q | tail -1 && git commit -m x"


def test_escape_proprio_do_owner():
    mod = _mod()
    assert mod.decidir(_evento(COMANDO_F025), ambiente={"MSS_PIPE_TESTE_OFF": "1"}) is None
    assert mod.decidir(_evento(COMANDO_F025), ambiente={"MSS_PIPE_TESTE_OFF": " "}) is not None


def test_escape_de_publicacao_nao_desliga_a_cerca_do_pipe():
    mod = _mod()
    assert mod.decidir(_evento(COMANDO_F025), ambiente={"MSS_PUBLICACAO_OFF": "1"}) is not None


def test_escape_do_pipe_nao_desliga_a_cerca_de_publicacao():
    mod = _mod()
    assert mod.decidir(_evento("git push origin main"),
                       ambiente={"MSS_PIPE_TESTE_OFF": "1"}) is not None


def test_bug_na_cerca_do_pipe_falha_aberta(monkeypatch):
    mod = _mod()
    monkeypatch.setattr(mod, "mascara_teste", lambda _c: 1 / 0)
    assert mod.decidir(_evento(COMANDO_F025), ambiente={}) is None


def test_bug_na_cerca_do_pipe_nao_abre_a_de_publicacao(monkeypatch):
    mod = _mod()
    monkeypatch.setattr(mod, "mascara_teste", lambda _c: 1 / 0)
    motivo = mod.decidir(_evento("python -m pytest -q | tail -1 && git push"), ambiente={})
    assert motivo is not None and "owner" in motivo.lower()


# --- AC4: processo, como o Claude Code roda ----------------------------------------------

def test_processo_nega_pelos_dois_protocolos():
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_PIPE_TESTE_OFF", "MSS_PUBLICACAO_OFF")}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento(COMANDO_F025)),
                          capture_output=True, text=True, env=amb, timeout=30)
    assert proc.returncode == 2, f"esperava exit 2; saiu {proc.returncode}: {proc.stderr}"
    hook = json.loads(proc.stdout)["hookSpecificOutput"]
    assert hook["permissionDecision"] == "deny"
    assert "F-025" in hook["permissionDecisionReason"]


def test_documentado_no_readme():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "MSS_PIPE_TESTE_OFF" in readme
    assert "F-025" in readme
