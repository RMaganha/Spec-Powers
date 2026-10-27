"""Trava "nunca trabalhar em worktree, nunca abrir conversa a partir de outra" (0.46.0).

Caso de 2026-10-27: a conversa da 0.44.0 abriu sozinha `.claude/worktrees/partida-em-dois-niveis` — o aviso
do kit mandava ("abra esta num worktree") — e deixou 2 commits e memória fora da `main`; e duas conversas
abertas a partir de outra ficaram penduradas uma na outra na barra lateral. O owner não usa nenhum dos dois.

Contrato (`hooks/sem_worktree.py` + 5ª cerca do `hooks/git_publicacao.py`):
- `WorktreeCreate` falha SEMPRE (sem caminho no stdout, exit ≠ 0), inclusive com o escape;
- `PreToolUse` nega `EnterWorktree`, `Agent` com `isolation: "worktree"`, escrita com o alvo dentro de um
  worktree, e abrir/passar conversa (`start_session`/`hand_off_to_session`) mandando entregar o texto pronto;
- `SessionStart` dentro de um worktree avisa; fora, calado;
- no shell: `git worktree add` e gravar dentro de um worktree são negados; `git worktree list` passa;
- escape só do owner: `MSS_WORKTREE_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "sem_worktree.py"
GIT_PUBLICACAO = REPO / "hooks" / "git_publicacao.py"
ABRIR_CONVERSA = "mcp__ccd_session__start_session"
PASSAR_CONVERSA = "mcp__ccd_session__hand_off_to_session"


def _carregar(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mod():
    return _carregar(HOOK, "sem_worktree")


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def repo_com_worktree(tmp_path):
    """Repo principal + um worktree de verdade, criado como a conversa da 0.44.0 criou."""
    principal = tmp_path / "kit"
    principal.mkdir()
    _git("init", "-q", "-b", "main", cwd=principal)
    _git("-c", "user.email=a@b", "-c", "user.name=a", "commit", "-q", "--allow-empty", "-m", "i", cwd=principal)
    wt = principal / ".claude" / "worktrees" / "partida-em-dois-niveis"
    _git("worktree", "add", "-q", str(wt), "-b", "worktree-partida", cwd=principal)
    return principal, wt


def _escrita(alvo, cwd, tool="Write"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(cwd),
            "tool_input": {"file_path": str(alvo), "content": "x"}}


# --- "dentro de um worktree": lido do arquivo .git, sem rodar o git ---------------------------------------

def test_detecta_worktree_e_nao_confunde_com_a_pasta_principal(repo_com_worktree, tmp_path):
    principal, wt = repo_com_worktree
    mod = _mod()
    assert mod.dentro_de_worktree(str(wt / "memory" / "nova.md")), "arquivo novo dentro do worktree passou"
    assert mod.dentro_de_worktree(str(wt)), "a raiz do worktree passou"
    assert not mod.dentro_de_worktree(str(principal / "memory" / "nova.md")), "pasta principal virou worktree"
    assert not mod.dentro_de_worktree(str(tmp_path / "solta" / "a.txt")), "pasta fora de repo virou worktree"


def test_submodulo_nao_e_worktree(tmp_path):
    sub = tmp_path / "kit" / "vendor" / "lib"
    sub.mkdir(parents=True)
    (sub / ".git").write_text("gitdir: ../../.git/modules/vendor/lib\n", encoding="utf-8")
    assert not _mod().dentro_de_worktree(str(sub / "a.py"))


# --- criar ou entrar em worktree: negado sempre ----------------------------------------------------------

def test_worktree_create_falha_sempre_ate_com_o_escape(tmp_path):
    ev = {"hook_event_name": "WorktreeCreate", "name": "bold-oak-a3f2", "cwd": str(tmp_path)}
    for amb in ({}, {"MSS_WORKTREE_OFF": "1"}):
        proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, **amb})
        assert proc.returncode != 0, f"worktree criado (escape={amb})"
        assert proc.stdout.strip() == "", "saiu caminho no stdout — o Claude Code criaria o worktree"
        assert "worktree" in proc.stderr.lower()


@pytest.mark.parametrize("entrada", [{"name": "partida"}, {"path": ".claude/worktrees/partida"}, {}])
def test_enter_worktree_e_negado(tmp_path, entrada):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "EnterWorktree", "cwd": str(tmp_path),
          "tool_input": entrada}
    tipo, motivo = _mod().avaliar(ev, ambiente={})
    assert tipo == "deny"
    assert "pasta principal" in motivo and "main" in motivo, "a negação não diz onde trabalhar"


def test_subagente_isolado_e_negado_e_o_comum_passa(tmp_path):
    base = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": str(tmp_path)}
    isolado = {**base, "tool_input": {"prompt": "x", "isolation": "worktree"}}
    comum = {**base, "tool_input": {"prompt": "x"}}
    assert _mod().avaliar(isolado, ambiente={})[0] == "deny"
    assert _mod().avaliar(comum, ambiente={}) == (None, None)


# --- gravar dentro de um worktree: negado --------------------------------------------------------------

@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
def test_gravar_no_worktree_e_negado(repo_com_worktree, tool):
    principal, wt = repo_com_worktree
    tipo, motivo = _mod().avaliar(_escrita(wt / "memory" / "MEMORY.md", principal, tool), ambiente={})
    assert tipo == "deny", f"{tool} gravou dentro do worktree"
    assert str(wt) in motivo or wt.name in motivo, "a negação não diz qual worktree"


def test_notebook_no_worktree_e_negado(repo_com_worktree):
    principal, wt = repo_com_worktree
    ev = {"hook_event_name": "PreToolUse", "tool_name": "NotebookEdit", "cwd": str(principal),
          "tool_input": {"notebook_path": str(wt / "a.ipynb")}}
    assert _mod().avaliar(ev, ambiente={})[0] == "deny"


def test_gravar_na_pasta_principal_passa(repo_com_worktree):
    principal, _ = repo_com_worktree
    assert _mod().avaliar(_escrita(principal / "memory" / "MEMORY.md", principal), ambiente={}) == (None, None)


def test_escape_do_owner_libera_a_gravacao(repo_com_worktree):
    principal, wt = repo_com_worktree
    ev = _escrita(wt / "a.md", principal)
    assert _mod().avaliar(ev, ambiente={"MSS_WORKTREE_OFF": "1"}) == (None, None)


# --- abrir ou passar conversa a partir desta: negado, com o texto pronto ------------------------------

@pytest.mark.parametrize("tool,entrada", [
    (ABRIR_CONVERSA, {"initiation": "user_asked", "title": "x", "prompt": "y", "use_worktree": False}),
    (ABRIR_CONVERSA, {"initiation": "own_initiative", "title": "x", "prompt": "y"}),
    (ABRIR_CONVERSA, {"initiation": "offer", "title": "x"}),
    (PASSAR_CONVERSA, {"title": "x", "remaining_plan": "y"}),
])
def test_abrir_conversa_a_partir_desta_e_negado(tmp_path, tool, entrada):
    ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(tmp_path), "tool_input": entrada}
    tipo, motivo = _mod().avaliar(ev, ambiente={})
    assert tipo == "deny", f"abriu conversa por {tool} {entrada}"
    low = motivo.lower()
    assert "texto pronto" in low and "+" in motivo, "a negação não manda entregar o texto pronto pro +"


def test_escape_do_owner_libera_a_conversa(tmp_path):
    ev = {"hook_event_name": "PreToolUse", "tool_name": ABRIR_CONVERSA, "cwd": str(tmp_path),
          "tool_input": {"initiation": "offer", "title": "x"}}
    assert _mod().avaliar(ev, ambiente={"MSS_WORKTREE_OFF": "1"}) == (None, None)


def test_outras_ferramentas_passam_caladas(tmp_path):
    for tool in ("Read", "Bash", "mcp__ccd_session__dismiss_task"):
        ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(tmp_path), "tool_input": {}}
        assert _mod().avaliar(ev, ambiente={}) == (None, None), tool


# --- conversa que já começa dentro de um worktree: aviso na abertura ------------------------------------

def test_abertura_dentro_de_worktree_avisa(repo_com_worktree):
    _, wt = repo_com_worktree
    tipo, texto = _mod().avaliar({"hook_event_name": "SessionStart", "cwd": str(wt)}, ambiente={})
    assert tipo == "avisa"
    assert "worktree" in texto.lower() and "pasta principal" in texto


def test_abertura_na_pasta_principal_e_calada(repo_com_worktree):
    principal, _ = repo_com_worktree
    assert _mod().avaliar({"hook_event_name": "SessionStart", "cwd": str(principal)}, ambiente={}) == (None, None)


# --- processo: os dois protocolos do deny, e entrada ruim não trava -------------------------------------

def _rodar(evento, **amb):
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento), capture_output=True,
                          text=True, encoding="utf-8", env={**os.environ, **amb})


def test_processo_nega_pelos_dois_protocolos(tmp_path):
    proc = _rodar({"hook_event_name": "PreToolUse", "tool_name": "EnterWorktree", "cwd": str(tmp_path),
                   "tool_input": {"name": "x"}})
    assert proc.returncode == 2
    saida = json.loads(proc.stdout)["hookSpecificOutput"]
    assert saida["hookEventName"] == "PreToolUse" and saida["permissionDecision"] == "deny"
    assert proc.stderr.strip()


def test_processo_avisa_na_abertura(repo_com_worktree):
    _, wt = repo_com_worktree
    proc = _rodar({"hook_event_name": "SessionStart", "cwd": str(wt)})
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "worktree" in saida["hookSpecificOutput"]["additionalContext"].lower()
    assert "worktree" in saida["systemMessage"].lower()


def test_processo_com_entrada_ruim_libera(tmp_path):
    proc = subprocess.run([sys.executable, str(HOOK)], input="isto não é json", capture_output=True, text=True)
    assert proc.returncode == 0 and proc.stdout.strip() == ""


def test_registrado_no_hooks_json():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]

    def comandos(evento, nome=None):
        return [(g.get("matcher", ""), h["command"]) for g in cfg.get(evento, []) for h in g["hooks"]
                if "sem_worktree.py" in h["command"]]
    assert comandos("WorktreeCreate"), "WorktreeCreate não registrado"
    assert comandos("SessionStart"), "SessionStart não registrado"
    matchers = " ".join(m for m, _ in comandos("PreToolUse")).split("|")
    for tool in ("EnterWorktree", "Agent", "Write", "Edit", "MultiEdit", "NotebookEdit",
                 ABRIR_CONVERSA, PASSAR_CONVERSA):
        assert tool in matchers, f"PreToolUse do sem_worktree.py não cobre {tool}"


# --- shell (5ª cerca do git_publicacao.py) ----------------------------------------------------------------

def _shell(comando, cwd, **amb):
    mod = _carregar(GIT_PUBLICACAO, "git_publicacao")
    ev = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(cwd)}
    return mod.avaliar(ev, {"CLAUDE_PROJECT_DIR": str(cwd), **amb}, git_destino=lambda p: ("feature/x", None))


@pytest.mark.parametrize("comando", [
    "git worktree add .claude/worktrees/x -b feature/x",
    "cd /tmp && git worktree add ../x",
    "git -C . worktree add -q ../x main",
])
def test_shell_criar_worktree_e_negado(repo_com_worktree, comando):
    principal, _ = repo_com_worktree
    tipo, motivo = _shell(comando, principal)
    assert tipo == "deny", f"passou: {comando}"
    assert "worktree" in motivo.lower()


def test_shell_gravar_dentro_de_worktree_e_negado(repo_com_worktree):
    principal, wt = repo_com_worktree
    for comando in (f'git -C "{wt}" commit -m x', f'cd "{wt}" && git add a.txt',
                    f'echo x > "{wt / "memory" / "a.md"}"'):
        tipo, _ = _shell(comando, principal)
        assert tipo == "deny", f"passou: {comando}"


def test_shell_leitura_e_pasta_principal_passam(repo_com_worktree):
    principal, wt = repo_com_worktree
    for comando in ("git worktree list", f'git -C "{wt}" status', "git commit -m x",
                    "grep 'git worktree add' docs/x.md"):
        tipo, _ = _shell(comando, principal)
        assert tipo != "deny", f"negou: {comando}"


def test_shell_escape_do_owner(repo_com_worktree):
    principal, _ = repo_com_worktree
    assert _shell("git worktree add ../x", principal, MSS_WORKTREE_OFF="1")[0] != "deny"


# --- o texto do kit parou de mandar abrir worktree ------------------------------------------------------

def test_kit_nao_manda_mais_abrir_worktree():
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    um_item = (REPO / "hooks" / "um_item_por_janela.py").read_text(encoding="utf-8")
    for nome, texto in (("nova-feature.md", nova), ("um_item_por_janela.py", um_item)):
        assert "using-git-worktrees" not in texto, f"{nome} ainda manda usar worktree"
        assert "num worktree" not in texto, f"{nome} ainda manda abrir num worktree"
    aviso = _carregar(REPO / "hooks" / "um_item_por_janela.py", "um_item_por_janela").AVISO.lower()
    assert "pergunte ao owner" in aviso, "aviso não manda parar e perguntar quando a pasta está em outra feature"
