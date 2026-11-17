"""`templates/testes_do_que_mudou.py` — na máquina roda só o teste do que mudou, escolhido pelo script, não no olho.

Decisão do owner (2026-11-17): rodar o teste do bpmn quando a mudança foi na memória não pega nada e só pesa. O
script lê o que mudou na branch e escolhe os arquivos de teste que citam a peça mudada.

Camadas: a escolha (`escolher`) é testada em memória — a lista do que mudou e o texto dos testes entram como dado.
Só o último teste conversa com o git de verdade.
"""
import importlib.util
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "testes_do_que_mudou.py"


def _mod():
    spec = importlib.util.spec_from_file_location("testes_do_que_mudou", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TESTES = {
    "tests/test_memoria_tabela.py": 'SCRIPT = REPO / "templates" / "memoria_tabela.py"\n',
    "tests/test_memoria_tabela_busca.py": 'from memoria_tabela import buscar\n',
    "tests/test_bpmn.py": 'SCRIPT = REPO / "templates" / "bpmn.py"\n',
    "tests/test_hook_git_publicacao.py": 'HOOK = REPO / "hooks" / "git_publicacao.py"\n',
    "tests/test_smoke_kit.py": 'texto = (REPO / "commands" / "bug.md").read_text()\n',
    "tests/test_servico.py": "from app.services.pedido import criar\n",
}


def test_mudou_a_memoria_roda_so_os_testes_da_memoria():
    escolhidos = _mod().escolher(["templates/memoria_tabela.py"], TESTES)
    assert sorted(escolhidos) == ["tests/test_memoria_tabela.py", "tests/test_memoria_tabela_busca.py"]


def test_cada_teste_escolhido_diz_por_que():
    escolhidos = _mod().escolher(["templates/memoria_tabela.py"], TESTES)
    assert any("memoria_tabela.py" in m for m in escolhidos["tests/test_memoria_tabela.py"])


def test_mudou_um_comando_md_roda_o_teste_que_o_cita():
    assert list(_mod().escolher(["commands/bug.md"], TESTES)) == ["tests/test_smoke_kit.py"]


def test_import_por_modulo_de_projeto_comum():
    assert list(_mod().escolher(["app/services/pedido.py"], TESTES)) == ["tests/test_servico.py"]


def test_arquivo_de_teste_que_mudou_entra():
    assert list(_mod().escolher(["tests/test_bpmn.py"], TESTES)) == ["tests/test_bpmn.py"]


def test_configuracao_do_pytest_mudou_roda_tudo():
    escolhidos = _mod().escolher(["conftest.py"], TESTES)
    assert sorted(escolhidos) == sorted(TESTES)


def test_conftest_vale_so_para_os_testes_da_pasta_dele():
    """O molde `templates/pytest/conftest.py` não é configuração de teste nenhum; `tests/conftest.py` é de todos
    os testes de `tests/`."""
    assert _mod().escolher(["templates/pytest/conftest.py"], TESTES) == {}
    assert sorted(_mod().escolher(["tests/conftest.py"], TESTES)) == sorted(TESTES)
    # ...mas o teste que cita o molde entra
    cita = {"tests/test_pytest_mss.py": 'MOLDE = REPO / "templates" / "pytest" / "conftest.py"\n'}
    assert list(_mod().escolher(["templates/pytest/conftest.py"], cita)) == ["tests/test_pytest_mss.py"]


def test_md_precisa_da_pasta_junto_do_nome():
    """Teste que só usa `DIARIO.md` como texto solto não testa o `memory/DIARIO.md` do kit."""
    testes = {"tests/test_a.py": 'motivo = "grave a linha no DIARIO.md"\n',
              "tests/test_b.py": 'p = REPO / "memory" / "DIARIO.md"\n'}
    assert list(_mod().escolher(["memory/DIARIO.md"], testes)) == ["tests/test_b.py"]


def test_mudanca_sem_teste_nao_escolhe_nada():
    assert _mod().escolher(["docs/LEIA-ME.md", "templates/anatomia.py"], TESTES) == {}


def test_nome_parecido_nao_conta():
    """`bpmn.py` não pode puxar um teste que só cita `bpmn_extra.py`."""
    testes = {"tests/test_x.py": 'X = "templates/bpmn_extra.py"\n'}
    assert _mod().escolher(["templates/bpmn.py"], testes) == {}


def test_le_o_que_mudou_no_git_de_verdade(tmp_path):
    """A conversa com o git: commits da branch desde a principal + o que está por commitar."""
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}

    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, env=env)

    git("init", "-q", "--template=", "-b", "main")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    git("add", "a.py")
    git("commit", "-q", "-m", "i")
    git("switch", "-q", "-c", "fix/x")
    (tmp_path / "b.py").write_text("y = 1\n", encoding="utf-8")
    git("add", "b.py")
    git("commit", "-q", "-m", "b")
    (tmp_path / "a.py").write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "novo.py").write_text("z = 1\n", encoding="utf-8")
    assert sorted(_mod().mudados(tmp_path)) == ["a.py", "b.py", "novo.py"]
