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
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "teto_ao_gravar.py"
LONGO = "detalhe " * 120
MARCA = "<!-- mss-spec:regras-do-kit -->"


@pytest.fixture(autouse=True)
def _estado_no_tmp(tmp_path, monkeypatch):
    """O estado por sessão do hook (temp do SO) fica isolado em cada teste."""
    pasta = tmp_path / "temp-do-so"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(pasta))


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


def _shell(raiz, comando, tool="Bash"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(raiz), "session_id": "s1",
            "tool_input": {"command": comando}}


def _envelhecer(caminho, segundos=3600):
    t = time.time() - segundos
    os.utime(caminho, (t, t))


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


def test_dentro_do_teto_fechada_sai_e_avisa_sem_falar_em_teto(tmp_path):
    """0.44.0: a forma vale em toda gravação — `fechada` sai do INDEX mesmo com o arquivo pequeno."""
    raiz = _projeto(tmp_path, index="# Índice\n\n## Em andamento\n- [a](../specs/a.md) — x — aberta\n"
                                     "- [b](../specs/b.md) — y — fechada: no ar\n")
    saida = _mod().responder(_edit(raiz), {})
    sp = raiz / "docs" / "superpowers"
    assert "[b]" not in (sp / "INDEX.md").read_text(encoding="utf-8")
    assert "[b]" in (sp / "INDEX-historico.md").read_text(encoding="utf-8")
    txt = _ctx(saida)
    assert "INDEX-historico.md" in txt and "releia" in txt.lower()
    assert "teto" not in txt.lower(), "abaixo do teto, o aviso não pode dizer que estourou"


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


def test_claude_md_com_marca_teto_10000_so_avisa(tmp_path):
    claude = "# Proj\n\n" + MARCA + "\n\n" + ("- **Regra**: " + LONGO + "\n") * 14
    raiz = _projeto(tmp_path, claude=claude)
    txt = _ctx(_mod().responder(_edit(raiz, rel="CLAUDE.md"), {}))
    assert "CLAUDE.md" in txt and ".claude/rules/" in txt and "nunca comprima" in txt.lower()
    assert "/mss-spec:upgrade" not in txt, "projeto já migrado não precisa de upgrade"
    assert (raiz / "CLAUDE.md").read_text(encoding="utf-8") == claude, "mexeu no CLAUDE.md sozinho"


def test_claude_md_sem_marca_acima_do_teto_manda_upgrade(tmp_path):
    claude = "# Proj\n\n" + ("- **Regra**: " + LONGO + "\n") * 14
    raiz = _projeto(tmp_path, claude=claude)
    txt = _ctx(_mod().responder(_edit(raiz, rel="CLAUDE.md"), {}))
    assert "/mss-spec:upgrade" in txt
    assert ".claude/rules/" not in txt, "mandou mover bloco num projeto que ainda não migrou"
    assert (raiz / "CLAUDE.md").read_text(encoding="utf-8") == claude, "mexeu no CLAUDE.md sozinho"


def test_kb_com_uma_casa(tmp_path):
    claude = MARCA + "\n" + "x" * (10500 - len(MARCA) - 1)
    raiz = _projeto(tmp_path, claude=claude)
    txt = _ctx(_mod().responder(_edit(raiz, rel="CLAUDE.md"), {}))
    assert "10,5 KB" in txt and "teto 10,0 KB" in txt


def test_kb_perto_do_teto_mostra_bytes(tmp_path):
    """10.020 B arredondaria pra '10,0 KB (teto 10,0 KB)': mostra bytes quando o arredondado empata."""
    claude = MARCA + "\n" + "x" * (10020 - len(MARCA) - 1)
    raiz = _projeto(tmp_path, claude=claude)
    txt = _ctx(_mod().responder(_edit(raiz, rel="CLAUDE.md"), {}))
    assert re.search(r"10\.0[2-4]\d B \(teto 10\.000 B\)", txt) and "10,0 KB" not in txt   # write_text no Windows põe CR


def test_claude_md_em_cp1252_com_marca_nao_manda_upgrade(tmp_path):
    raiz = _projeto(tmp_path)
    (raiz / "CLAUDE.md").write_bytes((MARCA + "\nSão Paulo\n" + "x" * 10500).encode("cp1252"))
    txt = _ctx(_mod().responder(_edit(raiz, rel="CLAUDE.md"), {}))
    assert ".claude/rules/" in txt and "/mss-spec:upgrade" not in txt


def test_git_add_e_commit_do_claude_md_nao_contam_como_gravacao(tmp_path):
    raiz = _projeto(tmp_path, claude=MARCA + "\n" + "x" * 10500)        # mtime recente, versão nunca vista
    mod = _mod()
    assert mod.responder(_shell(raiz, "git add CLAUDE.md"), {}) is None
    assert mod.responder(_shell(raiz, 'git commit -m "x" CLAUDE.md', "PowerShell"), {}) is None
    assert mod.responder(_shell(raiz, "  git diff CLAUDE.md"), {}) is None
    assert mod.responder(_shell(raiz, "echo x >> CLAUDE.md"), {}) is not None   # gravação de verdade segue valendo


# --- leitura pelo shell não é gravação -------------------------------------------------------

def test_wc_c_em_claude_md_antigo_nao_dispara(tmp_path):
    raiz = _projeto(tmp_path, claude=MARCA + "\n" + "x" * 10500)
    _envelhecer(raiz / "CLAUDE.md")
    assert _mod().responder(_shell(raiz, "wc -c CLAUDE.md"), {}) is None


def test_cat_do_index_antigo_nao_roda_enxugar(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    idx = raiz / "docs" / "superpowers" / "INDEX.md"
    _envelhecer(idx)
    antes = idx.read_text(encoding="utf-8")
    assert _mod().responder(_shell(raiz, "cat docs/superpowers/INDEX.md"), {}) is None
    assert idx.read_text(encoding="utf-8") == antes
    assert not (raiz / "docs" / "superpowers" / "BACKLOG.md").exists()


def test_gravacao_por_shell_recente_dispara(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    saida = _mod().responder(_shell(raiz, "Set-Content docs/superpowers/INDEX.md -Value x", "PowerShell"), {})
    assert saida is not None and "BACKLOG.md" in _ctx(saida)
    idx = raiz / "docs" / "superpowers" / "INDEX.md"
    assert len(idx.read_bytes()) <= 7000


def test_mesma_versao_nao_dispara_duas_vezes(tmp_path):
    raiz = _projeto(tmp_path, index=_index_gordo())
    mod = _mod()
    assert mod.responder(_edit(raiz), {}) is not None
    assert mod.responder(_shell(raiz, "wc -c docs/superpowers/INDEX.md"), {}) is None


def test_mesma_versao_do_claude_md_nao_avisa_duas_vezes(tmp_path):
    raiz = _projeto(tmp_path, claude=MARCA + "\n" + "x" * 10500)
    mod = _mod()
    assert mod.responder(_edit(raiz, rel="CLAUDE.md"), {}) is not None
    assert mod.responder(_shell(raiz, "wc -c CLAUDE.md"), {}) is None


def test_nova_gravacao_depois_da_leitura_dispara_de_novo(tmp_path):
    raiz = _projeto(tmp_path, claude=MARCA + "\n" + "x" * 10500)
    mod = _mod()
    assert mod.responder(_edit(raiz, rel="CLAUDE.md"), {}) is not None
    (raiz / "CLAUDE.md").write_text(MARCA + "\n" + "y" * 10800, encoding="utf-8")
    assert mod.responder(_shell(raiz, "echo y >> CLAUDE.md"), {}) is not None


def test_mudou_agora_janela_e_estado(tmp_path):
    mod = _mod()
    assert mod.JANELA_S == 120
    arq = tmp_path / "a.md"
    arq.write_text("x", encoding="utf-8")
    agora = time.time()
    assert mod.mudou_agora(str(arq), "s1", agora) is True
    assert mod.mudou_agora(str(arq), "s1", agora + 3600) is False       # fora da janela
    assert mod.mudou_agora(str(tmp_path / "nao-existe.md"), "s1", agora) is False


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
