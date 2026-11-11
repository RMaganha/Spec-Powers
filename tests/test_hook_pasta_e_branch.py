"""Duas conversas na mesma pasta não trocam a branch uma da outra — 6ª cerca do `git_publicacao.py` (0.59.0).

Nasceu do caso F-059 (`docs/EVALS.md`, 2026-11-11): `git status -sb && git switch -c feature/…` num comando só,
com a pasta na branch `chore/todo-conversa-nova-se-perde` de OUTRA conversa e mudança por commitar. A branch
nasceu ali, o commit da outra conversa caiu nela e, ao "devolver" a pasta, as duas conversas a moveram ao mesmo
tempo. A regra existia em prosa (memória + passo 0 do `nova-feature`) e desde a 0.57.0 havia um aviso de uma vez
por conversa — só para criar branch, e que passa na repetição.

Propriedades (spec `docs/specs/conversa-nova-nao-se-perde.md`, critérios 7 e 8):
- pasta na principal (`main`/`master`), ou numa branch que ESTA conversa abriu → criar e trocar passam calados;
- criar branch com a pasta fora da principal (sem dizer que ela sai da principal) → **nega**;
- trocar de branch numa branch que a conversa não abriu: mudança por commitar → **nega**; pasta limpa → **pede a
  aprovação do owner** (decisão dele, 2026-11-11: "fica o clique");
- `git checkout <arquivo>` e `git checkout -- <arquivo>` não são troca de branch;
- sem número de conversa não age; falha ABERTA; escape só do owner: `MSS_PASTA_BRANCH_OFF=1`.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "git_publicacao.py"
MODULO = REPO / "hooks" / "_pasta_e_branch.py"


def _mod():
    spec = importlib.util.spec_from_file_location("git_publicacao", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pb():
    spec = importlib.util.spec_from_file_location("_pasta_e_branch", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pasta(tmp_path, atual="main", outras=("feature/de-outra",)):
    """Pasta com um `.git` de mentira: só o que a cerca lê (HEAD e os nomes das branches)."""
    raiz = tmp_path / "proj"
    (raiz / ".git" / "refs" / "heads").mkdir(parents=True)
    for nome in {atual, "main", *outras}:
        ref = raiz / ".git" / "refs" / "heads" / nome
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text("0" * 40 + "\n", encoding="utf-8")
    (raiz / ".git" / "HEAD").write_text(f"ref: refs/heads/{atual}\n", encoding="utf-8")
    (raiz / "app.py").write_text("x = 1\n", encoding="utf-8")
    return raiz


def _amb(tmp_path):
    """Estado por conversa no TEMP do teste; a memória de ação fica fora (é outra cerca, com teste próprio)."""
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path), "MSS_MEMORIA_ACAO_OFF": "1",
            "MSS_ANCORA_OFF": "1"}


def _evento(comando, raiz, sessao, tool="Bash"):
    return {"hook_event_name": "PreToolUse", "cwd": str(raiz), "session_id": sessao,
            "tool_name": tool, "tool_input": {"command": comando}}


def _nova():
    return "s-" + uuid.uuid4().hex[:8]


def _avaliar(comando, raiz, sessao, amb, sujo=False):
    pb = _pb()
    return pb.avaliar(comando, str(raiz), sessao, amb, sujo=lambda pasta: sujo)


# --- critério 8: na principal, ou na branch que a conversa abriu, passa ---------------------------------

def test_criar_branch_na_principal_passa(tmp_path):
    raiz, amb = _pasta(tmp_path, "main"), _amb(tmp_path)
    assert _avaliar("git switch -c feature/nova", raiz, _nova(), amb) == (None, None, None)
    assert _avaliar("git checkout -b feature/nova", raiz, _nova(), amb) == (None, None, None)


def test_branch_que_a_conversa_abriu_e_dela(tmp_path):
    """Abriu na principal → a branch fica sendo desta conversa: voltar pra principal passa calado."""
    amb, s = _amb(tmp_path), _nova()
    raiz = _pasta(tmp_path, "main")
    assert _avaliar("git switch -c feature/minha", raiz, s, amb)[0] is None
    (raiz / ".git" / "HEAD").write_text("ref: refs/heads/feature/minha\n", encoding="utf-8")
    assert _avaliar("git switch main", raiz, s, amb, sujo=True) == (None, None, None), \
        "a conversa foi barrada na branch que ela mesma abriu"
    assert _avaliar("git checkout main", raiz, s, amb) == (None, None, None)


def test_outra_conversa_nao_herda_a_branch(tmp_path):
    amb = _amb(tmp_path)
    raiz = _pasta(tmp_path, "main")
    _avaliar("git switch -c feature/minha", raiz, "conversa-1", amb)
    (raiz / ".git" / "HEAD").write_text("ref: refs/heads/feature/minha\n", encoding="utf-8")
    tipo, motivo, _ = _avaliar("git switch main", raiz, "conversa-2", amb)
    assert tipo == "ask", "a conversa 2 trocou calada a branch que a conversa 1 abriu"
    assert "feature/minha" in motivo


# --- critério 7: pasta numa branch que a conversa não abriu ---------------------------------------------

def test_caso_f059_criar_branch_na_branch_de_outra_conversa_e_negado(tmp_path):
    """A sequência real: pasta em `chore/todo-conversa-nova-se-perde`, com mudança, e `git switch -c feature/…`."""
    raiz, amb = _pasta(tmp_path, "chore/todo-conversa-nova-se-perde"), _amb(tmp_path)
    tipo, motivo, _ = _avaliar("git status -sb && git switch -c feature/memoria-em-tabela-parte-2", raiz, _nova(),
                               amb, sujo=True)
    assert tipo == "deny", "a branch nasceu em cima da branch de outra conversa (F-059)"
    assert "chore/todo-conversa-nova-se-perde" in motivo, "o motivo não diz em que branch a pasta está"
    assert "pergunte ao owner" in motivo.lower()
    assert "MSS_PASTA_BRANCH_OFF" in motivo


def test_criar_dizendo_que_sai_da_principal_vira_troca(tmp_path):
    """`git switch -c x main` nasce da principal, mas tira a pasta da branch da outra conversa: é troca."""
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    assert _avaliar("git switch -c feature/x main", raiz, _nova(), amb, sujo=True)[0] == "deny"
    assert _avaliar("git checkout -b feature/x origin/main", raiz, _nova(), amb, sujo=False)[0] == "ask"


def test_trocar_com_mudanca_pendente_e_negado(tmp_path):
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    for comando in ("git switch main", "git checkout main", "git switch -", "git checkout feature/de-outra~0"):
        tipo, motivo, _ = _avaliar(comando, raiz, _nova(), amb, sujo=True)
        assert tipo == "deny", f"`{comando}` trocou a branch com mudança de outra conversa por commitar"
        assert "por commitar" in motivo


def test_trocar_com_a_pasta_limpa_pergunta_ao_owner(tmp_path):
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    tipo, motivo, _ = _avaliar("git switch main", raiz, _nova(), amb, sujo=False)
    assert tipo == "ask", "troca com a pasta limpa não pediu a aprovação do owner (decisão de 2026-11-11)"
    assert "feature/de-outra" in motivo and "outra conversa" in motivo


def test_sem_saber_se_ha_mudanca_pergunta(tmp_path):
    """O git não respondeu: não dá pra afirmar que está limpa nem negar por mudança que não se viu."""
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)

    def quebrado(pasta):
        raise OSError("git não respondeu")

    assert _pb().avaliar("git switch main", str(raiz), _nova(), amb, sujo=quebrado)[0] == "ask"


# --- o que não é troca de branch ------------------------------------------------------------------------

@pytest.mark.parametrize("comando", [
    "git checkout app.py",                      # restaura arquivo
    "git checkout -- app.py",
    "git checkout main -- app.py",              # arquivo de outra branch, sem trocar
    "git checkout -p",
    "git checkout",
    "git switch feature/de-outra",              # já está nela
    "git status -sb",
    "git commit -m \"git switch main\"",        # o texto da mensagem não é comando
    "echo git switch main",
    "git branch --show-current",
    "git stash list",
])
def test_nao_e_troca_de_branch(tmp_path, comando):
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    assert _avaliar(comando, raiz, _nova(), amb, sujo=True) == (None, None, None), f"`{comando}` foi barrado"


def test_powershell_tambem(tmp_path):
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    assert _avaliar("git status -sb; git switch -c feature/x", raiz, _nova(), amb)[0] == "deny"


def test_git_c_e_cd_apontam_a_pasta(tmp_path):
    """A pasta é a do `-C`, ou a do último `cd` antes do comando — não o cwd do evento."""
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    fora = tmp_path / "fora"
    fora.mkdir()
    pb = _pb()
    limpo = lambda pasta: False                                                    # noqa: E731
    assert pb.avaliar(f'git -C "{raiz}" switch main', str(fora), _nova(), amb, sujo=limpo)[0] == "ask"
    assert pb.avaliar(f'cd "{raiz}" && git switch main', str(fora), _nova(), amb, sujo=limpo)[0] == "ask"


# --- garantias ------------------------------------------------------------------------------------------

def test_sem_numero_de_conversa_nao_age(tmp_path):
    raiz, amb = _pasta(tmp_path, "feature/de-outra"), _amb(tmp_path)
    assert _avaliar("git switch -c feature/x", raiz, None, amb, sujo=True) == (None, None, None)


def test_escape_do_owner(tmp_path):
    raiz = _pasta(tmp_path, "feature/de-outra")
    amb = {**_amb(tmp_path), "MSS_PASTA_BRANCH_OFF": "1"}
    assert _avaliar("git switch -c feature/x", raiz, _nova(), amb, sujo=True) == (None, None, None)


def test_pasta_sem_git_ou_head_solto_libera(tmp_path):
    amb = _amb(tmp_path)
    sem_git = tmp_path / "sem-git"
    sem_git.mkdir()
    assert _avaliar("git switch -c feature/x", sem_git, _nova(), amb, sujo=True) == (None, None, None)
    raiz = _pasta(tmp_path, "feature/de-outra")
    (raiz / ".git" / "HEAD").write_text("0" * 40 + "\n", encoding="utf-8")       # HEAD destacado
    assert _avaliar("git switch main", raiz, _nova(), amb, sujo=True) == (None, None, None)


# --- dentro do hook de verdade --------------------------------------------------------------------------

def test_o_hook_nega_e_pergunta(tmp_path):
    mod, amb = _mod(), _amb(tmp_path)
    raiz = _pasta(tmp_path, "feature/de-outra")
    tipo, motivo = mod.avaliar(_evento("git switch -c feature/x", raiz, _nova()), amb)
    assert tipo == "deny" and "feature/de-outra" in motivo
    tipo, _ = mod.avaliar(_evento("git switch -c feature/x", raiz, _nova(), tool="PowerShell"), amb)
    assert tipo == "deny"


def test_merge_aprovado_nao_perde_a_pergunta(tmp_path):
    """Negar vence perguntar: `git merge` (pergunta) junto de criar branch na branch de outra conversa (nega)."""
    mod, amb = _mod(), _amb(tmp_path)
    raiz = _pasta(tmp_path, "feature/de-outra")
    tipo, motivo = mod.avaliar(_evento("git merge --no-ff x && git switch -c feature/y", raiz, _nova()), amb)
    assert tipo == "deny" and "feature/de-outra" in motivo


@pytest.mark.skipif(not shutil.which("git"), reason="precisa do git pra ver a mudança por commitar")
def test_processo_com_git_de_verdade(tmp_path):
    """Ponta a ponta: repositório real, branch de outra conversa, arquivo modificado → o processo nega; com a
    pasta limpa → devolve `ask` e sai 0 (o `ask` só vale com saída 0)."""
    raiz = tmp_path / "real"
    raiz.mkdir()

    def git(*args):
        subprocess.run(["git", "-C", str(raiz), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                       check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    (raiz / "a.txt").write_text("1\n", encoding="utf-8")
    git("add", "a.txt")
    git("commit", "-q", "-m", "c1")
    git("switch", "-q", "-c", "feature/de-outra")
    env = {**__import__("os").environ, "TEMP": str(tmp_path), "TMP": str(tmp_path), "MSS_MEMORIA_ACAO_OFF": "1",
           "MSS_ANCORA_OFF": "1", "MSS_REGISTRO_OFF": "1", "CLAUDE_PROJECT_DIR": str(raiz)}

    def rodar():
        return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento("git switch main", raiz, "s-real")),
                              capture_output=True, text=True, encoding="utf-8", env=env)

    limpo = rodar()
    assert limpo.returncode == 0, limpo.stderr
    assert json.loads(limpo.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"
    (raiz / "a.txt").write_text("2\n", encoding="utf-8")
    sujo = rodar()
    assert sujo.returncode == 2
    assert json.loads(sujo.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_documentado_no_readme_e_na_spec():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "_pasta_e_branch.py" in readme and "MSS_PASTA_BRANCH_OFF" in readme
    spec = (REPO / "docs" / "specs" / "conversa-nova-nao-se-perde.md").read_text(encoding="utf-8")
    assert "pedido de aprovação do owner" in spec
