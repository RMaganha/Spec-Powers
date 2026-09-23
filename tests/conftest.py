"""Fixtures da suíte inteira.

O registro dos hooks (`hooks/_registro.py`) grava em `~/.claude/mss-spec/` — a suíte NUNCA pode
sujar o registro real do owner. Toda a sessão de teste aponta o registro pra uma pasta temporária
(os testes que rodam o hook como processo copiam `os.environ`, então herdam o desvio).
"""
import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _registro_dos_hooks_fora_do_home(tmp_path_factory):
    anterior = os.environ.get("MSS_REGISTRO_ARQUIVO")
    os.environ["MSS_REGISTRO_ARQUIVO"] = str(tmp_path_factory.mktemp("registro") / "registro-hooks.jsonl")
    yield
    if anterior is None:
        os.environ.pop("MSS_REGISTRO_ARQUIVO", None)
    else:
        os.environ["MSS_REGISTRO_ARQUIVO"] = anterior
