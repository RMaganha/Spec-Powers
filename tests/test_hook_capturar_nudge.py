"""Lembrete de captura — ligado por padrão no Stop, por sessão, avisa o owner e nunca bloqueia (F-048).

Até a 0.49.0 era opt-in e desligado (decisão de 2026-07-30). A conversa da tarde de 2026-10-30 no Whats
encerrou sem diário porque a captura dependia de alguém lembrar de digitar `/mss-spec:memory capturar`.
O owner: "sempre chamar o diário".

Propriedades:
- 1º Stop da conversa só marca o começo (calado); passado o intervalo sem captura → aviso ao owner
  (`systemMessage`), e remarca; captura recente (Write em `memory/sessions/` dentro do intervalo) → calado;
- `MSS_CAPTURA_INTERVALO_S=0` avisa sempre (teste); sessões independentes; exit 0 sempre; falha ABERTA;
  escape `MSS_CAPTURA_NUDGE_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o texto do transcript entra como dado (lido pela
`_transcricao.gravacoes_do_texto`) e a marca de cada conversa fica num dicionário. O disco de verdade (ler o
transcript, gravar e ler a marca) fica num teste só, numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PADRAO = object()          # evento omitido = o evento padrão do teste; None é o caso da entrada malformada
HOOK = REPO / "hooks" / "capturar_nudge.py"
T0 = 1_800_000_000.0   # um instante qualquer


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("capturar_nudge", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _transcript(capturas=()):
    """O texto de um transcript com um Write em `memory/sessions/` por instante (epoch) de `capturas`."""
    linhas = [json.dumps({"type": "user", "message": {"content": "oi"}})]
    for epoch in capturas:
        linhas.append(json.dumps({"type": "assistant",
                                  "timestamp": datetime.fromtimestamp(epoch, timezone.utc).isoformat(),
                                  "message": {"content": [{"type": "tool_use", "name": "Write", "input": {
                                      "file_path": "C:\\proj\\memory\\sessions\\2026-10-30-x.md", "content": "x"}}]}}))
    return "\n".join(linhas) + "\n"


class Conversas:
    """A marca de cada conversa, em memória. `decidir` chama a regra com o texto do transcript como dado e guarda a
    marca que ela manda gravar — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.marcas, self.anotacoes = mod, {}, []
        self.tr = sys.modules["_transcricao"]

    def decidir(self, agora, sessao="s1", transcript="", ambiente=None, evento=PADRAO):
        ev = evento if evento is not PADRAO else {"hook_event_name": "Stop", "cwd": "C:\\proj", "session_id": sessao,
                                                "stop_hook_active": False, "transcript_path": "t.jsonl"}
        aviso, mudancas = self.mod.regra(ev, ambiente or {}, lambda: self.tr.gravacoes_do_texto(transcript),
                                         lambda s: self.marcas.get(s), agora)
        if "marca" in mudancas:
            self.marcas[sessao] = mudancas["marca"]
        self.anotacoes += mudancas["anotacoes"]
        return aviso


@pytest.fixture()
def conv(mod):
    return Conversas(mod)


# --- AC1: por sessão, com intervalo ---------------------------------------------------------

def test_primeiro_stop_so_marca_e_depois_do_intervalo_avisa(conv):
    assert conv.decidir(T0) is None, "avisou no 1º Stop da conversa"
    assert conv.decidir(T0 + 600) is None, "avisou antes do intervalo"
    aviso = conv.decidir(T0 + 1900)
    assert aviso and "/mss-spec:memory capturar" in aviso and "31 min" in aviso
    assert conv.decidir(T0 + 2000) is None, "avisou de novo logo depois"
    assert conv.decidir(T0 + 3800), "não avisou depois de mais um intervalo"
    assert conv.anotacoes == [("lembrou", "sem_captura_ha=31min"), ("lembrou", "sem_captura_ha=31min")]


def test_captura_recente_cala_e_rearma(conv):
    conv.decidir(T0)
    t = _transcript([T0 + 1500])           # às T0+1900 avisaria, mas houve captura às T0+1500
    assert conv.decidir(T0 + 1900, transcript=t) is None, "avisou com captura recente"
    assert conv.decidir(T0 + 3200, transcript=t) is None, "não rearmou a partir da captura"
    assert conv.decidir(T0 + 3400, transcript=t), "não avisou depois do intervalo pós-captura"


def test_captura_fora_de_memory_sessions_nao_conta(mod):
    tr = sys.modules["_transcricao"]
    gravs = tr.gravacoes_do_texto(_transcript([T0]).replace("memory\\\\sessions", "docs"))
    assert mod.captura_mais_recente(gravs) is None
    assert mod.captura_mais_recente(tr.gravacoes_do_texto(_transcript([T0, T0 + 50]))) == T0 + 50


def test_sessoes_sao_independentes(conv):
    conv.decidir(T0, "s-a")
    assert conv.decidir(T0 + 1900, "s-b") is None, "a marca de s-a valeu pra s-b"


def test_intervalo_zero_avisa_sempre(conv):
    amb = {"MSS_CAPTURA_INTERVALO_S": "0"}
    assert conv.decidir(T0, ambiente=amb) and conv.decidir(T0 + 1, ambiente=amb)
    assert conv.anotacoes == [("lembrou", "intervalo=0")] * 2


def test_throttle_puro_continua(mod):
    assert mod.deve_cutucar(ultimo_ts=1000.0, agora=1060.0, intervalo_s=1800) is False
    assert mod.deve_cutucar(ultimo_ts=1000.0, agora=4600.0, intervalo_s=1800) is True
    assert mod.deve_cutucar(ultimo_ts=None, agora=1000.0, intervalo_s=1800) is True


# --- AC2: escape, falha aberta, só Stop ----------------------------------------------------

def test_escape_do_owner(conv):
    assert conv.decidir(T0, ambiente={"MSS_CAPTURA_INTERVALO_S": "0", "MSS_CAPTURA_NUDGE_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "x", {}, {"hook_event_name": "PreToolUse"}])
def test_entrada_malformada_cala(conv, ruim):
    assert conv.decidir(T0, ambiente={"MSS_CAPTURA_INTERVALO_S": "0"}, evento=ruim) is None


def test_transcript_ilegivel_conta_como_sem_captura(conv):
    conv.decidir(T0, transcript="não é json\n")
    assert conv.decidir(T0 + 1900, transcript='{"type": "assistant", "message": {"content": [{"type"\n')


def test_intervalo_invalido_usa_o_padrao(conv):
    a = {"MSS_CAPTURA_INTERVALO_S": "trinta"}
    conv.decidir(T0, ambiente=a)
    assert conv.decidir(T0 + 600, ambiente=a) is None
    assert conv.decidir(T0 + 1900, ambiente=a)


def test_saida_avisa_o_owner_e_nunca_bloqueia(mod):
    saida = json.loads(mod.saida("rode /mss-spec:memory capturar"))
    assert saida == {"systemMessage": "rode /mss-spec:memory capturar"}
    assert "decision" not in saida, "o lembrete não bloqueia — a cobrança dura é do diario_junto"
    assert mod.saida(None) is None


# --- o disco de verdade e o processo (pasta montada uma vez) ------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("capturar_nudge")
    transcript = base / "t.jsonl"
    transcript.write_text(_transcript([T0 + 1500]), encoding="utf-8")
    return base, transcript


def test_casca_le_o_transcript_e_grava_a_marca(mod, pasta):
    base, transcript = pasta
    amb = {"TEMP": str(base), "TMP": str(base), "TMPDIR": str(base)}
    ev = {"hook_event_name": "Stop", "cwd": "C:\\proj", "session_id": "disco", "stop_hook_active": False,
          "transcript_path": str(transcript)}
    sem_captura = dict(ev, transcript_path=str(base / "nao-existe.jsonl"))
    assert mod.decidir(sem_captura, amb, agora=T0) is None
    assert (base / "mss_captura_disco.json").is_file(), "a marca do 1º Stop não foi gravada"
    assert mod.decidir(ev, amb, agora=T0 + 1900) is None, "a captura do transcript do disco não foi lida"
    assert mod.decidir(sem_captura, amb, agora=T0 + 3400), "a marca rearmada não foi lida do disco"


def test_processo_avisa_o_owner_e_nunca_bloqueia(pasta):
    base, transcript = pasta
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(base), "TMP": str(base), "TMPDIR": str(base), "MSS_CAPTURA_INTERVALO_S": "0"})
    ev = {"hook_event_name": "Stop", "cwd": "C:\\proj", "session_id": "proc", "stop_hook_active": False,
          "transcript_path": str(transcript)}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=amb, timeout=30)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert "/mss-spec:memory capturar" in saida["systemMessage"] and "decision" not in saida


# --- fiação, documentação ------------------------------------------------------------------

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
