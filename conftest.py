"""Pytest do kit mss-spec — molde `templates/pytest/conftest.py`, levado pelo `/mss-spec:upgrade`.

Não edite aqui: o upgrade substitui este arquivo. Fixtures do projeto ficam em `tests/conftest.py`.

1. Pasta temporária própria do projeto: `<temp>/pytest-<pasta do projeto>`, limpa no começo de cada
   rodada. Sem ela, todo projeto grava na mesma pasta do pytest, e a rodada interrompida deixa lixo
   travado por 3 dias que a próxima rodada, de qualquer projeto, percorre de novo.
2. Uma rodada de pytest por vez na máquina: quem chega espera a outra terminar. A trava é do sistema
   operacional e morre junto com o processo — pytest interrompido não deixa trava para trás.
3. No CI (GitHub Actions ou Azure Pipelines), a lista do que falhou sai numa linha de erro só, no formato da
   plataforma, e o teste marcado `@pytest.mark.externo` (precisa de banco ou serviço que o CI não alcança) é
   pulado, com um aviso de quantos. Na máquina, o `externo` roda normalmente.
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

TITULO_FALHAS = "testes que falharam"
MOTIVO_EXTERNO = "externo: precisa de banco ou serviço que o CI não alcança"
LIMITE_FALHAS = 200


def plataforma_do_ci(ambiente):
    """'github', 'azure' ou None (máquina), pela variável que cada plataforma põe em toda rodada."""
    if ambiente.get("GITHUB_ACTIONS") == "true":
        return "github"
    if str(ambiente.get("TF_BUILD", "")).lower() == "true":
        return "azure"
    return None


def _escapar(plataforma, texto):
    if plataforma == "github":
        return texto.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return (texto.replace("%", "%AZP25").replace(";", "%3B").replace("]", "%5D")
            .replace("\r", "%0D").replace("\n", "%0A"))


def linha_de_falhas(plataforma, falhas):
    """A linha de erro com um teste por linha (`%0A`), ou None sem falha ou fora do CI."""
    if not plataforma or not falhas:
        return None
    corpo = "%0A".join(_escapar(plataforma, f) for f in falhas[:LIMITE_FALHAS])
    if plataforma == "github":
        return f"::error title={TITULO_FALHAS}::{corpo}"
    return f"##vso[task.logissue type=error]{TITULO_FALHAS}:%0A{corpo}"


def linha_de_externos(plataforma, quantos):
    if not plataforma or not quantos:
        return None
    texto = f"{quantos} teste(s) marcado(s) externo não rodaram no CI"
    if plataforma == "github":
        return f"::warning title=testes externo pulados::{texto}"
    return f"##vso[task.logissue type=warning]{texto}"


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
    config.addinivalue_line("markers", MOTIVO_EXTERNO)
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


def pytest_collection_modifyitems(config, items):
    if not plataforma_do_ci(os.environ):
        return
    for item in items:
        if item.get_closest_marker("externo"):
            item.add_marker(pytest.mark.skip(reason=MOTIVO_EXTERNO))


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    plataforma = plataforma_do_ci(os.environ)
    if not plataforma:
        return
    stats = terminalreporter.stats
    falhas = list(dict.fromkeys(r.nodeid for chave in ("failed", "error") for r in stats.get(chave, [])))
    pulados = sum(1 for r in stats.get("skipped", [])
                  if isinstance(r.longrepr, tuple) and MOTIVO_EXTERNO in str(r.longrepr[-1]))
    for linha in (linha_de_falhas(plataforma, falhas), linha_de_externos(plataforma, pulados)):
        if linha:
            terminalreporter.write_line(linha)


def pytest_sessionfinish(session, exitstatus):
    """No CI, "nenhum teste coletado" (5) não é falha: projeto recém-constituído ainda não tem teste."""
    if exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED and plataforma_do_ci(os.environ):
        session.exitstatus = pytest.ExitCode.OK


def pytest_unconfigure(config):
    global _trava
    if _trava is not None:
        _trava.close()
        _trava = None
        os.environ.pop(ENV_DONO, None)
