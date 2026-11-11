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


@pytest.fixture(autouse=True, scope="session")
def _tabela_de_memoria_fora_do_home(tmp_path_factory):
    """A tabela de memória real (`~/mss-spec/memoria.sqlite3`) é do owner: hook ou script que rode na suíte
    sem informar a tabela grava numa pasta temporária, nunca na dele."""
    anterior = os.environ.get("MSS_MEMORIA_TABELA")
    os.environ["MSS_MEMORIA_TABELA"] = str(tmp_path_factory.mktemp("memoria") / "memoria.sqlite3")
    yield
    if anterior is None:
        os.environ.pop("MSS_MEMORIA_TABELA", None)
    else:
        os.environ["MSS_MEMORIA_TABELA"] = anterior


@pytest.fixture(autouse=True, scope="session")
def _conversas_em_texto_fora_do_home(tmp_path_factory):
    """As conversas em texto (`~/mss-spec/conversas/`, `templates/conversa_texto.py`) são do owner: script que
    rode na suíte sem informar a saída grava numa pasta temporária, nunca na dele."""
    anterior = os.environ.get("MSS_CONVERSAS_DIR")
    os.environ["MSS_CONVERSAS_DIR"] = str(tmp_path_factory.mktemp("conversas"))
    yield
    if anterior is None:
        os.environ.pop("MSS_CONVERSAS_DIR", None)
    else:
        os.environ["MSS_CONVERSAS_DIR"] = anterior
