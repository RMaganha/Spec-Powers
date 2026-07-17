"""Padrão de logging MSIG — stdout (o Azure captura) + arquivo rotativo em dev.

MODELO do plugin mss-spec — copie para `config/logging.py` (ou `utils/logger.py`)
no projeto. O `/mss-spec:log` faz essa cópia e instrumenta os arquivos escolhidos.

Por que assim:
- **stdout SEMPRE**: em Azure Web App o arquivo dentro do container é efêmero (some
  no restart/deploy/scale) — quem "pega" o log em prod é o stdout. Em dev, o mesmo
  stdout aparece no terminal.
- **arquivo rotativo SÓ em dev**: conveniência local (`logs/app.log`, 5 MB × 5). Em
  Azure não faz sentido (efêmero) e nem é criado.
- **ícone por nível SÓ em dev**: leitura rápida no terminal. Em Azure sai texto limpo
  (o log stream / Log Analytics não renderiza emoji e ainda atrapalha o parse).

Dev × Azure é detectado por `WEBSITE_SITE_NAME`: o Azure App Service **sempre** define
essa variável; no dev local ela nunca existe. Zero config.

`.env` (dev) / App Settings (Azure):
    LOG_ATIVO=true      # false → só WARNING+ (não silencia problema grave)
    LOG_LEVEL=INFO      # DEBUG|INFO|WARNING|ERROR|CRITICAL
    LOG_ICONES=true     # ícone por nível; efetivo só em dev (ignorado em Azure)

Uso no código (cada módulo identifica a si mesmo via __name__):
    import logging
    from config.logging import setup_logging
    setup_logging()                       # 1x no arranque (main.py)
    logger = logging.getLogger(__name__)  # nos demais módulos
    logger.info("conectado")

Segurança (casa com docs/SEGURANCA.md §8): NUNCA logue PII nem segredo. Ao logar algo
que toque credencial/connection string, passe por `mask_password` (utils/get_connection.py).
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Ícone por nível (dev). Mantidos como emoji simples pra renderizar no terminal.
_ICONES = {
    logging.DEBUG: "🐛",
    logging.INFO: "ℹ️",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "🔥",
}

_FMT_COM_ICONE = "%(asctime)s %(icone)s %(levelname)s %(name)s: %(message)s"
_FMT_SEM_ICONE = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def _em_dev() -> bool:
    """Dev = fora do Azure. O App Service sempre define WEBSITE_SITE_NAME."""
    return not os.getenv("WEBSITE_SITE_NAME")


def _flag(nome: str, padrao: bool) -> bool:
    v = os.getenv(nome)
    if v is None:
        return padrao
    return v.strip().lower() in ("1", "true", "yes", "on", "sim")


class _IconeFormatter(logging.Formatter):
    """Formatter que injeta o ícone do nível em `%(icone)s`."""

    def format(self, record: logging.LogRecord) -> str:
        record.icone = _ICONES.get(record.levelno, "")
        return super().format(record)


def setup_logging(dir_logs: str = "logs", nome_arquivo: str = "app.log") -> logging.Logger:
    """Configura o logger raiz no padrão MSIG. Chame uma vez, no arranque do app.

    Retorna o logger raiz (útil em teste). Idempotente: recria os handlers a cada
    chamada, sem empilhar (seguro sob reload/pytest).
    """
    ativo = _flag("LOG_ATIVO", True)
    nivel_txt = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
    nivel_base = getattr(logging, nivel_txt, logging.INFO)
    # LOG_ATIVO=false não silencia de vez: mantém WARNING+ (problema grave ainda aparece).
    nivel = nivel_base if ativo else logging.WARNING

    dev = _em_dev()
    com_icone = dev and _flag("LOG_ICONES", True)

    root = logging.getLogger()
    for h in list(root.handlers):  # idempotência: limpa antes de reconfigurar
        root.removeHandler(h)
    root.setLevel(nivel)

    if com_icone:
        formatter: logging.Formatter = _IconeFormatter(_FMT_COM_ICONE)
    else:
        formatter = logging.Formatter(_FMT_SEM_ICONE)

    # stdout SEMPRE (dev vê no terminal; Azure captura pro log stream).
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(nivel)
    stdout.setFormatter(formatter)
    root.addHandler(stdout)

    # arquivo rotativo SÓ em dev e só com LOG_ATIVO (em Azure é efêmero → não cria).
    if ativo and dev:
        Path(dir_logs).mkdir(parents=True, exist_ok=True)
        arquivo = RotatingFileHandler(
            Path(dir_logs) / nome_arquivo,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        arquivo.setLevel(nivel)
        arquivo.setFormatter(formatter)
        root.addHandler(arquivo)

    return root
