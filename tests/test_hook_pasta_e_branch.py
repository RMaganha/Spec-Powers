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

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o repositório (branch atual e branches), os arquivos
da pasta, a mudança por commitar e as branches que cada conversa abriu ficam num objeto do teste e entram como
dado; os caminhos não existem. Dentro do `git_publicacao.py`, o leitor do repositório do módulo é trocado pelo de
memória, como no `test_hook_outro_projeto_shell.py`. O git de verdade fica num repositório montado uma vez: um teste
da leitura e gravação (HEAD, refs, a pasta, o `git status` e o estado da conversa) e um do processo.
"""
import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "git_publicacao.py"
MODULO = REPO / "hooks" / "_pasta_e_branch.py"
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
AMB = {"TEMP": str(BASE / "temp"), "TMP": str(BASE / "temp"), "TMPDIR": str(BASE / "temp"),
       "MSS_MEMORIA_ACAO_OFF": "1", "MSS_ANCORA_OFF": "1"}   # a memória de ação e a âncora são outras cercas


@pytest.fixture(scope="module")
def pb():
    spec = importlib.util.spec_from_file_location("_pasta_e_branch_teste", MODULO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _chave(caminho):
    return os.path.normcase(os.path.normpath(str(caminho)))


class Maquina:
    """O que a cerca lê do disco, em memória: os repositórios (branch atual e branches), os arquivos da pasta, as
    pastas com mudança por commitar e as branches que cada conversa abriu. `avaliar` faz o papel da casca."""

    def __init__(self, pb):
        self.pb, self.repos, self.arquivos, self.abertas = pb, {}, set(), {}

    def pasta(self, atual="main", outras=("feature/de-outra",), nome="proj"):
        raiz = BASE / nome
        self.repos[_chave(raiz)] = {"atual": atual, "branches": {atual, "main", *outras}}
        self.arquivos.add(_chave(raiz / "app.py"))
        return raiz

    def head(self, raiz, atual):
        self.repos[_chave(raiz)]["atual"] = atual

    def repo_de(self, pasta):
        d = Path(os.path.abspath(pasta))
        for p in (d, *d.parents):                     # sobe os pais, como o `_git_dir`
            r = self.repos.get(_chave(p))
            if r is not None:
                return _chave(p), r["atual"], lambda nome, r=r: nome in r["branches"]
        return None

    def avaliar(self, comando, cwd, sessao, ambiente=None, sujo=False):
        verifica = sujo if callable(sujo) else (lambda pasta: sujo)
        tipo, motivo, detalhe, lembradas = self.pb.regra(
            comando, str(cwd), sessao, AMB if ambiente is None else ambiente, self.repo_de,
            lambda chave: self.abertas.get((sessao, chave), set()), verifica, lambda c: _chave(c) in self.arquivos)
        for chave, branch in lembradas:
            self.abertas.setdefault((sessao, chave), set()).add(branch)
        return tipo, motivo, detalhe


@pytest.fixture()
def maq(pb):
    return Maquina(pb)


def _evento(comando, raiz, sessao, tool="Bash"):
    return {"hook_event_name": "PreToolUse", "cwd": str(raiz), "session_id": sessao,
            "tool_name": tool, "tool_input": {"command": comando}}


# --- critério 8: na principal, ou na branch que a conversa abriu, passa ---------------------------------

def test_criar_branch_na_principal_passa(maq):
    raiz = maq.pasta("main")
    assert maq.avaliar("git switch -c feature/nova", raiz, "s1") == (None, None, None)
    assert maq.avaliar("git checkout -b feature/nova", raiz, "s2") == (None, None, None)


def test_branch_que_a_conversa_abriu_e_dela(maq):
    """Abriu na principal → a branch fica sendo desta conversa: voltar pra principal passa calado."""
    raiz = maq.pasta("main")
    assert maq.avaliar("git switch -c feature/minha", raiz, "s")[0] is None
    maq.head(raiz, "feature/minha")
    assert maq.avaliar("git switch main", raiz, "s", sujo=True) == (None, None, None), \
        "a conversa foi barrada na branch que ela mesma abriu"
    assert maq.avaliar("git checkout main", raiz, "s") == (None, None, None)


def test_outra_conversa_nao_herda_a_branch(maq):
    raiz = maq.pasta("main")
    maq.avaliar("git switch -c feature/minha", raiz, "conversa-1")
    maq.head(raiz, "feature/minha")
    tipo, motivo, _ = maq.avaliar("git switch main", raiz, "conversa-2")
    assert tipo == "ask", "a conversa 2 trocou calada a branch que a conversa 1 abriu"
    assert "feature/minha" in motivo


# --- critério 7: pasta numa branch que a conversa não abriu ---------------------------------------------

def test_caso_f059_criar_branch_na_branch_de_outra_conversa_e_negado(maq):
    """A sequência real: pasta em `chore/todo-conversa-nova-se-perde`, com mudança, e `git switch -c feature/…`."""
    raiz = maq.pasta("chore/todo-conversa-nova-se-perde")
    tipo, motivo, _ = maq.avaliar("git status -sb && git switch -c feature/memoria-em-tabela-parte-2", raiz, "s",
                                  sujo=True)
    assert tipo == "deny", "a branch nasceu em cima da branch de outra conversa (F-059)"
    assert "chore/todo-conversa-nova-se-perde" in motivo, "o motivo não diz em que branch a pasta está"
    assert "pergunte ao owner" in motivo.lower()
    assert "MSS_PASTA_BRANCH_OFF" in motivo


def test_criar_dizendo_que_sai_da_principal_vira_troca(maq):
    """`git switch -c x main` nasce da principal, mas tira a pasta da branch da outra conversa: é troca."""
    raiz = maq.pasta("feature/de-outra")
    assert maq.avaliar("git switch -c feature/x main", raiz, "s1", sujo=True)[0] == "deny"
    assert maq.avaliar("git checkout -b feature/x origin/main", raiz, "s2", sujo=False)[0] == "ask"


def test_trocar_com_mudanca_pendente_e_negado(maq):
    raiz = maq.pasta("feature/de-outra")
    for comando in ("git switch main", "git checkout main", "git switch -", "git checkout feature/de-outra~0"):
        tipo, motivo, _ = maq.avaliar(comando, raiz, "s", sujo=True)
        assert tipo == "deny", f"`{comando}` trocou a branch com mudança de outra conversa por commitar"
        assert "por commitar" in motivo


def test_trocar_com_a_pasta_limpa_pergunta_ao_owner(maq):
    raiz = maq.pasta("feature/de-outra")
    tipo, motivo, _ = maq.avaliar("git switch main", raiz, "s", sujo=False)
    assert tipo == "ask", "troca com a pasta limpa não pediu a aprovação do owner (decisão de 2026-11-11)"
    assert "feature/de-outra" in motivo and "outra conversa" in motivo


def test_sem_saber_se_ha_mudanca_pergunta(maq):
    """O git não respondeu: não dá pra afirmar que está limpa nem negar por mudança que não se viu."""
    raiz = maq.pasta("feature/de-outra")

    def quebrado(pasta):
        raise OSError("git não respondeu")

    assert maq.avaliar("git switch main", raiz, "s", sujo=quebrado)[0] == "ask"


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
def test_nao_e_troca_de_branch(maq, comando):
    raiz = maq.pasta("feature/de-outra")
    assert maq.avaliar(comando, raiz, "s", sujo=True) == (None, None, None), f"`{comando}` foi barrado"


def test_powershell_tambem(maq):
    raiz = maq.pasta("feature/de-outra")
    assert maq.avaliar("git status -sb; git switch -c feature/x", raiz, "s")[0] == "deny"


def test_git_c_e_cd_apontam_a_pasta(maq):
    """A pasta é a do `-C`, ou a do último `cd` antes do comando — não o cwd do evento."""
    raiz = maq.pasta("feature/de-outra")
    fora = BASE / "fora"
    assert maq.avaliar(f'git -C "{raiz}" switch main', fora, "s1")[0] == "ask"
    assert maq.avaliar(f'cd "{raiz}" && git switch main', fora, "s2")[0] == "ask"


def test_branch_criada_fica_lembrada_desta_conversa_neste_repositorio(maq):
    raiz = maq.pasta("main")
    maq.avaliar("git switch -c feature/a", raiz, "s")
    assert maq.abertas == {("s", _chave(raiz)): {"feature/a"}}


# --- garantias ------------------------------------------------------------------------------------------

def test_sem_numero_de_conversa_nao_age(maq):
    raiz = maq.pasta("feature/de-outra")
    assert maq.avaliar("git switch -c feature/x", raiz, None, sujo=True) == (None, None, None)


def test_escape_do_owner(maq):
    raiz = maq.pasta("feature/de-outra")
    assert maq.avaliar("git switch -c feature/x", raiz, "s", {**AMB, "MSS_PASTA_BRANCH_OFF": "1"}, sujo=True) == \
        (None, None, None)


def test_pasta_sem_git_ou_head_solto_libera(maq):
    assert maq.avaliar("git switch -c feature/x", BASE / "sem-git", "s", sujo=True) == (None, None, None)
    raiz = maq.pasta("feature/de-outra")
    maq.head(raiz, None)                                                          # HEAD destacado
    assert maq.avaliar("git switch main", raiz, "s", sujo=True) == (None, None, None)


def test_defeito_ao_ler_o_repositorio_libera(maq, pb):
    def quebrado(pasta):
        raise OSError(".git ilegível")

    assert pb.regra("git switch main", str(BASE), "s", AMB, quebrado, lambda c: set(), lambda p: True,
                    lambda c: False)[:3] == (None, None, None)


# --- dentro do hook de verdade (o leitor do repositório trocado pelo de memória) --------------------------

@pytest.fixture()
def hook(maq, monkeypatch):
    """O `git_publicacao.py` importa o `_pasta_e_branch` pelo `sys.path`: troca-se o leitor do repositório desse
    módulo pelo de memória."""
    spec = importlib.util.spec_from_file_location("git_publicacao", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(importlib.import_module("_pasta_e_branch"), "_repo_do_disco", maq.repo_de)
    return mod


def test_o_hook_nega_e_pergunta(hook, maq):
    raiz = maq.pasta("feature/de-outra")
    tipo, motivo = hook.avaliar(_evento("git switch -c feature/x", raiz, "s1"), AMB)
    assert tipo == "deny" and "feature/de-outra" in motivo
    tipo, _ = hook.avaliar(_evento("git switch -c feature/x", raiz, "s2", tool="PowerShell"), AMB)
    assert tipo == "deny"


def test_merge_aprovado_nao_perde_a_pergunta(hook, maq):
    """Negar vence perguntar: `git merge` (pergunta) junto de criar branch na branch de outra conversa (nega)."""
    raiz = maq.pasta("feature/de-outra")
    tipo, motivo = hook.avaliar(_evento("git merge --no-ff x && git switch -c feature/y", raiz, "s"), AMB)
    assert tipo == "deny" and "feature/de-outra" in motivo


# --- o git de verdade: um repositório montado uma vez -----------------------------------------------------

def _git(raiz, *args):
    subprocess.run(["git", "-C", str(raiz), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


@pytest.fixture(scope="module")
def repo_real(tmp_path_factory):
    if not shutil.which("git"):
        pytest.skip("precisa do git")
    base = tmp_path_factory.mktemp("pasta_branch")
    raiz, temp = base / "real", base / "temp"
    raiz.mkdir()
    temp.mkdir()
    _git(raiz, "init", "-q", "--template=", "-b", "main")
    (raiz / "a.txt").write_text("1\n", encoding="utf-8")
    _git(raiz, "add", "a.txt")
    _git(raiz, "commit", "-q", "-m", "c1")
    _git(raiz, "switch", "-q", "-c", "feature/de-outra")
    return raiz, {"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}


def test_casca_le_o_repositorio_a_pasta_o_git_status_e_o_estado(pb, repo_real):
    raiz, amb = repo_real
    assert pb.avaliar("git switch main", str(raiz), "d1", amb)[0] == "ask", "HEAD ou git status reais não lidos"
    assert pb.avaliar("git checkout a.txt", str(raiz), "d1", amb) == (None, None, None), "arquivo real não visto"
    _git(raiz, "switch", "-q", "main")
    assert pb.avaliar("git switch -c feature/minha", str(raiz), "d1", amb) == (None, None, None)
    _git(raiz, "switch", "-q", "-c", "feature/minha")
    assert pb.avaliar("git switch main", str(raiz), "d1", amb) == (None, None, None), \
        "a branch aberta por esta conversa não foi gravada ou lida do disco"
    assert pb.avaliar("git switch main", str(raiz), "d2", amb)[0] == "ask"
    _git(raiz, "switch", "-q", "feature/de-outra")


def test_processo_com_git_de_verdade_nega_com_mudanca(repo_real):
    """Ponta a ponta: branch de outra conversa, arquivo modificado → o processo nega e sai 2."""
    raiz, amb = repo_real
    (raiz / "a.txt").write_text("2\n", encoding="utf-8")
    env = {**os.environ, **amb, "MSS_MEMORIA_ACAO_OFF": "1", "MSS_ANCORA_OFF": "1", "MSS_REGISTRO_OFF": "1",
           "CLAUDE_PROJECT_DIR": str(raiz)}
    sujo = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento("git switch main", raiz, "s-real")),
                          capture_output=True, text=True, encoding="utf-8", env=env)
    assert sujo.returncode == 2
    assert json.loads(sujo.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_documentado_no_readme_e_na_spec():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "_pasta_e_branch.py" in readme and "MSS_PASTA_BRANCH_OFF" in readme
    spec = (REPO / "docs" / "specs" / "conversa-nova-nao-se-perde.md").read_text(encoding="utf-8")
    assert "pedido de aprovação do owner" in spec
