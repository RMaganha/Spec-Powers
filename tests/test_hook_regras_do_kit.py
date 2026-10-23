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
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "regras_do_kit.py"
BLOCOS_DIR = REPO / "templates" / "regras-do-kit"
MARCA = "<!-- mss-spec:regras-do-kit -->"


def _mod(caminho=HOOK, nome="regras_do_kit"):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path, claude="# Projeto\n\n" + MARCA + "\n\nresto\n"):
    """Projeto com `CLAUDE.md` (None = sem arquivo)."""
    if claude is not None:
        (tmp_path / "CLAUDE.md").write_bytes(claude.encode("utf-8"))
    return tmp_path


def _proj(tmp_path, nome="proj"):
    """Projeto com marca numa subpasta (libera o resto do `tmp_path` pra outros arquivos)."""
    pasta = tmp_path / nome
    pasta.mkdir()
    return _projeto(pasta)


def _evento(raiz, **extra):
    return {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(raiz),
            "session_id": "s1", **extra}


def _contexto(saida):
    return saida["hookSpecificOutput"]["additionalContext"]


# --- entrega ----------------------------------------------------------------------------------

def test_projeto_com_marca_recebe_bloco_1(tmp_path):
    saida = _mod().responder(_evento(_projeto(tmp_path)), {}, 1)
    esperado = (BLOCOS_DIR / "1-modo-de-trabalho.md").read_text(encoding="utf-8")
    assert _contexto(saida) == esperado
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_projeto_com_marca_recebe_bloco_2(tmp_path):
    saida = _mod().responder(_evento(_projeto(tmp_path)), {}, bloco=2)
    esperado = (BLOCOS_DIR / "2-regras-criticas.md").read_text(encoding="utf-8")
    assert _contexto(saida) == esperado
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_bloco_padrao_e_o_1(tmp_path):
    saida = _mod().responder(_evento(_projeto(tmp_path)), {})
    assert _contexto(saida) == (BLOCOS_DIR / "1-modo-de-trabalho.md").read_text(encoding="utf-8")


def test_projeto_sem_marca_fica_calado(tmp_path):
    raiz = _projeto(tmp_path, "# Projeto\n\nsem marca nenhuma\n")
    assert _mod().responder(_evento(raiz), {}, 1) is None
    assert _mod().responder(_evento(raiz), {}, 2) is None


def test_projeto_sem_claude_md_fica_calado(tmp_path):
    assert _mod().responder(_evento(_projeto(tmp_path, None)), {}, 1) is None


def test_marca_so_vale_na_linha_exata(tmp_path):
    """Marca citada no meio de uma frase (ex.: explicação) não ativa o hook."""
    raiz = _projeto(tmp_path, f"# Projeto\n\nA linha `{MARCA}` liga o hook.\n")
    assert _mod().responder(_evento(raiz), {}, 1) is None


def test_marca_com_crlf_e_bom_vale(tmp_path):
    raiz = _projeto(tmp_path, "﻿# Projeto\r\n\r\n" + MARCA + "\r\n\r\nresto\r\n")
    saida = _mod().responder(_evento(raiz), {}, 1)
    assert saida is not None and _contexto(saida)


def test_marca_na_1a_linha_com_bom_vale(tmp_path):
    raiz = _projeto(tmp_path, "﻿" + MARCA + "\r\n# Projeto\r\n")
    assert _mod().responder(_evento(raiz), {}, 2) is not None


def test_claude_md_em_cp1252_com_marca_ainda_injeta(tmp_path):
    """CLAUDE.md salvo em cp1252 (acento fora de UTF-8) não desliga as regras: a marca é ASCII."""
    raiz = _proj(tmp_path)
    (raiz / "CLAUDE.md").write_bytes(("# São Paulo\n\n" + MARCA + "\n").encode("cp1252"))
    assert _mod().tem_marca(str(raiz)) is True
    assert "additionalContext" in _mod().responder(_evento(raiz), {})["hookSpecificOutput"]


def test_tem_marca_direto(tmp_path):
    mod = _mod()
    assert mod.tem_marca(str(_projeto(tmp_path))) is True
    assert mod.tem_marca(str(tmp_path / "nao-existe")) is False


def test_prefere_claude_project_dir_ao_cwd(tmp_path):
    proj = _proj(tmp_path)
    outro = tmp_path / "outro"
    outro.mkdir()
    saida = _mod().responder(_evento(outro), {"CLAUDE_PROJECT_DIR": str(proj)}, 1)
    assert saida is not None and _contexto(saida)


# --- escape e falha aberta (antes da marca) ---------------------------------------------------

def test_escape_MSS_REGRAS_KIT_OFF(tmp_path):
    raiz = _projeto(tmp_path)
    assert _mod().responder(_evento(raiz), {"MSS_REGRAS_KIT_OFF": "1"}, 1) is None


def test_entrada_malformada_fica_calada():
    mod = _mod()
    for ruim in (None, [], "texto", {}, {"cwd": 42}, {"cwd": ""}):
        assert mod.responder(ruim, {}, 1) is None


def test_bloco_inexistente_sem_marca_fica_calado(tmp_path):
    assert _mod().responder(_evento(_projeto(tmp_path, "# sem marca\n")), {}, 9) is None


# --- falha VISÍVEL (depois da marca) ----------------------------------------------------------

def _avisou(saida):
    assert saida is not None
    assert "additionalContext" not in json.dumps(saida), "injetou contexto num defeito"
    msg = saida["systemMessage"]
    assert "regras do kit não carregaram" in msg and "/mss-spec:doctor" in msg
    assert "\n" not in msg, "o aviso tem que ser de 1 linha"


def test_bloco_ilegivel_avisa_visivel(tmp_path):
    mod = _mod()
    mod.BLOCOS = {1: "nao-existe.md", 2: "nao-existe-tambem.md"}
    _avisou(mod.responder(_evento(_projeto(tmp_path)), {}, 1))


def test_bloco_inexistente_com_marca_avisa_visivel(tmp_path):
    """`--bloco 9` (ou malformado) é defeito do hooks.json: com a marca confirmada, avisa."""
    _avisou(_mod().responder(_evento(_proj(tmp_path)), {}, 9))


def test_bloco_acima_do_limite_avisa_visivel(tmp_path):
    pasta = tmp_path / "blocos"
    pasta.mkdir()
    (pasta / "grande.md").write_text("x" * 9001, encoding="utf-8")
    mod = _mod()
    mod.PASTA_BLOCOS = pasta
    mod.BLOCOS = {1: "grande.md"}
    _avisou(mod.responder(_evento(_proj(tmp_path)), {}, 1))


def test_bloco_no_limite_exato_entrega(tmp_path):
    pasta = tmp_path / "blocos"
    pasta.mkdir()
    (pasta / "justo.md").write_text("x" * 9000, encoding="utf-8")
    mod = _mod()
    mod.PASTA_BLOCOS = pasta
    mod.BLOCOS = {1: "justo.md"}
    saida = mod.responder(_evento(_proj(tmp_path)), {}, 1)
    assert len(_contexto(saida)) == 9000


def test_limite_conta_caracteres_nao_bytes(tmp_path):
    """O teto do Claude Code é em caracteres: 9.000 'ç' (18 KB em bytes) ainda cabe."""
    pasta = tmp_path / "blocos"
    pasta.mkdir()
    (pasta / "acentos.md").write_text("ç" * 9000, encoding="utf-8")
    mod = _mod()
    mod.PASTA_BLOCOS = pasta
    mod.BLOCOS = {1: "acentos.md"}
    assert mod.responder(_evento(_proj(tmp_path)), {}, 1) is not None


def test_blocos_reais_cabem_no_limite():
    mod = _mod()
    assert mod.LIMITE == 9000
    for n, nome in mod.BLOCOS.items():
        texto = (BLOCOS_DIR / nome).read_text(encoding="utf-8")
        assert 0 < len(texto) <= mod.LIMITE, f"bloco {n} ({nome}) com {len(texto)} caracteres"


def test_constantes_do_contrato():
    mod = _mod()
    assert mod.MARCA == MARCA
    assert mod.BLOCOS == {1: "1-modo-de-trabalho.md", 2: "2-regras-criticas.md"}


# --- registro ---------------------------------------------------------------------------------

def test_registra_entregou_e_falhou(tmp_path, monkeypatch):
    arquivo = tmp_path / "reg" / "registro-hooks.jsonl"
    monkeypatch.setenv("MSS_REGISTRO_ARQUIVO", str(arquivo))
    monkeypatch.delenv("MSS_REGISTRO_OFF", raising=False)
    raiz = _proj(tmp_path)
    mod = _mod()
    mod.responder(_evento(raiz), {}, 1)
    mod.BLOCOS = {1: "nao-existe.md"}
    mod.responder(_evento(raiz), {}, 1)
    linhas = [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines()]
    assert [(x["hook"], x["decisao"]) for x in linhas] == [("regras_do_kit", "entregou"),
                                                           ("regras_do_kit", "falhou")]


# --- processo e registro no plugin ------------------------------------------------------------

def _rodar(evento, bloco="1", env=None, entrada=None):
    amb = {**os.environ, **(env or {})}
    amb.pop("MSS_REGRAS_KIT_OFF", None)
    amb.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run([sys.executable, str(HOOK), "--bloco", bloco],
                          input=json.dumps(evento) if entrada is None else entrada, text=True,
                          capture_output=True, env=amb, encoding="utf-8", timeout=30)


def test_processo_entrega_json_e_sai_zero(tmp_path):
    r = _rodar(_evento(_projeto(tmp_path)), "2")
    assert r.returncode == 0
    assert _contexto(json.loads(r.stdout)) == (BLOCOS_DIR / "2-regras-criticas.md").read_text(encoding="utf-8")


def test_processo_sem_marca_nao_imprime(tmp_path):
    r = _rodar(_evento(_projeto(tmp_path, "# sem marca\n")))
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_processo_sai_zero_com_entrada_malformada():
    r = _rodar({}, entrada="{nao é json")
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_processo_sai_zero_com_bloco_malformado(tmp_path):
    for ruim in ("abc", "", "9"):
        r = _rodar(_evento(_projeto(tmp_path)), ruim)
        assert r.returncode == 0, r.stderr


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
