"""Âncora do projeto ativo — a cerca determinística contra escrita em OUTRO projeto.

Nasceu de um acidente real: o owner trabalhava no projeto A, pediu "olha como o projeto B
fez isso", e o assistente passou a tratar o B como o projeto — editou lá e quebrou o B.
A prosa (regra no CLAUDE.md) é a camada 1; este hook é a camada que NÃO depende de o
assistente se comportar: PreToolUse em Write/Edit/NotebookEdit, nega fora da âncora.

Duas propriedades inegociáveis, cobertas aqui:
- **nega fora da âncora** (senão a cerca não cerca);
- **falha ABERTA** (entrada estranha, git ausente, bug → libera e sai 0), porque cerca com
  defeito não pode parar o trabalho legítimo dentro do próprio projeto.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "projeto_ativo.py"


def _mod():
    spec = importlib.util.spec_from_file_location("projeto_ativo", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evento(alvo, cwd, tool="Write", campo="file_path"):
    """Payload de PreToolUse como o Claude Code entrega no stdin do hook."""
    return {
        "hook_event_name": "PreToolUse",
        "cwd": str(cwd),
        "tool_name": tool,
        "tool_input": {campo: str(alvo)},
    }


# --- AC1: escrita fora da âncora é negada ---------------------------------------------

def test_bloqueia_escrita_fora_da_ancora(tmp_path):
    """O caso do acidente: projeto ativo é A, o alvo está em B → nega, e a mensagem
    manda abrir uma janela na raiz do outro projeto (a válvula de escape honesta)."""
    mod = _mod()
    projeto_a = tmp_path / "projeto-a"
    projeto_b = tmp_path / "projeto-b"
    (projeto_a / "src").mkdir(parents=True)
    (projeto_b / "src").mkdir(parents=True)

    motivo = mod.decidir(_evento(projeto_b / "src" / "app.py", cwd=projeto_a),
                         ambiente={}, git_common_dir=lambda _: None)

    assert motivo is not None, "escrita em OUTRO projeto passou — a cerca não cercou"
    assert "projeto-b" in motivo or str(projeto_b) in motivo, "motivo não cita o alvo barrado"
    assert "janela" in motivo.lower(), "motivo não oferece a saída: abrir uma janela no outro projeto"


def test_bloqueia_edit_e_notebook(tmp_path):
    """Vale pros três tools de escrita — o NotebookEdit usa outro campo (notebook_path)."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    outro = tmp_path / "outro"
    ativo.mkdir()
    outro.mkdir()
    sem_git = lambda _: None

    assert mod.decidir(_evento(outro / "x.py", ativo, tool="Edit"),
                       ambiente={}, git_common_dir=sem_git) is not None
    assert mod.decidir(_evento(outro / "x.ipynb", ativo, tool="NotebookEdit",
                               campo="notebook_path"),
                       ambiente={}, git_common_dir=sem_git) is not None


# --- AC2: dentro da âncora passa, silencioso ------------------------------------------

def test_libera_escrita_dentro_da_ancora(tmp_path):
    mod = _mod()
    ativo = tmp_path / "ativo"
    (ativo / "config").mkdir(parents=True)
    assert mod.decidir(_evento(ativo / "config" / "logging.py", ativo),
                       ambiente={}, git_common_dir=lambda _: None) is None


def test_libera_caminho_relativo(tmp_path):
    """Caminho relativo resolve CONTRA a âncora — não pode ser lido como 'fora'."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    ativo.mkdir()
    evento = _evento("config/logging.py", cwd=ativo)
    assert mod.decidir(evento, ambiente={}, git_common_dir=lambda _: None) is None


def test_ancora_prefere_claude_project_dir(tmp_path):
    """CLAUDE_PROJECT_DIR é a âncora quando existe; o cwd do evento é o fallback
    (o cwd pode ter derivado durante a sessão — a raiz do projeto, não)."""
    mod = _mod()
    projeto = tmp_path / "projeto"
    (projeto / "sub").mkdir(parents=True)
    fora = tmp_path / "fora"
    fora.mkdir()

    ambiente = {"CLAUDE_PROJECT_DIR": str(projeto)}
    # cwd do evento aponta pro lugar errado; a âncora ainda é o projeto
    assert mod.decidir(_evento(projeto / "sub" / "a.py", cwd=fora),
                       ambiente=ambiente, git_common_dir=lambda _: None) is None
    assert mod.decidir(_evento(fora / "a.py", cwd=fora),
                       ambiente=ambiente, git_common_dir=lambda _: None) is not None


# --- AC3: allow-list (temp do SO e ~/.claude) -----------------------------------------

def test_libera_temp_e_claude_home(tmp_path):
    """Scratchpad/temp e a config global do Claude não são 'outro projeto'."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    ativo.mkdir()
    temp = tmp_path / "temp"
    (temp / "claude").mkdir(parents=True)
    casa = tmp_path / "casa"
    (casa / ".claude").mkdir(parents=True)

    ambiente = {"TEMP": str(temp), "USERPROFILE": str(casa), "HOME": str(casa)}
    sem_git = lambda _: None
    assert mod.decidir(_evento(temp / "claude" / "rascunho.md", ativo),
                       ambiente=ambiente, git_common_dir=sem_git) is None
    assert mod.decidir(_evento(casa / ".claude" / "settings.json", ativo),
                       ambiente=ambiente, git_common_dir=sem_git) is None


# --- AC4: worktree do MESMO repo passa; outro repo não --------------------------------

def test_libera_worktree_do_mesmo_repo(tmp_path):
    """O próprio kit manda usar worktree (superpowers:using-git-worktrees), e o worktree
    fica FORA da pasta do projeto. Mesmo git-common-dir = mesmo repo = libera."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    ativo.mkdir()
    worktree = tmp_path / "ativo-worktrees" / "feature-x"
    worktree.mkdir(parents=True)
    comum = str(tmp_path / "ativo" / ".git")

    assert mod.decidir(_evento(worktree / "app.py", ativo),
                       ambiente={}, git_common_dir=lambda _: comum) is None


def test_bloqueia_outro_repo(tmp_path):
    """git-common-dir diferente = outro repositório = o caso do acidente."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    ativo.mkdir()
    outro = tmp_path / "outro"
    outro.mkdir()

    def git_common_dir(diretorio):
        return str(Path(diretorio) / ".git")     # cada pasta é um repo próprio

    assert mod.decidir(_evento(outro / "app.py", ativo),
                       ambiente={}, git_common_dir=git_common_dir) is not None


# --- AC5: escape consciente por env --------------------------------------------------

def test_env_desliga_a_cerca(tmp_path):
    mod = _mod()
    ativo = tmp_path / "ativo"
    outro = tmp_path / "outro"
    ativo.mkdir()
    outro.mkdir()
    assert mod.decidir(_evento(outro / "app.py", ativo),
                       ambiente={mod.ENV_DESLIGA: "1"},
                       git_common_dir=lambda _: None) is None


# --- AC6: normalização de caminho (Windows: case e barra) -----------------------------

def test_normaliza_case_e_barra(tmp_path):
    """No Windows, `C:\\X\\a` e `c:/x/a` são o MESMO caminho — comparar cru daria
    falso positivo, barrando escrita dentro do próprio projeto."""
    mod = _mod()
    ativo = tmp_path / "Ativo"
    (ativo / "sub").mkdir(parents=True)
    alvo = str(ativo / "sub" / "a.py")
    if sys.platform == "win32":
        alvo = alvo.replace("\\", "/").lower()
    assert mod.decidir(_evento(alvo, ativo), ambiente={},
                       git_common_dir=lambda _: None) is None


# --- AC7: falha ABERTA ---------------------------------------------------------------

def test_falha_aberta_em_entrada_estranha(tmp_path):
    """Sem file_path, tool que não escreve, evento vazio, âncora indeterminável:
    libera. Cerca com defeito não pode travar o trabalho legítimo."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    ativo.mkdir()
    sem_git = lambda _: None

    assert mod.decidir({}, ambiente={}, git_common_dir=sem_git) is None
    assert mod.decidir({"tool_name": "Write", "tool_input": {}, "cwd": str(ativo)},
                       ambiente={}, git_common_dir=sem_git) is None
    assert mod.decidir(_evento(tmp_path / "outro" / "a.py", ativo, tool="Read"),
                       ambiente={}, git_common_dir=sem_git) is None, \
        "hook não é pra vigiar leitura — ler outro projeto é o OBJETIVO do precedentes"
    assert mod.decidir(_evento(tmp_path / "outro" / "a.py", ativo, tool="Bash"),
                       ambiente={}, git_common_dir=sem_git) is None, \
        "Bash está fora de escopo (heurística de shell é furada) — só a prosa cobre"


def test_sonda_de_worktree_falha_FECHADA(tmp_path):
    """A ÚNICA exceção ao fail-open: se o git não pode ser consultado, a liberação de
    worktree não se aplica → nega. Sem git não existe worktree pra liberar, então tratar
    isso como 'indeterminado, libera' seria dar um jeito trivial de a cerca sumir
    (bastaria o git faltar no PATH)."""
    mod = _mod()
    ativo = tmp_path / "ativo"
    outro = tmp_path / "outro"
    ativo.mkdir()
    outro.mkdir()

    def explode(_):
        raise OSError("git não existe nesta máquina")

    assert mod.decidir(_evento(outro / "app.py", ativo),
                       ambiente={}, git_common_dir=explode) is not None


# --- Contrato do processo: JSON de deny + exit code ----------------------------------

def _rodar(evento, tmp_path):
    """Roda o hook como processo, com o ambiente NEUTRALIZADO: o tmp_path do pytest vive
    dentro do %TEMP% real (que é allow-list), e CLAUDE_PROJECT_DIR pode estar setado pela
    sessão — sem neutralizar, o teste mediria o ambiente da máquina, não o hook."""
    vazio = tmp_path / "env-neutro"
    vazio.mkdir(exist_ok=True)
    ambiente = {**os.environ, "MSS_ANCORA_OFF": "", "CLAUDE_PROJECT_DIR": "",
                "TEMP": str(vazio), "TMP": str(vazio), "TMPDIR": str(vazio)}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento),
                          capture_output=True, text=True, encoding="utf-8", env=ambiente)


def test_processo_nega_com_json_e_stderr(tmp_path):
    """Deny pelos DOIS protocolos aceitos pelo Claude Code: hookSpecificOutput no
    stdout e exit code 2 com o motivo no stderr (qualquer versão do runtime bloqueia)."""
    ativo = tmp_path / "ativo"
    outro = tmp_path / "outro"
    ativo.mkdir()
    outro.mkdir()

    proc = _rodar(_evento(outro / "app.py", ativo), tmp_path)

    assert proc.returncode == 2, f"esperava exit 2 (bloqueio); saiu {proc.returncode}"
    saida = json.loads(proc.stdout)
    hook = saida["hookSpecificOutput"]
    assert hook["hookEventName"] == "PreToolUse"
    assert hook["permissionDecision"] == "deny"
    assert "janela" in hook["permissionDecisionReason"].lower()
    assert proc.stderr.strip(), "stderr vazio — runtime que só lê stderr não veria o motivo"


def test_processo_libera_silencioso(tmp_path):
    ativo = tmp_path / "ativo"
    ativo.mkdir()
    proc = _rodar(_evento(ativo / "app.py", ativo), tmp_path)
    assert proc.returncode == 0, f"escrita no próprio projeto foi barrada: {proc.stderr}"
    assert proc.stdout.strip() == "", "hook falou sem precisar (poluição de contexto)"


def test_processo_falha_aberta_com_stdin_invalido():
    """stdin que não é JSON → sai 0 e calado. Nunca travar por bug do hook."""
    proc = subprocess.run([sys.executable, str(HOOK)], input="isto não é json",
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, "stdin inválido travou o tool — a cerca virou tranca"
