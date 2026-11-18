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

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o `.git` de cada pasta vem de um dicionário (o hook
só lê o arquivo `.git`, nunca roda o git); os caminhos não existem. Na 5ª cerca do `git_publicacao.py`, a leitura do
`.git` (`sem_worktree._marca_no_disco`) é trocada por `monkeypatch`. O disco de verdade fica num teste só, numa pasta
montada uma vez; o processo python, num teste só.
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

# o disco de mentira: a pasta principal, um worktree criado como a conversa da 0.44.0 criou e um submódulo
PRINCIPAL = os.path.abspath(str(REPO.parent / "kit-que-nao-existe"))
WT = os.path.join(PRINCIPAL, ".claude", "worktrees", "partida-em-dois-niveis")
SUB = os.path.join(PRINCIPAL, "vendor", "lib")
SOLTA = os.path.abspath(str(REPO.parent / "pasta-solta-que-nao-existe"))
DISCO = {
    PRINCIPAL: ("pasta", None),
    WT: ("arquivo", f"gitdir: {PRINCIPAL}/.git/worktrees/partida-em-dois-niveis\n"),
    SUB: ("arquivo", "gitdir: ../../.git/modules/vendor/lib\n"),
}


def _carregar(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _carregar(HOOK, "sem_worktree")


def _avaliar(mod, evento, ambiente=None):
    """O papel da casca, em memória: a regra com o disco de mentira."""
    tipo, texto, _ = mod.regra(evento, ambiente or {}, DISCO.get, SOLTA)
    return tipo, texto


def _escrita(alvo, cwd=PRINCIPAL, tool="Write"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(cwd),
            "tool_input": {"file_path": str(alvo), "content": "x"}}


# --- "dentro de um worktree": lido do arquivo .git, sem rodar o git ---------------------------------------

def test_detecta_worktree_e_nao_confunde_com_a_pasta_principal(mod):
    assert mod.dentro_de_worktree(os.path.join(WT, "memory", "nova.md"), DISCO.get) == WT, \
        "arquivo novo dentro do worktree passou"
    assert mod.dentro_de_worktree(WT, DISCO.get) == WT, "a raiz do worktree passou"
    assert not mod.dentro_de_worktree(os.path.join(PRINCIPAL, "memory", "nova.md"), DISCO.get), \
        "pasta principal virou worktree"
    assert not mod.dentro_de_worktree(os.path.join(SOLTA, "a.txt"), DISCO.get), "pasta fora de repo virou worktree"


def test_submodulo_nao_e_worktree(mod):
    assert not mod.dentro_de_worktree(os.path.join(SUB, "a.py"), DISCO.get)


# --- criar ou entrar em worktree: negado sempre ----------------------------------------------------------

@pytest.mark.parametrize("entrada", [{"name": "partida"}, {"path": ".claude/worktrees/partida"}, {}])
def test_enter_worktree_e_negado(mod, entrada):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "EnterWorktree", "cwd": PRINCIPAL, "tool_input": entrada}
    tipo, motivo = _avaliar(mod, ev)
    assert tipo == "deny"
    assert "pasta principal" in motivo and "main" in motivo, "a negação não diz onde trabalhar"


def test_subagente_isolado_e_negado_e_o_comum_passa(mod):
    base = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": PRINCIPAL}
    assert _avaliar(mod, {**base, "tool_input": {"prompt": "x", "isolation": "worktree"}})[0] == "deny"
    assert _avaliar(mod, {**base, "tool_input": {"prompt": "x"}}) == (None, None)


def test_worktree_create_sai_sem_caminho_ate_com_o_escape(mod):
    ev = {"hook_event_name": "WorktreeCreate", "name": "bold-oak-a3f2", "cwd": PRINCIPAL}
    assert _avaliar(mod, ev, {"MSS_WORKTREE_OFF": "1"}) == (None, None)
    impresso, erro, codigo = mod.saida(ev, None, None)
    assert impresso is None, "saiu caminho no stdout — o Claude Code criaria o worktree"
    assert codigo == 2 and "worktree" in erro.lower()


# --- gravar dentro de um worktree: negado --------------------------------------------------------------

@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
def test_gravar_no_worktree_e_negado(mod, tool):
    tipo, motivo = _avaliar(mod, _escrita(os.path.join(WT, "memory", "MEMORY.md"), tool=tool))
    assert tipo == "deny", f"{tool} gravou dentro do worktree"
    assert WT in motivo, "a negação não diz qual worktree"


def test_caminho_relativo_e_resolvido_pela_pasta_do_evento(mod):
    assert _avaliar(mod, _escrita("memory/MEMORY.md", cwd=WT))[0] == "deny"
    ev = _escrita("memory/MEMORY.md") | {"cwd": None}
    assert _avaliar(mod, ev) == (None, None), "sem cwd no evento, vale a pasta do processo"


def test_notebook_no_worktree_e_negado(mod):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "NotebookEdit", "cwd": PRINCIPAL,
          "tool_input": {"notebook_path": os.path.join(WT, "a.ipynb")}}
    assert _avaliar(mod, ev)[0] == "deny"


def test_gravar_na_pasta_principal_passa(mod):
    assert _avaliar(mod, _escrita(os.path.join(PRINCIPAL, "memory", "MEMORY.md"))) == (None, None)


def test_escape_do_owner_libera_a_gravacao(mod):
    assert _avaliar(mod, _escrita(os.path.join(WT, "a.md")), {"MSS_WORKTREE_OFF": "1"}) == (None, None)


def test_disco_ilegivel_libera_a_gravacao(mod):
    def quebrado(_pasta):
        raise OSError("sem permissão")
    tipo, _, _ = mod.regra(_escrita(os.path.join(WT, "a.md")), {}, quebrado, SOLTA)
    assert tipo is None, "cerca com defeito não pode parar a gravação legítima"


# --- abrir ou passar conversa a partir desta: negado, com o texto pronto ------------------------------

@pytest.mark.parametrize("tool,entrada", [
    (ABRIR_CONVERSA, {"initiation": "user_asked", "title": "x", "prompt": "y", "use_worktree": False}),
    (ABRIR_CONVERSA, {"initiation": "own_initiative", "title": "x", "prompt": "y"}),
    (ABRIR_CONVERSA, {"initiation": "offer", "title": "x"}),
    (PASSAR_CONVERSA, {"title": "x", "remaining_plan": "y"}),
])
def test_abrir_conversa_a_partir_desta_e_negado(mod, tool, entrada):
    ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": PRINCIPAL, "tool_input": entrada}
    tipo, motivo = _avaliar(mod, ev)
    assert tipo == "deny", f"abriu conversa por {tool} {entrada}"
    assert "texto pronto" in motivo.lower() and "+" in motivo, "a negação não manda entregar o texto pronto pro +"


def test_escape_do_owner_libera_a_conversa(mod):
    ev = {"hook_event_name": "PreToolUse", "tool_name": ABRIR_CONVERSA, "cwd": PRINCIPAL,
          "tool_input": {"initiation": "offer", "title": "x"}}
    assert _avaliar(mod, ev, {"MSS_WORKTREE_OFF": "1"}) == (None, None)


def test_outras_ferramentas_passam_caladas(mod):
    for tool in ("Read", "Bash", "mcp__ccd_session__dismiss_task"):
        ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": PRINCIPAL, "tool_input": {}}
        assert _avaliar(mod, ev) == (None, None), tool


def test_registro_guarda_o_que_negou_e_o_que_avisou(mod):
    _, _, negou = mod.regra(_escrita(os.path.join(WT, "a.md")), {}, DISCO.get, SOLTA)
    _, _, avisou = mod.regra({"hook_event_name": "SessionStart", "cwd": WT}, {}, DISCO.get, SOLTA)
    assert negou["anotacoes"] == [("negou", "Write em worktree")]
    assert avisou["anotacoes"] == [("avisou", "abertura em worktree")]


# --- conversa que já começa dentro de um worktree: aviso na abertura ------------------------------------

def test_abertura_dentro_de_worktree_avisa(mod):
    tipo, texto = _avaliar(mod, {"hook_event_name": "SessionStart", "cwd": WT})
    assert tipo == "avisa"
    assert "worktree" in texto.lower() and "pasta principal" in texto


def test_abertura_na_pasta_principal_e_calada(mod):
    assert _avaliar(mod, {"hook_event_name": "SessionStart", "cwd": PRINCIPAL}) == (None, None)


# --- a saída: os dois protocolos do deny, o aviso e o silêncio ------------------------------------------

def test_saida_nega_pelos_dois_protocolos(mod):
    impresso, erro, codigo = mod.saida({"hook_event_name": "PreToolUse"}, "deny", "BLOQUEADO — worktree")
    saida = json.loads(impresso)["hookSpecificOutput"]
    assert saida == {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                     "permissionDecisionReason": "BLOQUEADO — worktree"}
    assert erro == "BLOQUEADO — worktree" and codigo == 2


def test_saida_avisa_na_abertura_e_cala_quando_libera(mod):
    impresso, erro, codigo = mod.saida({"hook_event_name": "SessionStart"}, "avisa", "começou num worktree")
    saida = json.loads(impresso)
    assert saida["hookSpecificOutput"] == {"hookEventName": "SessionStart", "additionalContext": "começou num worktree"}
    assert saida["systemMessage"] == "começou num worktree" and erro is None and codigo == 0
    assert mod.saida({"hook_event_name": "PreToolUse"}, None, None) == (None, None, 0)
    assert mod.saida(None, None, None) == (None, None, 0)


# --- o disco de verdade e o processo (pasta montada uma vez) ------------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    """Um repositório de mentira no disco: `.git` pasta na principal, `.git` arquivo no worktree e no submódulo — o
    hook só lê esses arquivos, nunca roda o git."""
    principal = tmp_path_factory.mktemp("sem_worktree") / "kit"
    (principal / ".git").mkdir(parents=True)
    wt = principal / ".claude" / "worktrees" / "partida-em-dois-niveis"
    wt.mkdir(parents=True)
    (wt / ".git").write_text(f"gitdir: {principal.as_posix()}/.git/worktrees/partida-em-dois-niveis\n", encoding="utf-8")
    sub = principal / "vendor" / "lib"
    sub.mkdir(parents=True)
    (sub / ".git").write_text("gitdir: ../../.git/modules/vendor/lib\n", encoding="utf-8")
    return principal, wt, sub


def test_casca_le_o_git_do_disco(mod, pasta):
    principal, wt, sub = pasta
    assert mod.avaliar(_escrita(wt / "memory" / "MEMORY.md", principal), ambiente={})[0] == "deny"
    assert mod.avaliar({"hook_event_name": "SessionStart", "cwd": str(wt)}, ambiente={})[0] == "avisa"
    assert mod.avaliar(_escrita(principal / "memory" / "MEMORY.md", principal), ambiente={}) == (None, None)
    assert mod.avaliar(_escrita(sub / "a.py", principal), ambiente={}) == (None, None)
    assert mod.dentro_de_worktree(str(wt / "a.md")) == str(wt), "o padrão de dentro_de_worktree não é o disco"


def test_processo_worktree_create_falha_ate_com_o_escape(pasta):
    principal, _, _ = pasta
    ev = {"hook_event_name": "WorktreeCreate", "name": "bold-oak-a3f2", "cwd": str(principal)}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True,
                          text=True, encoding="utf-8", env={**os.environ, "MSS_WORKTREE_OFF": "1"}, timeout=30)
    assert proc.returncode == 2, "worktree criado com o escape"
    assert proc.stdout.strip() == "", "saiu caminho no stdout — o Claude Code criaria o worktree"
    assert "worktree" in proc.stderr.lower()


def test_registrado_no_hooks_json():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]

    def comandos(evento):
        return [(g.get("matcher", ""), h["command"]) for g in cfg.get(evento, []) for h in g["hooks"]
                if "sem_worktree.py" in h["command"]]
    assert comandos("WorktreeCreate"), "WorktreeCreate não registrado"
    assert comandos("SessionStart"), "SessionStart não registrado"
    matchers = " ".join(m for m, _ in comandos("PreToolUse")).split("|")
    for tool in ("EnterWorktree", "Agent", "Write", "Edit", "MultiEdit", "NotebookEdit",
                 ABRIR_CONVERSA, PASSAR_CONVERSA):
        assert tool in matchers, f"PreToolUse do sem_worktree.py não cobre {tool}"


# --- shell (5ª cerca do git_publicacao.py), com o .git lido do disco de mentira ----------------------------

@pytest.fixture()
def cerca(mod, monkeypatch):
    """A 5ª cerca do `git_publicacao.py` em memória: ela importa `dentro_de_worktree` deste hook, e a leitura do
    `.git` (`_marca_no_disco`) vira o disco de mentira."""
    monkeypatch.setitem(sys.modules, "sem_worktree", mod)
    monkeypatch.setattr(mod, "_marca_no_disco", DISCO.get)
    gp = _carregar(GIT_PUBLICACAO, "git_publicacao")

    def decidir(comando, **amb):
        motivo, _ = gp._decidir_worktree(comando, amb, PRINCIPAL)
        return motivo
    return decidir


@pytest.mark.parametrize("comando", [
    "git worktree add .claude/worktrees/x -b feature/x",
    "cd /tmp && git worktree add ../x",
    "git -C . worktree add -q ../x main",
])
def test_shell_criar_worktree_e_negado(cerca, comando):
    motivo = cerca(comando)
    assert motivo and "worktree" in motivo.lower(), f"passou: {comando}"


def test_shell_gravar_dentro_de_worktree_e_negado(cerca):
    for comando in (f'git -C "{WT}" commit -m x', f'cd "{WT}" && git add a.txt',
                    f'echo x > "{os.path.join(WT, "memory", "a.md")}"'):
        assert cerca(comando), f"passou: {comando}"


def test_shell_leitura_e_pasta_principal_passam(cerca):
    for comando in ("git worktree list", f'git -C "{WT}" status', "git commit -m x",
                    "grep 'git worktree add' docs/x.md"):
        assert cerca(comando) is None, f"negou: {comando}"


def test_shell_escape_do_owner(cerca):
    assert cerca("git worktree add ../x", MSS_WORKTREE_OFF="1") is None


# --- o texto do kit parou de mandar abrir worktree ------------------------------------------------------

def test_kit_nao_manda_mais_abrir_worktree():
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    um_item = (REPO / "hooks" / "um_item_por_janela.py").read_text(encoding="utf-8")
    for nome, texto in (("nova-feature.md", nova), ("um_item_por_janela.py", um_item)):
        assert "using-git-worktrees" not in texto, f"{nome} ainda manda usar worktree"
        assert "num worktree" not in texto, f"{nome} ainda manda abrir num worktree"
    aviso = _carregar(REPO / "hooks" / "um_item_por_janela.py", "um_item_por_janela").AVISO.lower()
    assert "pergunte ao owner" in aviso, "aviso não manda parar e perguntar quando a pasta está em outra feature"
