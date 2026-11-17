"""Pytest do kit mss-spec — molde `templates/pytest/conftest.py`, levado pelo `/mss-spec:upgrade`.

Não edite aqui: o upgrade substitui este arquivo. Fixtures do projeto ficam em `tests/conftest.py`.

1. Pasta temporária própria do projeto: `<temp>/pytest-<pasta do projeto>`, limpa no começo de cada
   rodada. Sem ela, todo projeto grava na mesma pasta do pytest, e a rodada interrompida deixa lixo
   travado por 3 dias que a próxima rodada, de qualquer projeto, percorre de novo.
2. Uma rodada de pytest por vez na máquina: quem chega espera a outra terminar. A trava é do sistema
   operacional e morre junto com o processo — pytest interrompido não deixa trava para trás.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

ENV_DONO = "MSS_PYTEST_TRAVA_DONO"   # setada pela rodada que tem a trava; um pytest aberto por um teste herda
ENV_TRAVA = "MSS_PYTEST_TRAVA"       # caminho do arquivo da trava (padrão: na pasta temporária do sistema)
_trava = None


def pasta_temporaria(raiz):
    return Path(tempfile.gettempdir()) / f"pytest-{Path(raiz).name}"


def _caminho_da_trava():
    return Path(os.environ.get(ENV_TRAVA) or Path(tempfile.gettempdir()) / "pytest-mss.trava")


def tentar_travar(caminho):
    """Arquivo aberto e travado, ou None se outra rodada está com a trava."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    arquivo = open(caminho, "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            arquivo.seek(0)
            msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        arquivo.close()
        return None
    return arquivo


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    global _trava
    if os.environ.get(ENV_DONO) or os.environ.get("PYTEST_XDIST_WORKER"):
        return
    caminho = _caminho_da_trava()
    quem = caminho.with_name(caminho.name + ".quem")
    avisou = False
    while (arquivo := tentar_travar(caminho)) is None:
        if not avisou:
            try:
                dono = quem.read_text(encoding="utf-8").strip()
            except OSError:
                dono = "outro projeto"
            sys.stderr.write(f"[mss-spec] aguardando o pytest de {dono} terminar (uma rodada por vez)...\n")
            sys.stderr.flush()
            avisou = True
        time.sleep(1)
    _trava = arquivo
    os.environ[ENV_DONO] = str(os.getpid())
    raiz = Path(config.rootpath)
    try:
        quem.write_text(f"{raiz.name} (pid {os.getpid()})", encoding="utf-8")
    except OSError:
        pass
    if config.option.basetemp is None:
        config.option.basetemp = str(pasta_temporaria(raiz))


def pytest_unconfigure(config):
    global _trava
    if _trava is not None:
        _trava.close()
        _trava = None
        os.environ.pop(ENV_DONO, None)
