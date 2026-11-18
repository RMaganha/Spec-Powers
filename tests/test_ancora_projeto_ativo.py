"""Âncora do projeto ativo — a cerca determinística contra escrita em OUTRO projeto.

Nasceu de um acidente real: o owner trabalhava no projeto A, pediu "olha como o projeto B
fez isso", e o assistente passou a tratar o B como o projeto — editou lá e quebrou o B.
A prosa (regra no CLAUDE.md) é a camada 1; este hook é a camada que NÃO depende de o
assistente se comportar: PreToolUse em Write/Edit/NotebookEdit, nega fora da âncora.

Duas propriedades inegociáveis, cobertas aqui:
- **nega fora da âncora** (senão a cerca não cerca);
- **falha ABERTA** (entrada estranha, git ausente, bug → libera e sai 0), porque cerca com
  defeito não pode parar o trabalho legítimo dentro do próprio projeto.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — os caminhos não existem (o `realpath` normaliza
caminho que não existe) e a resposta do git ("qual o .git comum desta pasta?") entra como função. O git de verdade
fica num teste só (a conversa com o git), num repositório montado uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "projeto_ativo.py"
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
ATIVO, OUTRO = BASE / "ativo", BASE / "outro"


def sem_git(_):
    return None


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("projeto_ativo", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _evento(alvo, cwd, tool="Write", campo="file_path"):
    """Payload de PreToolUse como o Claude Code entrega no stdin do hook."""
    return {"hook_event_name": "PreToolUse", "cwd": str(cwd), "tool_name": tool, "tool_input": {campo: str(alvo)}}


def _motivo(mod, evento, ambiente=None, git=sem_git):
    """O ambiente vazio por padrão: o caminho de teste vive no %TEMP% real, que é allow-list."""
    return mod.regra(evento, ambiente or {}, git)[0]


# --- AC1: escrita fora da âncora é negada ---------------------------------------------

def test_bloqueia_escrita_fora_da_ancora(mod):
    """O caso do acidente: projeto ativo é A, o alvo está em B → nega, e a mensagem
    manda abrir uma janela na raiz do outro projeto (a válvula de escape honesta)."""
    projeto_b = BASE / "projeto-b"
    motivo = _motivo(mod, _evento(projeto_b / "src" / "app.py", cwd=BASE / "projeto-a"))
    assert motivo is not None, "escrita em OUTRO projeto passou — a cerca não cercou"
    assert "projeto-b" in motivo or str(projeto_b) in motivo, "motivo não cita o alvo barrado"
    assert "janela" in motivo.lower(), "motivo não oferece a saída: abrir uma janela no outro projeto"


def test_bloqueia_edit_e_notebook(mod):
    """Vale pros três tools de escrita — o NotebookEdit usa outro campo (notebook_path)."""
    assert _motivo(mod, _evento(OUTRO / "x.py", ATIVO, tool="Edit")) is not None
    assert _motivo(mod, _evento(OUTRO / "x.ipynb", ATIVO, tool="NotebookEdit", campo="notebook_path")) is not None


# --- AC2: dentro da âncora passa, silencioso ------------------------------------------

def test_libera_escrita_dentro_da_ancora(mod):
    assert _motivo(mod, _evento(ATIVO / "config" / "logging.py", ATIVO)) is None


def test_libera_caminho_relativo(mod):
    """Caminho relativo resolve CONTRA a âncora — não pode ser lido como 'fora'."""
    assert _motivo(mod, _evento("config/logging.py", cwd=ATIVO)) is None


def test_ancora_prefere_claude_project_dir(mod):
    """CLAUDE_PROJECT_DIR é a âncora quando existe; o cwd do evento é o fallback
    (o cwd pode ter derivado durante a sessão — a raiz do projeto, não)."""
    projeto, fora = BASE / "projeto", BASE / "fora"
    ambiente = {"CLAUDE_PROJECT_DIR": str(projeto)}
    # cwd do evento aponta pro lugar errado; a âncora ainda é o projeto
    assert _motivo(mod, _evento(projeto / "sub" / "a.py", cwd=fora), ambiente) is None
    assert _motivo(mod, _evento(fora / "a.py", cwd=fora), ambiente) is not None


# --- AC3: allow-list (temp do SO e ~/.claude) -----------------------------------------

def test_libera_temp_e_claude_home(mod):
    """Scratchpad/temp e a config global do Claude não são 'outro projeto'."""
    temp, casa = BASE / "temp", BASE / "casa"
    ambiente = {"TEMP": str(temp), "USERPROFILE": str(casa), "HOME": str(casa)}
    assert _motivo(mod, _evento(temp / "claude" / "rascunho.md", ATIVO), ambiente) is None
    assert _motivo(mod, _evento(casa / ".claude" / "settings.json", ATIVO), ambiente) is None


# --- AC4: worktree do MESMO repo passa; outro repo não --------------------------------

def test_libera_worktree_do_mesmo_repo(mod):
    """O próprio kit manda usar worktree (superpowers:using-git-worktrees), e o worktree
    fica FORA da pasta do projeto. Mesmo git-common-dir = mesmo repo = libera."""
    comum = str(ATIVO / ".git")
    assert _motivo(mod, _evento(BASE / "ativo-worktrees" / "feature-x" / "app.py", ATIVO), git=lambda _: comum) is None


def test_bloqueia_outro_repo(mod):
    """git-common-dir diferente = outro repositório = o caso do acidente."""
    def git_common_dir(diretorio):
        return str(Path(diretorio) / ".git")     # cada pasta é um repo próprio

    assert _motivo(mod, _evento(OUTRO / "app.py", ATIVO), git=git_common_dir) is not None


# --- AC5: escape consciente por env --------------------------------------------------

def test_env_desliga_a_cerca(mod):
    assert _motivo(mod, _evento(OUTRO / "app.py", ATIVO), {mod.ENV_DESLIGA: "1"}) is None


# --- AC6: normalização de caminho (Windows: case e barra) -----------------------------

def test_normaliza_case_e_barra(mod):
    """No Windows, `C:\\X\\a` e `c:/x/a` são o MESMO caminho — comparar cru daria
    falso positivo, barrando escrita dentro do próprio projeto."""
    ativo = BASE / "Ativo"
    alvo = str(ativo / "sub" / "a.py")
    if sys.platform == "win32":
        alvo = alvo.replace("\\", "/").lower()
    assert _motivo(mod, _evento(alvo, ativo)) is None


# --- AC7: falha ABERTA ---------------------------------------------------------------

def test_falha_aberta_em_entrada_estranha(mod):
    """Sem file_path, tool que não escreve, evento vazio, âncora indeterminável:
    libera. Cerca com defeito não pode travar o trabalho legítimo."""
    assert _motivo(mod, {}) is None
    assert _motivo(mod, {"tool_name": "Write", "tool_input": {}, "cwd": str(ATIVO)}) is None
    assert _motivo(mod, _evento(OUTRO / "a.py", ATIVO, tool="Read")) is None, \
        "hook não é pra vigiar leitura — ler outro projeto é o OBJETIVO do precedentes"
    assert _motivo(mod, _evento(OUTRO / "a.py", ATIVO, tool="Bash")) is None, \
        "Bash está fora de escopo (heurística de shell é furada) — só a prosa cobre"


def test_sonda_de_worktree_falha_FECHADA(mod):
    """A ÚNICA exceção ao fail-open: se o git não pode ser consultado, a liberação de
    worktree não se aplica → nega. Sem git não existe worktree pra liberar, então tratar
    isso como 'indeterminado, libera' seria dar um jeito trivial de a cerca sumir
    (bastaria o git faltar no PATH)."""
    def explode(_):
        raise OSError("git não existe nesta máquina")

    assert _motivo(mod, _evento(OUTRO / "app.py", ATIVO), git=explode) is not None


def test_registro_diz_a_ferramenta_e_nunca_o_caminho(mod):
    _, anotacoes = mod.regra(_evento(OUTRO / "segredo.py", ATIVO), {}, sem_git)
    assert anotacoes == [("negou", "Write")]


def test_saida_pelos_dois_protocolos(mod):
    """Deny pelos DOIS protocolos aceitos pelo Claude Code: hookSpecificOutput no stdout e exit code 2 com o motivo
    no stderr (qualquer versão do runtime bloqueia); libera calado."""
    impresso, erro, codigo = mod.saida("abra uma janela no outro projeto")
    assert codigo == 2 and erro == "abra uma janela no outro projeto"
    assert json.loads(impresso)["hookSpecificOutput"] == {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": "abra uma janela no outro projeto"}
    assert mod.saida(None) == (None, None, 0)


# --- o git de verdade e o processo (um repositório montado uma vez) ------------------------------------

@pytest.fixture(scope="module")
def repo_real(tmp_path_factory):
    base = tmp_path_factory.mktemp("ancora")
    repo, solto = base / "repo", base / "solto"
    repo.mkdir()
    solto.mkdir()
    subprocess.run(["git", "init", "-q", "--template=", str(repo)], check=True, capture_output=True)
    return base, repo, solto


def test_git_common_dir_de_verdade(mod, repo_real):
    _, repo, solto = repo_real
    assert mod._git_common_dir(str(repo)) == mod.normalizar(str(repo / ".git")), \
        "o .git comum do repositório não veio do git"
    assert mod._git_common_dir(str(solto)) is None, "pasta fora de repositório virou repositório"


def test_processo_nega_com_json_e_stderr(repo_real):
    """O ambiente é neutralizado: o tmp_path do pytest vive dentro do %TEMP% real (que é allow-list), e
    CLAUDE_PROJECT_DIR pode estar setado pela sessão — sem neutralizar, o teste mediria a máquina, não o hook."""
    base, repo, solto = repo_real
    neutro = base / "temp-neutro"
    neutro.mkdir(exist_ok=True)
    ambiente = {**os.environ, "MSS_ANCORA_OFF": "", "CLAUDE_PROJECT_DIR": "",
                "TEMP": str(neutro), "TMP": str(neutro), "TMPDIR": str(neutro)}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento(solto / "app.py", repo)),
                          capture_output=True, text=True, encoding="utf-8", env=ambiente)
    assert proc.returncode == 2, f"esperava exit 2 (bloqueio); saiu {proc.returncode}"
    hook = json.loads(proc.stdout)["hookSpecificOutput"]
    assert hook["permissionDecision"] == "deny" and "janela" in hook["permissionDecisionReason"].lower()
    assert proc.stderr.strip(), "stderr vazio — runtime que só lê stderr não veria o motivo"
