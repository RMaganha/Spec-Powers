"""Testa o comportamento de `templates/logging.py` (padrão de log MSIG).

Diferente do smoke (que só valida wiring), aqui exercitamos os Critérios de Aceite
da spec direto no módulo real: stdout no nível, toggle LOG_ATIVO, arquivo rotativo
só em dev, e ícone por nível só em dev. O template é código funcional (sem
placeholders), então carregamos por caminho — com um nome de módulo próprio pra
NÃO sombrear o `logging` da stdlib.
"""
import importlib.util
import logging
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "templates" / "logging.py"


@pytest.fixture()
def log_mod(monkeypatch, tmp_path):
    """Carrega templates/logging.py como módulo isolado e limpa o root ao final.

    Faz chdir pra um tmp: assim, quando um teste chama setup_logging() sem dir_logs,
    o arquivo rotativo (dev) cai no tmp, nunca polui logs/ na raiz do repo.
    """
    monkeypatch.chdir(tmp_path)
    # dev por padrão nos testes: sem a env do Azure
    monkeypatch.delenv("WEBSITE_SITE_NAME", raising=False)
    for var in ("LOG_ATIVO", "LOG_LEVEL", "LOG_ICONES"):
        monkeypatch.delenv(var, raising=False)

    spec = importlib.util.spec_from_file_location("mss_log_template", TEMPLATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    yield mod

    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)


def test_stdout_no_nivel_default_info(log_mod, capsys):
    """LOG_ATIVO=true → loga pro stdout no nível INFO (default)."""
    log_mod.setup_logging()
    logging.getLogger("app.teste").info("ola mundo")
    out = capsys.readouterr().out
    assert "ola mundo" in out
    assert "INFO" in out
    assert "app.teste" in out  # identifica o módulo/arquivo de origem


def test_log_level_filtra_abaixo(log_mod, capsys, monkeypatch):
    """LOG_LEVEL=WARNING → INFO some, WARNING aparece."""
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    log_mod.setup_logging()
    logging.getLogger("app.teste").info("nao deve aparecer")
    logging.getLogger("app.teste").warning("deve aparecer")
    out = capsys.readouterr().out
    assert "nao deve aparecer" not in out
    assert "deve aparecer" in out


def test_log_ativo_false_so_warning_pra_cima(log_mod, capsys, monkeypatch):
    """LOG_ATIVO=false → não emite log de aplicação (INFO), mas mantém WARNING+."""
    monkeypatch.setenv("LOG_ATIVO", "false")
    log_mod.setup_logging()
    logging.getLogger("app.teste").info("silencio")
    logging.getLogger("app.teste").error("problema grave")
    out = capsys.readouterr().out
    assert "silencio" not in out
    assert "problema grave" in out


def test_dev_grava_arquivo_rotativo(log_mod, tmp_path):
    """Dev (sem WEBSITE_SITE_NAME) + LOG_ATIVO → grava arquivo rotativo em logs/."""
    from logging.handlers import RotatingFileHandler

    log_mod.setup_logging(dir_logs=str(tmp_path))
    logging.getLogger("app.teste").info("linha de arquivo")

    root = logging.getLogger()
    for h in root.handlers:
        h.flush()
    assert any(isinstance(h, RotatingFileHandler) for h in root.handlers)
    arquivo = tmp_path / "app.log"
    assert arquivo.exists()
    assert "linha de arquivo" in arquivo.read_text(encoding="utf-8")


def test_azure_nao_grava_arquivo(log_mod, tmp_path, monkeypatch):
    """Em Azure (WEBSITE_SITE_NAME setado) → só stdout, NENHUM arquivo (efêmero no container)."""
    from logging.handlers import RotatingFileHandler

    monkeypatch.setenv("WEBSITE_SITE_NAME", "mss-miti-ai-x-prod")
    log_mod.setup_logging(dir_logs=str(tmp_path))
    logging.getLogger("app.teste").info("so stdout")

    root = logging.getLogger()
    assert not any(isinstance(h, RotatingFileHandler) for h in root.handlers)
    assert not (tmp_path / "app.log").exists()


def test_icone_por_nivel_so_em_dev(log_mod, capsys):
    """Dev → ícone por nível no stdout (leitura rápida no terminal)."""
    log_mod.setup_logging()
    logging.getLogger("app.teste").warning("com icone")
    out = capsys.readouterr().out
    assert "⚠️" in out


def test_azure_sem_icone(log_mod, capsys, monkeypatch):
    """Azure → texto limpo, sem emoji (o log stream não renderiza)."""
    monkeypatch.setenv("WEBSITE_SITE_NAME", "mss-miti-ai-x-prod")
    log_mod.setup_logging()
    logging.getLogger("app.teste").warning("sem icone")
    out = capsys.readouterr().out
    assert "⚠️" not in out
    assert "sem icone" in out


def test_idempotente_nao_duplica_handlers(log_mod):
    """Chamar setup_logging duas vezes não empilha handlers (reload/testes)."""
    log_mod.setup_logging()
    n1 = len(logging.getLogger().handlers)
    log_mod.setup_logging()
    n2 = len(logging.getLogger().handlers)
    assert n1 == n2
