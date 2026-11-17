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

Camadas (2026-11-17): a REGRA é testada sem disco e sem git — os caminhos não existem e a resposta do git
("que repositório é este?") vem pronta no lugar de `_repo_de`. O git de verdade fica só no teste de `_repo_de`
(a conversa com o git), no fim do arquivo, com um repositório montado uma vez.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "git_publicacao.py"

BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
ANCORA, OUTRO, SOLTO, WT = BASE / "kit", BASE / "whats", BASE / "downloads", BASE / "wt"
REPOS = {ANCORA: "repo-kit", OUTRO: "repo-whats", WT: "repo-kit"}   # o worktree é do mesmo repositório


def _norm(caminho):
    return os.path.normcase(os.path.realpath(caminho))


def _repo_de_falso(caminho):
    for raiz, comum in REPOS.items():
        try:
            if os.path.commonpath([_norm(caminho), _norm(raiz)]) == _norm(raiz):
                return comum, str(raiz)
        except ValueError:
            continue
    return None, None


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("git_publicacao", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def cenario(mod, monkeypatch):
    monkeypatch.setattr(mod, "_repo_de", _repo_de_falso)
    return ANCORA, OUTRO, SOLTO


def _outro_projeto(mod, comando, ancora, **amb):
    """A regra desta cerca: o motivo da negação, ou None."""
    ev = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(ancora)}
    return mod._decidir_outro_projeto(ev, comando, {"CLAUDE_PROJECT_DIR": str(ancora), **amb}, str(ancora))[0]


# --- AC1: git de escrita no outro repo → nega ---------------------------------------------------

@pytest.mark.parametrize("modelo", [
    'git -C "{o}" commit -m x',
    'cd "{o}" && git add a.txt && git commit -m x',
    'cd "{o}" && git checkout -q -b chore/partida-enxuta main',
    'git -C "{o}" branch feature/x',
    'git -C "{o}" merge --no-ff chore/x -m "Merge"',
    'git -C "{o}" reset --hard HEAD~1',
])
def test_git_que_grava_no_outro_projeto_e_negado(mod, cenario, modelo):
    ancora, outro, _ = cenario
    motivo = _outro_projeto(mod, modelo.format(o=outro), ancora)
    assert motivo is not None, f"passou: {modelo}"
    assert str(outro) in motivo or outro.name in motivo, "a mensagem não diz qual é o outro projeto"


def test_mensagem_traz_o_comando_exato_pra_colar_la(mod, cenario):
    ancora, outro, _ = cenario
    comando = f'cd "{outro}" && git checkout -q -b chore/x main'
    motivo = _outro_projeto(mod, comando, ancora)
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
def test_leitura_e_escrita_fora_de_outro_repo_passam(mod, cenario, modelo):
    ancora, outro, solto = cenario
    assert _outro_projeto(mod, modelo.format(o=outro, a=ancora, s=solto), ancora) is None, f"barrou: {modelo}"


def test_worktree_do_mesmo_repo_nao_e_outro_projeto(mod, cenario):
    ancora, _, _ = cenario
    # gravar em worktree é negado por OUTRA cerca desde a 0.46.0 (test_hook_sem_worktree.py); aqui só esta
    assert _outro_projeto(mod, f'git -C "{WT}" commit -m x', ancora) is None


# --- AC3: script do kit e redirecionamento ------------------------------------------------------

def test_proj_com_aplicar_no_outro_projeto_e_negado(mod, cenario):
    ancora, outro, _ = cenario
    assert _outro_projeto(mod, f'python templates/rodizio_partida.py enxugar --proj "{outro}" --aplicar', ancora)


def test_proj_sem_aplicar_e_dry_run_e_passa(mod, cenario):
    ancora, outro, _ = cenario
    assert _outro_projeto(mod, f'python templates/rodizio_partida.py enxugar --proj "{outro}"', ancora) is None


@pytest.mark.parametrize("modelo", ['echo x > "{o}/a.txt"', 'echo x >> "{o}/a.txt"', 'echo x | tee -a "{o}/a.txt"'])
def test_redirecionar_pra_dentro_do_outro_projeto_e_negado(mod, cenario, modelo):
    ancora, outro, _ = cenario
    assert _outro_projeto(mod, modelo.format(o=outro), ancora) is not None


def test_corpo_de_heredoc_nao_conta(mod, cenario):
    ancora, outro, _ = cenario
    comando = f"cat > nota.txt <<'EOF'\nexemplo: echo x > \"{outro}/a.txt\"\nEOF"
    assert _outro_projeto(mod, comando, ancora) is None


@pytest.mark.skipif(os.name != "nt", reason="caminho /c/... do Git Bash só existe no Windows")
def test_caminho_do_git_bash_e_reconhecido(mod, cenario):
    ancora, outro, _ = cenario
    posix = "/" + str(outro)[0].lower() + str(outro)[2:].replace("\\", "/")
    assert _outro_projeto(mod, f'cd "{posix}" && git commit -m x', ancora) is not None


# --- AC4: escape e precedência ------------------------------------------------------------------

def test_escape_do_owner(mod, cenario):
    ancora, outro, _ = cenario
    assert _outro_projeto(mod, f'git -C "{outro}" commit -m x', ancora, MSS_ANCORA_OFF="1") is None


def test_negar_vence_o_pedido_de_aprovacao_do_merge(mod, cenario):
    """Merge na âncora pede aprovação; no outro projeto, nega. Passa por `avaliar` (a ordem das cercas)."""
    ancora, outro, _ = cenario

    def _avaliar(comando):
        ev = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(ancora)}
        amb = {"CLAUDE_PROJECT_DIR": str(ancora), "MSS_PASTA_BRANCH_OFF": "1", "MSS_MEMORIA_ACAO_OFF": "1"}
        return mod.avaliar(ev, amb, git_destino=lambda p: ("feature/x", None))[0]

    assert _avaliar("git merge feature/x") == "ask"
    assert _avaliar(f'git -C "{outro}" merge feature/x') == "deny"


# --- A conversa com o git: `_repo_de` com git de verdade (repositório montado uma vez) ------------

def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture(scope="module")
def repos_de_verdade(tmp_path_factory):
    base = tmp_path_factory.mktemp("repo_de")
    kit, outro, solto, wt = base / "kit", base / "whats", base / "downloads", base / "wt"
    for repo in (kit, outro):
        repo.mkdir()
        _git("init", "-q", "--template=", "-b", "main", cwd=repo)
        _git("-c", "user.email=a@b", "-c", "user.name=a", "commit", "-q", "--allow-empty", "-m", "i", cwd=repo)
    solto.mkdir()
    _git("worktree", "add", "-q", str(wt), "-b", "feature/y", cwd=kit)
    return kit, outro, solto, wt


def test_repo_de_distingue_repositorio_worktree_e_pasta_solta(mod, repos_de_verdade):
    kit, outro, solto, wt = repos_de_verdade
    comum_kit, raiz_kit = mod._repo_de(str(kit / "pasta" / "que-nao-existe"))
    assert comum_kit and _norm(raiz_kit) == _norm(kit), "não subiu até a pasta que existe"
    assert mod._repo_de(str(outro))[0] not in (None, comum_kit), "outro repositório não foi distinguido"
    assert mod._repo_de(str(wt))[0] == comum_kit, "worktree do mesmo repositório virou outro projeto"
    assert mod._repo_de(str(solto)) == (None, None), "pasta fora de repositório virou projeto"
