"""Orçamento da partida — avisa, na abertura da janela, quando os arquivos da partida estouram o teto.

Caso F-030: no Whats a partida lia `CLAUDE.md` 28 KB + `MAPA.md` 60 KB + `INDEX.md` 71 KB (tetos
10 · 6 · 7 KB). A janela passou de 73 mil pra 139 mil tokens antes da 1ª resposta, e item velho de
backlog (n8n, cotação) virou "fato" no plano de deploy. O `doctor` media e ninguém rodava.
Hook `SessionStart` mede na hora em que a leitura acontece.

Propriedades:
- dentro do teto (ou arquivo ausente) → silêncio;
- acima → `additionalContext` que nomeia SÓ os arquivos estourados, com bytes e teto, e diz o que
  ler de cada um (MAPA → "Onde estamos"; INDEX → "Em andamento") + backlog não é estado atual;
- texto ≤ 1.000 bytes mesmo com os quatro estourados;
- tetos = os do `tests/test_orcamento_contexto.py` e do `templates/rodizio_partida.py`;
- nunca bloqueia; falha ABERTA; escape `MSS_ORCAMENTO_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "orcamento_partida.py"


def _mod(caminho=HOOK, nome="orcamento_partida"):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path, claude=0, mapa=0, index=0, memory=0):
    """Projeto com os arquivos da partida no tamanho pedido (0 = arquivo ausente)."""
    for rel, n in (("CLAUDE.md", claude), ("docs/superpowers/MAPA.md", mapa),
                   ("docs/superpowers/INDEX.md", index), ("memory/MEMORY.md", memory)):
        if n:
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x" * n)
    return tmp_path


def _evento(raiz, **extra):
    return {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(raiz),
            "session_id": "s1", **extra}


def _contexto(saida):
    return saida["hookSpecificOutput"]["additionalContext"]


# --- AC1: silêncio dentro do orçamento --------------------------------------------------------

def test_dentro_do_teto_fica_calado(tmp_path):
    raiz = _projeto(tmp_path, claude=8000, mapa=3000, index=5000, memory=3000)
    assert _mod().responder(_evento(raiz), {}) is None


def test_projeto_sem_os_arquivos_fica_calado(tmp_path):
    assert _mod().responder(_evento(tmp_path), {}) is None


# --- AC2: acima do teto avisa, só do que estourou ---------------------------------------------

def test_numeros_do_whats_avisam_mapa_index_e_claude(tmp_path):
    """Os tamanhos reais da janela do F-030."""
    raiz = _projeto(tmp_path, claude=27933, mapa=60098, index=70720, memory=1661)
    txt = _contexto(_mod().responder(_evento(raiz), {}))
    for nome in ("CLAUDE.md", "MAPA.md", "INDEX.md"):
        assert nome in txt, f"não citou {nome} estourado"
    assert "MEMORY.md" not in txt, "citou o índice de memória, que está dentro do teto"
    assert "60 KB" in txt and "teto 6 KB" in txt, "não deu bytes e teto do MAPA"


def test_mapa_estourado_manda_ler_so_onde_estamos(tmp_path):
    raiz = _projeto(tmp_path, mapa=20000)
    txt = _contexto(_mod().responder(_evento(raiz), {}))
    assert "Onde estamos" in txt
    assert "INDEX.md" not in txt, "citou o INDEX, que nem existe"


def test_index_estourado_manda_ler_so_em_andamento(tmp_path):
    raiz = _projeto(tmp_path, index=20000)
    txt = _contexto(_mod().responder(_evento(raiz), {}))
    assert "Em andamento" in txt


def test_aviso_diz_que_backlog_nao_e_estado_atual(tmp_path):
    """O n8n e a cotação do F-030 vieram do backlog lido como fato."""
    raiz = _projeto(tmp_path, index=20000)
    txt = _contexto(_mod().responder(_evento(raiz), {})).lower()
    assert "backlog" in txt and "não" in txt and "fato" in txt


def test_aviso_manda_nao_ler_inteiro_e_avisar_o_owner(tmp_path):
    raiz = _projeto(tmp_path, mapa=20000)
    txt = _contexto(_mod().responder(_evento(raiz), {}))
    assert "inteiro" in txt, "não disse pra não ler o arquivo inteiro"
    assert "owner" in txt and "/mss-spec:doctor" in txt, "não mandou avisar o owner com o conserto"


def test_texto_cabe_em_mil_bytes_com_tudo_estourado(tmp_path):
    raiz = _projeto(tmp_path, claude=99999, mapa=99999, index=99999, memory=99999)
    txt = _contexto(_mod().responder(_evento(raiz), {}))
    assert len(txt.encode("utf-8")) <= 1000, f"aviso com {len(txt.encode('utf-8'))} bytes"


def test_saida_e_do_evento_session_start_com_system_message(tmp_path):
    raiz = _projeto(tmp_path, mapa=20000)
    saida = _mod().responder(_evento(raiz), {})
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "MAPA.md" in saida["systemMessage"]


def test_prefere_claude_project_dir_ao_cwd(tmp_path):
    proj = _projeto(tmp_path / "proj", mapa=20000)
    outro = tmp_path / "outro"
    outro.mkdir()
    saida = _mod().responder(_evento(outro), {"CLAUDE_PROJECT_DIR": str(proj)})
    assert saida is not None and "MAPA.md" in _contexto(saida)


# --- AC3: escape e falha aberta ---------------------------------------------------------------

def test_escape_do_owner(tmp_path):
    raiz = _projeto(tmp_path, mapa=20000)
    assert _mod().responder(_evento(raiz), {"MSS_ORCAMENTO_OFF": "1"}) is None


def test_entrada_malformada_libera():
    mod = _mod()
    for ruim in (None, [], "texto", {}, {"cwd": 42}, {"cwd": ""}):
        assert mod.responder(ruim, {}) is None


# --- AC4: tetos numa fonte só -----------------------------------------------------------------

def test_tetos_batem_com_o_teste_de_orcamento_e_o_rodizio():
    hook = _mod()
    orc = _mod(REPO / "tests" / "test_orcamento_contexto.py", "test_orcamento_contexto_ref")
    rod = _mod(REPO / "templates" / "rodizio_partida.py", "rodizio_partida_ref")
    tetos = dict(hook.ARQUIVOS)
    assert tetos["CLAUDE.md"] == orc.TETO_CLAUDE_MD
    assert tetos["docs/superpowers/MAPA.md"] == orc.TETO_MAPA == rod.TETO_MAPA
    assert tetos["docs/superpowers/INDEX.md"] == orc.TETO_INDEX == rod.TETO_INDEX
    assert tetos["memory/MEMORY.md"] == orc.TETO_MEMORY_TOPO


# --- AC5: processo e registro no plugin -------------------------------------------------------

def _rodar(evento, env=None):
    amb = {**os.environ, **(env or {})}
    amb.pop("MSS_ORCAMENTO_OFF", None)
    amb.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento), text=True,
                          capture_output=True, env=amb, encoding="utf-8", timeout=30)


def test_processo_avisa_com_json_e_sai_zero(tmp_path):
    raiz = _projeto(tmp_path, mapa=20000)
    r = _rodar(_evento(raiz))
    assert r.returncode == 0
    assert "MAPA.md" in _contexto(json.loads(r.stdout))


def test_processo_calado_nao_imprime(tmp_path):
    r = _rodar(_evento(tmp_path))
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_processo_entrada_malformada_sai_zero():
    r = subprocess.run([sys.executable, str(HOOK)], input="{nao é json", text=True,
                       capture_output=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_hook_registrado_no_session_start():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for grupo in cfg["hooks"].get("SessionStart", []) for h in grupo["hooks"]]
    assert any("orcamento_partida.py" in c for c in comandos), "orcamento_partida.py fora do SessionStart"
