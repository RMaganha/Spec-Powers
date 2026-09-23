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


DIARIO_WHATS = ("# Diário\n"
                "- [evolution-go-em-homologacao] evolution go em homologação na azure, deploy do webhook do whatsapp"
                " → sessions/2026-08-04-evolution-go-em-homologacao.md\n")
PROMPT_DEPLOY = "preciso publicar no azure de produção o webhook do whatsapp, deploy da main"


def test_hook_nao_injeta_diario_de_sessao(tmp_path):
    """F-030: no pedido de deploy de produção o hook injetou diários antigos (Blip, Evolution Go) e o
    assistente tratou o passado como estado atual. O `CLAUDE.md` já diz: diário é sob demanda."""
    raiz = _projeto(tmp_path)
    (raiz / "memory" / "DIARIO.md").write_text(DIARIO_WHATS, encoding="utf-8")
    saida = _mod().responder(_evento(PROMPT_DEPLOY, raiz), {})
    ctx = saida["hookSpecificOutput"]["additionalContext"] if saida else ""
    assert "memory/sessions/" not in ctx, "o hook injetou diário de sessão"


def test_buscar_manual_ainda_acha_o_diario(tmp_path):
    """O `/mss-spec:memory buscar` é pedido do owner: lá o diário continua valendo."""
    raiz = _projeto(tmp_path)
    (raiz / "memory" / "DIARIO.md").write_text(DIARIO_WHATS, encoding="utf-8")
    motor = _mod()._motor()
    r = motor.casar(raiz, PROMPT_DEPLOY, limite=10)
    assert any(x.ponteiro.startswith("memory/sessions/2026-08-04") for x in r)


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


def test_recall_le_o_fora_de_escopo_que_saiu_da_partida(tmp_path):
    """F-030: o "Fora de escopo" saiu do INDEX (não é mais lido na partida); o anti-re-litígio passa
    a chegar pelo recall — quando o prompt propõe de novo o que já foi recusado."""
    raiz = _projeto(tmp_path)
    sp = raiz / "docs" / "superpowers"
    sp.mkdir(parents=True)
    (sp / "FORA-DE-ESCOPO.md").write_text(
        "# Fora de escopo\n\n- **Redis para o handoff no WhatsApp** — descartado em 2026-07-30: a memória de "
        "sessão do servidor já resolve o handoff\n", encoding="utf-8")
    saida = _mod().responder(_evento("vamos colocar redis pra guardar o handoff do whatsapp", raiz), {})
    assert saida and "docs/superpowers/FORA-DE-ESCOPO.md:3" in saida["hookSpecificOutput"]["additionalContext"]


def test_recall_pula_linha_pausada_ou_obsoleta(tmp_path):
    raiz = _projeto(tmp_path)
    (raiz / "docs").mkdir()
    (raiz / "docs" / "decisoes.md").write_text(
        "# Decisões\n- 2026-07-01 — cotação via n8n com callback no whatsapp — obsoleta: n8n saiu da produção\n",
        encoding="utf-8")
    saida = _mod().responder(_evento("a cotação via n8n com callback no whatsapp funciona?", raiz), {})
    ctx = saida["hookSpecificOutput"]["additionalContext"] if saida else ""
    assert "decisoes.md" not in ctx, "o recall injetou uma decisão marcada obsoleta"
