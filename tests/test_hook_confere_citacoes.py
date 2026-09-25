"""Confere citações — antes de a resposta sair, o que ela CITA tem de existir no disco.

Caso F-035: a regra "não inventar fatos concretos" era prosa, e a doc da Anthropic ("Reduce
hallucinations") manda verificar com citação e retirar o que não se sustenta. Hook `Stop` lê a resposta
final (`last_assistant_message`) e confere, sem LLM, as citações verificáveis: caminho de arquivo em
`crase` ou em link (com `:linha` — a linha tem de existir), `/mss-spec:<comando>` e `F-0NN` do EVALS.
Achou o que não existe → devolve a resposta UMA vez (exit 2, `stop_hook_active` evita laço).

Propriedades:
- citação que existe (no projeto ou no kit) → silêncio; nome solto (`MAPA.md`) casa em qualquer pasta;
- não confere: bloco de código cercado, URL, glob, placeholder (`<x>`, `${X}`), texto com espaço;
- nunca devolve duas vezes; falha ABERTA; escape `MSS_CITACOES_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "confere_citacoes.py"


def _mod():
    spec = importlib.util.spec_from_file_location("confere_citacoes", HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def proj(tmp_path):
    raiz = tmp_path / "proj"
    (raiz / "services").mkdir(parents=True)
    (raiz / "services" / "agent_bot_core.py").write_text("a\nb\nc\n", encoding="utf-8")
    (raiz / "docs" / "superpowers").mkdir(parents=True)
    (raiz / "docs" / "superpowers" / "MAPA.md").write_text("# mapa\n", encoding="utf-8")
    (raiz / "docs" / "EVALS.md").write_text("| F-001 | x |\n| F-012 | y |\n", encoding="utf-8")
    return raiz


def _ev(raiz, texto, **extra):
    return {"hook_event_name": "Stop", "cwd": str(raiz), "session_id": "s1", "stop_hook_active": False,
            "last_assistant_message": texto, **extra}


def _motivo(raiz, texto, **extra):
    return _mod().decidir(_ev(raiz, texto, **extra), {})


# --- AC1: o que existe passa calado -----------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "O loop fica em `services/agent_bot_core.py`.",
    "Veja [agent_bot_core.py:2](services/agent_bot_core.py:2).",
    "Linha `services/agent_bot_core.py:3` faz isso.",
    "O `MAPA.md` diz onde estamos.",
    "Rode `/mss-spec:mapa` e `/mss-spec:precedentes-msig`.",
    "Isso é o caso F-012.",
    "Link do app: [MAPA.md](/docs/superpowers/MAPA.md).",
    "O índice fica em `superpowers/MAPA.md`.",
    "O motor é o `memoria_indice.py` do kit.",
    "Revise contra `docs/SEGURANCA.md`.",
    "O hook do kit fica em `hooks/git_publicacao.py`.",
])
def test_citacao_que_existe_passa(proj, texto):
    assert _motivo(proj, texto) is None, f"barrou: {texto}"


# --- AC2: o que não existe devolve ------------------------------------------------------------

@pytest.mark.parametrize("texto, citado", [
    ("A regra está em `services/agent_bot_regras.py`.", "services/agent_bot_regras.py"),
    ("Veja `services/agent_bot_core.py:99`.", "services/agent_bot_core.py:99"),
    ("Abra [x](docs/NAO-EXISTE.md).", "docs/NAO-EXISTE.md"),
    ("O `CONFIG-GERAL.md` tem a chave.", "CONFIG-GERAL.md"),
    ("Rode `/mss-spec:deploy-producao`.", "/mss-spec:deploy-producao"),
    ("Isso já aconteceu no F-099.", "F-099"),
])
def test_citacao_inexistente_devolve(proj, texto, citado):
    motivo = _motivo(proj, texto)
    assert motivo is not None, f"passou: {texto}"
    assert citado in motivo, "o motivo não diz qual citação falhou"
    assert "não sei" in motivo.lower(), "o motivo não oferece o 'não sei'"


def test_linha_alem_do_fim_diz_quantas_o_arquivo_tem(proj):
    motivo = _motivo(proj, "Veja `services/agent_bot_core.py:99`.")
    assert "3 linhas" in motivo


# --- AC3: o que não se confere --------------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "```bash\npython services/nao_existe.py\n```",
    "Veja https://exemplo.com/docs/nao_existe.md e `https://x.io/a.py`.",
    "Qualquer `**/*.py` casa.",
    "Crie `<assunto>.md` em `docs/specs/<assunto>.md`.",
    "Use `${CLAUDE_PLUGIN_ROOT}/templates/x.py`.",
    "Rode `python services/nao_existe.py --aplicar`.",
    "Sem EVALS no projeto o F-777 não é conferido.",
    "| Backlog | → `docs/superpowers/BACKLOG.md` |",
    "Vou criar `hooks/confere_novo.py` com o verificador.",
    "O detalhe vai para `EM-ANDAMENTO.md`, com ponteiro.",
    "Arquivo novo: `tests/test_proposto.py`.",
    "O túnel vira um arquivo do projeto (`sql/setup/tunel-azure.py`).",
    "Não existe nenhum arquivo `indice.md` no repositório.",
])
def test_o_que_nao_e_citacao_verificavel_passa(proj, texto):
    if "F-777" in texto:
        (proj / "docs" / "EVALS.md").unlink()
    assert _motivo(proj, texto) is None, f"barrou: {texto}"


# --- AC4: uma vez só, escape, falha aberta ----------------------------------------------------

def test_nunca_devolve_duas_vezes(proj):
    assert _motivo(proj, "Veja `services/nao.py`.", stop_hook_active=True) is None


def test_escape_do_owner(proj):
    assert _mod().decidir(_ev(proj, "Veja `services/nao.py`."), {"MSS_CITACOES_OFF": "1"}) is None


def test_entrada_malformada_libera():
    mod = _mod()
    for ruim in (None, [], "x", {}, {"last_assistant_message": 3}, {"cwd": "", "last_assistant_message": "`a/b.py`"}):
        assert mod.decidir(ruim, {}) is None


def test_le_o_transcript_quando_falta_o_texto_final(proj, tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "isSidechain": False, "message": {
        "content": [{"type": "text", "text": "Veja `services/nao.py`."}]}}) + "\n", encoding="utf-8")
    ev = {"hook_event_name": "Stop", "cwd": str(proj), "stop_hook_active": False, "transcript_path": str(t)}
    assert _mod().decidir(ev, {}) is not None


# --- AC5: processo e registro -----------------------------------------------------------------

def _rodar(ev):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_CITACOES_OFF", "CLAUDE_PROJECT_DIR")}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                          encoding="utf-8", env=amb, timeout=30)


def test_processo_devolve_com_exit_2_e_motivo_no_stderr(proj):
    r = _rodar(_ev(proj, "Veja `services/nao.py`."))
    assert r.returncode == 2 and "services/nao.py" in r.stderr


def test_processo_calado_sai_zero(proj):
    r = _rodar(_ev(proj, "Veja `services/agent_bot_core.py`."))
    assert r.returncode == 0 and not r.stdout.strip() and not r.stderr.strip()


def test_hook_registrado_no_stop():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert any("confere_citacoes.py" in h["command"] for g in cfg["hooks"].get("Stop", []) for h in g["hooks"])
