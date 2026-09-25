"""Registro dos hooks — uma linha local por vez que um hook do kit AGIU (negou, bloqueou, avisou,
injetou, lembrou), pra medir o que hoje não dá: quantas vezes a cerca de publicação barrou algo,
se o recall acerta, se o alerta de contexto calcula a janela certa (caso F-027, que só apareceu
porque o owner comparou com o print do app).

Contrato que estes testes travam:
- grava SÓ quando o hook age; passar calado não gera linha;
- NUNCA grava o texto do prompt nem a linha de comando (só hook, decisão, código curto, pasta do
  projeto, início do id da sessão);
- registro que não dá pra gravar NÃO muda decisão nenhuma — inclusive a da cerca de publicação,
  que falha FECHADA;
- `MSS_REGISTRO_OFF=1` desliga; arquivo acima do teto faz rodízio (`.1`), não cresce sem limite.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOKS = REPO / "hooks"
SEGREDO = "SEGREDO123xyz"


def _mod_registro():
    spec = importlib.util.spec_from_file_location("_registro", HOOKS / "_registro.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _rodar(hook, evento, env_extra):
    amb = {k: v for k, v in os.environ.items()
           if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update(env_extra)
    return subprocess.run([sys.executable, str(HOOKS / hook)], input=json.dumps(evento),
                          capture_output=True, text=True, env=amb, timeout=60)


def _linhas(arquivo):
    if not arquivo.exists():
        return []
    return [json.loads(l) for l in arquivo.read_text(encoding="utf-8").splitlines() if l.strip()]


# --- cenários: cada hook num caso em que AGE (com o segredo onde o owner poderia digitá-lo) ------

def _cenario_publicacao(tmp):
    return ("git_publicacao.py",
            {"hook_event_name": "PreToolUse", "cwd": str(tmp / "proj"), "session_id": "abcdef123456",
             "tool_name": "Bash", "tool_input": {"command": f"git push https://x:{SEGREDO}@h/r.git main"}},
            {}, "negou", "git push")


def _cenario_pipe(tmp):
    return ("git_publicacao.py",
            {"hook_event_name": "PreToolUse", "cwd": str(tmp / "proj"), "session_id": "abcdef123456",
             "tool_name": "Bash",
             "tool_input": {"command": f"python -m pytest -q | tail -1 && git commit -m {SEGREDO}"}},
            {}, "negou", "pipe")


def _cenario_ancora(tmp):
    proj = tmp / "proj"
    proj.mkdir(exist_ok=True)
    return ("projeto_ativo.py",
            {"hook_event_name": "PreToolUse", "cwd": str(proj), "session_id": "abcdef123456",
             "tool_name": "Write",
             "tool_input": {"file_path": str(tmp / "outro" / f"{SEGREDO}.md"), "content": SEGREDO}},
            {"CLAUDE_PROJECT_DIR": str(proj)}, "negou", "Write")


def _cenario_um_item(tmp):
    proj = tmp / "proj"
    (proj / "docs" / "superpowers").mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "superpowers" / "INDEX.md").write_text(
        "# Índice\n\n## A fazer\n1. cadastro de clientes — tela e API — aberta\n", encoding="utf-8")
    return ("um_item_por_janela.py",
            {"hook_event_name": "UserPromptSubmit", "cwd": str(proj), "session_id": "abcdef123456",
             "prompt": f"/mss-spec:nova-feature {SEGREDO}"},
            {"MSS_UM_ITEM_ESTADO": str(tmp / "um-item-janelas.json")}, "avisou", "abertas=1")


def _cenario_recall(tmp):
    proj = tmp / "proj"
    mem = proj / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "MEMORY.md").write_text("# topo\n", encoding="utf-8")
    (mem / "mount-de-codigo-no-docker-pelo-git-bash.md").write_text(
        "---\nname: mount-de-codigo-no-docker-pelo-git-bash\n"
        "description: montar a fonte com -v no Git Bash do Windows cai em silêncio\n"
        "gatilho: quando montar código com `docker -v` no Git Bash e o teste novo der No such file\n---\n",
        encoding="utf-8")
    prompt = f"o docker -v pelo git bash montou pasta vazia e o teste deu No such file {SEGREDO}"
    return ("recall_memoria.py",
            {"hook_event_name": "UserPromptSubmit", "cwd": str(proj), "session_id": "abcdef123456",
             "prompt": prompt},
            {}, "injetou", "memory/mount-de-codigo-no-docker-pelo-git-bash.md")


def _cenario_alerta(tmp):
    transcript = tmp / "sessao.jsonl"
    transcript.write_text(json.dumps({"type": "assistant", "isSidechain": False, "message": {
        "model": "claude-opus-4-6", "content": SEGREDO,
        "usage": {"input_tokens": 2, "cache_read_input_tokens": 179_000, "cache_creation_input_tokens": 998}}})
        + "\n", encoding="utf-8")
    return ("alerta_contexto.py",
            {"hook_event_name": "UserPromptSubmit", "cwd": str(tmp), "session_id": "abcdef123456",
             "transcript_path": str(transcript), "prompt": SEGREDO},
            {}, "avisou", "janela=200000")


def _cenario_nudge(tmp):
    return ("capturar_nudge.py",
            {"hook_event_name": "Stop", "cwd": str(tmp), "session_id": "abcdef123456"},
            {}, "lembrou", "")


def _cenario_orcamento(tmp):
    proj = tmp / "proj"
    (proj / "docs" / "superpowers").mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "superpowers" / "MAPA.md").write_bytes(b"x" * 20000)
    return ("orcamento_partida.py",
            {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(proj),
             "session_id": "abcdef123456"},
            {}, "avisou", "MAPA.md=20000")


def _cenario_teto(tmp):
    proj = tmp / "proj"
    sp = proj / "docs" / "superpowers"
    sp.mkdir(parents=True, exist_ok=True)
    (sp / "INDEX.md").write_text("# Índice\n\n## Backlog\n\n" + "".join(
        f"- ideia-{i} — {'x ' * 400} — aberta\n" for i in range(12)), encoding="utf-8")
    return ("teto_ao_gravar.py",
            {"hook_event_name": "PostToolUse", "tool_name": "Edit", "cwd": str(proj), "session_id": "abcdef123456",
             "tool_input": {"file_path": str(sp / "INDEX.md")}},
            {}, "moveu", "INDEX.md=")


def _cenario_citacoes(tmp):
    proj = tmp / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    return ("confere_citacoes.py",
            {"hook_event_name": "Stop", "cwd": str(proj), "session_id": "abcdef123456", "stop_hook_active": False,
             "last_assistant_message": f"{SEGREDO} — veja `services/nao_existe.py`."},
            {}, "devolveu", "citacoes=1")


CENARIOS = [_cenario_publicacao, _cenario_pipe, _cenario_ancora, _cenario_um_item,
            _cenario_recall, _cenario_alerta, _cenario_nudge, _cenario_orcamento, _cenario_teto,
            _cenario_citacoes]
IDS = ["publicacao", "pipe", "ancora", "um_item", "recall", "alerta", "nudge", "orcamento", "teto", "citacoes"]


def _preparar(cenario, tmp_path, env):
    """Cada rodada com a sua pasta temporária (o alerta e o nudge guardam estado no TEMP)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    temp = tmp_path / "temp"
    temp.mkdir(exist_ok=True)
    hook, evento, env_hook, decisao, detalhe = cenario(tmp_path)
    amb = {"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp), **env_hook, **env}
    return hook, evento, amb, decisao, detalhe


# --- AC1: hook que age grava UMA linha, com os campos certos -------------------------------

@pytest.mark.parametrize("cenario", CENARIOS, ids=IDS)
def test_hook_que_age_grava_uma_linha(cenario, tmp_path):
    arquivo = tmp_path / "reg" / "registro-hooks.jsonl"
    hook, evento, amb, decisao, detalhe = _preparar(cenario, tmp_path / "rodada",
                                                    {"MSS_REGISTRO_ARQUIVO": str(arquivo)})
    _rodar(hook, evento, amb)
    linhas = _linhas(arquivo)
    assert len(linhas) == 1, f"{hook}: esperava 1 linha, veio {linhas}"
    linha = linhas[0]
    assert linha["hook"] == hook[:-3]
    assert linha["decisao"] == decisao
    assert detalhe in linha["detalhe"]
    assert linha["sessao"] == "abcdef12"
    assert linha["quando"][:4].isdigit()


# --- AC2: nunca grava prompt nem comando ----------------------------------------------------

@pytest.mark.parametrize("cenario", CENARIOS, ids=IDS)
def test_nunca_grava_o_texto_do_prompt_nem_do_comando(cenario, tmp_path):
    arquivo = tmp_path / "reg" / "registro-hooks.jsonl"
    hook, evento, amb, _, _ = _preparar(cenario, tmp_path / "rodada", {"MSS_REGISTRO_ARQUIVO": str(arquivo)})
    _rodar(hook, evento, amb)
    assert arquivo.exists(), f"{hook} não gravou — o teste de vazamento ficaria vazio"
    assert SEGREDO not in arquivo.read_text(encoding="utf-8"), f"{hook} vazou texto do owner no registro"


# --- AC3: passar calado não grava nada -----------------------------------------------------

@pytest.mark.parametrize("hook,evento", [
    ("git_publicacao.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                           "tool_input": {"command": "git status"}}),
    ("git_publicacao.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                           "tool_input": {"command": "python -m pytest -q && git commit -m x"}}),
    ("um_item_por_janela.py", {"hook_event_name": "UserPromptSubmit", "prompt": "oi, tudo bem?"}),
    ("recall_memoria.py", {"hook_event_name": "UserPromptSubmit", "prompt": "/mss-spec:mapa"}),
    ("orcamento_partida.py", {"hook_event_name": "SessionStart", "source": "startup"}),
    ("confere_citacoes.py", {"hook_event_name": "Stop", "stop_hook_active": False,
                             "last_assistant_message": "tudo certo, sem citação"}),
])
def test_hook_que_passa_calado_nao_grava(hook, evento, tmp_path):
    arquivo = tmp_path / "registro-hooks.jsonl"
    evento = {"cwd": str(tmp_path), **evento}
    _rodar(hook, evento, {"MSS_REGISTRO_ARQUIVO": str(arquivo)})
    assert _linhas(arquivo) == []


# --- AC4: registro quebrado não muda NENHUMA decisão ---------------------------------------

@pytest.mark.parametrize("cenario", CENARIOS, ids=IDS)
def test_registro_que_nao_grava_nao_muda_a_decisao(cenario, tmp_path):
    bloqueio = tmp_path / "sou-um-arquivo"
    bloqueio.write_text("x", encoding="utf-8")
    quebrado = {"MSS_REGISTRO_ARQUIVO": str(bloqueio / "registro-hooks.jsonl")}   # pai é arquivo
    hook, ev1, amb1, _, _ = _preparar(cenario, tmp_path / "a", quebrado)
    _, ev2, amb2, _, _ = _preparar(cenario, tmp_path / "b", {"MSS_REGISTRO_OFF": "1"})
    com_defeito = _rodar(hook, ev1, amb1)
    sem_registro = _rodar(hook, ev2, amb2)
    def trocar(texto):                               # as duas rodadas só diferem na pasta temporária
        for pasta in (str(tmp_path / "a"), str(tmp_path / "b")):
            texto = texto.replace(json.dumps(pasta)[1:-1], "<tmp>").replace(pasta, "<tmp>")
        return texto
    assert com_defeito.returncode == sem_registro.returncode, hook
    assert trocar(com_defeito.stdout) == trocar(sem_registro.stdout), hook
    assert trocar(com_defeito.stderr) == trocar(sem_registro.stderr), hook


def test_cerca_de_publicacao_segue_negando_com_registro_quebrado(tmp_path):
    bloqueio = tmp_path / "sou-um-arquivo"
    bloqueio.write_text("x", encoding="utf-8")
    proc = _rodar("git_publicacao.py",
                  {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": "git push origin main"}},
                  {"MSS_REGISTRO_ARQUIVO": str(bloqueio / "r.jsonl")})
    assert proc.returncode == 2 and "deny" in proc.stdout


# --- AC5: escape e teto --------------------------------------------------------------------

def test_escape_do_owner_nao_grava(tmp_path):
    arquivo = tmp_path / "registro-hooks.jsonl"
    hook, evento, amb, _, _ = _preparar(_cenario_publicacao, tmp_path / "rodada",
                                        {"MSS_REGISTRO_ARQUIVO": str(arquivo), "MSS_REGISTRO_OFF": "1"})
    proc = _rodar(hook, evento, amb)
    assert proc.returncode == 2, "o escape do REGISTRO desligou a cerca"
    assert not arquivo.exists()


def test_acima_do_teto_faz_rodizio(tmp_path, monkeypatch):
    reg = _mod_registro()
    arquivo = tmp_path / "registro-hooks.jsonl"
    arquivo.write_text("x" * 50 + "\n", encoding="utf-8")
    monkeypatch.setattr(reg, "TETO_BYTES", 40)
    reg.registrar("git_publicacao", "negou", "git push", {"cwd": "/c/proj"},
                  ambiente={"MSS_REGISTRO_ARQUIVO": str(arquivo)})
    assert (tmp_path / "registro-hooks.jsonl.1").read_text(encoding="utf-8").startswith("x" * 50)
    assert len(_linhas(arquivo)) == 1


def test_detalhe_curto_e_numa_linha_so(tmp_path):
    reg = _mod_registro()
    arquivo = tmp_path / "registro-hooks.jsonl"
    reg.registrar("h", "negou", "a\nb" + "c" * 500, {}, ambiente={"MSS_REGISTRO_ARQUIVO": str(arquivo)})
    linha = _linhas(arquivo)[0]
    assert "\n" not in linha["detalhe"] and len(linha["detalhe"]) <= reg.TETO_DETALHE


def test_padrao_e_na_pasta_do_kit_no_home():
    reg = _mod_registro()
    assert reg.caminho({}) == Path.home() / ".claude" / "mss-spec" / "registro-hooks.jsonl"


# --- AC6: leitura --------------------------------------------------------------------------

def test_resumo_conta_por_hook_e_decisao(tmp_path):
    reg = _mod_registro()
    arquivo = tmp_path / "registro-hooks.jsonl"
    amb = {"MSS_REGISTRO_ARQUIVO": str(arquivo)}
    for _ in range(3):
        reg.registrar("git_publicacao", "negou", "git push", {"cwd": "/c/a"}, ambiente=amb)
    reg.registrar("recall_memoria", "injetou", "docs/decisoes.md:25", {"cwd": "/c/a"}, ambiente=amb)
    amb_proc = {k: v for k, v in os.environ.items() if not k.startswith("MSS_")}
    proc = subprocess.run([sys.executable, str(HOOKS / "_registro.py"), "resumo"],
                          capture_output=True, text=True, encoding="utf-8", timeout=30, env={**amb_proc, **amb})
    assert proc.returncode == 0, proc.stderr
    assert "git_publicacao" in proc.stdout and "3" in proc.stdout
    assert "recall_memoria" in proc.stdout and "docs/decisoes.md:25" in proc.stdout


def test_resumo_sem_registro_nao_quebra(tmp_path):
    amb_proc = {k: v for k, v in os.environ.items() if not k.startswith("MSS_")}
    proc = subprocess.run([sys.executable, str(HOOKS / "_registro.py"), "resumo"],
                          capture_output=True, text=True, encoding="utf-8", timeout=30,
                          env={**amb_proc, "MSS_REGISTRO_ARQUIVO": str(tmp_path / "nada.jsonl")})
    assert proc.returncode == 0 and "nenhum" in proc.stdout.lower()


def test_documentado_no_readme():
    readme = (HOOKS / "README.md").read_text(encoding="utf-8")
    assert "MSS_REGISTRO_OFF" in readme
    assert "_registro.py resumo" in readme
