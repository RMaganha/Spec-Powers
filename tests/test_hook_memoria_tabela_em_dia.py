"""Hook `memoria_tabela_em_dia.py` — a tabela de memória se atualiza sozinha (parte 2, 0.56.0).

Por que existe: a parte 1 entregou um modo manual e a tabela real ficou só com o kit; o owner recusou comando
pra lembrar — "vai fazer se perder quando eu perguntar" (caso F-057). Decisões 13 e 15 da spec
(docs/specs/memoria-em-tabela.md): a tabela se atualiza quando a conversa abre no projeto (montada na hora se
não existir) e logo depois de cada gravação de memória. Calado quando dá certo; nunca trava.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — se o projeto tem `memory/` entra como função e o
motor (`templates/memoria_tabela.py`) entra falso, um objeto do teste que guarda com o que foi chamado e devolve
o resultado combinado; os caminhos não existem. O que o motor faz (ler o projeto, montar só o que mudou, não ler
arquivo quando a tabela está em dia, dois projetos na mesma tabela, html) é provado em `tests/test_memoria_tabela.py`.
O disco de verdade, com o motor de verdade, fica num teste só, numa pasta montada uma vez; o processo python, num
teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "memoria_tabela_em_dia.py"
RAIZ = REPO.parent / "projeto-que-nao-existe-alfa"          # absoluto em qualquer sistema; nunca criado
TABELA = Path("/tabela/de/teste.sqlite3")


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("memoria_tabela_em_dia", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _feito(novos=0, refeitos=0, removidos=0, iguais=0, linhas=12):
    return SimpleNamespace(novos=novos, refeitos=refeitos, removidos=removidos, iguais=iguais,
                           por_tipo={"anotacao": linhas})


class Motor:
    """O motor falso: guarda as chamadas e devolve o que o teste combinou (um resultado, None = em dia, ou um erro)."""
    SOURCES_SEM_AVISO = ("resume", "compact")

    def __init__(self, feito=None, sono=None, erro=None):
        self.feito, self.sono, self.erro = feito, sono, erro
        self.atualizou, self.sono_pedido, self.carregado = [], [], 0

    def caminho_tabela(self):
        return Path("/casa/mss-spec/memoria.sqlite3")

    def atualizar(self, raiz, tabela):
        if self.erro:
            raise self.erro
        self.atualizou.append((raiz, tabela))
        return self.feito

    def aviso_de_sono(self, raiz, tabela, pasta, atual):
        self.sono_pedido.append((pasta, atual))
        return self.sono


class Janela:
    """O papel da casca, em memória: quais projetos têm `memory/`, o motor falso e as anotações do registro."""

    def __init__(self, mod, motor, com_memoria=(RAIZ,)):
        self.mod, self.motor, self.com_memoria, self.anotacoes = mod, motor, set(com_memoria), []

    def _carregar(self):
        self.motor.carregado += 1
        return self.motor

    def responder(self, evento, ambiente=None):
        amb = {"MSS_MEMORIA_TABELA": str(TABELA)} if ambiente is None else ambiente
        resposta, mudancas = self.mod.regra(evento, amb, lambda raiz: raiz in self.com_memoria, self._carregar)
        self.anotacoes += mudancas["anotacoes"]
        return resposta


def _abertura(raiz=RAIZ, source="startup", **extra):
    return dict({"hook_event_name": "SessionStart", "source": source, "cwd": str(raiz)}, **extra)


def _gravou(rel, tool="Write", raiz=RAIZ):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(raiz),
            "tool_input": {"file_path": str(raiz / rel)}}


def _texto(resposta):
    assert "systemMessage" not in resposta, "é recado pro assistente: o owner não tem nada a fazer"
    assert resposta["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    return resposta["hookSpecificOutput"]["additionalContext"]


# ------------------------------------------------------------------ abertura da conversa

def test_abertura_sem_tabela_monta_e_diz_ao_assistente(mod):
    jan = Janela(mod, Motor(feito=_feito(novos=12)))
    texto = _texto(jan.responder(_abertura()))
    assert "montada" in texto and "12 linhas" in texto and str(TABELA) in texto
    assert jan.motor.atualizou == [(RAIZ, TABELA)]
    assert jan.anotacoes[0][0] == "montou"


def test_abertura_com_a_tabela_em_dia_fica_calada(mod):
    jan = Janela(mod, Motor(feito=None))
    assert jan.responder(_abertura()) is None
    assert jan.motor.atualizou == [(RAIZ, TABELA)] and jan.anotacoes == []


def test_abertura_com_arquivo_mudado_por_fora_atualiza_calada(mod):
    jan = Janela(mod, Motor(feito=_feito(novos=1, iguais=11)))
    assert jan.responder(_abertura()) is None
    assert jan.anotacoes == [("atualizou", "1 novo(s) · 0 refeito(s) · 0 removido(s)")]


def test_sem_a_variavel_a_tabela_e_a_do_motor(mod):
    jan = Janela(mod, Motor(feito=None))
    jan.responder(_abertura(), ambiente={})
    assert jan.motor.atualizou == [(RAIZ, Path("/casa/mss-spec/memoria.sqlite3"))]


def test_a_raiz_e_a_do_projeto_da_janela_nao_a_pasta_do_evento(mod):
    jan = Janela(mod, Motor(feito=None))
    jan.responder(_abertura(RAIZ / "docs"), ambiente={"MSS_MEMORIA_TABELA": str(TABELA), "CLAUDE_PROJECT_DIR": str(RAIZ)})
    assert jan.motor.atualizou == [(RAIZ, TABELA)]


# ------------------------------------------------------------------ sono da memória

def test_sono_atrasado_vai_pro_assistente_junto_do_recado(mod):
    jan = Janela(mod, Motor(feito=_feito(novos=12), sono="[mss-spec] sono da memória atrasado: 10 conversas"))
    texto = _texto(jan.responder(_abertura(transcript_path=str(RAIZ / "conversas" / "atual.jsonl"))))
    assert "montada" in texto and "sono da memória atrasado" in texto
    assert jan.motor.sono_pedido == [(RAIZ / "conversas", RAIZ / "conversas" / "atual.jsonl")]
    assert ("sono_atrasado", "[mss-spec] sono da memória atrasado: 10 conversas") in jan.anotacoes


@pytest.mark.parametrize("source", ["resume", "compact"])
def test_retomar_ou_compactar_nao_conta_conversas(mod, source):
    jan = Janela(mod, Motor(feito=None, sono="atrasado"))
    assert jan.responder(_abertura(source=source, transcript_path=str(RAIZ / "a.jsonl"))) is None
    assert jan.motor.sono_pedido == []


def test_sem_o_arquivo_da_conversa_nao_conta(mod):
    jan = Janela(mod, Motor(feito=None, sono="atrasado"))
    assert jan.responder(_abertura()) is None and jan.motor.sono_pedido == []


# ------------------------------------------------------------------ depois de gravar

@pytest.mark.parametrize("rel", ["memory/feedback_novo.md", "docs/specs/novo.md", "to-dolist.md", "projeto.md",
                                 "docs/pagina.html"])
@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
def test_gravou_memoria_a_tabela_acompanha_sem_dizer_nada(mod, rel, tool):
    jan = Janela(mod, Motor(feito=_feito(novos=1, iguais=11), sono="atrasado"))
    assert jan.responder(_gravou(rel, tool)) is None
    assert jan.motor.atualizou == [(RAIZ, TABELA)] and jan.motor.sono_pedido == []


def test_gravacao_fora_do_alcance_nem_carrega_o_motor(mod):
    outro = RAIZ.parent / "projeto-que-nao-existe-beta"
    jan = Janela(mod, Motor(feito=_feito(novos=1)), com_memoria=(RAIZ, outro))
    eventos = [_gravou("src/app.py"), _gravou("docs/variaveis.txt"), _gravou("README.md"),
               _gravou("memory/project_boleto.md", raiz=outro) | {"cwd": str(RAIZ)},
               _gravou("memory/project_boleto.md", tool="Bash"),
               {"hook_event_name": "PostToolUse", "tool_name": "Write", "cwd": str(RAIZ), "tool_input": {}},
               {"hook_event_name": "UserPromptSubmit", "cwd": str(RAIZ), "prompt": "oi"}]
    for evento in eventos:
        assert jan.responder(evento) is None
    assert jan.motor.carregado == 0, "nenhum desses eventos é gravação de memória deste projeto"


def test_caminho_relativo_e_resolvido_pela_raiz_do_projeto(mod):
    jan = Janela(mod, Motor(feito=None))
    evento = _gravou("x") | {"tool_input": {"file_path": "memory/project_boleto.md"}}
    assert jan.responder(evento) is None and jan.motor.atualizou == [(RAIZ, TABELA)]


# ------------------------------------------------------------------ quando não age e quando falha

def test_projeto_sem_pasta_memory_nao_ganha_tabela(mod):
    jan = Janela(mod, Motor(feito=_feito(novos=12)), com_memoria=())
    assert jan.responder(_abertura()) is None and jan.motor.carregado == 0


def test_escape_do_owner_desliga(mod):
    jan = Janela(mod, Motor(feito=_feito(novos=12)))
    assert jan.responder(_abertura(), ambiente={"MSS_MEMORIA_TABELA_OFF": "1"}) is None
    assert jan.motor.carregado == 0


def test_tabela_presa_nao_trava_a_abertura_e_manda_buscar_nos_arquivos(mod):
    jan = Janela(mod, Motor(erro=OSError("database is locked")))
    texto = _texto(jan.responder(_abertura()))
    assert "memory/MEMORY.md" in texto and "OSError" in texto
    assert jan.responder(_gravou("to-dolist.md")) is None, \
        "depois de gravar a falha é calada: a busca confere de novo antes de procurar"
    assert jan.anotacoes == [("falhou", "OSError"), ("falhou", "OSError")]


@pytest.mark.parametrize("evento", [None, [], "x", {}, {"hook_event_name": "SessionStart"},
                                    {"hook_event_name": "SessionStart", "cwd": 3},
                                    {"hook_event_name": "PostToolUse", "cwd": str(RAIZ), "tool_name": "Write",
                                     "tool_input": None}])
def test_evento_torto_nunca_levanta(mod, evento):
    assert Janela(mod, Motor(feito=_feito(novos=12))).responder(evento, ambiente={}) is None


def test_saida_e_o_json_da_resposta(mod):
    resposta = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "tabela montada"}}
    assert json.loads(mod.saida(resposta)) == resposta
    assert mod.saida(None) is None


def test_copias_das_constantes_sao_iguais_as_do_motor(mod):
    motor = mod._motor()
    assert (mod.PASTAS, mod.SOLTOS, mod.EXTENSOES) == (motor.PASTAS, motor.SOLTOS, motor.EXTENSOES)
    assert Motor.SOURCES_SEM_AVISO == motor.SOURCES_SEM_AVISO


# ------------------------------------------------------------------ o disco de verdade e o processo (pasta montada uma vez)

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("memoria_tabela_em_dia")
    raiz = base / "alfa"
    (raiz / "memory").mkdir(parents=True)
    (raiz / "docs").mkdir()
    (raiz / "CLAUDE.md").write_text("# Projeto Alfa — objetivo\n", encoding="utf-8")
    (raiz / "memory" / "project_boleto.md").write_text(
        "---\nname: project-boleto\ndescription: O boleto vem do CRM\n---\n\nusa a tabela TB_BOLETO\n", encoding="utf-8")
    (raiz / "docs" / "guia.md").write_text("# Guia\n\n## Parte\nfala do flamingo\n", encoding="utf-8")
    (base / "casa").mkdir()
    return base, raiz


def test_casca_monta_com_o_motor_de_verdade_e_em_dia_nao_le_arquivo(mod, pasta, monkeypatch):
    base, raiz = pasta
    tabela = base / "t.sqlite3"
    texto = _texto(mod.responder(_abertura(raiz), {"MSS_MEMORIA_TABELA": str(tabela)}))
    assert tabela.is_file() and "montada" in texto
    motor = mod._motor()

    def proibido(*_a, **_k):
        raise AssertionError("tabela em dia: não era pra ler arquivo nem chamar o git")

    monkeypatch.setattr(motor, "_ler_projeto", proibido)
    monkeypatch.setattr(motor, "_git", proibido)
    monkeypatch.setattr(mod, "_motor", lambda: motor)
    assert mod.responder(_abertura(raiz), {"MSS_MEMORIA_TABELA": str(tabela)}) is None
    assert mod.responder(_abertura(base / "sem-memory"), {"MSS_MEMORIA_TABELA": str(tabela)}) is None


def test_processo_com_os_padroes_monta_na_pasta_do_usuario_e_sai_com_0(pasta):
    base, raiz = pasta
    casa = base / "casa"
    env = dict(os.environ, USERPROFILE=str(casa), HOME=str(casa), PYTHONIOENCODING="utf-8")
    for chave in ("MSS_MEMORIA_TABELA", "MSS_MEMORIA_TABELA_OFF", "CLAUDE_PROJECT_DIR"):
        env.pop(chave, None)
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_abertura(raiz)), capture_output=True,
                       text=True, encoding="utf-8", env=env, timeout=120)
    assert r.returncode == 0, r.stderr
    assert (casa / "mss-spec" / "memoria.sqlite3").is_file()
    assert json.loads(r.stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart"


# ------------------------------------------------------------------ ligação ao kit

def test_hook_ligado_na_abertura_e_depois_de_gravar_e_documentado(mod):
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    abertura = [h["command"] for g in cfg["SessionStart"] if not g.get("matcher") for h in g["hooks"]]
    assert any("memoria_tabela_em_dia.py" in c for c in abertura), \
        "memoria_tabela_em_dia.py fora do SessionStart (ou preso a um matcher: tem de valer em toda abertura)"
    gravacao = [g for g in cfg["PostToolUse"] if any("memoria_tabela_em_dia.py" in h["command"] for h in g["hooks"])]
    assert len(gravacao) == 1, "memoria_tabela_em_dia.py fora do PostToolUse"
    assert set(gravacao[0]["matcher"].split("|")) == set(mod.TOOLS_DE_ARQUIVO), "matcher difere das ferramentas do hook"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "| `memoria_tabela_em_dia.py` |" in readme and "MSS_MEMORIA_TABELA_OFF" in readme, \
        "hooks/README.md não descreve o hook nem o escape"
