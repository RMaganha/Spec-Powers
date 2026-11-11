"""Hook `memoria_tabela_em_dia.py` — a tabela de memória se atualiza sozinha (parte 2, 0.56.0).

Por que existe: a parte 1 entregou um modo manual e a tabela real ficou só com o kit; o owner recusou comando
pra lembrar — "vai fazer se perder quando eu perguntar" (caso F-057). Decisões 13 e 15 da spec
(docs/specs/memoria-em-tabela.md): a tabela se atualiza quando a conversa abre no projeto (montada na hora se
não existir) e logo depois de cada gravação de memória. Calado quando dá certo; nunca trava.
"""
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from test_memoria_tabela import _grava, _projeto, _sql

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "memoria_tabela_em_dia.py"


def _mod():
    spec = importlib.util.spec_from_file_location("memoria_tabela_em_dia", HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _amb(tabela, **extra):
    return dict({"MSS_MEMORIA_TABELA": str(tabela)}, **extra)


def _abertura(raiz):
    return {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(raiz)}


def _gravou(raiz, rel, tool="Write"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(raiz),
            "tool_input": {"file_path": str(Path(raiz) / rel)}}


def _linhas(tabela, onde="tipo <> 'controle'"):
    return _sql(tabela, f"SELECT count(*) FROM memoria WHERE {onde}")[0][0]


# ------------------------------------------------------------------ abertura da conversa

def test_abertura_sem_tabela_monta_na_hora_e_diz_ao_assistente(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "casa" / "t.sqlite3"
    saida = _mod().responder(_abertura(raiz), _amb(tabela))
    assert tabela.is_file() and _linhas(tabela) == 12
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    texto = saida["hookSpecificOutput"]["additionalContext"]
    assert "montada" in texto and "12" in texto
    assert "systemMessage" not in saida, "é recado pro assistente: o owner não tem nada a fazer"


def test_abertura_com_a_tabela_em_dia_fica_calada_e_nao_le_arquivo(tmp_path, monkeypatch):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.responder(_abertura(raiz), _amb(tabela))
    motor = mod._motor()

    def proibido(*_a, **_k):
        raise AssertionError("tabela em dia: não era pra ler arquivo nem chamar o git")

    monkeypatch.setattr(motor, "_ler_projeto", proibido)
    monkeypatch.setattr(motor, "_git", proibido)
    monkeypatch.setattr(mod, "_motor", lambda: motor)
    assert mod.responder(_abertura(raiz), _amb(tabela)) is None


def test_abertura_com_arquivo_mudado_por_fora_atualiza_calada(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.responder(_abertura(raiz), _amb(tabela))
    _grava(raiz, "docs/chegou-no-pull.md", "# Novo\n\n## Parte\nveio de fora falando do flamingo\n")
    assert mod.responder(_abertura(raiz), _amb(tabela)) is None
    assert _sql(tabela, "SELECT arq FROM memoria WHERE memoria MATCH 'flamingo'") == [("docs/chegou-no-pull.md",)]


def test_segundo_projeto_na_mesma_tabela_tambem_e_montado_na_abertura(tmp_path):
    tabela, mod = tmp_path / "t.sqlite3", _mod()
    mod.responder(_abertura(_projeto(tmp_path, "alfa", "Projeto Alfa")), _amb(tabela))
    saida = mod.responder(_abertura(_projeto(tmp_path, "beta", "Projeto Beta")), _amb(tabela))
    assert "montada" in saida["hookSpecificOutput"]["additionalContext"]
    assert _linhas(tabela, "projeto = 'Projeto Beta' AND tipo <> 'controle'") == 12


# ------------------------------------------------------------------ depois de gravar

def test_gravou_memoria_a_tabela_acompanha_sem_dizer_nada(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.responder(_abertura(raiz), _amb(tabela))
    _grava(raiz, "memory/feedback_novo.md", "---\nname: feedback-novo\ndescription: nota nova\n---\n\ncorpo novo tucano\n")
    for tool in ("Write", "Edit", "MultiEdit"):
        assert mod.responder(_gravou(raiz, "memory/feedback_novo.md", tool), _amb(tabela)) is None
    assert _sql(tabela, "SELECT arq FROM memoria WHERE memoria MATCH 'tucano'") == [("memory/feedback_novo.md",)]


def test_gravou_documento_solto_ou_html_tambem_conta(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.responder(_abertura(raiz), _amb(tabela))
    for rel, texto, palavra in (("docs/specs/novo.md", "# Novo\n\n## Estado atual\nfala do pelicano\n", "pelicano"),
                                ("to-dolist.md", "# To-do\n\n- comprar o dominio albatroz\n", "albatroz"),
                                ("docs/pagina.html", "<html><body><h2>Pagina</h2><p>fala do tamandua</p></body></html>", "tamandua")):
        _grava(raiz, rel, texto)
        assert mod.responder(_gravou(raiz, rel), _amb(tabela)) is None
        assert _sql(tabela, f"SELECT arq FROM memoria WHERE memoria MATCH '{palavra}'") == [(rel,)], rel


def test_gravacao_fora_do_alcance_nao_mexe_em_nada(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    outro = _projeto(tmp_path, "beta", "Projeto Beta")
    eventos = [_gravou(raiz, "src/app.py"), _gravou(raiz, "docs/variaveis.txt"), _gravou(raiz, "README.md"),
               _gravou(outro, "memory/project_boleto.md") | {"cwd": str(raiz)},
               _gravou(raiz, "memory/project_boleto.md", tool="Bash"),
               {"hook_event_name": "PostToolUse", "tool_name": "Write", "cwd": str(raiz), "tool_input": {}},
               {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": "oi"}]
    for evento in eventos:
        assert mod.responder(evento, _amb(tabela)) is None
    assert not tabela.exists(), "nenhum desses eventos é gravação de memória deste projeto"


def test_caminho_relativo_e_resolvido_pela_raiz_do_projeto(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    evento = _gravou(raiz, "x") | {"tool_input": {"file_path": "memory/project_boleto.md"}}
    assert mod.responder(evento, _amb(tabela)) is None
    assert _linhas(tabela) == 12


def test_a_raiz_e_a_do_projeto_da_janela_nao_a_pasta_do_evento(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    evento = _abertura(raiz / "docs")
    assert mod.responder(evento, _amb(tabela, CLAUDE_PROJECT_DIR=str(raiz))) is not None
    assert _sql(tabela, "SELECT DISTINCT raiz FROM memoria") == [(raiz.resolve().as_posix(),)]


# ------------------------------------------------------------------ quando não age e quando falha

def test_projeto_sem_pasta_memory_nao_ganha_tabela(tmp_path):
    raiz, tabela = tmp_path / "solto", tmp_path / "t.sqlite3"
    _grava(raiz, "docs/guia.md", "# Guia\n\n## Parte\ntexto\n")
    assert _mod().responder(_abertura(raiz), _amb(tabela)) is None
    assert not tabela.exists()


def test_escape_do_owner_desliga(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    assert _mod().responder(_abertura(raiz), _amb(tabela, MSS_MEMORIA_TABELA_OFF="1")) is None
    assert not tabela.exists()


def _presa(tabela):
    outro = sqlite3.connect(str(tabela))
    outro.execute("BEGIN EXCLUSIVE")
    return outro


def test_tabela_presa_nao_trava_a_abertura_e_manda_buscar_nos_arquivos(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.responder(_abertura(raiz), _amb(tabela))
    _grava(raiz, "to-dolist.md", "# To-do\n\n- item novo\n")
    outro = _presa(tabela)
    try:
        saida = mod.responder(_abertura(raiz), _amb(tabela))
        calado = mod.responder(_gravou(raiz, "to-dolist.md"), _amb(tabela))
    finally:
        outro.rollback()
        outro.close()
    texto = saida["hookSpecificOutput"]["additionalContext"]
    assert "memory/MEMORY.md" in texto and "systemMessage" not in saida
    assert calado is None, "depois de gravar a falha é calada: a busca confere de novo antes de procurar"


def test_evento_torto_nunca_levanta():
    mod = _mod()
    for evento in (None, [], "x", {}, {"hook_event_name": "SessionStart"}, {"hook_event_name": "SessionStart", "cwd": 3},
                   {"hook_event_name": "PostToolUse", "cwd": "Z:/nao/existe", "tool_name": "Write", "tool_input": None}):
        assert mod.responder(evento, {}) is None


def test_copias_das_constantes_sao_iguais_as_do_motor():
    mod = _mod()
    motor = mod._motor()
    assert (mod.PASTAS, mod.SOLTOS, mod.EXTENSOES) == (motor.PASTAS, motor.SOLTOS, motor.EXTENSOES)


# ------------------------------------------------------------------ como processo, com os padrões

def _rodar(evento, casa, raw=None, env_extra=None):
    env = dict(os.environ, USERPROFILE=str(casa), HOME=str(casa), PYTHONIOENCODING="utf-8")
    for chave in ("MSS_MEMORIA_TABELA", "MSS_MEMORIA_TABELA_OFF", "CLAUDE_PROJECT_DIR"):
        env.pop(chave, None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(evento),
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)


def test_processo_com_os_padroes_monta_na_pasta_do_usuario_e_sai_com_0(tmp_path):
    raiz, casa = _projeto(tmp_path), tmp_path / "casa"
    casa.mkdir()
    r = _rodar(_abertura(raiz), casa)
    assert r.returncode == 0, r.stderr
    assert (casa / "mss-spec" / "memoria.sqlite3").is_file()
    assert json.loads(r.stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    de_novo = _rodar(_abertura(raiz), casa)
    assert de_novo.returncode == 0 and de_novo.stdout.strip() == "", "em dia: silêncio"


def test_processo_com_entrada_torta_sai_com_0_calado(tmp_path):
    r = _rodar(None, tmp_path, raw="{nao é json")
    assert r.returncode == 0 and r.stdout.strip() == ""


# ------------------------------------------------------------------ ligação ao kit

def test_hook_ligado_na_abertura_e_depois_de_gravar_e_documentado():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    abertura = [h["command"] for g in cfg["SessionStart"] if not g.get("matcher") for h in g["hooks"]]
    assert any("memoria_tabela_em_dia.py" in c for c in abertura), \
        "memoria_tabela_em_dia.py fora do SessionStart (ou preso a um matcher: tem de valer em toda abertura)"
    gravacao = [g for g in cfg["PostToolUse"] if any("memoria_tabela_em_dia.py" in h["command"] for h in g["hooks"])]
    assert len(gravacao) == 1, "memoria_tabela_em_dia.py fora do PostToolUse"
    assert set(gravacao[0]["matcher"].split("|")) == set(_mod().TOOLS_DE_ARQUIVO), "matcher difere das ferramentas do hook"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "| `memoria_tabela_em_dia.py` |" in readme and "MSS_MEMORIA_TABELA_OFF" in readme, \
        "hooks/README.md não descreve o hook nem o escape"
