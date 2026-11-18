"""Diário junto da memória — memória gravada sem `memory/sessions/` não sai (caso F-048).

A conversa da tarde de 2026-10-30 no Whats gravou `docs/EVALS.md` (F-093, F-094) e duas specs e encerrou sem
diário: o problema que ficou aberto (resposta do especialista que não volta pro WhatsApp em produção) não
ficou escrito em lugar nenhum. O owner: "o diário tem que ser junto com a memória, assim que gravar ela".

Propriedades:
- `Stop`: gravou `memory/<x>.md` (fora topo/índice), `docs/EVALS.md` ou `docs/decisoes.md` e nenhum
  `memory/sessions/<x>.md` → devolve a resposta pelo contrato do Stop (JSON `block`, exit 0);
- cobra uma vez por arquivo de memória; memória nova depois da cobrança cobra de novo; diário gravado → passa;
- `stop_hook_active` → passa (nunca laço); subagente não conta; falha ABERTA; escape `MSS_DIARIO_JUNTO_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o texto do transcript entra como dado (lido pela
`_transcricao.gravacoes_do_texto`) e as memórias já cobradas de cada conversa ficam num dicionário. O disco de
verdade (ler o transcript, gravar e ler as cobradas) fica num teste só, numa pasta montada uma vez; o processo
python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "diario_junto.py"
PROJ = "C:\\Ronaldo\\_Mitsui\\Python\\IA Bot Agent\\IA Bot Agent - Whats"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("diario_junto", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _transcript(caminhos, sidechain=()):
    """O texto de um transcript com um Write por caminho (e os de `sidechain` marcados como subagente)."""
    linhas = [json.dumps({"type": "user", "message": {"content": "oi"}})]
    for c in caminhos:
        linhas.append(json.dumps({"type": "assistant", "timestamp": "2026-10-30T18:00:00.000Z", "message": {
            "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": c, "content": "x"}}]}}))
    for c in sidechain:
        linhas.append(json.dumps({"type": "assistant", "isSidechain": True, "message": {
            "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": c}}]}}))
    return "\n".join(linhas) + "\n"


class Conversas:
    """As memórias já cobradas de cada conversa, em memória. `decidir` chama a regra com o texto do transcript como
    dado e guarda o que ela manda marcar — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.cobradas, self.anotacoes = mod, {}, []
        self.tr = sys.modules["_transcricao"]

    def decidir(self, transcript, sessao="s1", ativo=False, ambiente=None, evento=None):
        ev = evento if evento is not None else {"hook_event_name": "Stop", "cwd": PROJ, "session_id": sessao,
                                                "stop_hook_active": ativo, "transcript_path": "t.jsonl"}
        motivo, mudancas = self.mod.regra(ev, ambiente or {}, lambda: self.tr.gravacoes_do_texto(transcript),
                                          lambda s: set(self.cobradas.get(s, set())))
        if "marcar" in mudancas:
            self.cobradas.setdefault(sessao, set()).update(mudancas["marcar"])
        self.anotacoes += mudancas["anotacoes"]
        return motivo


@pytest.fixture()
def conv(mod):
    return Conversas(mod)


# --- AC1: a conversa real — EVALS e specs gravadas, diário nenhum ------------------------------

def test_evals_sem_diario_devolve(conv):
    motivo = conv.decidir(_transcript([PROJ + "\\docs\\EVALS.md", PROJ + "\\docs\\specs\\financeiro-no-whatsapp.md"]))
    assert motivo and "memory/sessions/" in motivo and "docs/EVALS.md" in motivo
    assert "/mss-spec:memory capturar" in motivo and "DIARIO.md" in motivo


@pytest.mark.parametrize("caminho", [
    PROJ + "\\memory\\token-do-whatsapp-sem-gate.md",
    "memory/token-do-whatsapp-sem-gate.md",
    PROJ + "/docs/decisoes.md",
    "docs/EVALS.md",
])
def test_memoria_decisao_e_evals_contam(conv, caminho):
    assert conv.decidir(_transcript([caminho]))


@pytest.mark.parametrize("caminho", [
    PROJ + "\\memory\\MEMORY.md",
    PROJ + "\\memory\\DIARIO.md",
    PROJ + "\\memory\\indice\\integracoes.md",
    PROJ + "\\docs\\specs\\handoff-chatwoot.md",
    PROJ + "\\chat_server.py",
    PROJ + "\\memory\\rascunho.txt",
])
def test_topo_indice_spec_e_codigo_nao_contam(conv, caminho):
    assert conv.decidir(_transcript([caminho])) is None


# --- AC2: com o diário, passa; cobra uma vez por memória ------------------------------------

def test_com_diario_passa(conv):
    t = _transcript([PROJ + "\\docs\\EVALS.md", PROJ + "\\memory\\sessions\\2026-10-30-token-whatsapp.md"])
    assert conv.decidir(t) is None


def test_cobra_uma_vez_e_de_novo_so_com_memoria_nova(conv):
    t1 = _transcript([PROJ + "\\docs\\EVALS.md"])
    assert conv.decidir(t1)
    assert conv.decidir(t1) is None, "cobrou duas vezes a mesma memória"
    motivo = conv.decidir(_transcript([PROJ + "\\docs\\EVALS.md", PROJ + "\\memory\\nova-memoria.md"]))
    assert motivo and "nova-memoria.md" in motivo and "EVALS.md" not in motivo.split("—")[1]


def test_sessoes_sao_independentes(conv):
    t = _transcript([PROJ + "\\docs\\EVALS.md"])
    assert conv.decidir(t, "s-a")
    assert conv.decidir(t, "s-b"), "a cobrança de s-a valeu pra s-b"


# --- AC3: nunca laço, subagente, escape, falha aberta --------------------------------------

def test_stop_hook_active_passa(conv):
    assert conv.decidir(_transcript([PROJ + "\\docs\\EVALS.md"]), ativo=True) is None


def test_gravacao_de_subagente_nao_conta(conv):
    assert conv.decidir(_transcript([], sidechain=[PROJ + "\\docs\\EVALS.md"])) is None


def test_escape_do_owner(conv):
    assert conv.decidir(_transcript([PROJ + "\\docs\\EVALS.md"]), ambiente={"MSS_DIARIO_JUNTO_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "x", {}, {"hook_event_name": "PreToolUse"}])
def test_entrada_malformada_libera(conv, ruim):
    assert conv.decidir(_transcript([PROJ + "\\docs\\EVALS.md"]), evento=ruim) is None


def test_transcript_ilegivel_libera(conv):
    assert conv.decidir('{"type": "assistant", "message": {"content": [{"type": "tool_use"\nnão é json\n') is None
    assert conv.decidir("") is None


def test_registro_guarda_a_devolucao_sem_o_texto(conv):
    conv.decidir(_transcript([PROJ + "\\docs\\EVALS.md"]))
    assert conv.anotacoes == [("devolveu", "memoria_sem_diario=1")]


def test_saida_pelo_contrato_do_stop(mod):
    assert json.loads(mod.saida("grave o diário")) == {"decision": "block", "reason": "grave o diário"}
    assert mod.saida(None) is None


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("diario_junto")
    transcript = base / "t.jsonl"
    transcript.write_text(_transcript([PROJ + "\\docs\\EVALS.md"]), encoding="utf-8")
    return base, transcript


def test_casca_le_o_transcript_e_grava_as_cobradas(mod, pasta):
    base, transcript = pasta
    amb = {"TEMP": str(base), "TMP": str(base), "TMPDIR": str(base)}
    ev = {"hook_event_name": "Stop", "cwd": PROJ, "session_id": "disco", "stop_hook_active": False,
          "transcript_path": str(transcript)}
    assert mod.decidir(ev, amb), "o transcript do disco não foi lido"
    assert mod.decidir(ev, amb) is None, "a cobrança gravada no disco não foi lida"
    assert mod.decidir(dict(ev, session_id="outra", transcript_path=str(base / "nao-existe.jsonl")), amb) is None


def test_processo_devolve_pelo_contrato_do_stop(pasta):
    base, transcript = pasta
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(base), "TMP": str(base), "TMPDIR": str(base)})
    ev = {"hook_event_name": "Stop", "cwd": PROJ, "session_id": "proc", "stop_hook_active": False,
          "transcript_path": str(transcript)}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=amb, timeout=30)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["decision"] == "block" and "memory/sessions/" in saida["reason"]


# --- fiação -----------------------------------------------------------------------------------

def test_hook_registrado_no_stop():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert any("diario_junto.py" in h["command"] for g in cfg["hooks"].get("Stop", []) for h in g["hooks"])


def test_documentado_no_readme():
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "diario_junto.py" in doc and "memory/sessions/" in doc
