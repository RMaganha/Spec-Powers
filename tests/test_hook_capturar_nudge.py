"""Lembrete de captura — ligado por padrão no Stop, por sessão, avisa o owner e nunca bloqueia (F-048).

Até a 0.49.0 era opt-in e desligado (decisão de 2026-07-30). A conversa da tarde de 2026-10-30 no Whats
encerrou sem diário porque a captura dependia de alguém lembrar de digitar `/mss-spec:memory capturar`.
O owner: "sempre chamar o diário".

Propriedades:
- 1º Stop da conversa só marca o começo (calado); passado o intervalo sem captura → aviso ao owner
  (`systemMessage`), e remarca; captura recente (Write em `memory/sessions/` dentro do intervalo) → calado;
- `MSS_CAPTURA_INTERVALO_S=0` avisa sempre (teste); sessões independentes; exit 0 sempre; falha ABERTA;
  escape `MSS_CAPTURA_NUDGE_OFF=1`.
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
HOOK = REPO / "hooks" / "capturar_nudge.py"
T0 = 1_800_000_000.0   # um instante qualquer


def _mod():
    spec = importlib.util.spec_from_file_location("capturar_nudge", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def amb(tmp_path):
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)}


def _transcript(tmp_path, capturas_iso=()):
    linhas = []
    for ts in capturas_iso:
        linhas.append(json.dumps({"type": "assistant", "timestamp": ts, "message": {"content": [
            {"type": "tool_use", "name": "Write",
             "input": {"file_path": "C:\\proj\\memory\\sessions\\2026-10-30-x.md", "content": "x"}}]}}))
    t = tmp_path / f"t-{uuid.uuid4().hex[:6]}.jsonl"
    t.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return str(t)


def _ev(tmp_path, sessao=None, transcript=None):
    return {"hook_event_name": "Stop", "cwd": "C:\\proj", "session_id": sessao or "s-" + uuid.uuid4().hex[:8],
            "stop_hook_active": False, "transcript_path": transcript or _transcript(tmp_path)}


# --- AC1: por sessão, com intervalo ---------------------------------------------------------

def test_primeiro_stop_so_marca_e_depois_do_intervalo_avisa(amb, tmp_path):
    mod, s = _mod(), "s-" + uuid.uuid4().hex[:8]
    assert mod.decidir(_ev(tmp_path, s), amb, agora=T0) is None, "avisou no 1º Stop da conversa"
    assert mod.decidir(_ev(tmp_path, s), amb, agora=T0 + 600) is None, "avisou antes do intervalo"
    aviso = mod.decidir(_ev(tmp_path, s), amb, agora=T0 + 1900)
    assert aviso and "/mss-spec:memory capturar" in aviso and "31 min" in aviso
    assert mod.decidir(_ev(tmp_path, s), amb, agora=T0 + 2000) is None, "avisou de novo logo depois"
    assert mod.decidir(_ev(tmp_path, s), amb, agora=T0 + 3800), "não avisou depois de mais um intervalo"


def test_captura_recente_cala_e_rearma(amb, tmp_path):
    mod, s = _mod(), "s-" + uuid.uuid4().hex[:8]
    mod.decidir(_ev(tmp_path, s), amb, agora=T0)
    # às T0+1900 avisaria, mas o transcript mostra uma captura às T0+1500 (2027-01-15T08:25:00Z ≈ T0+1500)
    t = _transcript(tmp_path, [mod.datetime.fromtimestamp(T0 + 1500, mod.timezone.utc).isoformat()])
    assert mod.decidir(_ev(tmp_path, s, t), amb, agora=T0 + 1900) is None, "avisou com captura recente"
    assert mod.decidir(_ev(tmp_path, s, t), amb, agora=T0 + 3200) is None, "não rearmou a partir da captura"
    assert mod.decidir(_ev(tmp_path, s, t), amb, agora=T0 + 3400), "não avisou depois do intervalo pós-captura"


def test_sessoes_sao_independentes(amb, tmp_path):
    mod = _mod()
    mod.decidir(_ev(tmp_path, "s-a"), amb, agora=T0)
    assert mod.decidir(_ev(tmp_path, "s-b"), amb, agora=T0 + 1900) is None, "a marca de s-a valeu pra s-b"


def test_intervalo_zero_avisa_sempre(amb, tmp_path):
    assert _mod().decidir(_ev(tmp_path), {**amb, "MSS_CAPTURA_INTERVALO_S": "0"}, agora=T0)


def test_throttle_puro_continua():
    mod = _mod()
    assert mod.deve_cutucar(ultimo_ts=1000.0, agora=1060.0, intervalo_s=1800) is False
    assert mod.deve_cutucar(ultimo_ts=1000.0, agora=4600.0, intervalo_s=1800) is True
    assert mod.deve_cutucar(ultimo_ts=None, agora=1000.0, intervalo_s=1800) is True


# --- AC2: escape, falha aberta, só Stop ----------------------------------------------------

def test_escape_do_owner(amb, tmp_path):
    assert _mod().decidir(_ev(tmp_path), {**amb, "MSS_CAPTURA_INTERVALO_S": "0", "MSS_CAPTURA_NUDGE_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "x", {}, {"hook_event_name": "PreToolUse"},
                                  {"hook_event_name": "Stop", "session_id": None, "transcript_path": 3}])
def test_entrada_malformada_cala(amb, ruim):
    assert _mod().decidir(ruim, {**amb, "MSS_CAPTURA_INTERVALO_S": "0"}) is None or ruim.get("hook_event_name") == "Stop"


def test_intervalo_invalido_usa_o_padrao(amb, tmp_path):
    mod, s = _mod(), "s-" + uuid.uuid4().hex[:8]
    a = {**amb, "MSS_CAPTURA_INTERVALO_S": "trinta"}
    mod.decidir(_ev(tmp_path, s), a, agora=T0)
    assert mod.decidir(_ev(tmp_path, s), a, agora=T0 + 600) is None
    assert mod.decidir(_ev(tmp_path, s), a, agora=T0 + 1900)


# --- AC3: processo, fiação, documentação ---------------------------------------------------

def _rodar(ev, tmp_path, extra=None):
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path), **(extra or {})})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=amb, timeout=30)


def test_processo_avisa_o_owner_e_nunca_bloqueia(tmp_path):
    r = _rodar(_ev(tmp_path), tmp_path, {"MSS_CAPTURA_INTERVALO_S": "0"})
    assert r.returncode == 0
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert "systemMessage" in saida and "/mss-spec:memory capturar" in saida["systemMessage"]
    assert "decision" not in saida, "o lembrete não bloqueia — a cobrança dura é do diario_junto"


def test_processo_calado_no_primeiro_stop(tmp_path):
    r = _rodar(_ev(tmp_path), tmp_path)
    assert r.returncode == 0 and not r.stdout.strip()


def test_ligado_por_padrao_no_stop():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert any("capturar_nudge.py" in h["command"] for g in cfg["hooks"].get("Stop", []) for h in g["hooks"]), \
        "o lembrete de captura não está ligado no Stop"


def test_documentado_como_ligado():
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    low = doc.lower()
    assert "capturar_nudge.py" in doc
    assert "ligado por padrão" in low and "/mss-spec:memory capturar" in doc
    assert "não grava" in low or "nunca grava" in low
    assert "não bloqueia" in low or "não-bloqueante" in low or "nunca bloqueia" in low
    assert "MSS_CAPTURA_NUDGE_OFF" in doc, "o README não diz como desligar"
