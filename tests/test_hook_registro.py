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

Camadas (2026-11-17): a linha (`linha_de`) e o `resumo` são testados em memória. "Grava só quando age e nunca o
texto" é conferido no arquivo de cada hook, pelas anotações que a `regra` dele devolve (a casca só repassa ao
registro). "Registro que não grava não muda a decisão" é conferido aqui em todos os hooks, sem processo: a casca
decide antes de registrar, e o `_anotar` de cada hook engole o defeito do registro. O disco de verdade (gravar,
rodízio, ler o `.1`) fica num teste só; o processo (`_registro.py resumo`), num teste só.
"""
import datetime
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
QUANDO = datetime.datetime(2026, 11, 17, 12, 0, 0)
HOOKS_DO_KIT = sorted(p.stem for p in HOOKS.glob("*.py") if not p.name.startswith("_"))


@pytest.fixture(scope="module")
def reg():
    spec = importlib.util.spec_from_file_location("_registro_teste", HOOKS / "_registro.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --- a linha: campos, só rótulos, escape --------------------------------------------------------

def test_linha_tem_os_campos_e_so_o_inicio_da_sessao(reg):
    linha = reg.linha_de("git_publicacao", "negou", "git push", {"cwd": "/c/proj", "session_id": "abcdef123456",
                                                                  "prompt": SEGREDO}, {}, QUANDO)
    assert linha == {"quando": "2026-11-17T12:00:00", "hook": "git_publicacao", "decisao": "negou",
                     "detalhe": "git push", "projeto": "proj", "sessao": "abcdef12"}
    assert SEGREDO not in json.dumps(linha), "o texto do evento entrou na linha"


def test_projeto_vem_do_claude_project_dir_antes_do_cwd(reg):
    linha = reg.linha_de("h", "negou", "", {"cwd": "/c/outro"}, {"CLAUDE_PROJECT_DIR": "/c/kit"}, QUANDO)
    assert linha["projeto"] == "kit"
    assert reg.linha_de("h", "negou", "", None, {}, QUANDO)["projeto"] == ""


def test_detalhe_curto_e_numa_linha_so(reg):
    linha = reg.linha_de("h", "negou", "a\nb" + "c" * 500, {}, {}, QUANDO)
    assert "\n" not in linha["detalhe"] and len(linha["detalhe"]) <= reg.TETO_DETALHE


def test_escape_do_owner_nao_gera_linha(reg):
    assert reg.linha_de("h", "negou", "x", {}, {"MSS_REGISTRO_OFF": "1"}, QUANDO) is None


def test_padrao_e_na_pasta_do_kit_no_home(reg):
    assert reg.caminho({}) == Path.home() / ".claude" / "mss-spec" / "registro-hooks.jsonl"
    assert reg.caminho({"MSS_REGISTRO_ARQUIVO": "x/r.jsonl"}) == Path("x/r.jsonl")


# --- registro que não grava não muda nenhuma decisão (todos os hooks) ------------------------------

def _hook(nome):
    spec = importlib.util.spec_from_file_location(f"{nome}_registro_teste", HOOKS / f"{nome}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize("nome", HOOKS_DO_KIT)
def test_registro_quebrado_nao_derruba_o_hook(nome):
    """O `_anotar` de cada hook engole o defeito do registro: a decisão já foi tomada pela regra e sai igual."""
    mod = _hook(nome)
    assert hasattr(mod, "_anotar"), f"{nome} registra sem passar pelo _anotar"

    def quebrado(*_a, **_k):
        raise OSError("registro sem onde gravar")

    mod._registrar = quebrado
    mod._anotar("negou", "x", {"session_id": "s"})
    mod._registrar = None
    mod._anotar("negou", "x", {"session_id": "s"})


def test_lista_dos_hooks_bate_com_o_hooks_json():
    """Hook novo que entra no `hooks.json` entra nesta varredura."""
    cfg = (HOOKS / "hooks.json").read_text(encoding="utf-8")
    assert len(HOOKS_DO_KIT) == 18
    assert [n for n in HOOKS_DO_KIT if f"{n}.py" not in cfg] == [], "hook fora do hooks.json"


# --- leitura: o resumo -----------------------------------------------------------------------------

def _linhas():
    base = {"projeto": "a", "sessao": "s"}
    return ([{**base, "quando": "2026-11-17T10:00:00", "hook": "git_publicacao", "decisao": "negou",
              "detalhe": "git push"}] * 3
            + [{**base, "quando": "2026-11-17T11:00:00", "hook": "recall_memoria", "decisao": "injetou",
                "detalhe": "docs/decisoes.md:25"},
               {**base, "quando": "2020-01-01T00:00:00", "hook": "velho", "decisao": "avisou", "detalhe": ""}])


def test_resumo_conta_por_hook_e_decisao(reg):
    texto = reg.resumo(_linhas())
    assert "git_publicacao" in texto and "3×" in texto
    assert "recall_memoria" in texto and "docs/decisoes.md:25" in texto
    assert "última: 2026-11-17T10:00:00" in texto


def test_resumo_por_dias_corta_o_antigo_e_sem_registro_nao_quebra(reg):
    assert "velho" in reg.resumo(_linhas()) and "velho" not in reg.resumo(_linhas(), dias=365 * 3)
    assert "nenhum" in reg.resumo([]).lower()
    assert "nenhum" in reg.resumo([{"quando": "2000-01-01T00:00:00", "hook": "h", "decisao": "d"}], dias=1).lower()


# --- o disco de verdade e o processo -------------------------------------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    return tmp_path_factory.mktemp("registro")


def test_disco_grava_faz_rodizio_e_le_o_1_e_o_atual(reg, pasta, monkeypatch):
    tmp_path = pasta
    arquivo = tmp_path / "registro-hooks.jsonl"
    amb = {"MSS_REGISTRO_ARQUIVO": str(arquivo)}
    arquivo.write_text(json.dumps({"hook": "antigo", "decisao": "negou"}) + "\n" + "x" * 50 + "\n", encoding="utf-8")
    monkeypatch.setattr(reg, "TETO_BYTES", 40)
    reg.registrar("git_publicacao", "negou", "git push", {"cwd": "/c/proj"}, ambiente=amb)
    assert (tmp_path / "registro-hooks.jsonl.1").read_text(encoding="utf-8").startswith('{"hook": "antigo"')
    assert [l["hook"] for l in reg.ler(amb)] == ["antigo", "git_publicacao"], "não leu o .1 e o atual, em ordem"
    reg.registrar("h", "negou", "x", {}, ambiente={"MSS_REGISTRO_ARQUIVO": str(arquivo / "nao" / "da.jsonl")})


def test_processo_resumo(pasta):
    arquivo = pasta / "registro-do-processo.jsonl"
    arquivo.write_text(json.dumps({"quando": "2026-11-17T10:00:00", "hook": "git_publicacao", "decisao": "negou",
                                   "detalhe": "git push"}) + "\n", encoding="utf-8")
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_")}
    proc = subprocess.run([sys.executable, str(HOOKS / "_registro.py"), "resumo"], capture_output=True, text=True,
                          encoding="utf-8", timeout=30, env={**amb, "MSS_REGISTRO_ARQUIVO": str(arquivo)})
    assert proc.returncode == 0, proc.stderr
    assert "git_publicacao" in proc.stdout and "git push" in proc.stdout


def test_documentado_no_readme():
    readme = (HOOKS / "README.md").read_text(encoding="utf-8")
    assert "MSS_REGISTRO_OFF" in readme
    assert "_registro.py resumo" in readme
