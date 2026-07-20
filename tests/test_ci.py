"""CI com artefatos de teste (item 12) — trava o mecanismo, no estilo do item 9.

O kit traz um .gitlab-ci.yml que roda a suíte e publica JUnit XML + cobertura como
ARTEFATOS do CI (efêmeros, nunca commitados). Como o item 9, o mecanismo está
preparado, NÃO ativado: git remote vazio, então apontar/rodar num host real é passo
manual do owner. Este teste garante que a estrutura e os flags estão certos e que
run output está gitignorado.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CI = REPO / ".gitlab-ci.yml"

# Saídas de run que o CI gera e que NUNCA podem entrar no repo (anti-padrão do item 12).
RUN_OUTPUTS = ("report.xml", "coverage.xml", "htmlcov/", ".coverage")

# Arquivos onde um addopts do pytest poderia morar e vazar os flags de CI pro run local.
PYTEST_CONFIGS = ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini")


def _ci_doc():
    yaml = pytest.importorskip("yaml")
    assert CI.exists(), "falta .gitlab-ci.yml na raiz"
    return yaml.safe_load(CI.read_text(encoding="utf-8"))


def _test_job():
    """O job que roda pytest (procura por script que chama pytest, ignorando as chaves de topo)."""
    doc = _ci_doc()
    jobs = {
        k: v
        for k, v in doc.items()
        if isinstance(v, dict) and any("pytest" in str(s) for s in v.get("script", []))
    }
    assert jobs, ".gitlab-ci.yml não tem nenhum job que rode pytest"
    return next(iter(jobs.values()))


def test_ci_declara_reports_junit_e_cobertura():
    """AC1: o job declara artifacts.reports.junit E artifacts.reports.coverage_report (cobertura)."""
    job = _test_job()
    reports = job.get("artifacts", {}).get("reports", {})
    assert "junit" in reports, ".gitlab-ci.yml: job não declara artifacts.reports.junit"
    cov = reports.get("coverage_report", {})
    assert cov.get("coverage_format") == "cobertura", (
        ".gitlab-ci.yml: coverage_report não usa coverage_format cobertura"
    )


def test_ci_job_gera_junit_e_cobertura_no_comando():
    """AC2: o comando do job gera JUnit XML (--junitxml) e cobertura Cobertura (--cov + --cov-report=xml)."""
    script = " ".join(_test_job().get("script", []))
    assert "--junitxml" in script, "job de CI não gera JUnit XML (--junitxml)"
    assert "--cov" in script, "job de CI não mede cobertura (--cov)"
    assert "--cov-report=xml" in script, "job de CI não emite cobertura Cobertura (--cov-report=xml)"


def test_flags_de_ci_nao_vazam_pro_pytest_local():
    """AC2: os flags de artefato vivem no comando do job, não num addopts que quebre `pytest -q` local."""
    for nome in PYTEST_CONFIGS:
        cfg = REPO / nome
        if not cfg.exists():
            continue
        texto = cfg.read_text(encoding="utf-8")
        m = re.search(r"addopts\s*=([^\n]*)", texto)
        if m:
            addopts = m.group(1)
            assert "--cov" not in addopts and "--junitxml" not in addopts, (
                f"{nome}: addopts carrega flags de CI (--cov/--junitxml) — quebraria o pytest -q local"
            )


def test_run_output_gitignorado():
    """AC3: as saídas de run do CI estão ignoradas — run output nunca entra no repo."""
    gi = (REPO / ".gitignore").read_text(encoding="utf-8")
    faltando = [o for o in RUN_OUTPUTS if o not in gi]
    assert not faltando, ".gitignore não ignora as saídas de run do CI: " + ", ".join(faltando)


def test_ci_sem_host_inventado_placeholder():
    """AC4: como o item 9, o mecanismo é placeholder — sem host git inventado; ativação é passo do owner."""
    texto = CI.read_text(encoding="utf-8")
    assert "https://" not in texto and "git@" not in texto, (
        ".gitlab-ci.yml não pode conter host git inventado (git remote está vazio, como no item 9)"
    )
    assert "não ativado" in texto.lower() or "placeholder" in texto.lower(), (
        ".gitlab-ci.yml deve marcar que está preparado, NÃO ativado (passo do owner), como o item 9"
    )
