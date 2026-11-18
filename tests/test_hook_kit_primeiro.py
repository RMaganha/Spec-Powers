"""O kit entra primeiro — skill do superpowers só por dentro de um comando do kit (caso F-048).

Nasceu da conversa "Validar mensagens WhatsApp em produção" (Whats, 2026-10-30): às 15:14 o owner disse
"vamos tratar aqui mesmo o bug" e o assistente invocou `superpowers:systematic-debugging` direto, sem o
`/mss-spec:bug`. O passo 1 do bug (memória antes da hipótese) não aconteceu, e em 8 minutos a hipótese
errada (`MITI_DEV_AUTH`) estava na mesa. A regra 11 e o `bug.md` já mandavam entrar pelo kit; o
`superpowers:using-superpowers` manda "bug → systematic-debugging primeiro". Prosa contra prosa, ganhou
a do superpowers — 2ª reincidência (a 1ª foi a de 2026-10-27 que criou o `bug.md`). Aqui a cerca é
determinística.

Propriedades:
- `PreToolUse` em `Skill`: `superpowers:*` sem nenhuma entrada pelo kit nesta sessão → **nega**, dizendo
  a porta certa (bug · nova-feature · duvida · analise); `mss-spec:*` → marca a entrada e libera;
- entrada pelo kit também conta quando o owner digita `/mss-spec:<x>` (`UserPromptSubmit`) e quando o
  assistente lê `commands/<x>.md` do kit (`PreToolUse` em `Read` — é assim que rodam os comandos
  `disable-model-invocation`, como o `nova-feature`);
- estado por sessão (duas conversas não se misturam); falha ABERTA; escape só do owner:
  `MSS_KIT_PRIMEIRO_OFF=1`; registra `negou` no registro local.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — quais conversas já entraram pelo kit fica num objeto
do teste e entra como dado. O disco de verdade (gravar e ler a entrada de cada conversa) fica num teste só, numa
pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "kit_primeiro.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("kit_primeiro", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Conversas:
    """Quais conversas já entraram pelo kit, em memória — o que o hook guarda no temp do SO. `decidir` chama a regra
    com isso como dado e guarda a entrada que ela devolve — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.entraram, self.anotacoes = mod, {}, []

    def decidir(self, evento, ambiente=None):
        motivo, mudancas = self.mod.regra(evento, ambiente or {}, lambda sessao: sessao in self.entraram)
        if "marcar" in mudancas:
            self.entraram[evento.get("session_id")] = mudancas["marcar"]
        self.anotacoes += mudancas["anotacoes"]
        return motivo


@pytest.fixture()
def kit(mod):
    return Conversas(mod)


def _skill(nome, sessao, cwd=None):
    return {"hook_event_name": "PreToolUse", "tool_name": "Skill", "session_id": sessao,
            "cwd": str(cwd or REPO), "tool_input": {"skill": nome, "args": ""}}


def _read(caminho, sessao):
    return {"hook_event_name": "PreToolUse", "tool_name": "Read", "session_id": sessao,
            "cwd": str(REPO), "tool_input": {"file_path": str(caminho)}}


def _prompt(texto, sessao):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sessao, "cwd": str(REPO), "prompt": texto}


# --- AC1: a sequência real de 2026-10-30 ------------------------------------------------------

def test_sequencia_real_do_whats(kit):
    """15:14 — "vamos tratar aqui mesmo o bug" → systematic-debugging direto: NEGADO, com a porta certa.
    Depois o assistente invoca o `mss-spec:bug` (que, no passo 2, chama o superpowers): liberado."""
    motivo = kit.decidir(_skill("superpowers:systematic-debugging", "s"))
    assert motivo, "systematic-debugging sem o kit passou"
    assert "/mss-spec:bug" in motivo and "superpowers:systematic-debugging" in motivo
    assert kit.decidir(_skill("mss-spec:bug", "s")) is None, "o comando do kit foi barrado"
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s")) is None, \
        "depois do bug, o superpowers continuou negado"


def test_motivo_aponta_as_cinco_portas(kit):
    motivo = kit.decidir(_skill("superpowers:brainstorming", "s"))
    for porta in ("/mss-spec:bug", "/mss-spec:nova-feature", "/mss-spec:duvida", "/mss-spec:tarefa",
                  "/mss-spec:analise"):
        assert porta in motivo, f"a negativa não aponta {porta}"
    assert "MSS_KIT_PRIMEIRO_OFF" in motivo, "a negativa não diz o escape do owner"


def test_tarefa_do_dia_a_dia_e_entrada_pelo_kit(kit):
    """A porta mais usada: `mss-spec:tarefa` conta como entrada e libera o superpowers que ela usar depois."""
    assert kit.decidir(_skill("mss-spec:tarefa", "s")) is None
    assert kit.decidir(_skill("superpowers:test-driven-development", "s")) is None
    assert (REPO / "commands" / "tarefa.md").exists(), "a porta /mss-spec:tarefa que a negativa aponta não existe"


# --- AC2: as três formas de entrar pelo kit ---------------------------------------------------

def test_owner_que_digita_o_comando_conta_como_entrada(kit):
    assert kit.decidir(_prompt("/mss-spec:duvida como o token é gerado?", "s")) is None, "o prompt não é calado"
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s")) is None


def test_prompt_comum_nao_conta_como_entrada(kit):
    kit.decidir(_prompt("vamos tratar aqui mesmo o bug, segue o print", "s"))
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s"))


def test_ler_o_comando_do_kit_conta_como_entrada(kit):
    """`nova-feature` é `disable-model-invocation`: roda por leitura do `commands/nova-feature.md`."""
    assert kit.decidir(_read(REPO / "commands" / "nova-feature.md", "s")) is None
    assert kit.decidir(_skill("superpowers:brainstorming", "s")) is None


def test_ler_outro_arquivo_nao_conta(kit):
    kit.decidir(_read(REPO / "hooks" / "README.md", "s"))
    # commands/ de outro lugar — absoluto em qualquer sistema (`C:/...` no Linux vira pasta dentro do kit)
    kit.decidir(_read(Path(REPO.anchor) / "qualquer" / "projeto" / "commands" / "bug.md", "s"))
    assert kit.decidir(_skill("superpowers:brainstorming", "s"))


def test_comando_instalado_fora_do_repo_conta(kit):
    """Instalado em `~/.claude/skills/mss-spec/` ou no cache do marketplace, o caminho muda; `mss-spec` no caminho basta."""
    kit.decidir(_read(Path.home() / ".claude" / "skills" / "mss-spec" / "commands" / "analise.md", "s"))
    assert kit.decidir(_skill("superpowers:brainstorming", "s")) is None


# --- AC3: sessões não se misturam; o resto passa; escape; falha aberta ------------------------

def test_sessoes_sao_independentes(kit):
    kit.decidir(_skill("mss-spec:bug", "s1"))
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s1")) is None
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s2")), "a entrada de s1 valeu pra s2"


@pytest.mark.parametrize("skill", ["mss-spec:mapa", "anthropic-skills:docs", "dataviz", "code-review"])
def test_skill_que_nao_e_do_superpowers_passa(kit, skill):
    assert kit.decidir(_skill(skill, "s")) is None


def test_outra_ferramenta_passa(kit):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": "s", "cwd": str(REPO),
          "tool_input": {"command": "git status"}}
    assert kit.decidir(ev) is None


def test_escape_do_owner(kit):
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s"), {"MSS_KIT_PRIMEIRO_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "texto", {}, {"hook_event_name": "PreToolUse"},
                                  {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": None},
                                  {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": {"skill": 7}}])
def test_entrada_malformada_libera(kit, ruim):
    assert kit.decidir(ruim) is None


def test_negativa_fica_no_registro_sem_o_texto_do_prompt(kit):
    kit.decidir(_prompt("vamos tratar aqui mesmo o bug, segue o print", "s"))
    kit.decidir(_skill("superpowers:systematic-debugging", "s"))
    assert kit.anotacoes == [("negou", "superpowers:systematic-debugging")]


def test_saida_como_a_cerca_de_publicacao(mod):
    """Mesmo contrato do `git_publicacao.py`, o que já funciona ao vivo nesta máquina: JSON `deny` no
    stdout + motivo no stderr + exit 2; liberar é calado."""
    impresso, erro, codigo = mod.saida("entre por /mss-spec:bug")
    assert codigo == 2 and erro == "entre por /mss-spec:bug"
    assert json.loads(impresso)["hookSpecificOutput"] == {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                          "permissionDecisionReason": "entre por /mss-spec:bug"}
    assert mod.saida(None) == (None, None, 0)


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def temp(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("kit_primeiro")
    return {"TEMP": str(pasta), "TMP": str(pasta), "TMPDIR": str(pasta)}


def test_casca_grava_e_le_a_entrada_de_cada_conversa(mod, temp):
    assert mod.decidir(_skill("superpowers:brainstorming", "d1"), temp), "sem entrada gravada, devia negar"
    assert mod.decidir(_skill("mss-spec:bug", "d1"), temp) is None
    assert mod.decidir(_skill("superpowers:brainstorming", "d1"), temp) is None, "a entrada gravada não foi lida"
    assert mod.decidir(_skill("superpowers:brainstorming", "d2"), temp), "a entrada de d1 valeu pra d2"


def test_processo_nega_como_a_cerca_de_publicacao(temp):
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update(temp)
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_skill("superpowers:systematic-debugging", "proc")),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=amb, timeout=30)
    assert r.returncode == 2
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "/mss-spec:bug" in saida["hookSpecificOutput"]["permissionDecisionReason"]
    assert "/mss-spec:bug" in r.stderr


# --- fiação -----------------------------------------------------------------------------------

def test_hook_registrado_nos_tres_eventos():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    assert any("kit_primeiro.py" in h["command"] for g in cfg["UserPromptSubmit"] for h in g["hooks"]), \
        "kit_primeiro não vê o owner digitar /mss-spec:<x>"
    grupos = [g for g in cfg["PreToolUse"] if any("kit_primeiro.py" in h["command"] for h in g["hooks"])]
    assert grupos, "kit_primeiro não está no PreToolUse"
    matcher = grupos[0].get("matcher", "")
    assert "Skill" in matcher and "Read" in matcher, f"matcher sem Skill e Read: {matcher!r}"


def test_documentado_no_readme_e_na_regra_11():
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "kit_primeiro.py" in doc, "hooks/README.md não documenta o kit_primeiro"
    regras = (REPO / "templates" / "regras-do-kit" / "2-regras-criticas.md").read_text(encoding="utf-8")
    regra11 = next(l for l in regras.splitlines() if l.startswith("11."))
    assert "kit_primeiro" in regra11 or "superpowers só por dentro" in regra11.lower(), \
        "a regra 11 não diz que a cerca agora é hook"

# --- 0.59.0: comando do kit dentro de texto colado (caso F-053) ------------------------------------

COLADO = '<pasted_content id="6303">\n/mss-spec:nova-feature upgrade em uma rodada só\n\nHoje o upgrade roda em 3 passes.\n</pasted_content>'


def test_comando_colado_conta_como_entrada(kit):
    """A forma real da conversa do F-053: o pedido chega dentro de `<pasted_content id="…">`."""
    assert kit.decidir(_prompt(COLADO, "s")) is None
    assert kit.decidir(_skill("superpowers:brainstorming", "s")) is None, \
        "o comando colado não contou como entrada pelo kit (F-053)"


def test_comando_citado_no_meio_do_colado_nao_conta(kit):
    kit.decidir(_prompt('<pasted_content id="1">\nolhe o log; depois rodo /mss-spec:bug\n</pasted_content>', "s"))
    assert kit.decidir(_skill("superpowers:systematic-debugging", "s")), \
        "comando citado no meio do texto colado contou como entrada"
