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


def marca_no(texto):
    """True se o texto do `CLAUDE.md` tem a linha-marca (depois de tirar BOM e `\\r`)."""
    return any(linha.strip() == MARCA for linha in (texto or "").lstrip("﻿").replace("\r", "").split("\n"))


class DiscoReal:
    """O disco que a regra consulta. Em teste, a regra recebe no lugar um objeto com os mesmos 3 métodos."""

    @staticmethod
    def eh_pasta(caminho):
        return os.path.isdir(caminho)

    @staticmethod
    def ler_claude(raiz):
        """O `CLAUDE.md` da raiz, ou None. `errors="replace"`: a marca é ASCII, então um CLAUDE.md fora de UTF-8
        ainda a mostra."""
        try:
            with open(os.path.join(raiz, "CLAUDE.md"), encoding="utf-8", errors="replace") as f:
                return f.read()
        except (OSError, UnicodeError):
            return None

    @staticmethod
    def ler_bloco(nome):
        """O texto de um bloco de `PASTA_BLOCOS` (levanta se não abre)."""
        return (PASTA_BLOCOS / nome).read_text(encoding="utf-8")


def tem_marca(raiz):
    return marca_no(DiscoReal.ler_claude(raiz))


RAIZ_DO_KIT = Path(__file__).resolve().parent.parent


def _com_caminho(texto, ambiente):
    """`${CLAUDE_PLUGIN_ROOT}` trocado pelo caminho do kit, com barra `/` (0.67.0, caso F-077): o texto que entra
    pelo hook não passa pela troca que o Claude faz nos comandos, e a regra "leia `commands/<x>.md`" sem caminho
    mandou a conversa procurar o arquivo em `~/.claude/plugins`. A variável do ambiente vence; sem ela, a pasta
    acima de `hooks/`."""
    raiz = str(ambiente.get("CLAUDE_PLUGIN_ROOT") or "").strip() or str(RAIZ_DO_KIT)
    return texto.replace("${CLAUDE_PLUGIN_ROOT}", raiz.replace("\\", "/").rstrip("/"))


def _bloco_valido(texto):
    """O texto do bloco sem BOM; levanta se está vazio ou passa do limite."""
    texto = texto.lstrip("﻿")
    if not texto.strip():
        raise ValueError("bloco vazio")
    if len(texto) > LIMITE:
        raise ValueError(f"bloco com {len(texto)} caracteres, acima de {LIMITE}")
    return texto


def regra(evento, ambiente, bloco, disco):
    """A REGRA, sem disco: `disco` responde se a raiz é pasta, o texto do CLAUDE.md e o texto de um bloco
    (`DiscoReal`, ou o de teste). Devolve `(saida, anotacoes)`: saida = dict pra imprimir, ou None = silêncio.
    Antes da marca, defeito → None; depois, aviso visível."""
    anotacoes = []
    try:
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None, anotacoes
        if not isinstance(evento, dict):
            return None, anotacoes
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip() or not disco.eh_pasta(raiz):
            return None, anotacoes
        if not marca_no(disco.ler_claude(raiz)):
            return None, anotacoes
    except Exception:                                # noqa: BLE001 — antes da marca: calado
        return None, anotacoes
    # Marca confirmada: daqui em diante, silêncio seria o defeito.
    try:
        texto = _bloco_valido(_com_caminho(disco.ler_bloco(BLOCOS[bloco]), ambiente))
        anotacoes.append(("entregou", f"bloco={bloco} caracteres={len(texto)}"))
        return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}}, anotacoes
    except Exception as erro:                        # noqa: BLE001 — falha VISÍVEL
        anotacoes.append(("falhou", f"bloco={bloco} {type(erro).__name__}"))
        return {"systemMessage": AVISO}, anotacoes


def responder(evento, ambiente=None, bloco=1):
    """A casca: a regra com o disco de verdade, e o registro gravado. dict pra imprimir, ou None = silêncio."""
    ambiente = os.environ if ambiente is None else ambiente
    saida, anotacoes = regra(evento, ambiente, bloco, DiscoReal)
    for decisao, detalhe in anotacoes:
        _anotar(decisao, detalhe, evento)
    return saida


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
        from _entrada import ler_evento          # UTF-8, seja qual for a página de código do console
        evento = ler_evento()
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
