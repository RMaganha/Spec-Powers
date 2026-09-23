"""Hook do mss-spec: TETO AO GRAVAR — o excesso da partida sai na hora em que entra.

Por que existe (caso F-030, `docs/EVALS.md`): quem escreve no MAPA/INDEX (`/mss-spec:mapa`, `nova-feature`,
`memory capturar`) só acrescenta, e ninguém tirava. O `doctor` media, o hook de abertura avisava, e o Whats
chegou a 160 KB de partida mesmo assim — porque o conserto dependia de alguém lembrar de rodar o rodízio.
Aqui o conserto roda na própria gravação.

Contrato:
- evento `PostToolUse`; age só quando a ferramenta gravou `docs/superpowers/MAPA.md`,
  `docs/superpowers/INDEX.md` ou o `CLAUDE.md` da raiz (`CLAUDE_PROJECT_DIR` › `cwd`): Write/Edit/MultiEdit
  pelo `file_path`; Bash/PowerShell quando o comando cita o nome do arquivo;
- MAPA/INDEX acima do teto → `templates/rodizio_partida.py enxugar --aplicar` (move, nunca apaga, com
  conservação conferida; para assim que cabe) + `additionalContext` dizendo o que foi pra onde e pra
  reler antes do próximo Edit; se o que sobra é conteúdo vivo, pede o resumo pra spec;
- `CLAUDE.md` acima de 10 KB → só avisa (destino de bloco de regra é julgamento; F-029: nunca comprimir);
- arquivo com conflito de merge → não toca e avisa;
- **nunca bloqueia**; **falha ABERTA**: defeito → exit 0 calado.

Escape consciente, só do owner: `MSS_TETO_OFF=1`.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path


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
            _registrar("teto_ao_gravar", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_TETO_OFF"
TETO_CLAUDE_MD = 10000
ALVOS = ("docs/superpowers/MAPA.md", "docs/superpowers/INDEX.md", "CLAUDE.md")
TOOLS_DE_ARQUIVO = ("Write", "Edit", "MultiEdit")
TOOLS_DE_SHELL = ("Bash", "PowerShell")


def _motor():
    caminho = Path(__file__).resolve().parent.parent / "templates" / "rodizio_partida.py"
    spec = importlib.util.spec_from_file_location("rodizio_partida", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _norm(p):
    return os.path.normcase(os.path.abspath(p))


def tocados(evento, raiz):
    """Quais dos ALVOS esta gravação pode ter mexido (relativos à raiz)."""
    entrada = evento.get("tool_input")
    if not isinstance(entrada, dict):
        return []
    tool = evento.get("tool_name")
    if tool in TOOLS_DE_ARQUIVO:
        caminho = entrada.get("file_path")
        if not isinstance(caminho, str) or not caminho.strip():
            return []
        alvo = _norm(caminho if os.path.isabs(caminho) else os.path.join(raiz, caminho))
        return [rel for rel in ALVOS if alvo == _norm(os.path.join(raiz, *rel.split("/")))]
    if tool in TOOLS_DE_SHELL:
        comando = entrada.get("command")
        if not isinstance(comando, str):
            return []
        return [rel for rel in ALVOS if rel.rsplit("/", 1)[-1] in comando]
    return []


def _kb(n):
    return f"{n / 1000:.1f} KB".replace(".", ",")


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip() or not isinstance(evento, dict):
            return None
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip() or not os.path.isdir(raiz):
            return None
        alvos = tocados(evento, raiz)
        if not alvos:
            return None
        partes, detalhes = [], []
        if any(a != "CLAUDE.md" for a in alvos):
            motor = _motor()
            for qual, r in motor.enxugar(Path(raiz), aplicar=True).items():
                nome = "MAPA.md" if qual == "mapa" else "INDEX.md"
                if r.passos:
                    partes.append(f"{nome} {_kb(r.bytes_antes)} → {_kb(r.bytes_depois)}: " + " · ".join(r.passos))
                    detalhes.append(f"{nome}={r.bytes_antes}->{r.bytes_depois}")
                partes += r.problemas + r.avisos
        if "CLAUDE.md" in alvos:
            n = os.path.getsize(os.path.join(raiz, "CLAUDE.md")) if os.path.isfile(os.path.join(raiz, "CLAUDE.md")) else 0
            if n > TETO_CLAUDE_MD:
                partes.append(f"CLAUDE.md com {_kb(n)} (teto 10 KB): mova um bloco INTEIRO com ponteiro — regra de "
                              "tipo de arquivo pra `.claude/rules/<x>.md` com `paths:`, procedimento pra `docs/` — e "
                              "nunca comprima a redação de uma regra (F-029). Não movi nada aqui: é julgamento.")
                detalhes.append(f"CLAUDE.md={n}")
        if not partes:
            return None
        moveu = any("→" in p for p in partes)
        texto = ("[mss-spec] teto da partida (F-030): " + " | ".join(partes)
                 + (". Nada foi apagado (o `git diff` mostra). Releia o arquivo antes do próximo Edit nele — o texto "
                    "mudou de lugar." if moveu else "")
                 + " Avise o owner em 1 linha.")
        _anotar("moveu" if moveu else "avisou", " ".join(detalhes)[:200], evento)
        return {
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": texto},
            "systemMessage": "[mss-spec] teto da partida: " + " | ".join(p[:120] for p in partes)[:300],
        }
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    saida = responder(evento)
    if saida is not None:
        print(json.dumps(saida))
    sys.exit(0)                                      # SEMPRE 0 — não bloqueia


if __name__ == "__main__":
    main()
