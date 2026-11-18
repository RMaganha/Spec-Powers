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

Camadas (2026-11-17): a REGRA (`regra`, `uso_de_linhas`) é testada em memória — as linhas do transcript entram como
texto e a faixa já avisada de cada sessão fica num dicionário. O disco de verdade (a cauda de um transcript grande,
gravar e apagar a faixa) fica num teste só, numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from _texto_kit import texto_do_kit

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "alerta_contexto.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("alerta_contexto", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _assistente(tokens, modelo="claude-opus-4-6", sidechain=False):
    return {"type": "assistant", "isSidechain": sidechain,
            "message": {"model": modelo, "usage": {
                "input_tokens": 2, "cache_read_input_tokens": tokens - 1002,
                "cache_creation_input_tokens": 1000, "output_tokens": 500}}}


def _linhas(*entradas):
    return [json.dumps(e) for e in entradas]


class Sessoes:
    """A faixa já avisada de cada sessão, em memória. `responder` chama a regra com as linhas do transcript como
    dado e guarda a faixa que ela devolve — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.faixas, self.anotacoes = mod, {}, []

    def responder(self, linhas, evento="UserPromptSubmit", sessao="s1", ambiente=None, **extra):
        ev = {"hook_event_name": evento, "session_id": sessao, "transcript_path": "t.jsonl", "prompt": "segue",
              **extra}
        saida, mudancas = self.mod.regra(ev, ambiente or {}, lambda: self.mod.uso_de_linhas(linhas),
                                         lambda: self.faixas.get(sessao))
        if "faixa" in mudancas:
            self.faixas[sessao] = mudancas["faixa"]
        self.anotacoes += mudancas["anotacoes"]
        return saida


@pytest.fixture()
def ses(mod):
    return Sessoes(mod)


# --- leitura do uso -------------------------------------------------------------------

def test_uso_soma_input_e_caches_da_ultima_resposta(mod):
    assert mod.uso_de_linhas(_linhas(_assistente(40_000), {"type": "user"}, _assistente(120_000))) == \
        (120_000, "claude-opus-4-6")


def test_uso_ignora_subagente_e_linha_quebrada(mod):
    linhas = _linhas(_assistente(90_000), _assistente(190_000, sidechain=True)) + ["{isto não é json"]
    assert mod.uso_de_linhas(linhas)[0] == 90_000


def test_sem_resposta_do_assistente_e_silencio(ses):
    assert ses.responder(_linhas({"type": "user"}, {"type": "system"})) is None


# --- janela e faixas -------------------------------------------------------------------

def test_janela_padrao_1m_e_override(mod):
    assert mod.janela_de(100_000, "claude-opus-4-6", {}) == 200_000
    assert mod.janela_de(100_000, "claude-opus-4-6[1m]", {}) == 1_000_000
    assert mod.janela_de(250_000, "claude-opus-4-6", {}) == 1_000_000   # 200k não comporta
    assert mod.janela_de(100_000, "claude-opus-4-6", {"MSS_JANELA_TOKENS": "400000"}) == 400_000
    assert mod.janela_de(100_000, "x", {"MSS_JANELA_TOKENS": "lixo"}) == 200_000


def test_familia_5_tem_janela_de_1m(mod):
    """F-027 — o print do owner: `claude-opus-5-5` mostrava 184,8k / 1M (18%) e o hook calculava 92%
    de 200 mil. O id no transcript vem sem `[1m]`; a família 5 (Opus/Sonnet/Fable) é 1M."""
    for modelo in ("claude-opus-5-5", "claude-sonnet-5", "claude-fable-5-1"):
        assert mod.janela_de(184_800, modelo, {}) == 1_000_000, modelo
    for modelo in ("claude-haiku-4-5-20251001", "claude-opus-4-6", "claude-sonnet-4-5"):
        assert mod.janela_de(100_000, modelo, {}) == 200_000, modelo


def test_print_do_owner_fica_calado(ses):
    assert ses.responder(_linhas(_assistente(184_800, modelo="claude-opus-5-5"))) is None


def test_janela_de_compactacao_do_owner_vence_o_modelo(mod):
    """`CLAUDE_CODE_AUTO_COMPACT_WINDOW` (doc do Claude Code) é onde a compactação mira: o alerta mira ali."""
    amb = {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "500000"}
    assert mod.janela_de(100_000, "claude-opus-5-5", amb) == 500_000
    amb["MSS_JANELA_TOKENS"] = "300000"
    assert mod.janela_de(100_000, "claude-opus-5-5", amb) == 300_000        # o do kit vence


def test_faixas_escalonadas(mod):
    assert mod.faixa_de(74.9, 75) is None
    assert mod.faixa_de(75.0, 75) == 75
    assert mod.faixa_de(84.9, 75) == 75
    assert mod.faixa_de(85.2, 75) == 85
    assert mod.faixa_de(97.0, 75) == 95


# --- o alerta --------------------------------------------------------------------------

def test_abaixo_do_limiar_calado(ses):
    assert ses.responder(_linhas(_assistente(149_000))) is None            # 74,5% de 200 mil


def test_no_limiar_avisa_owner_e_assistente(ses):
    saida = ses.responder(_linhas(_assistente(152_000)))                    # 76%
    assert saida is not None
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "76%" in ctx and "152 mil de 200 mil" in ctx
    for marca in ("MAPA.md", "/mss-spec:to-dolist adicionar", "/clear", "subagente",
                  "não abra assunto novo", "início da sua próxima mensagem"):
        assert marca in ctx, f"aviso ao assistente sem {marca!r}"
    assert "76%" in saida["systemMessage"] and "/clear" in saida["systemMessage"]


def test_avisa_uma_vez_por_faixa_e_escala(ses):
    t = _linhas(_assistente(152_000))
    assert ses.responder(t) is not None
    assert ses.responder(t) is None                                         # mesma faixa
    assert ses.responder(t, evento="PostToolUse") is None                   # o outro evento também
    saida = ses.responder(_linhas(_assistente(172_000)), evento="PostToolUse")   # 86%
    assert saida is not None and "86%" in saida["systemMessage"]
    assert saida["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_compactou_rearma(ses):
    assert ses.responder(_linhas(_assistente(160_000))) is not None
    assert ses.responder(_linhas(_assistente(30_000))) is None              # depois do /compact
    assert ses.faixas["s1"] is None
    assert ses.responder(_linhas(_assistente(151_000))) is not None         # avisa de novo


def test_sessoes_nao_se_misturam(ses):
    t = _linhas(_assistente(160_000))
    assert ses.responder(t, sessao="a") is not None
    assert ses.responder(t, sessao="b") is not None


def test_limiar_configuravel(ses):
    t = _linhas(_assistente(125_000))                                       # 62,5%
    assert ses.responder(t) is None
    assert ses.responder(t, sessao="s2", ambiente={"MSS_ALERTA_CONTEXTO_PCT": "60"}) is not None
    assert ses.responder(t, sessao="s3", ambiente={"MSS_ALERTA_CONTEXTO_PCT": "0"}) is None   # inválido → 75


def test_subagente_evento_desconhecido_e_escape(ses):
    t = _linhas(_assistente(190_000))
    assert ses.responder(t, agent_id="abc") is None
    assert ses.responder(t, evento="Stop") is None
    assert ses.responder(t, ambiente={"MSS_ALERTA_CONTEXTO_OFF": "1"}) is None


def test_falha_aberta(mod):
    assert mod.regra(None, {}, lambda: None, lambda: None)[0] is None
    assert mod.regra({"hook_event_name": "UserPromptSubmit"}, {}, lambda: None, lambda: None)[0] is None


def test_registro_diz_a_faixa_sem_o_texto(ses):
    ses.responder(_linhas(_assistente(152_000)), prompt="SEGREDO")
    assert ses.anotacoes == [("avisou", "faixa=75 pct=76 janela=200000 modelo=claude-opus-4-6")]


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    return tmp_path_factory.mktemp("alerta_contexto")


def _gravar_transcript(caminho, *entradas):
    caminho.write_text("\n".join(json.dumps(e) for e in entradas) + "\n", encoding="utf-8")
    return caminho


def test_casca_le_a_cauda_e_grava_e_apaga_a_faixa(mod, pasta, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))
    lixo = {"type": "user", "message": {"content": "x" * 5000}}
    grande = _gravar_transcript(pasta / "grande.jsonl", *([_assistente(10_000)] + [lixo] * 400 + [_assistente(155_000)]))
    assert grande.stat().st_size > mod.CAUDA_BYTES
    assert mod.uso_atual(str(grande))[0] == 155_000, "a cauda do transcript grande não achou a última resposta"
    ev = {"hook_event_name": "UserPromptSubmit", "session_id": "disco", "transcript_path": str(grande)}
    assert mod.responder(ev, {}) is not None
    assert mod.responder(ev, {}) is None, "a faixa gravada no disco não foi lida"
    _gravar_transcript(grande, _assistente(30_000))
    assert mod.responder(ev, {}) is None
    assert not os.path.exists(mod._estado("disco")), "depois do /compact a faixa não foi apagada"
    assert mod.responder(dict(ev, transcript_path=str(pasta / "nao-existe.jsonl")), {}) is None


def test_processo_nunca_bloqueia(pasta):
    t = _gravar_transcript(pasta / "processo.jsonl", _assistente(180_000))
    env = dict(os.environ, TEMP=str(pasta), TMP=str(pasta), TMPDIR=str(pasta))
    env.pop("MSS_ALERTA_CONTEXTO_OFF", None)
    ev = {"hook_event_name": "UserPromptSubmit", "session_id": "proc", "transcript_path": str(t), "prompt": "segue"}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=30)
    assert r.returncode == 0 and "90%" in json.loads(r.stdout)["systemMessage"]


# --- fiação -----------------------------------------------------------------------------

def test_registrado_nos_dois_eventos():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    for evento in ("UserPromptSubmit", "PostToolUse"):
        cmds = [h["command"] for g in grupos.get(evento, []) for h in g["hooks"]]
        assert any("alerta_contexto.py" in c for c in cmds), f"alerta_contexto fora do {evento}"


def test_documentado():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "alerta_contexto.py" in readme and "MSS_ALERTA_CONTEXTO_OFF" in readme
    assert "MSS_JANELA_TOKENS" in readme and "MSS_ALERTA_CONTEXTO_PCT" in readme
    claude = texto_do_kit()
    assert "75%" in claude and "bola de neve" in claude.lower()
    todo = (REPO / "commands" / "to-dolist.md").read_text(encoding="utf-8")
    assert "bola de neve" in todo.lower() and "trava:" in todo
