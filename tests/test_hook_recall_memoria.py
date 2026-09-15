"""Recall determinístico — hook UserPromptSubmit que injeta os ponteiros de memória que casam com o prompt.

Por que existe: o owner de um projeto grande voltava às conversas antigas pra re-explicar ao assistente onde
um assunto foi tratado. O índice estava lá; ninguém abria. Agora o Python casa e injeta ≤ 600 bytes.

Propriedades: não bloqueia nunca · silêncio quando nada casa · ignora `/comando` e prompt curto · projeto
sem memory/ → silêncio · falha ABERTA (bug → exit 0, stdout vazio) · escape `MSS_RECALL_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "recall_memoria.py"


def _mod():
    spec = importlib.util.spec_from_file_location("recall_memoria", HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path):
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("# topo\n", encoding="utf-8")
    (mem / "mount-de-codigo-no-docker-pelo-git-bash.md").write_text(
        "---\nname: mount-de-codigo-no-docker-pelo-git-bash\n"
        "description: montar a fonte com -v no Git Bash do Windows cai em silêncio\n"
        "gatilho: quando montar código com `docker -v` no Git Bash e o teste novo der No such file\n---\n",
        encoding="utf-8")
    return raiz


def _evento(prompt, raiz):
    return {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": prompt}


def _rodar(evento, raw=None, env_extra=None):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_RECALL_OFF", "CLAUDE_PROJECT_DIR")}
    amb.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(evento),
                          capture_output=True, text=True, env=amb, timeout=30)


PROMPT = "o docker -v pelo git bash montou pasta vazia e o teste deu No such file"


def test_injeta_ponteiro_quando_casa(tmp_path):
    mod = _mod()
    saida = mod.responder(_evento(PROMPT, _projeto(tmp_path)), {})
    assert saida is not None
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("[mss-spec recall]") and "memory/mount-de-codigo-no-docker-pelo-git-bash.md" in ctx
    assert len(ctx.encode("utf-8")) <= 600


def test_silencio_quando_nada_casa(tmp_path):
    mod = _mod()
    assert mod.responder(_evento("ajusta o rodapé da página de login por favor", _projeto(tmp_path)), {}) is None


def test_ignora_comando_prompt_curto_e_projeto_sem_memoria(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    assert mod.responder(_evento("/mss-spec:doctor docker git bash mount teste", raiz), {}) is None
    assert mod.responder(_evento("docker bash", raiz), {}) is None
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    assert mod.responder(_evento(PROMPT, vazio), {}) is None


def test_escape_e_falha_aberta(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    assert mod.responder(_evento(PROMPT, raiz), {"MSS_RECALL_OFF": "1"}) is None
    assert mod.responder("isto não é um dict", {}) is None
    assert mod.responder({"prompt": 42, "cwd": str(raiz)}, {}) is None


def test_claude_project_dir_vence_o_cwd(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    outro = tmp_path / "outro"
    outro.mkdir()
    assert mod.responder(_evento(PROMPT, outro), {"CLAUDE_PROJECT_DIR": str(raiz)}) is not None


def test_processo_injeta_json_e_sai_zero(tmp_path):
    raiz = _projeto(tmp_path)
    proc = _rodar(_evento(PROMPT, raiz))
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert "mount-de-codigo-no-docker-pelo-git-bash.md" in saida["hookSpecificOutput"]["additionalContext"]


def test_processo_json_malformado_sai_zero_e_calado(tmp_path):
    proc = _rodar(None, raw="{isto não é json")
    assert proc.returncode == 0 and proc.stdout.strip() == ""


def test_hook_registrado_em_user_prompt_submit():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["UserPromptSubmit"]
    comandos = [h["command"] for g in grupos for h in g["hooks"]]
    assert any("recall_memoria.py" in c and "CLAUDE_PLUGIN_ROOT" in c for c in comandos), comandos
    assert any("um_item_por_janela.py" in c for c in comandos), "não pode derrubar a cerca que já existia"
