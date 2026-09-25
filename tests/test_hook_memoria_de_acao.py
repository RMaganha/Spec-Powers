"""Memória na hora da ação (F-034) e resposta com rotas não pedidas (F-033).

F-034: o recall casa o prompt do owner; memória cujo gatilho é uma AÇÃO do assistente não chegava — o heredoc
com acento quebrou 3 vezes com a memória existindo, e "falta atualizar o plugin" foi dito com a memória da
junction dizendo o contrário. Memória declara `gatilho_comando:`/`gatilho_resposta:` (regex); o comando que
casa é negado UMA vez por sessão com a memória no motivo; a resposta que casa volta UMA vez por sessão.

F-033: o owner pediu um passo a passo e recebeu "Rota 1 / Rota 2", "dia definitivo", pendências. Medido em 211
respostas reais: ≥ 2 marcadores de rota alternativa numa resposta de mais de 300 palavras, sem o pedido falar
em opções, só pega a resposta do caso.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, REPO / "hooks" / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _temp_isolado(tmp_path, monkeypatch):
    pasta = tmp_path / "temp"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))


@pytest.fixture()
def proj(tmp_path):
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    mem.mkdir(parents=True)
    (mem / "feedback_nao_rodar_seed.md").write_text(
        "---\nname: feedback_nao_rodar_seed\ndescription: o seed apaga a base de homologação\n"
        "gatilho: quando for popular a base\ngatilho_comando: \\bseed\\.py\\b\n"
        "gatilho_resposta: (?i)rode o seed\nmetadata:\n  type: feedback\n---\n", encoding="utf-8")
    (mem / "velha.md").write_text("---\nname: velha\nobsoleta: 2026-01-01\ngatilho_comando: \\bls\\b\n---\n",
                                  encoding="utf-8")
    (mem / "quebrada.md").write_text("---\nname: quebrada\ngatilho_comando: ([\n---\n", encoding="utf-8")
    return raiz


def _cmd(raiz, comando, sessao="s1"):
    ev = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(raiz), "session_id": sessao}
    return _carregar("git_publicacao").avaliar(ev, {"CLAUDE_PROJECT_DIR": str(raiz)},
                                               git_destino=lambda p: ("feature/x", None))


# --- F-034, lado do comando -------------------------------------------------------------------

def test_comando_que_casa_a_memoria_e_negado_com_ela_no_motivo(proj):
    tipo, motivo = _cmd(proj, "python seed.py --tudo")
    assert tipo == "deny"
    assert "feedback_nao_rodar_seed" in motivo and "apaga a base" in motivo
    assert "repita" in motivo.lower(), "o motivo não diz que repetir o comando passa"


def test_so_uma_vez_por_sessao(proj):
    assert _cmd(proj, "python seed.py")[0] == "deny"
    assert _cmd(proj, "python seed.py")[0] is None, "negou de novo na mesma sessão"
    assert _cmd(proj, "python seed.py", sessao="s2")[0] == "deny", "outra sessão não viu a memória"


def test_comando_que_nao_casa_passa(proj):
    assert _cmd(proj, "python app.py")[0] is None


def test_obsoleta_e_regex_quebrado_nao_contam(proj):
    assert _cmd(proj, "ls -la")[0] is None


def test_escape_do_owner(proj):
    ev = {"tool_name": "Bash", "tool_input": {"command": "python seed.py"}, "cwd": str(proj), "session_id": "s1"}
    tipo, _ = _carregar("git_publicacao").avaliar(ev, {"CLAUDE_PROJECT_DIR": str(proj), "MSS_MEMORIA_ACAO_OFF": "1"},
                                                  git_destino=lambda p: ("feature/x", None))
    assert tipo is None


def test_memoria_do_kit_vale_em_qualquer_projeto(tmp_path):
    """O heredoc com acento é memória da MÁQUINA: mora no kit e vale no Whats também."""
    outro = tmp_path / "outro"
    outro.mkdir()
    tipo, motivo = _cmd(outro, "python - <<'PYEOF'\nprint('ação')\nPYEOF")
    assert tipo == "deny" and "project_heredoc_grande_com_acento_quebra_no_git_bash" in motivo


def test_heredoc_sem_acento_passa(tmp_path):
    outro = tmp_path / "outro"
    outro.mkdir()
    assert _cmd(outro, "python - <<'PYEOF'\nprint('ok')\nPYEOF")[0] is None


# --- lado da resposta (F-034) e rotas (F-033) -------------------------------------------------

def _transcript(tmp_path, prompt):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "user", "message": {"content": prompt}}) + "\n", encoding="utf-8")
    return str(t)


def _stop(raiz, texto, tmp_path, prompt="me passa o passo a passo", sessao="s1"):
    ev = {"hook_event_name": "Stop", "cwd": str(raiz), "session_id": sessao, "stop_hook_active": False,
          "last_assistant_message": texto, "transcript_path": _transcript(tmp_path, prompt)}
    return _carregar("confere_citacoes").decidir(ev, {})


def test_resposta_que_casa_a_memoria_volta_uma_vez(proj, tmp_path):
    motivo = _stop(proj, "Pronto. Agora rode o seed pra popular.", tmp_path)
    assert motivo and "feedback_nao_rodar_seed" in motivo
    assert _stop(proj, "Pronto. Agora rode o seed pra popular.", tmp_path) is None, "voltou 2× na mesma sessão"


def test_frase_real_do_plugin_casa_a_memoria_da_junction(tmp_path):
    outro = tmp_path / "outro"
    outro.mkdir()
    frase = "Para o hook novo valer nas próximas janelas, falta atualizar o plugin nesta máquina para a 0.32.0."
    motivo = _stop(outro, frase, tmp_path)
    assert motivo and "project_mss_spec_instalado_por_junction" in motivo


LONGA = " ".join(["passo"] * 320)


def test_rotas_nao_pedidas_numa_resposta_longa_voltam(proj, tmp_path):
    texto = f"{LONGA}\n**Rota 1 — direto do servidor**\n...\n**Rota 2 — pela sua máquina**\n..."
    motivo = _stop(proj, texto, tmp_path)
    assert motivo and "F-033" in motivo and "pergunt" in motivo.lower()


def test_rotas_pedidas_passam(proj, tmp_path):
    texto = f"{LONGA}\n**Opção A**\n...\n**Opção B**\n..."
    assert _stop(proj, texto, tmp_path, prompt="quais as opções pra fazer o restore?") is None


def test_resposta_curta_com_duas_opcoes_passa(proj, tmp_path):
    assert _stop(proj, "Rota 1: servidor. Rota 2: sua máquina. Qual vale?", tmp_path) is None


def test_stderr_do_processo_sai_como_nos_outros_hooks(proj, tmp_path):
    """Item 1: `print` comum no stderr, igual aos hooks que já aparecem certos ao vivo (o encoding explícito em
    UTF-8 da 0.35.0 viraria `â€”` se o Claude Code lê na página de código do Windows — não sabemos qual lê)."""
    src = (REPO / "hooks" / "confere_citacoes.py").read_text(encoding="utf-8")
    assert "sys.stderr.buffer.write" not in src
    assert "print(motivo, file=sys.stderr)" in src
