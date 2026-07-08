"""Conexão pyodbc com o SQL Server corporativo — padrão MSIG multi-ambiente.

MODELO do plugin mss-spec — copie para `utils/get_connection.py` no projeto e adapte
os nomes `<BASE>` ao domínio. Referência canônica (arquivo REAL, com os pares das
bases SSC / MS10=tkgs_corp / TRP / OnBase já prontos):
    C:\\Ronaldo\\_Mitsui\\Python\\Transportes\\V2\\get_connection.py

Regras do padrão:
- Credencial NUNCA em `.env` nem em texto plano: cada base tem um par Fernet
  KEY/CIPHERTEXT **por ambiente** (DEV/D0 · HML/HI · PROD), embutido NESTE arquivo.
- O `.env` carrega SÓ o seletor de ambiente: `CONEXAO_PRD` (vazio/ausente = DEV;
  qualquer valor = PROD) e `API_ENV=PRD` em produção.
- Base já usada em outro projeto → copie o par pronto do arquivo de referência
  (decisão do owner). Base nova → gere o par localmente, SEM ecoar segredo:
      from cryptography.fernet import Fernet
      key = Fernet.generate_key()
      ct  = Fernet(key).encrypt(b"Driver={ODBC Driver 17 for SQL Server};Server=...;Database=...;UID=...;PWD=...")
      # grave key e ct AQUI; a conn string em texto plano não fica em lugar nenhum
- Nota honesta: chave+cifra no mesmo repo = quem tem o repo decripta. Aceito porque
  os repos são privados/internos; evita credencial circulando em texto plano. Para
  segurança real (repo exposto), a chave teria que vir de fora (Key Vault).
"""
from __future__ import annotations

import logging
import os
import time

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()  # precisa rodar antes de qualquer os.getenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Pares Fernet por base e ambiente. DEV = D0.
DEV_<BASE>_KEY = b"<par gerado/copiado>"
DEV_<BASE>_CIPHERTEXT = b"<par gerado/copiado>"
HML_<BASE>_KEY = b"<par gerado/copiado>"
HML_<BASE>_CIPHERTEXT = b"<par gerado/copiado>"
PROD_<BASE>_KEY = b"<par gerado/copiado>"
PROD_<BASE>_CIPHERTEXT = b"<par gerado/copiado>"

# -----------------------------------------------------------------------------


def mask_password(conn_str: str) -> str:
    """Mascara a senha na connection string para logging seguro."""
    parts = []
    for part in conn_str.split(";"):
        if "=" in part:
            key, _ = part.split("=", 1)
            if key.strip().lower() in ("pwd", "password"):
                parts.append(f"{key}=***HIDDEN***")
            else:
                parts.append(part)
        elif part.strip():
            parts.append(part)
    return ";".join(parts)


def _build_conn_str(raw: str, label: str) -> str:
    """Aplica TLS e timeout à connection string descriptografada (lógica central)."""
    if "encrypt" not in raw.lower():
        raw += ";Encrypt=yes;TrustServerCertificate=yes"
    if "timeout" not in raw.lower():
        raw += ";timeout=30"
    return raw


def _connect(conn_str: str, label: str):
    """pyodbc.connect com logging e tratamento de erro padronizados."""
    import pyodbc  # import tardio: testes não precisam do driver ODBC

    logger.info(f"[{label}] Conn string FINAL: {mask_password(conn_str)}")
    start = time.time()
    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        logger.info(f"[{label}] Conexão estabelecida em {time.time() - start:.3f}s")
        return conn
    except Exception as e:
        logger.error(f"[{label}] Falha após {time.time() - start:.3f}s: {type(e).__name__}: {str(e)[:200]}")
        raise


def _decrypt(key: bytes, ciphertext: bytes, label: str) -> str:
    if b"<" in key or b"<" in ciphertext:
        raise RuntimeError(f"[{label}] Par KEY/CIPHERTEXT ainda é placeholder — preencha neste arquivo.")
    return Fernet(key).decrypt(ciphertext).decode()


# -----------------------------------------------------------------------------


def get_connection_<base>():
    """Conexão com a base <BASE>. Sem CONEXAO_PRD = DEV (D0); com = PROD."""
    prd = bool(os.getenv("CONEXAO_PRD"))
    label = "<BASE>"
    logger.info(f"[{label}] Iniciando conexão (ambiente: {'PROD' if prd else 'DEV'})")

    key = PROD_<BASE>_KEY if prd else DEV_<BASE>_KEY
    ciphertext = PROD_<BASE>_CIPHERTEXT if prd else DEV_<BASE>_CIPHERTEXT

    return _connect(_build_conn_str(_decrypt(key, ciphertext, label), label), label)


def get_connection_<base>_hml():
    """Conexão com a <BASE> de Homologação (HI) — só fora de produção."""
    label = "<BASE>-HML"
    logger.info(f"[{label}] Iniciando conexão (ambiente: HML)")
    return _connect(_build_conn_str(_decrypt(HML_<BASE>_KEY, HML_<BASE>_CIPHERTEXT, label), label), label)


def is_ambiente_prd() -> bool:
    """True quando o app roda em produção (API_ENV=PRD)."""
    return os.getenv("API_ENV", "").upper() == "PRD"


# -----------------------------------------------------------------------------
# (OPCIONAL — apps Streamlit: cache de conexão por sessão, com healthcheck.
#  Requer `import streamlit as st` no topo. Ver o arquivo de referência do
#  Transportes V2, função get_connection_ms10_session_cached.)
