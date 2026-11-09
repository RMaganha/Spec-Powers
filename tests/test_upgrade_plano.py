"""upgrade_plano.py — a abertura do /mss-spec:upgrade: o que o projeto precisa, em que ordem, e o que o git tem
pendente (0.54.0). Só lê.

Por que: o upgrade rodava em até 3 passes separados (migração do CLAUDE.md · to-dolist · categorias), cada um
terminando sozinho e exigindo árvore limpa e branch nova. No Transportes V2 (2026-11-09) isso virou 3 conversas,
todas paradas na mesma pergunta sobre 3 arquivos modificados sem commit na branch `fix/atm-virada-outubro`.
Spec: docs/superpowers/specs/2026-07-16-upgrade-design.md ("Estado atual").
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "upgrade_plano.py"
MARCA = "<!-- mss-spec:regras-do-kit -->"

CLAUDE_COM_MARCA = "# Projeto\n\n" + MARCA + "\n\n## Contexto\n- **Infra:** própria\n"
CLAUDE_SEM_MARCA = "# Projeto\n\n## Modo de trabalho\n- Idioma: pt-BR\n\n## Contexto\n- **Infra:** própria\n"
TODO_NO_FORMATO = "- Verificar o plugin (add: 2026-07-16)\n"
TODO_ANTIGO = "# to-dolist\n\n1. **Rodar a régua** amanhã\n   conferir a saída\n"


def _mod():
    spec = importlib.util.spec_from_file_location("upgrade_plano", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _git(proj, *args):
    return subprocess.run(["git", *args], cwd=proj, check=True, capture_output=True, text=True,
                          encoding="utf-8").stdout


def _projeto(tmp_path, marca=True, todo_antigo=False, git=True, principal="main"):
    proj = tmp_path / "proj"
    (proj / "docs" / "superpowers").mkdir(parents=True)
    (proj / "CLAUDE.md").write_text(CLAUDE_COM_MARCA if marca else CLAUDE_SEM_MARCA, encoding="utf-8")
    (proj / "to-dolist.md").write_text(TODO_ANTIGO if todo_antigo else TODO_NO_FORMATO, encoding="utf-8")
    (proj / ".gitignore").write_text("/to-dolist.md\n.env\n" if todo_antigo else ".env\n", encoding="utf-8")
    (proj / "app.py").write_text("print(1)\n", encoding="utf-8")
    if git:
        _git(proj, "init", "-q", "-b", principal)
        _git(proj, "config", "user.email", "t@t")
        _git(proj, "config", "user.name", "t")
        # no desenho do kit o to-dolist está no git; no formato antigo está ignorado (fora dele)
        _git(proj, "add", "CLAUDE.md", ".gitignore", "app.py", *([] if todo_antigo else ["to-dolist.md"]))
        _git(proj, "commit", "-q", "-m", "inicio")
    return proj


def _suja_em_outra_branch(proj):
    """O caso do Transportes: branch de fix, 3 arquivos modificados sem commit e 2 não rastreados."""
    _git(proj, "switch", "-q", "-c", "fix/atm-virada-outubro")
    (proj / "app.py").write_text("print(2)\n", encoding="utf-8")
    claude = proj / "CLAUDE.md"
    claude.write_text(claude.read_text(encoding="utf-8") + "\n- mais uma linha\n", encoding="utf-8")
    (proj / ".gitignore").write_text(".env\n*.log\n", encoding="utf-8")
    (proj / "docker-compose.office.yml").write_text("services: {}\n", encoding="utf-8")
    (proj / "publicar").mkdir()
    (proj / "publicar" / "x.txt").write_text("x\n", encoding="utf-8")


# --- os passes e a ordem ---------------------------------------------------------------------------

def test_sem_marca_e_to_dolist_antigo_sao_tres_passes_na_ordem(tmp_path):
    proj = _projeto(tmp_path, marca=False, todo_antigo=True)
    plano = _mod().montar(proj)
    assert [p.nome for p in plano.passes] == ["migração do CLAUDE.md", "to-dolist", "categorias 1-3"]
    assert plano.status() == "migração do CLAUDE.md ⬜ · to-dolist ⬜ · categorias ⬜"


def test_com_marca_e_to_dolist_no_desenho_so_as_categorias(tmp_path):
    proj = _projeto(tmp_path, marca=True, todo_antigo=False)
    plano = _mod().montar(proj)
    assert [p.nome for p in plano.passes] == ["categorias 1-3"]
    assert plano.status() == "migração do CLAUDE.md ✓ · to-dolist ✓ · categorias ⬜"


def test_com_marca_e_to_dolist_antigo_sao_dois_passes(tmp_path):
    proj = _projeto(tmp_path, marca=True, todo_antigo=True)
    plano = _mod().montar(proj)
    assert [p.nome for p in plano.passes] == ["to-dolist", "categorias 1-3"]
    assert plano.status() == "migração do CLAUDE.md ✓ · to-dolist ⬜ · categorias ⬜"
    # o passe do to-dolist diz o que achou, com as palavras do conversor
    assert any("ignora o to-dolist" in m for m in plano.passes[0].motivos)


def test_sem_claude_md_a_migracao_nao_se_aplica_e_o_relatorio_diz(tmp_path):
    proj = _projeto(tmp_path)
    (proj / "CLAUDE.md").unlink()
    plano = _mod().montar(proj)
    assert [p.nome for p in plano.passes] == ["categorias 1-3"]
    assert "sem CLAUDE.md" in plano.status()


# --- a situação do git: uma vez, num bloco só ------------------------------------------------------

def test_arvore_suja_em_outra_branch_sai_num_bloco_so(tmp_path):
    proj = _projeto(tmp_path)
    _suja_em_outra_branch(proj)
    plano = _mod().montar(proj)
    g = plano.git
    assert g.branch == "fix/atm-virada-outubro" and g.principal == "main" and g.remoto is False
    assert g.modificados == [".gitignore", "CLAUDE.md", "app.py"]
    assert g.nao_rastreados == ["docker-compose.office.yml", "publicar/"]
    texto = _mod().relatorio(plano)
    bloco = [l for l in texto.splitlines() if l.startswith("Git:")]
    assert len(bloco) == 1, "a situação do git sai UMA vez, num bloco só"
    assert "3 modificado(s)" in bloco[0] and "2 não rastreado(s)" in bloco[0]
    assert "guardar uma vez" in bloco[0] and "devolver no fim" in bloco[0]
    assert "stash" in bloco[0]


def test_arvore_limpa_na_principal_nada_a_guardar(tmp_path):
    proj = _projeto(tmp_path)
    plano = _mod().montar(proj)
    assert plano.git.branch == "main" and plano.git.modificados == [] and plano.git.nao_rastreados == []
    texto = _mod().relatorio(plano)
    assert "nada a guardar" in texto


def test_arvore_limpa_em_outra_branch_ainda_assim_volta_pra_ela_no_fim(tmp_path):
    proj = _projeto(tmp_path)
    _git(proj, "switch", "-q", "-c", "fix/outra")
    texto = _mod().relatorio(_mod().montar(proj))
    assert "nada a guardar" in texto and "fix/outra" in texto and "volta" in texto


def test_principal_master_e_remoto_sao_reconhecidos(tmp_path):
    proj = _projeto(tmp_path, principal="master")
    _git(proj, "remote", "add", "origin", "https://example.invalid/x.git")
    g = _mod().montar(proj).git
    assert g.principal == "master" and g.remoto is True
    assert "pull --ff-only" in _mod().relatorio(_mod().montar(proj))


def test_sem_principal_conhecida_o_relatorio_pede_ao_owner(tmp_path):
    proj = _projeto(tmp_path, principal="trunk")
    texto = _mod().relatorio(_mod().montar(proj))
    assert "principal" in texto and "não sei" in texto


def test_fora_de_git_o_relatorio_diz_isso(tmp_path):
    proj = _projeto(tmp_path, git=False)
    plano = _mod().montar(proj)
    assert plano.git is None
    assert "sem git" in _mod().relatorio(plano)


# --- CLI: só lê ------------------------------------------------------------------------------------

def _digest(proj):
    return {p.relative_to(proj).as_posix(): hashlib.sha1(p.read_bytes()).hexdigest()
            for p in proj.rglob("*") if p.is_file() and ".git" not in p.parts}


def test_cli_checar_imprime_o_status_e_nao_grava_nada(tmp_path):
    proj = _projeto(tmp_path, marca=False, todo_antigo=True)
    _suja_em_outra_branch(proj)
    antes = _digest(proj)
    r = subprocess.run([sys.executable, str(SCRIPT), "checar", "--proj", str(proj)], capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines()[0] == "migração do CLAUDE.md ⬜ · to-dolist ⬜ · categorias ⬜"
    assert "1. migração do CLAUDE.md" in r.stdout and "2. to-dolist" in r.stdout and "3. categorias 1-3" in r.stdout
    assert "Git:" in r.stdout
    assert _digest(proj) == antes, "o checar só lê"
    assert _git(proj, "branch", "--show-current").strip() == "fix/atm-virada-outubro"


def test_o_kit_esta_no_proprio_desenho():
    plano = _mod().montar(REPO)
    assert [p.nome for p in plano.passes] == ["categorias 1-3"]
