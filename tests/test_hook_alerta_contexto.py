"""Alerta de contexto — avisa quando a janela passa de 75% (bola de neve de assuntos).

A janela aberta pra UM assunto vira bola de neve ("pra fechar A preciso entender B") e o contexto
enche sem ninguém ver. Hook `UserPromptSubmit` + `PostToolUse` lê o `usage` da última resposta do
assistente no transcript e, no limiar, injeta o aviso (o assistente repassa ao owner) e mostra
`systemMessage` no terminal.

Propriedades:
- abaixo do limiar → silêncio; no limiar → avisa; uma vez por faixa (75 · 85 · 95) por sessão;
- caiu abaixo do limiar (compactou) → rearma;
- conta input + cache_read + cache_creation da ÚLTIMA mensagem do assistente fora de subagente;
- janela: `MSS_JANELA_TOKENS` › `[1m]` no modelo › uso acima de 200 mil → 1M › 200 mil;
- limiar configurável (`MSS_ALERTA_CONTEXTO_PCT`); evento de subagente ignorado;
- nunca bloqueia; falha ABERTA; escape `MSS_ALERTA_CONTEXTO_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "alerta_contexto.py"


def _mod():
    spec = importlib.util.spec_from_file_location("alerta_contexto", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _temp_isolado(tmp_path, monkeypatch):
    """O estado de 'já avisei nesta faixa' vive no temp do SO — cada teste com o seu."""
    pasta = tmp_path / "temp"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))
    return pasta


def _assistente(tokens, modelo="claude-opus-4-6", sidechain=False):
    return {"type": "assistant", "isSidechain": sidechain,
            "message": {"model": modelo, "usage": {
                "input_tokens": 2, "cache_read_input_tokens": tokens - 1002,
                "cache_creation_input_tokens": 1000, "output_tokens": 500}}}


def _transcript(tmp_path, *entradas, nome="sessao.jsonl"):
    p = tmp_path / nome
    linhas = [json.dumps(e) for e in entradas]
    p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return p


def _evento(transcript, evento="UserPromptSubmit", sessao="s1", **extra):
    e = {"hook_event_name": evento, "session_id": sessao, "transcript_path": str(transcript),
         "cwd": str(transcript.parent), "prompt": "segue"}
    e.update(extra)
    return e


# --- leitura do uso -------------------------------------------------------------------

def test_uso_soma_input_e_caches_da_ultima_resposta(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(40_000), {"type": "user"}, _assistente(120_000))
    assert mod.uso_atual(str(t)) == (120_000, "claude-opus-4-6")


def test_uso_ignora_subagente_e_linha_quebrada(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(90_000), _assistente(190_000, sidechain=True))
    with open(t, "a", encoding="utf-8") as f:
        f.write("{isto não é json\n")
    assert mod.uso_atual(str(t))[0] == 90_000


def test_uso_le_so_a_cauda_de_transcript_grande(tmp_path):
    """Transcript de sessão longa passa de MB: a leitura é só da cauda, e acha a última resposta."""
    mod = _mod()
    lixo = {"type": "user", "message": {"content": "x" * 5000}}
    t = _transcript(tmp_path, *([_assistente(10_000)] + [lixo] * 400 + [_assistente(155_000)]))
    assert t.stat().st_size > mod.CAUDA_BYTES
    assert mod.uso_atual(str(t))[0] == 155_000


def test_sem_resposta_do_assistente_e_silencio(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, {"type": "user"}, {"type": "system"})
    assert mod.responder(_evento(t), {}) is None


# --- janela e faixas -------------------------------------------------------------------

def test_janela_padrao_1m_e_override():
    mod = _mod()
    assert mod.janela_de(100_000, "claude-opus-4-6", {}) == 200_000
    assert mod.janela_de(100_000, "claude-opus-4-6[1m]", {}) == 1_000_000
    assert mod.janela_de(250_000, "claude-opus-4-6", {}) == 1_000_000   # 200k não comporta
    assert mod.janela_de(100_000, "claude-opus-4-6", {"MSS_JANELA_TOKENS": "400000"}) == 400_000
    assert mod.janela_de(100_000, "x", {"MSS_JANELA_TOKENS": "lixo"}) == 200_000


def test_familia_5_tem_janela_de_1m():
    """F-027 — o print do owner: `claude-opus-5-5` mostrava 184,8k / 1M (18%) e o hook calculava 92%
    de 200 mil. O id no transcript vem sem `[1m]`; a família 5 (Opus/Sonnet/Fable) é 1M."""
    mod = _mod()
    for modelo in ("claude-opus-5-5", "claude-sonnet-5", "claude-fable-5-1"):
        assert mod.janela_de(184_800, modelo, {}) == 1_000_000, modelo
    for modelo in ("claude-haiku-4-5-20251001", "claude-opus-4-6", "claude-sonnet-4-5"):
        assert mod.janela_de(100_000, modelo, {}) == 200_000, modelo


def test_print_do_owner_fica_calado(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(184_800, modelo="claude-opus-5-5"))
    assert mod.responder(_evento(t), {}) is None


def test_janela_de_compactacao_do_owner_vence_o_modelo():
    """`CLAUDE_CODE_AUTO_COMPACT_WINDOW` (doc do Claude Code) é onde a compactação mira: o alerta mira ali."""
    mod = _mod()
    amb = {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "500000"}
    assert mod.janela_de(100_000, "claude-opus-5-5", amb) == 500_000
    amb["MSS_JANELA_TOKENS"] = "300000"
    assert mod.janela_de(100_000, "claude-opus-5-5", amb) == 300_000        # o do kit vence


def test_faixas_escalonadas():
    mod = _mod()
    assert mod.faixa_de(74.9, 75) is None
    assert mod.faixa_de(75.0, 75) == 75
    assert mod.faixa_de(84.9, 75) == 75
    assert mod.faixa_de(85.2, 75) == 85
    assert mod.faixa_de(97.0, 75) == 95


# --- o alerta --------------------------------------------------------------------------

def test_abaixo_do_limiar_calado(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(149_000))            # 74,5% de 200 mil
    assert mod.responder(_evento(t), {}) is None


def test_no_limiar_avisa_owner_e_assistente(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(152_000))            # 76%
    saida = mod.responder(_evento(t), {})
    assert saida is not None
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "76%" in ctx and "152 mil de 200 mil" in ctx
    for marca in ("MAPA.md", "/mss-spec:to-dolist adicionar", "/clear", "subagente",
                  "não abra assunto novo", "início da sua próxima mensagem"):
        assert marca in ctx, f"aviso ao assistente sem {marca!r}"
    assert "76%" in saida["systemMessage"] and "/clear" in saida["systemMessage"]


def test_avisa_uma_vez_por_faixa_e_escala(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(152_000))
    assert mod.responder(_evento(t), {}) is not None
    assert mod.responder(_evento(t), {}) is None                               # mesma faixa
    assert mod.responder(_evento(t, evento="PostToolUse"), {}) is None         # o outro evento também
    t = _transcript(tmp_path, _assistente(172_000))                            # 86%
    saida = mod.responder(_evento(t, evento="PostToolUse"), {})
    assert saida is not None and "86%" in saida["systemMessage"]
    assert saida["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_compactou_rearma(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(160_000))
    assert mod.responder(_evento(t), {}) is not None
    t = _transcript(tmp_path, _assistente(30_000))                             # depois do /compact
    assert mod.responder(_evento(t), {}) is None
    t = _transcript(tmp_path, _assistente(151_000))
    assert mod.responder(_evento(t), {}) is not None                           # avisa de novo


def test_sessoes_nao_se_misturam(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(160_000))
    assert mod.responder(_evento(t, sessao="a"), {}) is not None
    assert mod.responder(_evento(t, sessao="b"), {}) is not None


def test_limiar_configuravel(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(125_000))            # 62,5%
    assert mod.responder(_evento(t), {}) is None
    assert mod.responder(_evento(t, sessao="s2"), {"MSS_ALERTA_CONTEXTO_PCT": "60"}) is not None
    assert mod.responder(_evento(t, sessao="s3"), {"MSS_ALERTA_CONTEXTO_PCT": "0"}) is None  # inválido → 75


def test_subagente_evento_desconhecido_e_escape(tmp_path):
    mod = _mod()
    t = _transcript(tmp_path, _assistente(190_000))
    assert mod.responder(_evento(t, agent_id="abc"), {}) is None
    assert mod.responder(_evento(t, evento="Stop"), {}) is None
    assert mod.responder(_evento(t), {"MSS_ALERTA_CONTEXTO_OFF": "1"}) is None


def test_falha_aberta(tmp_path):
    mod = _mod()
    assert mod.responder(None, {}) is None
    assert mod.responder({"hook_event_name": "UserPromptSubmit"}, {}) is None
    assert mod.responder(_evento(tmp_path / "nao-existe.jsonl"), {}) is None


# --- protocolo de processo e registro ---------------------------------------------------

def _rodar(stdin, temp):
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    env.pop("MSS_ALERTA_CONTEXTO_OFF", None)
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True,
                          text=True, encoding="utf-8", env=env, timeout=30)


def test_processo_nunca_bloqueia(tmp_path, _temp_isolado):
    t = _transcript(tmp_path, _assistente(180_000))
    r = _rodar(json.dumps(_evento(t)), _temp_isolado)
    assert r.returncode == 0
    saida = json.loads(r.stdout)
    assert "90%" in saida["systemMessage"]
    r = _rodar("isto não é json", _temp_isolado)
    assert r.returncode == 0 and r.stdout == ""


def test_registrado_nos_dois_eventos():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    for evento in ("UserPromptSubmit", "PostToolUse"):
        cmds = [h["command"] for g in grupos.get(evento, []) for h in g["hooks"]]
        assert any("alerta_contexto.py" in c for c in cmds), f"alerta_contexto fora do {evento}"


def test_documentado():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "alerta_contexto.py" in readme and "MSS_ALERTA_CONTEXTO_OFF" in readme
    assert "MSS_JANELA_TOKENS" in readme and "MSS_ALERTA_CONTEXTO_PCT" in readme
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "75%" in claude and "bola de neve" in claude.lower()
    todo = (REPO / "commands" / "to-dolist.md").read_text(encoding="utf-8")
    assert "bola de neve" in todo.lower() and "trava:" in todo
