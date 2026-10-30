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
HOOK = REPO / "hooks" / "kit_primeiro.py"


def _mod():
    spec = importlib.util.spec_from_file_location("kit_primeiro", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def amb(tmp_path):
    """Estado por sessão vai pro TEMP do teste — nada vaza entre testes nem pra máquina."""
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)}


def _skill(nome, sessao, cwd=None):
    return {"hook_event_name": "PreToolUse", "tool_name": "Skill", "session_id": sessao,
            "cwd": str(cwd or REPO), "tool_input": {"skill": nome, "args": ""}}


def _read(caminho, sessao):
    return {"hook_event_name": "PreToolUse", "tool_name": "Read", "session_id": sessao,
            "cwd": str(REPO), "tool_input": {"file_path": str(caminho)}}


def _prompt(texto, sessao):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sessao, "cwd": str(REPO), "prompt": texto}


def _nova():
    return "s-" + uuid.uuid4().hex[:8]


# --- AC1: a sequência real de 2026-10-30 ------------------------------------------------------

def test_sequencia_real_do_whats(amb):
    """15:14 — "vamos tratar aqui mesmo o bug" → systematic-debugging direto: NEGADO, com a porta certa.
    Depois o assistente invoca o `mss-spec:bug` (que, no passo 2, chama o superpowers): liberado."""
    mod, s = _mod(), _nova()
    motivo = mod.decidir(_skill("superpowers:systematic-debugging", s), amb)
    assert motivo, "systematic-debugging sem o kit passou"
    assert "/mss-spec:bug" in motivo and "superpowers:systematic-debugging" in motivo
    assert mod.decidir(_skill("mss-spec:bug", s), amb) is None, "o comando do kit foi barrado"
    assert mod.decidir(_skill("superpowers:systematic-debugging", s), amb) is None, \
        "depois do bug, o superpowers continuou negado"


def test_motivo_aponta_as_cinco_portas(amb):
    motivo = _mod().decidir(_skill("superpowers:brainstorming", _nova()), amb)
    for porta in ("/mss-spec:bug", "/mss-spec:nova-feature", "/mss-spec:duvida", "/mss-spec:tarefa",
                  "/mss-spec:analise"):
        assert porta in motivo, f"a negativa não aponta {porta}"
    assert "MSS_KIT_PRIMEIRO_OFF" in motivo, "a negativa não diz o escape do owner"


def test_tarefa_do_dia_a_dia_e_entrada_pelo_kit(amb):
    """A porta mais usada: `mss-spec:tarefa` conta como entrada e libera o superpowers que ela usar depois."""
    mod, s = _mod(), _nova()
    assert mod.decidir(_skill("mss-spec:tarefa", s), amb) is None
    assert mod.decidir(_skill("superpowers:test-driven-development", s), amb) is None
    assert (REPO / "commands" / "tarefa.md").exists(), "a porta /mss-spec:tarefa que a negativa aponta não existe"


# --- AC2: as três formas de entrar pelo kit ---------------------------------------------------

def test_owner_que_digita_o_comando_conta_como_entrada(amb):
    mod, s = _mod(), _nova()
    assert mod.decidir(_prompt("/mss-spec:duvida como o token é gerado?", s), amb) is None, "o prompt não é calado"
    assert mod.decidir(_skill("superpowers:systematic-debugging", s), amb) is None


def test_prompt_comum_nao_conta_como_entrada(amb):
    mod, s = _mod(), _nova()
    mod.decidir(_prompt("vamos tratar aqui mesmo o bug, segue o print", s), amb)
    assert mod.decidir(_skill("superpowers:systematic-debugging", s), amb)


def test_ler_o_comando_do_kit_conta_como_entrada(amb):
    """`nova-feature` é `disable-model-invocation`: roda por leitura do `commands/nova-feature.md`."""
    mod, s = _mod(), _nova()
    assert mod.decidir(_read(REPO / "commands" / "nova-feature.md", s), amb) is None
    assert mod.decidir(_skill("superpowers:brainstorming", s), amb) is None


def test_ler_outro_arquivo_nao_conta(amb):
    mod, s = _mod(), _nova()
    mod.decidir(_read(REPO / "hooks" / "README.md", s), amb)
    mod.decidir(_read(Path("C:/qualquer/projeto/commands/bug.md"), s), amb)   # commands/ de outro lugar
    assert mod.decidir(_skill("superpowers:brainstorming", s), amb)


def test_comando_instalado_fora_do_repo_conta(amb):
    """Instalado em `~/.claude/skills/mss-spec/` ou no cache do marketplace, o caminho muda; `mss-spec` no caminho basta."""
    mod, s = _mod(), _nova()
    mod.decidir(_read(Path.home() / ".claude" / "skills" / "mss-spec" / "commands" / "analise.md", s), amb)
    assert mod.decidir(_skill("superpowers:brainstorming", s), amb) is None


# --- AC3: sessões não se misturam; o resto passa; escape; falha aberta ------------------------

def test_sessoes_sao_independentes(amb):
    mod, s1, s2 = _mod(), _nova(), _nova()
    mod.decidir(_skill("mss-spec:bug", s1), amb)
    assert mod.decidir(_skill("superpowers:systematic-debugging", s1), amb) is None
    assert mod.decidir(_skill("superpowers:systematic-debugging", s2), amb), "a entrada de s1 valeu pra s2"


@pytest.mark.parametrize("skill", ["mss-spec:mapa", "anthropic-skills:docs", "dataviz", "code-review"])
def test_skill_que_nao_e_do_superpowers_passa(amb, skill):
    assert _mod().decidir(_skill(skill, _nova()), amb) is None


def test_outra_ferramenta_passa(amb):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": _nova(), "cwd": str(REPO),
          "tool_input": {"command": "git status"}}
    assert _mod().decidir(ev, amb) is None


def test_escape_do_owner(amb):
    assert _mod().decidir(_skill("superpowers:systematic-debugging", _nova()), {**amb, "MSS_KIT_PRIMEIRO_OFF": "1"}) is None


@pytest.mark.parametrize("ruim", [None, "texto", {}, {"hook_event_name": "PreToolUse"},
                                  {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": None},
                                  {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": {"skill": 7}}])
def test_entrada_malformada_libera(amb, ruim):
    assert _mod().decidir(ruim, amb) is None


# --- AC4: o processo, o registro e a fiação --------------------------------------------------

def _rodar(ev, tmp_path, extra=None):
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path), **(extra or {})})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=amb, timeout=30)


def test_processo_nega_como_a_cerca_de_publicacao(tmp_path):
    """Mesmo contrato do `git_publicacao.py`, o que já funciona ao vivo nesta máquina: JSON `deny` no
    stdout + motivo no stderr + exit 2."""
    r = _rodar(_skill("superpowers:systematic-debugging", _nova()), tmp_path)
    assert r.returncode == 2
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "/mss-spec:bug" in saida["hookSpecificOutput"]["permissionDecisionReason"]
    assert "/mss-spec:bug" in r.stderr


def test_processo_calado_quando_libera(tmp_path):
    s = _nova()
    assert _rodar(_skill("mss-spec:bug", s), tmp_path).returncode == 0
    r = _rodar(_skill("superpowers:systematic-debugging", s), tmp_path)
    assert r.returncode == 0 and not r.stdout.strip()


def test_negativa_fica_no_registro_sem_o_texto_do_prompt(tmp_path):
    reg = tmp_path / "registro-hooks.jsonl"
    r = _rodar(_skill("superpowers:systematic-debugging", "abcdef123456"), tmp_path,
               {"MSS_REGISTRO_ARQUIVO": str(reg)})
    assert r.returncode == 2
    linhas = [json.loads(l) for l in reg.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(linhas) == 1
    assert linhas[0]["hook"] == "kit_primeiro" and linhas[0]["decisao"] == "negou"
    assert "superpowers:systematic-debugging" in linhas[0]["detalhe"]
    assert linhas[0]["sessao"] == "abcdef12"


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
