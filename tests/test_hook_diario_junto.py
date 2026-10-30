"""Diário junto da memória — memória gravada sem `memory/sessions/` não sai (caso F-048).

A conversa da tarde de 2026-10-30 no Whats gravou `docs/EVALS.md` (F-093, F-094) e duas specs e encerrou sem
diário: o problema que ficou aberto (resposta do especialista que não volta pro WhatsApp em produção) não
ficou escrito em lugar nenhum. O owner: "o diário tem que ser junto com a memória, assim que gravar ela".

Propriedades:
- `Stop`: gravou `memory/<x>.md` (fora topo/índice), `docs/EVALS.md` ou `docs/decisoes.md` e nenhum
  `memory/sessions/<x>.md` → devolve a resposta pelo contrato do Stop (JSON `block`, exit 0);
- cobra uma vez por arquivo de memória; memória nova depois da cobrança cobra de novo; diário gravado → passa;
- `stop_hook_active` → passa (nunca laço); subagente não conta; falha ABERTA; escape `MSS_DIARIO_JUNTO_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "diario_junto.py"
PROJ = "C:\\Ronaldo\\_Mitsui\\Python\\IA Bot Agent\\IA Bot Agent - Whats"


def _mod():
    spec = importlib.util.spec_from_file_location("diario_junto", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def amb(tmp_path):
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)}


def _transcript(tmp_path, caminhos, sidechain=()):
    """Um transcript com um Write por caminho (e os de `sidechain` marcados como subagente)."""
    linhas = [json.dumps({"type": "user", "message": {"content": "oi"}})]
    for c in caminhos:
        linhas.append(json.dumps({"type": "assistant", "timestamp": "2026-10-30T18:00:00.000Z", "message": {
            "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": c, "content": "x"}}]}}))
    for c in sidechain:
        linhas.append(json.dumps({"type": "assistant", "isSidechain": True, "message": {
            "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": c}}]}}))
    t = tmp_path / f"t-{uuid.uuid4().hex[:6]}.jsonl"
    t.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return str(t)


def _ev(transcript, sessao=None, ativo=False):
    return {"hook_event_name": "Stop", "cwd": PROJ, "session_id": sessao or "s-" + uuid.uuid4().hex[:8],
            "stop_hook_active": ativo, "transcript_path": transcript}


# --- AC1: a conversa real — EVALS e specs gravadas, diário nenhum ------------------------------

def test_evals_sem_diario_devolve(amb, tmp_path):
    t = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md", PROJ + "\\docs\\specs\\financeiro-no-whatsapp.md"])
    motivo = _mod().decidir(_ev(t), amb)
    assert motivo and "memory/sessions/" in motivo and "docs/EVALS.md" in motivo
    assert "/mss-spec:memory capturar" in motivo and "DIARIO.md" in motivo


@pytest.mark.parametrize("caminho", [
    PROJ + "\\memory\\token-do-whatsapp-sem-gate.md",
    "memory/token-do-whatsapp-sem-gate.md",
    PROJ + "/docs/decisoes.md",
    "docs/EVALS.md",
])
def test_memoria_decisao_e_evals_contam(amb, tmp_path, caminho):
    assert _mod().decidir(_ev(_transcript(tmp_path, [caminho])), amb)


@pytest.mark.parametrize("caminho", [
    PROJ + "\\memory\\MEMORY.md",
    PROJ + "\\memory\\DIARIO.md",
    PROJ + "\\memory\\indice\\integracoes.md",
    PROJ + "\\docs\\specs\\handoff-chatwoot.md",
    PROJ + "\\chat_server.py",
    PROJ + "\\memory\\rascunho.txt",
])
def test_topo_indice_spec_e_codigo_nao_contam(amb, tmp_path, caminho):
    assert _mod().decidir(_ev(_transcript(tmp_path, [caminho])), amb) is None


# --- AC2: com o diário, passa; cobra uma vez por memória ------------------------------------

def test_com_diario_passa(amb, tmp_path):
    t = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md", PROJ + "\\memory\\sessions\\2026-10-30-token-whatsapp.md"])
    assert _mod().decidir(_ev(t), amb) is None


def test_cobra_uma_vez_e_de_novo_so_com_memoria_nova(amb, tmp_path):
    mod, s = _mod(), "s-" + uuid.uuid4().hex[:8]
    t1 = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md"])
    assert mod.decidir(_ev(t1, s), amb)
    assert mod.decidir(_ev(t1, s), amb) is None, "cobrou duas vezes a mesma memória"
    t2 = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md", PROJ + "\\memory\\nova-memoria.md"])
    motivo = mod.decidir(_ev(t2, s), amb)
    assert motivo and "nova-memoria.md" in motivo and "EVALS.md" not in motivo.split("—")[1]


def test_sessoes_sao_independentes(amb, tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md"])
    assert mod.decidir(_ev(t, "s-a"), amb)
    assert mod.decidir(_ev(t, "s-b"), amb), "a cobrança de s-a valeu pra s-b"


# --- AC3: nunca laço, subagente, escape, falha aberta --------------------------------------

def test_stop_hook_active_passa(amb, tmp_path):
    t = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md"])
    assert _mod().decidir(_ev(t, ativo=True), amb) is None


def test_gravacao_de_subagente_nao_conta(amb, tmp_path):
    t = _transcript(tmp_path, [], sidechain=[PROJ + "\\docs\\EVALS.md"])
    assert _mod().decidir(_ev(t), amb) is None


def test_escape_do_owner(amb, tmp_path):
    t = _transcript(tmp_path, [PROJ + "\\docs\\EVALS.md"])
    assert _mod().decidir(_ev(t), {**amb, "MSS_DIARIO_JUNTO_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "x", {}, {"hook_event_name": "PreToolUse"},
                                  {"hook_event_name": "Stop", "transcript_path": "C:/nao/existe.jsonl"},
                                  {"hook_event_name": "Stop", "transcript_path": 7}])
def test_entrada_malformada_libera(amb, ruim):
    assert _mod().decidir(ruim, amb) is None


def test_transcript_ilegivel_libera(amb, tmp_path):
    t = tmp_path / "ruim.jsonl"
    t.write_text('{"type": "assistant", "message": {"content": [{"type": "tool_use"\nnão é json\n', encoding="utf-8")
    assert _mod().decidir(_ev(str(t)), amb) is None


# --- AC4: processo, registro e fiação ------------------------------------------------------

def _rodar(ev, tmp_path, extra=None):
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path), **(extra or {})})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=amb, timeout=30)


def test_processo_devolve_pelo_contrato_do_stop(tmp_path):
    r = _rodar(_ev(_transcript(tmp_path, [PROJ + "\\docs\\EVALS.md"])), tmp_path)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["decision"] == "block" and "memory/sessions/" in saida["reason"]


def test_processo_calado_quando_passa(tmp_path):
    r = _rodar(_ev(_transcript(tmp_path, [PROJ + "\\chat_server.py"])), tmp_path)
    assert r.returncode == 0 and not r.stdout.strip()


def test_devolucao_fica_no_registro(tmp_path):
    reg = tmp_path / "registro-hooks.jsonl"
    _rodar(_ev(_transcript(tmp_path, [PROJ + "\\docs\\EVALS.md"]), "abcdef123456"), tmp_path,
           {"MSS_REGISTRO_ARQUIVO": str(reg)})
    linhas = [json.loads(l) for l in reg.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(linhas) == 1 and linhas[0]["hook"] == "diario_junto" and linhas[0]["decisao"] == "devolveu"
    assert "memoria_sem_diario=1" in linhas[0]["detalhe"]


def test_hook_registrado_no_stop():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert any("diario_junto.py" in h["command"] for g in cfg["hooks"].get("Stop", []) for h in g["hooks"])


def test_documentado_no_readme():
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "diario_junto.py" in doc and "memory/sessions/" in doc
