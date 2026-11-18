"""Molde `templates/pytest/conftest.py`: pasta temporária própria do projeto e uma rodada de pytest por vez.

Nasceu do bug da suíte lenta (2026-11-17): todo projeto gravava na mesma pasta temporária do pytest,
a rodada interrompida deixava lixo travado por 3 dias e duas suítes ao mesmo tempo somavam a carga.
Os testes da regra chamam as funções direto; só 1 teste sobe um pytest de verdade (a espera pela trava).
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
MOLDE = REPO / "templates" / "pytest" / "conftest.py"


def _mod():
    spec = importlib.util.spec_from_file_location("mss_pytest_molde", MOLDE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _config(raiz, basetemp=None):
    return SimpleNamespace(rootpath=Path(raiz), option=SimpleNamespace(basetemp=basetemp),
                           addinivalue_line=lambda nome, valor: None)


def test_pasta_temporaria_e_do_projeto(monkeypatch, tmp_path):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    assert _mod().pasta_temporaria(Path("C:/x/atm-transporte")) == tmp_path / "pytest-atm-transporte"


def test_trava_so_um_por_vez_e_solta_ao_fechar(tmp_path):
    m = _mod()
    caminho = tmp_path / "trava"
    primeira = m.tentar_travar(caminho)
    assert primeira is not None
    assert m.tentar_travar(caminho) is None, "segunda rodada pegou a trava com a primeira viva"
    primeira.close()
    terceira = m.tentar_travar(caminho)
    assert terceira is not None, "fechar (ou o processo morrer) não soltou a trava"
    terceira.close()


def test_configure_poe_a_pasta_do_projeto_e_trava(monkeypatch, tmp_path):
    m = _mod()
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setenv(m.ENV_TRAVA, str(tmp_path / "trava"))
    monkeypatch.delenv(m.ENV_DONO, raising=False)
    cfg = _config(tmp_path / "kit")
    m.pytest_configure(cfg)
    try:
        assert cfg.option.basetemp == str(tmp_path / "pytest-kit")
        assert os.environ[m.ENV_DONO] == str(os.getpid())
        assert m.tentar_travar(tmp_path / "trava") is None, "a rodada não segurou a trava"
        assert "kit" in (tmp_path / "trava.quem").read_text(encoding="utf-8")
    finally:
        m.pytest_unconfigure(cfg)
    assert m.ENV_DONO not in os.environ
    solta = m.tentar_travar(tmp_path / "trava")
    assert solta is not None, "o fim da rodada não soltou a trava"
    solta.close()


def test_pytest_de_dentro_da_rodada_nao_trava_nem_troca_a_pasta(monkeypatch, tmp_path):
    """Um pytest aberto por um teste herda o dono: esperar a trava seria esperar por si mesmo, e usar a
    pasta do projeto apagaria a da rodada de fora."""
    m = _mod()
    monkeypatch.setenv(m.ENV_TRAVA, str(tmp_path / "trava"))
    monkeypatch.setenv(m.ENV_DONO, "123")
    cfg = _config(tmp_path / "kit")
    m.pytest_configure(cfg)
    m.pytest_unconfigure(cfg)
    assert cfg.option.basetemp is None
    assert not (tmp_path / "trava").exists()


def test_pasta_dada_na_linha_de_comando_fica(monkeypatch, tmp_path):
    m = _mod()
    monkeypatch.setenv(m.ENV_TRAVA, str(tmp_path / "trava"))
    monkeypatch.delenv(m.ENV_DONO, raising=False)
    cfg = _config(tmp_path / "kit", basetemp=str(tmp_path / "minha"))
    m.pytest_configure(cfg)
    m.pytest_unconfigure(cfg)
    assert cfg.option.basetemp == str(tmp_path / "minha")


def test_kit_usa_o_proprio_molde():
    assert (REPO / "conftest.py").read_bytes() == MOLDE.read_bytes(), "conftest.py da raiz difere do molde"
    assert (REPO / "pytest.ini").read_bytes() == (REPO / "templates" / "pytest" / "pytest.ini").read_bytes()


def test_repositorio_de_teste_nasce_sem_o_modelo_do_git():
    """Cada `git init` copia 14 scripts de exemplo e mais 4 itens que teste nenhum usa (41 itens contra 23 com
    `--template=`, medido em 2026-11-17). Repositório de teste nasce com `--template=`."""
    sem = []
    for arquivo in sorted((REPO / "tests").glob("*.py")):
        for n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
            if '"init"' in linha and "--template=" not in linha:
                sem.append(f"{arquivo.name}:{n}")
    assert not sem, f"git init sem --template=: {sem}"


def test_kickoff_e_upgrade_levam_o_molde_aos_projetos():
    for comando in ("kickoff.md", "upgrade.md"):
        texto = (REPO / "commands" / comando).read_text(encoding="utf-8")
        assert "templates/pytest/conftest.py" in texto, f"{comando} não leva o conftest.py do kit"
        assert "templates/pytest/pytest.ini" in texto, f"{comando} não leva o pytest.ini do kit"
        assert "[tool.pytest.ini_options]" in texto, f"{comando} criaria pytest.ini por cima da configuração do projeto"


def test_segunda_rodada_espera_a_primeira_terminar(tmp_path):
    """Ponta a ponta: um pytest de verdade, com a trava segura aqui, espera; solta a trava, ele roda."""
    m = _mod()
    proj, temp = tmp_path / "proj", tmp_path / "temp"
    (proj / "tests").mkdir(parents=True)
    temp.mkdir()
    shutil.copy(MOLDE, proj / "conftest.py")
    shutil.copy(REPO / "templates" / "pytest" / "pytest.ini", proj / "pytest.ini")
    (proj / "tests" / "test_a.py").write_text("def test_a(tmp_path):\n    assert tmp_path.is_dir()\n",
                                              encoding="utf-8")
    trava = tmp_path / "trava"
    env = {k: v for k, v in os.environ.items() if k != m.ENV_DONO}
    env.update({m.ENV_TRAVA: str(trava), "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)})
    segura = m.tentar_travar(trava)
    assert segura is not None
    (tmp_path / "trava.quem").write_text("atendimento-whatsapp (pid 1)", encoding="utf-8")
    erro = tmp_path / "stderr.txt"
    with open(erro, "wb") as saida_erro:
        filho = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=proj,
                                 env=env, stdout=subprocess.DEVNULL, stderr=saida_erro)
        try:
            limite = time.monotonic() + 60
            while b"aguardando" not in erro.read_bytes() and filho.poll() is None and time.monotonic() < limite:
                time.sleep(0.5)
            assert filho.poll() is None, "a 2ª rodada não esperou a trava"
            assert b"aguardando o pytest de atendimento-whatsapp" in erro.read_bytes()
        finally:
            segura.close()
        assert filho.wait(timeout=120) == 0, erro.read_text(encoding="utf-8", errors="replace")
    assert (temp / "pytest-proj").is_dir(), "a rodada não usou a pasta temporária do projeto"


# --- CI: lista do que falhou numa linha só e teste `externo` pulado (spec docs/specs/molde-de-ci.md) ---


class _Item:
    def __init__(self, externo):
        self.externo, self.marcas = externo, []

    def get_closest_marker(self, nome):
        return object() if nome == "externo" and self.externo else None

    def add_marker(self, marca):
        self.marcas.append(marca)


class _Reporter:
    def __init__(self, stats):
        self.stats, self.linhas = stats, []

    def write_line(self, linha):
        self.linhas.append(linha)


def test_plataforma_do_ci_pela_variavel_que_cada_uma_poe():
    m = _mod()
    assert m.plataforma_do_ci({"GITHUB_ACTIONS": "true"}) == "github"
    assert m.plataforma_do_ci({"TF_BUILD": "True"}) == "azure"
    assert m.plataforma_do_ci({}) is None


def test_linha_de_falhas_no_github_e_uma_anotacao_so():
    m = _mod()
    assert m.linha_de_falhas("github", ["t.py::a", "t.py::b"]) == "::error title=testes que falharam::t.py::a%0At.py::b"


def test_linha_de_falhas_no_azure_escapa_o_que_quebra_o_comando():
    m = _mod()
    linha = m.linha_de_falhas("azure", ["t.py::a[x;y]", "t.py::b[50%]"])
    assert linha.startswith("##vso[task.logissue type=error]testes que falharam:%0A")
    corpo = linha.split("]", 1)[1]
    assert "t.py::a[x%3By%5D" in corpo and "%AZP25" in corpo
    assert "\n" not in linha and ";" not in corpo and "]" not in corpo


def test_linha_de_falhas_sem_falha_ou_fora_do_ci_nao_sai_e_corta_em_200():
    m = _mod()
    assert m.linha_de_falhas("github", []) is None
    assert m.linha_de_falhas(None, ["t.py::a"]) is None
    assert m.linha_de_falhas("github", [f"t.py::{i}" for i in range(250)]).count("%0A") == 199


def test_linha_de_externos_diz_quantos_pulou():
    m = _mod()
    assert m.linha_de_externos("github", 3).startswith("::warning title=testes externo pulados::3 ")
    assert m.linha_de_externos("azure", 1).startswith("##vso[task.logissue type=warning]")
    assert m.linha_de_externos("github", 0) is None
    assert m.linha_de_externos(None, 2) is None


def test_externo_e_pulado_no_ci_e_roda_na_maquina(monkeypatch):
    m = _mod()
    itens = [_Item(True), _Item(False)]
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    m.pytest_collection_modifyitems(None, itens)
    assert len(itens[0].marcas) == 1 and itens[1].marcas == []
    assert itens[0].marcas[0].kwargs["reason"] == m.MOTIVO_EXTERNO
    monkeypatch.delenv("GITHUB_ACTIONS")
    monkeypatch.delenv("TF_BUILD", raising=False)
    maquina = [_Item(True)]
    m.pytest_collection_modifyitems(None, maquina)
    assert maquina[0].marcas == []


def test_marca_externo_registrada_ate_na_rodada_de_dentro(monkeypatch, tmp_path):
    m = _mod()
    monkeypatch.setenv(m.ENV_TRAVA, str(tmp_path / "trava"))
    monkeypatch.setenv(m.ENV_DONO, "123")
    registradas = []
    cfg = _config(tmp_path / "kit")
    cfg.addinivalue_line = lambda nome, valor: registradas.append((nome, valor))
    m.pytest_configure(cfg)
    assert any(nome == "markers" and valor.startswith("externo:") for nome, valor in registradas)


def test_resumo_no_ci_escreve_falhas_e_pulados_e_fora_dele_nada(monkeypatch):
    m = _mod()
    stats = {"failed": [SimpleNamespace(nodeid="t.py::a")], "error": [SimpleNamespace(nodeid="t.py::b")],
             "skipped": [SimpleNamespace(longrepr=("t.py", 1, "Skipped: " + m.MOTIVO_EXTERNO)),
                         SimpleNamespace(longrepr=("t.py", 2, "Skipped: outro motivo"))]}
    monkeypatch.setenv("TF_BUILD", "True")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    reporter = _Reporter(stats)
    m.pytest_terminal_summary(reporter, 1, None)
    assert reporter.linhas[0] == "##vso[task.logissue type=error]testes que falharam:%0At.py::a%0At.py::b"
    assert reporter.linhas[1].startswith("##vso[task.logissue type=warning]1 ")
    monkeypatch.delenv("TF_BUILD")
    fora = _Reporter(stats)
    m.pytest_terminal_summary(fora, 1, None)
    assert fora.linhas == []


def test_no_ci_projeto_sem_teste_ainda_nao_fica_vermelho(monkeypatch):
    """Projeto recém-constituído pelo kickoff ainda não tem teste: o pytest sai com 5 e o CI ficaria vermelho."""
    m = _mod()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    sessao = SimpleNamespace(exitstatus=5)
    m.pytest_sessionfinish(sessao, 5)
    assert sessao.exitstatus == 0
    falhou = SimpleNamespace(exitstatus=1)
    m.pytest_sessionfinish(falhou, 1)
    assert falhou.exitstatus == 1
    monkeypatch.delenv("GITHUB_ACTIONS")
    monkeypatch.delenv("TF_BUILD", raising=False)
    maquina = SimpleNamespace(exitstatus=5)
    m.pytest_sessionfinish(maquina, 5)
    assert maquina.exitstatus == 5
