"""Comportamento do gerador do painel "anatomia de runtime" (templates/anatomia.py).

O painel responde o que o mapa-neural não responde: QUANDO cada peça do kit entra na janela
(partida/evento/demanda/fecho), QUEM lê × escreve cada artefato, riscos e fila. Regra dura:
número que aparece no HTML é MEDIDO (manifesto, frontmatter, bytes, tabela do EVALS) — nunca
escrito à mão; e o metadado curado (matriz/riscos) só pode citar alvo que EXISTE (painel não
mente em silêncio).
"""
import importlib.util
import re
import shutil
import subprocess
import sys

import pytest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _mod():
    spec = importlib.util.spec_from_file_location("anatomia", REPO / "templates" / "anatomia.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def anat():
    return _mod()


# ---------------------------------------------------------------- extração (medido, não escrito)

def test_versao_dos_manifestos(anat):
    """A versão vem do plugin.json e tem que bater com o marketplace.json."""
    v = anat.versao_kit(REPO)
    assert re.fullmatch(r"\d+\.\d+\.\d+", v), f"versão não-semver: {v!r}"


def test_versao_tolera_bom(tmp_path, anat):
    """Regressão de 2026-08-25: PowerShell 5.1 gravou manifesto com BOM e o json.loads padrão
    explodiu. O gerador lê com utf-8-sig — manifesto com BOM não pode derrubar o painel."""
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_bytes(
        b'\xef\xbb\xbf{"name": "x", "version": "9.9.9"}')
    assert anat.versao_kit(tmp_path) == "9.9.9"


def test_comandos_extraidos_do_frontmatter(anat):
    """Todo commands/*.md entra com nome, bytes>0, description e a marca invocável ×
    disable-model-invocation — é o que distribui a lane 'sob demanda' sozinha (AC2)."""
    cmds = anat.comandos(REPO)
    nomes = {c["nome"] for c in cmds}
    assert "nova-feature" in nomes and "divergir" in nomes and "anatomia" in nomes
    for c in cmds:
        assert c["bytes"] > 0, c["nome"]
        assert c["description"], f"{c['nome']}: sem description no frontmatter"
    pornome = {c["nome"]: c for c in cmds}
    assert pornome["nova-feature"]["disable"] is True
    assert pornome["mapa-neural"]["disable"] is False, "mapa-neural é invocável (sem disable)"


def test_hooks_e_rules_extraidos(anat):
    """hooks.json diz o que está REGISTRADO; hooks/*.py fora dele aparecem como presentes e
    não-registrados (o nudge opt-in). Rules vêm de templates/rules/ com seus paths:."""
    hk = anat.hooks_do_kit(REPO)
    registrados = [h for h in hk if h["registrado"]]
    assert any("projeto_ativo" in h["arquivo"] for h in registrados), "cerca não aparece registrada"
    assert any(not h["registrado"] and "capturar_nudge" in h["arquivo"] for h in hk), \
        "nudge opt-in não aparece como presente-e-não-registrado"
    rl = anat.rules_do_kit(REPO)
    assert {r["nome"] for r in rl} >= {"frontend", "banco-e-segredo", "rota-e-endpoint"}
    assert all(r["paths"] for r in rl), "rule sem paths: no frontmatter"


def test_orcamento_e_evals_medidos(anat):
    """Orçamento em bytes dos arquivos da partida (só os existentes, com teto) e contagem
    de casos do EVALS (total e abertos) direto da tabela — nada estimado."""
    orc = anat.orcamento(REPO)
    alvos = {o["arquivo"] for o in orc}
    assert "CLAUDE.md" not in alvos or all(o["bytes"] > 0 for o in orc)
    assert any("MAPA.md" in o["arquivo"] for o in orc)
    assert all(o["teto"] > 0 for o in orc)
    ev = anat.evals(REPO)
    assert ev["total"] >= 14
    assert isinstance(ev["abertos"], list)


# ---------------------------------------------------------------- metadado curado não mente

def test_metadado_curado_cita_so_alvo_existente(anat):
    """AC3 — cada entrada curada (matriz lê×escreve, riscos, lanes fixas) declara os arquivos
    do kit que cita em `alvos`; alvo que deixou de existir = teste vermelho, não painel mentindo."""
    faltando = [f"{origem}: {alvo}"
                for origem, alvo in anat.alvos_curados()
                if not (REPO / alvo).exists()]
    assert not faltando, "metadado curado citando alvo que não existe:\n" + "\n".join(faltando)


# ---------------------------------------------------------------- render

@pytest.fixture(scope="module")
def html_gerado(tmp_path_factory, anat):
    out = tmp_path_factory.mktemp("anatomia")
    caminho = anat.gerar(proj=REPO, kit=REPO, out=out)
    return Path(caminho).read_text(encoding="utf-8")


def test_html_self_contained_com_4_secoes(html_gerado):
    """AC1 — as 4 seções presentes e nada externo (proxy MSIG: zero CDN)."""
    for marca in ("Quando cada peça", "lê × ", "falha", "Fila"):
        assert marca.lower() in html_gerado.lower(), f"seção ausente: {marca}"
    assert "<script src=" not in html_gerado, "script externo — o painel tem que ser self-contained"
    assert "<link " not in html_gerado, "stylesheet/font externo — o painel tem que ser self-contained"


def test_html_numeros_medidos(html_gerado, anat):
    """AC1 — versão e contagem de comandos no HTML são as medidas, não literais defasados."""
    assert anat.versao_kit(REPO) in html_gerado, "a versão do manifesto não está no painel"
    n = len(anat.comandos(REPO))
    assert f"<b>{n}</b> comando" in html_gerado, f"a contagem medida ({n}) não está no painel"
    assert "divergir" in html_gerado and "anatomia" in html_gerado, \
        "comando do kit não apareceu na lane 'sob demanda' (AC2)"


def test_js_do_painel_passa_no_node_check(html_gerado, tmp_path):
    """Guarda da tela branca: substring verde não pega erro de parse — `node --check` pega.
    (pula se node não estiver no PATH)"""
    if not shutil.which("node"):
        pytest.skip("node não disponível — guarda de sintaxe pulada")
    scripts = re.findall(r"<script>(.*?)</script>", html_gerado, re.S)
    assert scripts, "o painel deveria ter JS inline (hover da matriz)"
    f = tmp_path / "painel.js"
    f.write_text("\n".join(scripts), encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, f"JS do painel com erro de sintaxe:\n{r.stderr}"
