"""Recall determinístico — hook UserPromptSubmit que injeta os ponteiros de memória que casam com o prompt.

Por que existe: o owner de um projeto grande voltava às conversas antigas pra re-explicar ao assistente onde
um assunto foi tratado. O índice estava lá; ninguém abria. Agora o Python casa e injeta ≤ 600 bytes.

Propriedades: não bloqueia nunca · silêncio quando nada casa · ignora `/comando` e prompt curto · projeto
sem memory/ → silêncio · diário de sessão fica de fora (F-030) · falha ABERTA (bug → exit 0, stdout vazio) ·
escape `MSS_RECALL_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — se o projeto tem `memory/` entra como função e o
motor (`templates/memoria_indice.py`) entra falso, um objeto do teste que guarda com o que `casar` foi chamado e
devolve a injeção combinada; os caminhos não existem. O que o motor casa (gatilho, PROCEDIMENTO com a instrução
de seguir, diário só quando pedido, fora de escopo e decisão obsoleta fora, 600 bytes) é provado em
`tests/test_memoria_indice.py`. O disco de verdade, com o motor de verdade, fica num teste só, numa pasta montada
uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "recall_memoria.py"
RAIZ = REPO.parent / "projeto-que-nao-existe-recall"          # absoluto em qualquer sistema; nunca criado
PROMPT = "o docker -v pelo git bash montou pasta vazia e o teste deu No such file"
INJECAO = ("[mss-spec recall] casou com o seu prompt — abra antes de agir:\n"
           "- memory/mount-de-codigo-no-docker-pelo-git-bash.md — montar a fonte com -v no Git Bash cai em silêncio\n"
           "- docs/decisoes.md:12 — 2026-09-30 — usar a fila X em vez de Y")


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("recall_memoria", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class Motor:
    """O motor falso: as palavras do prompt são os tokens; `casar` guarda com o que foi chamado e a injeção é a que o
    teste combinou ("" = nada casou)."""

    def __init__(self, injecao=INJECAO, erro=None):
        self.injecao, self.erro, self.casou, self.carregado = injecao, erro, [], 0

    def tokens(self, prompt):
        return [p for p in prompt.split() if len(p) > 3], set()

    def casar(self, proj, prompt, limite, diario):
        if self.erro:
            raise self.erro
        self.casou.append({"proj": proj, "prompt": prompt, "limite": limite, "diario": diario})
        return ["achado"] if self.injecao else []

    def formatar_injecao(self, achados):
        return self.injecao if achados else ""


class Janela:
    """O papel da casca, em memória: quais projetos têm `memory/`, o motor falso e as anotações do registro."""

    def __init__(self, mod, motor, com_memoria=(RAIZ,)):
        self.mod, self.motor, self.com_memoria, self.anotacoes = mod, motor, set(com_memoria), []

    def _carregar(self):
        self.motor.carregado += 1
        return self.motor

    def responder(self, evento, ambiente=None):
        resposta, mudancas = self.mod.regra(evento, ambiente or {}, lambda proj: proj in self.com_memoria,
                                            self._carregar)
        self.anotacoes += mudancas["anotacoes"]
        return resposta


def _evento(prompt=PROMPT, raiz=RAIZ):
    return {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": prompt}


def test_injeta_ponteiro_quando_casa(mod):
    jan = Janela(mod, Motor())
    saida = jan.responder(_evento())
    assert saida == {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": INJECAO}}
    assert jan.motor.casou == [{"proj": RAIZ, "prompt": PROMPT, "limite": 3, "diario": False}]


def test_hook_nao_injeta_diario_de_sessao(mod):
    """F-030: no pedido de deploy de produção o hook injetou diários antigos (Blip, Evolution Go) e o
    assistente tratou o passado como estado atual. O `CLAUDE.md` já diz: diário é sob demanda."""
    jan = Janela(mod, Motor())
    jan.responder(_evento("preciso publicar no azure de produção o webhook do whatsapp, deploy da main"))
    assert jan.motor.casou[0]["diario"] is False, "o hook pediu o diário de sessão ao motor"


def test_registro_guarda_so_o_ponteiro(mod):
    jan = Janela(mod, Motor())
    jan.responder(_evento())
    assert jan.anotacoes == [("injetou", "memory/mount-de-codigo-no-docker-pelo-git-bash.md, docs/decisoes.md:12")]
    assert "docker -v" not in jan.anotacoes[0][1] and "silêncio" not in jan.anotacoes[0][1], \
        "o registro levou o prompt ou o resumo da memória"


def test_silencio_quando_nada_casa(mod):
    jan = Janela(mod, Motor(injecao=""))
    assert jan.responder(_evento("ajusta o rodapé da página de login por favor")) is None
    assert jan.anotacoes == []


def test_ignora_comando_e_prompt_curto(mod):
    jan = Janela(mod, Motor())
    assert jan.responder(_evento("/mss-spec:doctor docker git bash mount teste")) is None
    assert jan.responder(_evento("   /mss-spec:tarefa ajustar docker bash mount")) is None
    assert jan.responder(_evento("docker bash")) is None
    assert jan.motor.casou == []


def test_projeto_sem_memoria_nem_carrega_o_motor(mod):
    jan = Janela(mod, Motor(), com_memoria=())
    assert jan.responder(_evento()) is None and jan.motor.carregado == 0


def test_escape_e_falha_aberta(mod):
    jan = Janela(mod, Motor())
    assert jan.responder(_evento(), {"MSS_RECALL_OFF": "1"}) is None
    for ruim in ("isto não é um dict", None, {"prompt": 42, "cwd": str(RAIZ)}, {"prompt": PROMPT},
                 {"prompt": PROMPT, "cwd": 7}):
        assert jan.responder(ruim) is None, ruim
    assert jan.motor.carregado == 0
    quebrado = Janela(mod, Motor(erro=RuntimeError("índice ilegível")))
    assert quebrado.responder(_evento()) is None and quebrado.anotacoes == []


def test_claude_project_dir_vence_o_cwd(mod):
    jan = Janela(mod, Motor())
    assert jan.responder(_evento(raiz=RAIZ.parent / "outro"), {"CLAUDE_PROJECT_DIR": str(RAIZ)}) is not None
    assert jan.motor.casou[0]["proj"] == RAIZ


def test_saida_e_o_json_da_resposta(mod):
    resposta = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": INJECAO}}
    assert json.loads(mod.saida(resposta)) == resposta
    assert mod.saida(None) is None


# --- o disco de verdade e o processo (pasta montada uma vez) ------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("recall_memoria") / "proj"
    mem = raiz / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("# topo\n", encoding="utf-8")
    (mem / "mount-de-codigo-no-docker-pelo-git-bash.md").write_text(
        "---\nname: mount-de-codigo-no-docker-pelo-git-bash\n"
        "description: montar a fonte com -v no Git Bash do Windows cai em silêncio\n"
        "gatilho: quando montar código com `docker -v` no Git Bash e o teste novo der No such file\n---\n",
        encoding="utf-8")
    (raiz.parent / "sem-memoria").mkdir()
    return raiz


def test_casca_casa_com_o_motor_de_verdade(mod, pasta):
    saida = mod.responder(_evento(raiz=pasta), {})
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("[mss-spec recall]") and "memory/mount-de-codigo-no-docker-pelo-git-bash.md" in ctx
    assert len(ctx.encode("utf-8")) <= 600
    assert mod.responder(_evento(raiz=pasta.parent / "sem-memoria"), {}) is None


def test_processo_injeta_json_e_sai_zero(pasta):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_RECALL_OFF", "CLAUDE_PROJECT_DIR")}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento(raiz=pasta)), capture_output=True,
                          text=True, encoding="utf-8", env=amb, timeout=30)
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert "mount-de-codigo-no-docker-pelo-git-bash.md" in saida["hookSpecificOutput"]["additionalContext"]


def test_hook_registrado_em_user_prompt_submit():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["UserPromptSubmit"]
    comandos = [h["command"] for g in grupos for h in g["hooks"]]
    assert any("recall_memoria.py" in c and "CLAUDE_PLUGIN_ROOT" in c for c in comandos), comandos
    assert any("um_item_por_janela.py" in c for c in comandos), "não pode derrubar a cerca que já existia"
