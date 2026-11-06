"""Decisão junto da mudança de comportamento — mudou como o assistente age sem registrar por quê, a resposta volta.

Benchmark MSIG_Agentes (2026-11-06), item 3: lá toda alteração de comportamento (regra global, persona, hook,
roteador) gera decisão no mesmo fechamento, e o sync avisa quando publica um desses arquivos sem decisão do
dia — "daqui a dois meses ninguém sabe por que o kit age assim". Aqui `docs/decisoes.md` existia e o
`capturar_nudge.py` cobrava por tempo; nada cobrava a decisão quando a gravação é num arquivo de comportamento.

Propriedades:
- `Stop`: gravou comportamento (`CLAUDE.md` da raiz, `.claude/rules/*.md`, `.claude/settings.json`,
  `.claude/hooks/*`; no kit `hooks/*.py`, `commands/*.md`, `templates/regras-do-kit/*`, `templates/rules/*.md`)
  e nenhuma decisão (`docs/decisoes.md`, `docs/specs/*.md`, `docs/superpowers/specs/*.md`) → devolve (JSON
  `block`, exit 0);
- cobra uma vez por arquivo; arquivo novo depois da cobrança cobra de novo; decisão gravada → passa;
- teste, README e módulo `_x.py` não contam; `stop_hook_active` → passa; subagente não conta; falha ABERTA;
  escape `MSS_DECISAO_JUNTO_OFF=1`.
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
HOOK = REPO / "hooks" / "decisao_junto.py"
PROJ = "C:\\Ronaldo\\_Mitsui\\Python\\IA Bot Agent\\IA Bot Agent - Whats"
KIT = "C:\\Ronaldo\\_Mitsui\\Python\\Spec-Powers"


def _mod():
    spec = importlib.util.spec_from_file_location("decisao_junto", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def amb(tmp_path):
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)}


def _transcript(tmp_path, caminhos, sidechain=()):
    linhas = [json.dumps({"type": "user", "message": {"content": "oi"}})]
    for c in caminhos:
        linhas.append(json.dumps({"type": "assistant", "timestamp": "2026-11-06T18:00:00.000Z", "message": {
            "content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": c, "old_string": "a", "new_string": "b"}}]}}))
    for c in sidechain:
        linhas.append(json.dumps({"type": "assistant", "isSidechain": True, "message": {
            "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": c}}]}}))
    t = tmp_path / f"t-{uuid.uuid4().hex[:6]}.jsonl"
    t.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return str(t)


def _ev(transcript, sessao=None, ativo=False):
    return {"hook_event_name": "Stop", "cwd": KIT, "session_id": sessao or "s-" + uuid.uuid4().hex[:8],
            "stop_hook_active": ativo, "transcript_path": transcript}


# --- AC1: comportamento sem decisão devolve; o que conta e o que não conta ------------------------

def test_hook_do_kit_sem_decisao_devolve(amb, tmp_path):
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py", KIT + "\\commands\\bug.md"])
    motivo = _mod().decidir(_ev(t), amb)
    assert motivo and "docs/decisoes.md" in motivo and "hooks/git_publicacao.py" in motivo and "commands/bug.md" in motivo
    assert "decidimos <X> em vez de <Y>" in motivo and "MSS_DECISAO_JUNTO_OFF" in motivo


@pytest.mark.parametrize("caminho", [
    PROJ + "\\CLAUDE.md",
    PROJ + "\\.claude\\rules\\banco-e-segredo.md",
    PROJ + "\\.claude\\settings.json",
    PROJ + "\\.claude\\hooks\\meu_hook.py",
    KIT + "\\templates\\regras-do-kit\\2-regras-criticas.md",
    KIT + "\\templates\\rules\\frontend.md",
    "hooks/regras_do_kit.py",
    "commands/tarefa.md",
])
def test_arquivos_de_comportamento_contam(amb, tmp_path, caminho):
    assert _mod().decidir(_ev(_transcript(tmp_path, [caminho])), amb)


@pytest.mark.parametrize("caminho", [
    PROJ + "\\app\\main.py",
    PROJ + "\\memory\\nova-memoria.md",
    PROJ + "\\docs\\ARQUITETURA.md",
    KIT + "\\tests\\test_hook_decisao_junto.py",
    KIT + "\\hooks\\README.md",
    KIT + "\\hooks\\_registro.py",
    KIT + "\\templates\\CLAUDE.md",
    PROJ + "\\.claude\\settings.local.json",
])
def test_codigo_memoria_teste_readme_e_molde_nao_contam(amb, tmp_path, caminho):
    assert _mod().decidir(_ev(_transcript(tmp_path, [caminho])), amb) is None


# --- AC2: com a decisão, passa (decisoes.md ou Histórico da spec); cobra uma vez --------------------

@pytest.mark.parametrize("decisao", [
    KIT + "\\docs\\decisoes.md",
    KIT + "\\docs\\specs\\regras-do-kit-pelo-plugin.md",
    KIT + "\\docs\\superpowers\\specs\\2026-11-06-x-design.md",
    "docs/decisoes.md",
])
def test_com_decisao_passa(amb, tmp_path, decisao):
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py", decisao])
    assert _mod().decidir(_ev(t), amb) is None


def test_cobra_uma_vez_e_de_novo_so_com_arquivo_novo(amb, tmp_path):
    mod, s = _mod(), "s-" + uuid.uuid4().hex[:8]
    t1 = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py"])
    assert mod.decidir(_ev(t1, s), amb)
    assert mod.decidir(_ev(t1, s), amb) is None, "cobrou duas vezes o mesmo arquivo"
    t2 = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py", KIT + "\\commands\\bug.md"])
    motivo = mod.decidir(_ev(t2, s), amb)
    assert motivo and "commands/bug.md" in motivo and "git_publicacao" not in motivo.split("—")[1]


def test_sessoes_sao_independentes(amb, tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py"])
    assert mod.decidir(_ev(t, "s-a"), amb)
    assert mod.decidir(_ev(t, "s-b"), amb), "a cobrança de s-a valeu pra s-b"


# --- AC3: nunca laço, subagente, escape, falha aberta ----------------------------------------------

def test_stop_hook_active_passa(amb, tmp_path):
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py"])
    assert _mod().decidir(_ev(t, ativo=True), amb) is None


def test_gravacao_de_subagente_nao_conta(amb, tmp_path):
    t = _transcript(tmp_path, [], sidechain=[KIT + "\\hooks\\git_publicacao.py"])
    assert _mod().decidir(_ev(t), amb) is None


def test_escape_do_owner(amb, tmp_path):
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py"])
    assert _mod().decidir(_ev(t), {**amb, "MSS_DECISAO_JUNTO_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "x", {}, {"hook_event_name": "PreToolUse"},
                                  {"hook_event_name": "Stop", "transcript_path": "C:/nao/existe.jsonl"},
                                  {"hook_event_name": "Stop", "transcript_path": 7}])
def test_entrada_malformada_libera(amb, ruim):
    assert _mod().decidir(ruim, amb) is None


# --- AC4: processo, registro e fiação -------------------------------------------------------------

def _rodar(ev, tmp_path, extra=None):
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path), **(extra or {})})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=amb, timeout=30)


def test_processo_devolve_por_json_com_exit_0(tmp_path):
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py"])
    r = _rodar(_ev(t), tmp_path)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["decision"] == "block" and "docs/decisoes.md" in saida["reason"]


def test_processo_libera_calado_com_decisao(tmp_path):
    t = _transcript(tmp_path, [KIT + "\\hooks\\git_publicacao.py", KIT + "\\docs\\decisoes.md"])
    r = _rodar(_ev(t), tmp_path)
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_processo_entrada_vazia_libera(tmp_path):
    r = subprocess.run([sys.executable, str(HOOK)], input="", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_fiacao_no_hooks_json_e_no_readme():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    stops = [h["command"] for grupo in cfg["hooks"]["Stop"] for h in grupo["hooks"]]
    assert any("decisao_junto.py" in c for c in stops), "decisao_junto.py não está no Stop do hooks.json"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "`decisao_junto.py` | `Stop`" in readme, "hooks/README.md sem a linha do decisao_junto na tabela"
    assert "MSS_DECISAO_JUNTO_OFF" in readme
