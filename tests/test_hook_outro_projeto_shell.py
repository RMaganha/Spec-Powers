"""Cerca de outro projeto no SHELL — gravar em outro repositório a partir desta janela é negado.

Caso F-031: na janela do kit, o assistente enxugou o `CLAUDE.md`, o `MAPA.md` e o `INDEX.md` do Whats por
`cd <Whats> && git checkout -b … && git commit` e por script com `--proj` — a cerca da âncora só vigiava
Write/Edit, então nada barrou. Decisão do owner: NEGAR sempre e entregar o comando exato pra colar na janela
do outro projeto.

Contrato (no mesmo processo do `git_publicacao.py`, que já sabe achar a pasta do comando):
- "outro projeto" = um repositório git DIFERENTE do da âncora (`CLAUDE_PROJECT_DIR` › cwd). Pasta fora de
  repo e worktree do mesmo repo não são outro projeto;
- grava = git de escrita (`add`, `commit`, `checkout`, `switch`, `branch <nome>`, `merge`, `rebase`, `reset`,
  `stash`, `push`…) na pasta de `-C` › último `cd` › cwd; `--proj <dir>` junto de `--aplicar`; `>`/`>>`/`tee`
  pra um caminho lá dentro (corpo de heredoc não conta);
- leitura (`status`, `log`, `diff`, `branch --show-current`) segue livre;
- a mensagem traz a raiz do outro projeto e o comando VERBATIM pra colar lá;
- negar vence o "pedir aprovação" da cerca de publicação; falha ABERTA; escape `MSS_ANCORA_OFF=1`;
- brecha declarada: script que grava com o caminho escrito DENTRO dele não aparece no comando.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "git_publicacao.py"


def _mod():
    spec = importlib.util.spec_from_file_location("git_publicacao", HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def cenario(tmp_path):
    ancora, outro, solto = tmp_path / "kit", tmp_path / "whats", tmp_path / "downloads"
    for repo in (ancora, outro):
        repo.mkdir()
        _git("init", "-q", "-b", "main", cwd=repo)
        _git("-c", "user.email=a@b", "-c", "user.name=a", "commit", "-q", "--allow-empty", "-m", "i", cwd=repo)
    solto.mkdir()
    return ancora, outro, solto


def _avaliar(comando, ancora, **amb):
    ev = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(ancora)}
    return _mod().avaliar(ev, {"CLAUDE_PROJECT_DIR": str(ancora), **amb}, git_destino=lambda p: ("feature/x", None))


# --- AC1: git de escrita no outro repo → nega ---------------------------------------------------

@pytest.mark.parametrize("modelo", [
    'git -C "{o}" commit -m x',
    'cd "{o}" && git add a.txt && git commit -m x',
    'cd "{o}" && git checkout -q -b chore/partida-enxuta main',
    'git -C "{o}" branch feature/x',
    'git -C "{o}" merge --no-ff chore/x -m "Merge"',
    'git -C "{o}" reset --hard HEAD~1',
])
def test_git_que_grava_no_outro_projeto_e_negado(cenario, modelo):
    ancora, outro, _ = cenario
    tipo, motivo = _avaliar(modelo.format(o=outro), ancora)
    assert tipo == "deny", f"passou: {modelo}"
    assert str(outro) in motivo or outro.name in motivo, "a mensagem não diz qual é o outro projeto"


def test_mensagem_traz_o_comando_exato_pra_colar_la(cenario):
    ancora, outro, _ = cenario
    comando = f'cd "{outro}" && git checkout -q -b chore/x main'
    _, motivo = _avaliar(comando, ancora)
    assert comando in motivo, "a mensagem não traz o comando verbatim"
    assert "janela" in motivo and "MSS_ANCORA_OFF" in motivo


# --- AC2: leitura, âncora, worktree e pasta solta → livre ---------------------------------------

@pytest.mark.parametrize("modelo", [
    'cd "{o}" && git status --short && git log --oneline -3',
    'git -C "{o}" branch --show-current',
    'git -C "{o}" diff --stat',
    'git -C "{o}" tag --list',
    'git -C "{o}" stash list',
    'git -C "{a}" commit -m x',
    'echo x > "{s}/nota.txt"',
    'echo x 2>/dev/null',
])
def test_leitura_e_escrita_fora_de_outro_repo_passam(cenario, modelo):
    ancora, outro, solto = cenario
    tipo, _ = _avaliar(modelo.format(o=outro, a=ancora, s=solto), ancora)
    assert tipo is None, f"barrou: {modelo}"


def test_worktree_do_mesmo_repo_nao_e_outro_projeto(cenario, tmp_path):
    ancora, _, _ = cenario
    wt = tmp_path / "wt"
    _git("worktree", "add", "-q", str(wt), "-b", "feature/y", cwd=ancora)
    tipo, _ = _avaliar(f'git -C "{wt}" commit -m x', ancora)
    assert tipo is None


# --- AC3: script do kit e redirecionamento ------------------------------------------------------

def test_proj_com_aplicar_no_outro_projeto_e_negado(cenario):
    ancora, outro, _ = cenario
    tipo, _ = _avaliar(f'python templates/rodizio_partida.py enxugar --proj "{outro}" --aplicar', ancora)
    assert tipo == "deny"


def test_proj_sem_aplicar_e_dry_run_e_passa(cenario):
    ancora, outro, _ = cenario
    tipo, _ = _avaliar(f'python templates/rodizio_partida.py enxugar --proj "{outro}"', ancora)
    assert tipo is None


@pytest.mark.parametrize("modelo", ['echo x > "{o}/a.txt"', 'echo x >> "{o}/a.txt"', 'echo x | tee -a "{o}/a.txt"'])
def test_redirecionar_pra_dentro_do_outro_projeto_e_negado(cenario, modelo):
    ancora, outro, _ = cenario
    tipo, _ = _avaliar(modelo.format(o=outro), ancora)
    assert tipo == "deny"


def test_corpo_de_heredoc_nao_conta(cenario):
    ancora, outro, _ = cenario
    comando = f"cat > nota.txt <<'EOF'\nexemplo: echo x > \"{outro}/a.txt\"\nEOF"
    tipo, _ = _avaliar(comando, ancora)
    assert tipo is None


@pytest.mark.skipif(os.name != "nt", reason="caminho /c/... do Git Bash só existe no Windows")
def test_caminho_do_git_bash_e_reconhecido(cenario):
    ancora, outro, _ = cenario
    posix = "/" + str(outro)[0].lower() + str(outro)[2:].replace("\\", "/")
    tipo, _ = _avaliar(f'cd "{posix}" && git commit -m x', ancora)
    assert tipo == "deny"


# --- AC4: escape e precedência ------------------------------------------------------------------

def test_escape_do_owner(cenario):
    ancora, outro, _ = cenario
    tipo, _ = _avaliar(f'git -C "{outro}" commit -m x', ancora, MSS_ANCORA_OFF="1")
    assert tipo is None


def test_negar_vence_o_pedido_de_aprovacao_do_merge(cenario):
    """Merge na âncora pede aprovação; no outro projeto, nega."""
    ancora, outro, _ = cenario
    assert _avaliar("git merge feature/x", ancora)[0] == "ask"
    assert _avaliar(f'git -C "{outro}" merge feature/x', ancora)[0] == "deny"
