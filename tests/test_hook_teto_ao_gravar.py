"""Teto ao gravar — depois de gravar MAPA/INDEX, o excesso sai na hora (move, nunca apaga).

Caso F-030: o `doctor` media o orçamento e o hook de abertura avisava, mas quem MOVIA era gente — e o Whats
chegou a 160 KB de partida. Hook `PostToolUse` roda o `rodizio_partida.enxugar` quando a gravação deixou o
arquivo acima do teto e conta o que foi pra onde. `CLAUDE.md` acima de 10 KB: só avisa (escolher o destino de
um bloco de regra é julgamento — F-029).

Propriedades:
- só age em gravação de `docs/superpowers/MAPA.md`, `docs/superpowers/INDEX.md` ou `CLAUDE.md` do projeto
  (Write/Edit/MultiEdit pelo caminho; Bash/PowerShell quando o comando cita o arquivo);
- dentro do teto → silêncio; acima → move e avisa; conteúdo vivo que não cabe → pede o resumo;
- nunca bloqueia; falha ABERTA; escape `MSS_TETO_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "teto_ao_gravar.py"
LONGO = "detalhe " * 120


def _mod():
    spec = importlib.util.spec_from_file_location("teto_ao_gravar", HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _index_gordo():
    return ("# Índice de tarefas\n\n## Em andamento\n\n- [a](../specs/a.md) — curta — aberta\n\n## Backlog\n\n"
            + "".join(f"- ideia-{i} — {LONGO} — aberta\n" for i in range(12)))


def _projeto(tmp_path, index=None, mapa=None, claude=None):
    raiz = tmp_path / "proj"
    sp = raiz / "docs" / "superpowers"
    sp.mkdir(parents=True)
    if index is not None:
        (sp / "INDEX.md").write_text(index, encoding="utf-8")
    if mapa is not None:
        (sp / "MAPA.md").write_text(mapa, encoding="utf-8")
    if claude is not None:
        (raiz / "CLAUDE.md").write_text(claude, encoding="utf-8")
    return raiz


def _edit(raiz, rel="docs/superpowers/INDEX.md", tool="Edit"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(raiz), "session_id": "s1",
            "tool_input": {"file_path": str(raiz / rel)}}


def _ctx(saida):
    return saida["hookSpecificOutput"]["additionalContext"]


# --- AC1: move na hora ------------------------------------------------------------------------

def test_index_acima_do_teto_e_enxugado_na_hora(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    saida = _mod().responder(_edit(raiz), {})
    idx = (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8")
    assert len(idx.encode()) <= 7000, "o hook não moveu o excesso"
    assert "ideia-11" in (raiz / "docs" / "superpowers" / "BACKLOG.md").read_text(encoding="utf-8")
    txt = _ctx(saida)
    assert "BACKLOG.md" in txt and "nada foi apagado" in txt.lower()
    assert "releia" in txt.lower(), "não avisou pra reler antes do próximo Edit (o texto mudou de lugar)"
    assert saida["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_dentro_do_teto_fica_calado(tmp_path):
    raiz = _projeto(tmp_path, index="# Índice\n\n## Em andamento\n- [a](../specs/a.md) — x — aberta\n")
    assert _mod().responder(_edit(raiz), {}) is None


def test_gravacao_de_outro_arquivo_nao_dispara(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    antes = (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8")
    assert _mod().responder(_edit(raiz, rel="src/app.py"), {}) is None
    assert (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8") == antes


def test_bash_que_cita_o_index_dispara(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    ev = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "cwd": str(raiz), "session_id": "s1",
          "tool_input": {"command": "cat >> docs/superpowers/INDEX.md <<'EOF'\n- x\nEOF"}}
    assert _mod().responder(ev, {}) is not None


def test_bash_que_nao_cita_nao_dispara(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    ev = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "cwd": str(raiz), "session_id": "s1",
          "tool_input": {"command": "git status"}}
    assert _mod().responder(ev, {}) is None


def test_mapa_com_bloco_atual_gigante_pede_o_resumo(tmp_path):
    mapa = "# Mapa\n\n## Onde estamos\n\n" + ("📍 " + LONGO + "\n") * 12 + "\n## Próximo passo\n\n1. x\n"
    raiz = _projeto(tmp_path, mapa=mapa)
    txt = _ctx(_mod().responder(_edit(raiz, rel="docs/superpowers/MAPA.md", tool="Write"), {}))
    assert "resuma" in txt.lower() and "spec" in txt.lower()


def test_claude_md_acima_do_teto_so_avisa(tmp_path):
    claude = "# Proj\n\n" + ("- **Regra**: " + LONGO + "\n") * 14
    raiz = _projeto(tmp_path, claude=claude)
    txt = _ctx(_mod().responder(_edit(raiz, rel="CLAUDE.md"), {}))
    assert "CLAUDE.md" in txt and ".claude/rules/" in txt and "nunca comprima" in txt.lower()
    assert (raiz / "CLAUDE.md").read_text(encoding="utf-8") == claude, "mexeu no CLAUDE.md sozinho"


# --- AC2: escape, falha aberta, conflito ------------------------------------------------------

def test_escape_do_owner(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    assert _mod().responder(_edit(raiz), {"MSS_TETO_OFF": "1"}) is None


def test_entrada_malformada_libera():
    mod = _mod()
    for ruim in (None, [], "x", {}, {"tool_name": "Edit"}, {"tool_name": "Edit", "tool_input": "x", "cwd": "."}):
        assert mod.responder(ruim, {}) is None


def test_conflito_de_merge_nao_e_tocado(tmp_path):
    raiz = _projeto(tmp_path, index="<<<<<<< HEAD\n" + _index_gordo() + ">>>>>>> x\n")
    antes = (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8")
    saida = _mod().responder(_edit(raiz), {})
    assert (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8") == antes
    assert saida is not None and "conflito" in _ctx(saida).lower()


# --- AC3: processo e registro no plugin -------------------------------------------------------

def test_processo_sai_zero_com_json(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_TETO_OFF", "CLAUDE_PROJECT_DIR")}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_edit(raiz)), capture_output=True,
                       text=True, encoding="utf-8", env=amb, timeout=60)
    assert r.returncode == 0 and "BACKLOG.md" in _ctx(json.loads(r.stdout))


def test_hook_registrado_no_post_tool_use():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    grupos = cfg["hooks"].get("PostToolUse", [])
    assert any("teto_ao_gravar.py" in h["command"] for g in grupos for h in g["hooks"])
