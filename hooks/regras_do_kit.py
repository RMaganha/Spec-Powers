"""Hook do mss-spec: REGRAS DO KIT — entrega, em toda janela, as regras que o plugin carrega.

Por que existe: as regras do kit (modo de trabalho · regras críticas) moravam coladas no `CLAUDE.md`
de cada projeto — cópia que envelhece e some a cada atualização do plugin. Agora moram em
`templates/regras-do-kit/` (1-modo-de-trabalho.md · 2-regras-criticas.md) e este hook as injeta no
`SessionStart`. O `CLAUDE.md` do projeto só carrega a marca `<!-- mss-spec:regras-do-kit -->`.

Contrato:
- evento `SessionStart` (startup, resume, clear, compact); **nunca bloqueia** (exit 0 sempre);
- `python regras_do_kit.py --bloco N`: uma entrada por bloco em `hooks/hooks.json`, porque o Claude
  Code corta cada `additionalContext` em 10.000 caracteres (acima, vira arquivo + prévia de 2.000) —
  daí `LIMITE` = 9.000 caracteres por bloco, com folga;
- raiz = `CLAUDE_PROJECT_DIR` › `cwd`; sem a linha-marca no `CLAUDE.md` da raiz → silêncio
  (projeto que não é do kit não recebe nada); a marca vale com BOM e CRLF;
- **falha VISÍVEL depois da marca**: bloco ilegível, acima do limite ou qualquer defeito →
  `systemMessage` de 1 linha, nunca bloco truncado. É o hook em que o silêncio custa caro: sem ele
  a janela abre sem as regras e ninguém percebe. Antes da marca, defeito → calado.

Escape consciente, só do owner: `MSS_REGRAS_KIT_OFF=1`.
"""
import json
import os
import sys
from pathlib import Path


# Registro local do que este hook FEZ (`hooks/_registro.py`). Nunca muda a decisão.
try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("regras_do_kit", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_REGRAS_KIT_OFF"
MARCA = "<!-- mss-spec:regras-do-kit -->"
BLOCOS = {1: "1-modo-de-trabalho.md", 2: "2-regras-criticas.md"}
PASTA_BLOCOS = Path(__file__).resolve().parent.parent / "templates" / "regras-do-kit"
LIMITE = 9000                                        # caracteres; o teto do Claude Code é 10.000
AVISO = "[mss-spec] regras do kit não carregaram — rode /mss-spec:doctor"


def tem_marca(raiz):
    """True se o `CLAUDE.md` da raiz tem a linha-marca (depois de tirar BOM e `\\r`)."""
    try:
        with open(os.path.join(raiz, "CLAUDE.md"), encoding="utf-8", errors="replace") as f:
            texto = f.read().lstrip("﻿")
    except (OSError, UnicodeError):
        return False
    return any(linha.strip() == MARCA for linha in texto.replace("\r", "").split("\n"))


def _ler_bloco(bloco):
    """Texto do bloco; levanta se o bloco não existe, não abre, está vazio ou passa do limite."""
    texto = (PASTA_BLOCOS / BLOCOS[bloco]).read_text(encoding="utf-8").lstrip("﻿")
    if not texto.strip():
        raise ValueError("bloco vazio")
    if len(texto) > LIMITE:
        raise ValueError(f"bloco com {len(texto)} caracteres, acima de {LIMITE}")
    return texto


def responder(evento, ambiente=None, bloco=1):
    """dict pra imprimir, ou None = silêncio. Antes da marca, defeito → None; depois, aviso visível."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None
        if not isinstance(evento, dict):
            return None
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip() or not os.path.isdir(raiz):
            return None
        if not tem_marca(raiz):
            return None
    except Exception:                                # noqa: BLE001 — antes da marca: calado
        return None
    # Marca confirmada: daqui em diante, silêncio seria o defeito.
    try:
        texto = _ler_bloco(bloco)
        _anotar("entregou", f"bloco={bloco} caracteres={len(texto)}", evento)
        return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}}
    except Exception as erro:                        # noqa: BLE001 — falha VISÍVEL
        _anotar("falhou", f"bloco={bloco} {type(erro).__name__}", evento)
        return {"systemMessage": AVISO}


def _bloco_do_argv(argv):
    """`--bloco N` → int; ausente ou malformado → 0 (bloco inexistente: avisa depois da marca)."""
    try:
        if "--bloco" in argv:
            return int(argv[argv.index("--bloco") + 1])
        return 1
    except Exception:                                # noqa: BLE001
        return 0


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    try:
        saida = responder(evento, bloco=_bloco_do_argv(sys.argv[1:]))
        if saida is not None:
            print(json.dumps(saida))
    except Exception:                                # noqa: BLE001
        pass
    sys.exit(0)                                      # SEMPRE 0 — não bloqueia


if __name__ == "__main__":
    main()
