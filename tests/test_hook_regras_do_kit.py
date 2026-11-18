"""Regras do kit pelo plugin — o hook `SessionStart` entrega os dois blocos em toda janela.

As regras do kit moram em `templates/regras-do-kit/` (1-modo-de-trabalho.md · 2-regras-criticas.md);
o `CLAUDE.md` do projeto só carrega a marca `<!-- mss-spec:regras-do-kit -->`. O hook injeta cada
bloco como `additionalContext` (uma entrada em `hooks.json` por bloco: o Claude Code corta em
10.000 caracteres cada string).

Propriedades:
- marca na raiz (`CLAUDE_PROJECT_DIR` › `cwd`) → injeta o bloco; sem marca → silêncio;
- marca vale com BOM e CRLF;
- é o hook em que silêncio custa caro: depois de confirmada a marca, defeito (bloco ilegível ou
  acima de 9.000 caracteres) → `systemMessage` de 1 linha, nunca bloco truncado;
- nunca bloqueia (exit 0); escape `MSS_REGRAS_KIT_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o `CLAUDE.md` de cada projeto e os blocos (os do kit,
ou blocos de teste) ficam num objeto do teste e entram como dado; os caminhos dos projetos não existem. O disco de
verdade (CLAUDE.md em cp1252 e os blocos do kit) fica num teste só, numa pasta montada uma vez; o processo python,
num teste só.
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
HOOK = REPO / "hooks" / "regras_do_kit.py"
BLOCOS_DIR = REPO / "templates" / "regras-do-kit"
MARCA = "<!-- mss-spec:regras-do-kit -->"
PROJ = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco" / "proj"
COM_MARCA = "# Projeto\n\n" + MARCA + "\n\nresto\n"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("regras_do_kit", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class Disco:
    """O que a regra lê, em memória: o `CLAUDE.md` de cada projeto e os blocos (os do kit, por padrão)."""

    def __init__(self, claude=COM_MARCA, blocos=None):
        self.claudes = {str(PROJ): claude} if claude is not None else {}
        self.pastas = {str(PROJ)}
        self.blocos = blocos

    def eh_pasta(self, caminho):
        return caminho in self.pastas

    def ler_claude(self, raiz):
        return self.claudes.get(raiz)

    def ler_bloco(self, nome):
        if self.blocos is None:
            return (BLOCOS_DIR / nome).read_text(encoding="utf-8")
        return self.blocos[nome]


def _evento(raiz=PROJ, **extra):
    return {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(raiz), "session_id": "s1", **extra}


def _contexto(saida):
    return saida["hookSpecificOutput"]["additionalContext"]


def _responder(mod, disco, bloco=1, ambiente=None, evento=None):
    return mod.regra(_evento() if evento is None else evento, ambiente or {}, bloco, disco)[0]


# --- entrega ----------------------------------------------------------------------------------

def test_projeto_com_marca_recebe_bloco_1(mod):
    saida = _responder(mod, Disco(), 1)
    assert _contexto(saida) == (BLOCOS_DIR / "1-modo-de-trabalho.md").read_text(encoding="utf-8")
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_projeto_com_marca_recebe_bloco_2(mod):
    saida = _responder(mod, Disco(), 2)
    assert _contexto(saida) == (BLOCOS_DIR / "2-regras-criticas.md").read_text(encoding="utf-8")


def test_projeto_sem_marca_fica_calado(mod):
    disco = Disco("# Projeto\n\nsem marca nenhuma\n")
    assert _responder(mod, disco, 1) is None and _responder(mod, disco, 2) is None


def test_projeto_sem_claude_md_fica_calado(mod):
    assert _responder(mod, Disco(None), 1) is None


def test_marca_so_vale_na_linha_exata(mod):
    """Marca citada no meio de uma frase (ex.: explicação) não ativa o hook."""
    assert _responder(mod, Disco(f"# Projeto\n\nA linha `{MARCA}` liga o hook.\n"), 1) is None


def test_marca_com_crlf_e_bom_vale(mod):
    assert _responder(mod, Disco("﻿# Projeto\r\n\r\n" + MARCA + "\r\n\r\nresto\r\n"), 1) is not None
    assert _responder(mod, Disco("﻿" + MARCA + "\r\n# Projeto\r\n"), 2) is not None


def test_prefere_claude_project_dir_ao_cwd(mod):
    saida = _responder(mod, Disco(), 1, {"CLAUDE_PROJECT_DIR": str(PROJ)}, _evento(PROJ.parent / "outro"))
    assert saida is not None and _contexto(saida)


# --- escape e falha aberta (antes da marca) ---------------------------------------------------

def test_escape_MSS_REGRAS_KIT_OFF(mod):
    assert _responder(mod, Disco(), 1, {"MSS_REGRAS_KIT_OFF": "1"}) is None


def test_entrada_malformada_fica_calada(mod):
    for ruim in (None, [], "texto", {}, {"cwd": 42}, {"cwd": ""}):
        assert _responder(mod, Disco(), 1, evento=ruim) is None


def test_bloco_inexistente_sem_marca_fica_calado(mod):
    assert _responder(mod, Disco("# sem marca\n"), 9) is None


# --- falha VISÍVEL (depois da marca) ----------------------------------------------------------

def _avisou(saida):
    assert saida is not None
    assert "additionalContext" not in json.dumps(saida), "injetou contexto num defeito"
    msg = saida["systemMessage"]
    assert "regras do kit não carregaram" in msg and "/mss-spec:doctor" in msg
    assert "\n" not in msg, "o aviso tem que ser de 1 linha"


def test_bloco_ilegivel_avisa_visivel(mod):
    _avisou(_responder(mod, Disco(blocos={}), 1))


def test_bloco_inexistente_com_marca_avisa_visivel(mod):
    """`--bloco 9` (ou malformado) é defeito do hooks.json: com a marca confirmada, avisa."""
    _avisou(_responder(mod, Disco(), 9))
    _avisou(_responder(mod, Disco(), 0))


def test_bloco_vazio_avisa_visivel(mod):
    _avisou(_responder(mod, Disco(blocos={"1-modo-de-trabalho.md": "﻿  \n"}), 1))


def test_bloco_acima_do_limite_avisa_visivel(mod):
    _avisou(_responder(mod, Disco(blocos={"1-modo-de-trabalho.md": "x" * 9001}), 1))


def test_bloco_no_limite_exato_entrega(mod):
    assert len(_contexto(_responder(mod, Disco(blocos={"1-modo-de-trabalho.md": "x" * 9000}), 1))) == 9000


def test_limite_conta_caracteres_nao_bytes(mod):
    """O teto do Claude Code é em caracteres: 9.000 'ç' (18 KB em bytes) ainda cabe."""
    assert _responder(mod, Disco(blocos={"1-modo-de-trabalho.md": "ç" * 9000}), 1) is not None


def test_blocos_reais_cabem_no_limite(mod):
    assert mod.LIMITE == 9000
    for n, nome in mod.BLOCOS.items():
        texto = (BLOCOS_DIR / nome).read_text(encoding="utf-8")
        assert 0 < len(texto) <= mod.LIMITE, f"bloco {n} ({nome}) com {len(texto)} caracteres"


def test_constantes_do_contrato(mod):
    assert mod.MARCA == MARCA
    assert mod.BLOCOS == {1: "1-modo-de-trabalho.md", 2: "2-regras-criticas.md"}


@pytest.mark.parametrize("argv,bloco", [([], 1), (["--bloco", "2"], 2), (["--bloco", "abc"], 0),
                                        (["--bloco"], 0), (["--bloco", ""], 0), (["--bloco", "9"], 9)])
def test_bloco_do_argv(mod, argv, bloco):
    """Bloco ausente vale 1; malformado vale 0 — bloco inexistente, que avisa depois da marca."""
    assert mod._bloco_do_argv(argv) == bloco


# --- registro ---------------------------------------------------------------------------------

def test_registra_entregou_e_falhou(mod):
    _, entregou = mod.regra(_evento(), {}, 1, Disco())
    _, falhou = mod.regra(_evento(), {}, 1, Disco(blocos={}))
    assert [d for d, _ in entregou] == ["entregou"] and [d for d, _ in falhou] == ["falhou"]


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def projetos(tmp_path_factory):
    base = tmp_path_factory.mktemp("regras_do_kit")
    com, sem = base / "com-marca", base / "sem-claude"
    com.mkdir()
    sem.mkdir()
    (com / "CLAUDE.md").write_bytes(("# São Paulo\n\n" + MARCA + "\n").encode("cp1252"))   # fora de UTF-8
    return com, sem


def test_casca_le_o_claude_md_e_o_bloco_do_kit(mod, projetos):
    com, sem = projetos
    assert mod.tem_marca(str(com)) is True, "o CLAUDE.md em cp1252 perdeu a marca"
    assert mod.tem_marca(str(sem)) is False
    saida = mod.responder(_evento(com), {}, 2)
    assert _contexto(saida) == (BLOCOS_DIR / "2-regras-criticas.md").read_text(encoding="utf-8")
    assert mod.responder(_evento(sem), {}, 1) is None


def test_processo_entrega_json_e_sai_zero(projetos):
    com, _ = projetos
    amb = {**os.environ}
    amb.pop("MSS_REGRAS_KIT_OFF", None)
    amb.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run([sys.executable, str(HOOK), "--bloco", "2"], input=json.dumps(_evento(com)), text=True,
                       capture_output=True, env=amb, encoding="utf-8", timeout=30)
    assert r.returncode == 0
    assert _contexto(json.loads(r.stdout)) == (BLOCOS_DIR / "2-regras-criticas.md").read_text(encoding="utf-8")


# --- fiação -----------------------------------------------------------------------------------

def test_hooks_json_tem_duas_entradas_no_session_start():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    grupos = cfg["hooks"]["SessionStart"]
    comandos = [h["command"] for g in grupos for h in g["hooks"]]
    assert sum('regras_do_kit.py" --bloco 1' in c for c in comandos) == 1
    assert sum('regras_do_kit.py" --bloco 2' in c for c in comandos) == 1
    for g in grupos:
        if any("regras_do_kit.py" in h["command"] for h in g["hooks"]):
            assert "matcher" not in g, "sem matcher: vale pra startup, resume, clear e compact"


def test_documentado_no_readme():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "regras_do_kit.py" in readme
    assert "MSS_REGRAS_KIT_OFF" in readme
    assert "mss-spec:regras-do-kit" in readme
    assert "falha visível" in readme.lower()
