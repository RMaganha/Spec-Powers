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

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o texto do transcript entra como dado (lido pela
`_transcricao.gravacoes_do_texto`) e os arquivos já cobrados de cada conversa ficam num dicionário. O disco de
verdade (ler o transcript, gravar e ler os cobrados) fica num teste só, numa pasta montada uma vez; o processo
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
HOOK = REPO / "hooks" / "decisao_junto.py"
PROJ = "C:\\Ronaldo\\_Mitsui\\Python\\IA Bot Agent\\IA Bot Agent - Whats"
KIT = "C:\\Ronaldo\\_Mitsui\\Python\\Spec-Powers"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("decisao_junto", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _transcript(caminhos, sidechain=()):
    """O texto de um transcript com um Edit por caminho (e os de `sidechain` marcados como subagente)."""
    linhas = [json.dumps({"type": "user", "message": {"content": "oi"}})]
    for c in caminhos:
        linhas.append(json.dumps({"type": "assistant", "timestamp": "2026-11-06T18:00:00.000Z", "message": {
            "content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": c, "old_string": "a", "new_string": "b"}}]}}))
    for c in sidechain:
        linhas.append(json.dumps({"type": "assistant", "isSidechain": True, "message": {
            "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": c}}]}}))
    return "\n".join(linhas) + "\n"


class Conversas:
    """Os arquivos já cobrados de cada conversa, em memória. `decidir` chama a regra com o texto do transcript como
    dado e guarda o que ela manda marcar — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.cobradas, self.anotacoes = mod, {}, []
        self.tr = sys.modules["_transcricao"]

    def decidir(self, transcript, sessao="s1", ativo=False, ambiente=None, evento=None):
        ev = evento if evento is not None else {"hook_event_name": "Stop", "cwd": KIT, "session_id": sessao,
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


# --- AC1: comportamento sem decisão devolve; o que conta e o que não conta ------------------------

def test_hook_do_kit_sem_decisao_devolve(conv):
    motivo = conv.decidir(_transcript([KIT + "\\hooks\\git_publicacao.py", KIT + "\\commands\\bug.md"]))
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
def test_arquivos_de_comportamento_contam(conv, caminho):
    assert conv.decidir(_transcript([caminho]))


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
def test_codigo_memoria_teste_readme_e_molde_nao_contam(conv, caminho):
    assert conv.decidir(_transcript([caminho])) is None


# --- AC2: com a decisão, passa (decisoes.md ou Histórico da spec); cobra uma vez --------------------

@pytest.mark.parametrize("decisao", [
    KIT + "\\docs\\decisoes.md",
    KIT + "\\docs\\specs\\regras-do-kit-pelo-plugin.md",
    KIT + "\\docs\\superpowers\\specs\\2026-11-06-x-design.md",
    "docs/decisoes.md",
])
def test_com_decisao_passa(conv, decisao):
    assert conv.decidir(_transcript([KIT + "\\hooks\\git_publicacao.py", decisao])) is None


def test_cobra_uma_vez_e_de_novo_so_com_arquivo_novo(conv):
    t1 = _transcript([KIT + "\\hooks\\git_publicacao.py"])
    assert conv.decidir(t1)
    assert conv.decidir(t1) is None, "cobrou duas vezes o mesmo arquivo"
    motivo = conv.decidir(_transcript([KIT + "\\hooks\\git_publicacao.py", KIT + "\\commands\\bug.md"]))
    assert motivo and "commands/bug.md" in motivo and "git_publicacao" not in motivo.split("—")[1]


def test_sessoes_sao_independentes(conv):
    t = _transcript([KIT + "\\hooks\\git_publicacao.py"])
    assert conv.decidir(t, "s-a")
    assert conv.decidir(t, "s-b"), "a cobrança de s-a valeu pra s-b"


# --- AC3: nunca laço, subagente, escape, falha aberta ----------------------------------------------

def test_stop_hook_active_passa(conv):
    assert conv.decidir(_transcript([KIT + "\\hooks\\git_publicacao.py"]), ativo=True) is None


def test_gravacao_de_subagente_nao_conta(conv):
    assert conv.decidir(_transcript([], sidechain=[KIT + "\\hooks\\git_publicacao.py"])) is None


def test_escape_do_owner(conv):
    t = _transcript([KIT + "\\hooks\\git_publicacao.py"])
    assert conv.decidir(t, ambiente={"MSS_DECISAO_JUNTO_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "x", {}, {"hook_event_name": "PreToolUse"}])
def test_entrada_malformada_libera(conv, ruim):
    assert conv.decidir(_transcript([KIT + "\\hooks\\git_publicacao.py"]), evento=ruim) is None


def test_transcript_vazio_ou_ilegivel_libera(conv):
    assert conv.decidir("") is None
    assert conv.decidir('{"type": "assistant", "message": {"content": [{"type": "tool_use"\nnão é json\n') is None


def test_registro_guarda_a_devolucao_sem_o_texto(conv):
    conv.decidir(_transcript([KIT + "\\hooks\\git_publicacao.py"]))
    assert conv.anotacoes == [("devolveu", "comportamento_sem_decisao=1")]


def test_saida_pelo_contrato_do_stop(mod):
    assert json.loads(mod.saida("registre a decisão")) == {"decision": "block", "reason": "registre a decisão"}
    assert mod.saida(None) is None


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("decisao_junto")
    transcript = base / "t.jsonl"
    transcript.write_text(_transcript([KIT + "\\hooks\\git_publicacao.py"]), encoding="utf-8")
    return base, transcript


def test_casca_le_o_transcript_e_grava_os_cobrados(mod, pasta):
    base, transcript = pasta
    amb = {"TEMP": str(base), "TMP": str(base), "TMPDIR": str(base)}
    ev = {"hook_event_name": "Stop", "cwd": KIT, "session_id": "disco", "stop_hook_active": False,
          "transcript_path": str(transcript)}
    assert mod.decidir(ev, amb), "o transcript do disco não foi lido"
    assert mod.decidir(ev, amb) is None, "a cobrança gravada no disco não foi lida"
    assert mod.decidir(dict(ev, session_id="outra", transcript_path=str(base / "nao-existe.jsonl")), amb) is None


def test_processo_devolve_por_json_com_exit_0(pasta):
    base, transcript = pasta
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(base), "TMP": str(base), "TMPDIR": str(base)})
    ev = {"hook_event_name": "Stop", "cwd": KIT, "session_id": "proc", "stop_hook_active": False,
          "transcript_path": str(transcript)}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=amb, timeout=30)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["decision"] == "block" and "docs/decisoes.md" in saida["reason"]


def test_fiacao_no_hooks_json_e_no_readme():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    stops = [h["command"] for grupo in cfg["hooks"]["Stop"] for h in grupo["hooks"]]
    assert any("decisao_junto.py" in c for c in stops), "decisao_junto.py não está no Stop do hooks.json"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "`decisao_junto.py` | `Stop`" in readme, "hooks/README.md sem a linha do decisao_junto na tabela"
    assert "MSS_DECISAO_JUNTO_OFF" in readme
