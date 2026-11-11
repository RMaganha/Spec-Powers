"""Hook do mss-spec: MEMÓRIA EM TABELA EM DIA — a tabela de memória se atualiza sozinha.

Por que existe (caso F-057, `docs/EVALS.md`): a parte 1 da memória em tabela entregou um modo manual
(`/mss-spec:memory tabela`) e a tabela real ficou só com o kit. O owner recusou comando pra lembrar: *"vai fazer
se perder quando eu perguntar"*. Decisão dele (2026-11-11, `docs/specs/memoria-em-tabela.md`, 13 e 15): grava-se
no arquivo e a tabela acompanha; ela se atualiza quando a conversa abre no projeto e é montada na hora se não
existir.

Contrato:
- evento `SessionStart` (startup, resume, clear, compact): atualiza a tabela do projeto da janela
  (`CLAUDE_PROJECT_DIR` › `cwd`). Em dia → silêncio, sem ler arquivo nem chamar o git (a conferência compara só
  nome, tamanho e data). Montada do zero → UMA linha pro assistente. Não deu pra atualizar → uma linha pro
  assistente mandando buscar nos arquivos;
- evento `PostToolUse` de Write/Edit/MultiEdit: age só quando o arquivo gravado é `.md`/`.html` de `memory/`,
  de `docs/`, o `to-dolist.md` ou o `projeto.md` DESTE projeto. Sempre calado, dê certo ou não (a busca confere
  de novo antes de procurar);
- projeto sem a pasta `memory/` → nada (não é projeto com memória do kit);
- recado só pro ASSISTENTE: nunca `systemMessage`, nunca "avise o owner" — ele não tem nada a fazer
  (`docs/decisoes.md`, 2026-11-03: hook que fica alarmando o owner não serve);
- **nunca bloqueia**; **falha ABERTA**: qualquer defeito → exit 0. Nenhum script da máquina, tarefa agendada ou
  processo solto: tudo roda dentro do próprio hook (`docs/decisoes.md`, 2026-11-03).
O motor é o `templates/memoria_tabela.py` (`atualizar`), o mesmo do `buscar`.

Escape consciente, só do owner: `MSS_MEMORIA_TABELA_OFF=1`.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path


# Registro local do que este hook FEZ (`hooks/_registro.py`). Nunca muda a decisão: sem o módulo,
# ou com qualquer defeito dele, o hook segue exatamente igual.
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
            _registrar("memoria_tabela_em_dia", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_MEMORIA_TABELA_OFF"
TOOLS_DE_ARQUIVO = ("Write", "Edit", "MultiEdit")
# cópia de templates/memoria_tabela.py (decide se a gravação interessa ANTES de carregar o motor; um teste
# trava a igualdade)
PASTAS = ("memory", "docs")
SOLTOS = ("to-dolist.md", "projeto.md")
EXTENSOES = (".md", ".html")
RESERVA = "`memory/MEMORY.md` → o subíndice da família → a memória, e a palavra em `memory/` e `docs/`"


def _motor():
    """Importa templates/memoria_tabela.py pelo caminho do plugin (hooks/ e templates/ são irmãos)."""
    caminho = Path(__file__).resolve().parent.parent / "templates" / "memoria_tabela.py"
    spec = importlib.util.spec_from_file_location("memoria_tabela", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def no_alcance(evento, raiz: Path) -> bool:
    """True se a ferramenta gravou um arquivo que a tabela guarda, dentro do projeto da janela."""
    if evento.get("tool_name") not in TOOLS_DE_ARQUIVO:
        return False
    entrada = evento.get("tool_input")
    caminho = entrada.get("file_path") if isinstance(entrada, dict) else None
    if not isinstance(caminho, str) or not caminho.strip():
        return False
    alvo = Path(caminho) if os.path.isabs(caminho) else raiz / caminho
    try:
        rel = alvo.resolve().relative_to(raiz.resolve()).as_posix()
    except (OSError, ValueError):
        return False                                 # fora do projeto da janela
    if not rel.lower().endswith(EXTENSOES):
        return False
    return rel in SOLTOS or rel.split("/", 1)[0] in PASTAS


def _para_o_assistente(nome, texto):
    return {"hookSpecificOutput": {"hookEventName": nome, "additionalContext": texto}}


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → silêncio ou o recado de reserva (falha aberta)."""
    nome = None
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip() or not isinstance(evento, dict):
            return None
        nome = evento.get("hook_event_name")
        if nome not in ("SessionStart", "PostToolUse"):
            return None
        raiz_txt = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz_txt, str) or not raiz_txt.strip():
            return None
        raiz = Path(raiz_txt)
        if not (raiz / "memory").is_dir():
            return None
        if nome == "PostToolUse" and not no_alcance(evento, raiz):
            return None
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None
    try:
        motor = _motor()
        informada = str(ambiente.get("MSS_MEMORIA_TABELA", "")).strip()
        tabela = Path(informada) if informada else motor.caminho_tabela()
        feito = motor.atualizar(raiz, tabela)
        if feito is None:
            return None                              # em dia
        linhas = sum(feito.por_tipo.values())
        do_zero = feito.novos > 0 and not (feito.refeitos or feito.removidos or feito.iguais)
        _anotar("montou" if do_zero else "atualizou",
                f"{feito.novos} novo(s) · {feito.refeitos} refeito(s) · {feito.removidos} removido(s)", evento)
        if nome == "SessionStart" and do_zero:
            return _para_o_assistente(nome, f"[mss-spec] tabela de memória deste projeto montada agora ({linhas} "
                                            f"linhas, em {tabela}). É cópia pra busca: o arquivo no git segue sendo o "
                                            "original. Recado só pra você — o owner não precisa fazer nada.")
        return None
    except Exception as erro:                        # noqa: BLE001 — falha ABERTA
        _anotar("falhou", type(erro).__name__, evento)
        if nome == "SessionStart":
            return _para_o_assistente(nome, "[mss-spec] a tabela de memória não pôde ser atualizada agora "
                                            f"({type(erro).__name__}). Não trava nada: se a busca não responder, vá nos "
                                            f"arquivos — {RESERVA}. Recado só pra você.")
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    saida = responder(evento)
    if saida is not None:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:                            # noqa: BLE001
            pass
        print(json.dumps(saida, ensure_ascii=False))
    sys.exit(0)                                      # SEMPRE 0 — não bloqueia


if __name__ == "__main__":
    main()
