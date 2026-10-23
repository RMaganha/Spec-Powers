"""Regra por tipo de arquivo, lida ANTES de gravar — o hook `PreToolUse` Write|Edit|MultiEdit.

Por que existe: as regras de caminho (`.claude/rules/*.md`, frontmatter `paths:`) carregam quando o
assistente LÊ um arquivo que casa; quando ele CRIA um arquivo novo (ou edita sem ler antes) a regra
não carrega — no Whats, `banco.md` faltou em 5 conversas que criaram `sql/`. Este hook nega UMA vez
por sessão e por regra, com o texto da regra no motivo; a 2ª gravação passa.

Propriedades:
- casa o caminho (relativo à raiz, `\\` → `/`, sem diferenciar maiúsculas) contra o `paths:`;
- nega uma vez por regra por sessão (estado no temp do SO); várias regras no mesmo arquivo → uma
  negação só, com todos os textos; caminho fora da raiz nunca casa;
- falha ABERTA (defeito → silêncio) e exit 0 sempre; escape `MSS_REGRA_OFF=1`.
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
HOOK = REPO / "hooks" / "regra_antes_de_gravar.py"


def _mod():
    spec = importlib.util.spec_from_file_location("regra_antes_de_gravar", HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _temp_isolado(tmp_path, monkeypatch):
    """O estado "já mostrada" vai pro temp do SO — a suíte usa um temp só dela."""
    pasta = tmp_path / "_temp"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))


def _regra(raiz, nome, paths, corpo="Texto da regra.\n", frontmatter=None):
    pasta = Path(raiz) / ".claude" / "rules"
    pasta.mkdir(parents=True, exist_ok=True)
    if frontmatter is None:
        itens = "".join(f'  - "{p}"\n' for p in paths)
        frontmatter = f"---\npaths:\n{itens}---\n" if paths else "---\ndescription: sem paths\n---\n"
    (pasta / nome).write_text(frontmatter + "\n" + corpo, encoding="utf-8")


def _projeto(tmp_path):
    raiz = tmp_path / "proj"
    raiz.mkdir()
    return raiz


def _evento(raiz, alvo, tool="Write", sessao="s1", **extra):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(raiz),
            "session_id": sessao, "tool_input": {"file_path": str(alvo)}, **extra}


def _motivo(saida):
    assert saida["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert saida["hookSpecificOutput"]["permissionDecision"] == "deny"
    return saida["hookSpecificOutput"]["permissionDecisionReason"]


# --- casa_glob --------------------------------------------------------------------------------

@pytest.mark.parametrize("rel,padrao,esperado", [
    ("sql/setup/14a.sql", "**/*.sql", True),
    ("x.sql", "**/*.sql", True),
    ("sql/carga/README.md", "sql/**", True),
    ("persistencia/a.py", "persistencia/**", True),
    ("tests/test_a.py", "tests/**", True),
    ("web/chat.html", "web/**", True),
    ("docker-compose.office.yml", "docker-compose*.yml", True),
    ("Dockerfile", "Dockerfile", True),
    ("app/Dockerfile", "Dockerfile", False),
    ("services/a.py", "apis/**", False),
])
def test_casa_glob_padroes_do_whats(rel, padrao, esperado):
    assert _mod().casa_glob(rel, padrao) is esperado


def test_casa_glob_barra_invertida_e_maiusculas():
    mod = _mod()
    assert mod.casa_glob("SQL\\Novo.SQL", "**/*.sql") is True
    assert mod.casa_glob("Web/Chat.html", "web/**") is True


def test_casa_glob_asterisco_simples_nao_atravessa_pasta_e_interrogacao_e_um_char():
    mod = _mod()
    assert mod.casa_glob("a/b.sql", "*.sql") is False
    assert mod.casa_glob("b.sql", "*.sql") is True
    assert mod.casa_glob("a1.py", "a?.py") is True
    assert mod.casa_glob("a12.py", "a?.py") is False
    assert mod.casa_glob("a.py", "a.py") is True and mod.casa_glob("axpy", "a.py") is False


# --- regras_do_projeto ------------------------------------------------------------------------

def test_regras_do_projeto_le_nome_paths_e_texto_sem_frontmatter(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql", "**/db/**"], corpo="# Banco\n\n- parametrizado\n")
    _regra(raiz, "sem-paths.md", [])
    regras = _mod().regras_do_projeto(str(raiz))
    assert [(n, p) for n, p, _ in regras] == [("banco.md", ["**/*.sql", "**/db/**"])]
    texto = regras[0][2]
    assert "# Banco" in texto and "parametrizado" in texto
    assert "---" not in texto and "paths:" not in texto


def test_regras_do_projeto_aceita_crlf_e_bom(tmp_path):
    raiz = _projeto(tmp_path)
    pasta = raiz / ".claude" / "rules"
    pasta.mkdir(parents=True)
    (pasta / "a.md").write_bytes("﻿---\r\npaths:\r\n  - \"**/*.sql\"\r\n---\r\n\r\n# A\r\n".encode("utf-8"))
    regras = _mod().regras_do_projeto(str(raiz))
    assert regras and regras[0][1] == ["**/*.sql"] and "# A" in regras[0][2]


def test_regras_do_projeto_sem_pasta_devolve_vazio(tmp_path):
    assert _mod().regras_do_projeto(str(_projeto(tmp_path))) == []


# --- decisão ----------------------------------------------------------------------------------

def test_write_de_sql_novo_nega_com_o_texto_da_regra(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"], corpo="# Banco\n\n- SQL sempre parametrizado.\n")
    alvo = str(raiz) + "\\sql\\novo.sql"                  # barra invertida (Windows)
    saida = _mod().responder(_evento(raiz, alvo), {})
    motivo = _motivo(saida)
    assert "SQL sempre parametrizado." in motivo
    assert "repita a gravação" in motivo.lower()
    assert "sql/novo.sql" in motivo
    assert ".claude/rules/banco.md" in motivo
    assert "---" not in motivo and "paths:" not in motivo


def test_edit_e_multiedit_tambem_negam(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    for i, tool in enumerate(("Edit", "MultiEdit")):
        saida = _mod().responder(_evento(raiz, raiz / "a.sql", tool=tool, sessao=f"t{i}"), {})
        assert saida is not None, tool


def test_outras_ferramentas_passam(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, raiz / "a.sql", tool="Read"), {}) is None
    assert _mod().responder(_evento(raiz, raiz / "a.sql", tool="Bash"), {}) is None


def test_segunda_gravacao_na_mesma_sessao_passa(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    ev = _evento(raiz, raiz / "sql" / "novo.sql")
    assert _mod().responder(ev, {}) is not None
    assert _mod().responder(ev, {}) is None


def test_mesma_regra_em_outro_arquivo_da_mesma_sessao_tambem_passa(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, raiz / "a.sql"), {}) is not None
    assert _mod().responder(_evento(raiz, raiz / "b.sql"), {}) is None


def test_outra_sessao_nega_de_novo(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, raiz / "a.sql", sessao="A"), {}) is not None
    assert _mod().responder(_evento(raiz, raiz / "a.sql", sessao="A"), {}) is None
    assert _mod().responder(_evento(raiz, raiz / "a.sql", sessao="B"), {}) is not None


def test_arquivo_que_nao_casa_passa(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, raiz / "app.py"), {}) is None


def test_regra_sem_paths_ignorada(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "geral.md", [])
    assert _mod().responder(_evento(raiz, raiz / "a.sql"), {}) is None


def test_projeto_sem_rules_passa(tmp_path):
    raiz = _projeto(tmp_path)
    assert _mod().responder(_evento(raiz, raiz / "a.sql"), {}) is None


def test_arquivo_fora_da_raiz_passa(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, tmp_path / "outro" / "a.sql"), {}) is None
    # prefixo parecido não é "dentro": proj-2 não está em proj
    assert _mod().responder(_evento(raiz, tmp_path / "proj-2" / "a.sql"), {}) is None


def test_caminho_relativo_resolve_contra_o_cwd(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, "sql/novo.sql"), {}) is not None


def test_raiz_vem_do_claude_project_dir_antes_do_cwd(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    outro = tmp_path / "outro"
    outro.mkdir()
    ev = _evento(outro, raiz / "a.sql")
    assert _mod().responder(ev, {"CLAUDE_PROJECT_DIR": str(raiz)}) is not None


def test_duas_regras_casam_nega_uma_vez_com_as_duas(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "logging.md", ["**/*.py"], corpo="REGRA-DE-LOG\n")
    _regra(raiz, "estrutura-em-camadas.md", ["**/*.py"], corpo="REGRA-DE-CAMADAS\n")
    ev = _evento(raiz, raiz / "servicos" / "a.py")
    motivo = _motivo(_mod().responder(ev, {}))
    assert "REGRA-DE-LOG" in motivo and "REGRA-DE-CAMADAS" in motivo
    assert _mod().responder(ev, {}) is None
    assert _mod().responder(_evento(raiz, raiz / "b.py"), {}) is None   # as duas já foram mostradas


def test_mostrada_e_por_regra(tmp_path):
    """Outra regra que casa só em outro tipo de arquivo ainda nega."""
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    _regra(raiz, "frontend.md", ["**/*.html"])
    assert _mod().responder(_evento(raiz, raiz / "a.sql"), {}) is not None
    assert _mod().responder(_evento(raiz, raiz / "a.html"), {}) is not None
    assert _mod().responder(_evento(raiz, raiz / "b.html"), {}) is None


# --- escape e falha aberta --------------------------------------------------------------------

def test_escape_MSS_REGRA_OFF(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, raiz / "a.sql"), {"MSS_REGRA_OFF": "1"}) is None


def test_defeito_libera(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "quebrada.md", ["**/*.sql"], frontmatter='---\npaths:\n  - "**/*.sql"\n')   # sem o fecha-frontmatter
    (raiz / ".claude" / "rules" / "binaria.md").write_bytes(b"\xff\xfe\x00\x01---\n")
    assert _mod().responder(_evento(raiz, raiz / "a.sql"), {}) is None


def test_evento_malformado_libera(tmp_path):
    mod = _mod()
    for ev in ({}, {"tool_name": "Write"}, {"tool_name": "Write", "tool_input": None},
               {"tool_name": "Write", "tool_input": {"file_path": 7}, "cwd": str(tmp_path)}):
        assert mod.responder(ev, {}) is None


def test_registra_negou_com_o_nome_da_regra_e_sem_caminho(tmp_path, monkeypatch):
    registro = tmp_path / "reg.jsonl"
    monkeypatch.setenv("MSS_REGISTRO_ARQUIVO", str(registro))
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"])
    assert _mod().responder(_evento(raiz, raiz / "sql" / "segredo.sql"), {}) is not None
    linha = json.loads(registro.read_text(encoding="utf-8").splitlines()[-1])
    assert linha["hook"] == "regra_antes_de_gravar" and linha["decisao"] == "negou"
    assert "banco.md" in linha["detalhe"] and "segredo" not in linha["detalhe"]


# --- processo ---------------------------------------------------------------------------------

def _rodar(stdin_texto, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run([sys.executable, str(HOOK)], input=stdin_texto, capture_output=True,
                          text=True, encoding="utf-8", env=env)


def test_processo_nega_em_json_e_sai_zero(tmp_path):
    raiz = _projeto(tmp_path)
    _regra(raiz, "banco.md", ["**/*.sql"], corpo="Acentuação: não concatene.\n")
    ev = _evento(raiz, raiz / "a.sql", sessao="proc-" + tmp_path.name)
    proc = _rodar(json.dumps(ev), {"CLAUDE_PROJECT_DIR": str(raiz), "MSS_REGISTRO_OFF": "1",
                                   "TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)})
    assert proc.returncode == 0
    assert "não concatene" in _motivo(json.loads(proc.stdout))


def test_processo_sai_zero_calado_com_entrada_malformada():
    for texto in ("", "isto não é json", "[1, 2]", "null"):
        proc = _rodar(texto)
        assert proc.returncode == 0 and proc.stdout == "", texto


# --- fiação -----------------------------------------------------------------------------------

def test_hooks_json_pretooluse_write_edit_multiedit():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    achados = [g for g in grupos
               if any("regra_antes_de_gravar.py" in h["command"] for h in g["hooks"])]
    assert len(achados) == 1, "regra_antes_de_gravar.py deve estar em exatamente um grupo do PreToolUse"
    grupo = achados[0]
    assert set(grupo["matcher"].split("|")) == {"Write", "Edit", "MultiEdit"}
    assert "CLAUDE_PLUGIN_ROOT" in grupo["hooks"][0]["command"]


def test_documentado_no_readme():
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "regra_antes_de_gravar.py" in doc and "MSS_REGRA_OFF" in doc
    assert "Onze hooks" in doc
