"""Texto das regras do kit, onde quer que ele more.

Desde a 0.42.0 as regras do kit saem do `templates/CLAUDE.md` (que ficou só com a parte do projeto) e
vivem em dois blocos em `templates/regras-do-kit/`, que o hook `regras_do_kit.py` injeta em toda
janela. Um teste que procura TEXTO DE REGRA DO KIT lê `texto_do_kit()`; um teste que olha a parte do
projeto (Contexto/Infra, orçamento, tamanho de linha) continua lendo `templates/CLAUDE.md`.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MOLDE = REPO / "templates" / "CLAUDE.md"
BLOCOS = (
    REPO / "templates" / "regras-do-kit" / "1-modo-de-trabalho.md",
    REPO / "templates" / "regras-do-kit" / "2-regras-criticas.md",
)


def texto_do_kit() -> str:
    """Molde do projeto + bloco 1 + bloco 2, com `\\n` entre eles."""
    return "\n".join(p.read_text(encoding="utf-8") for p in (MOLDE, *BLOCOS))
