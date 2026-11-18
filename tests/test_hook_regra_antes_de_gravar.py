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

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o `CLAUDE.md`, as regras de `.claude/rules/` de cada
projeto e as regras já mostradas em cada conversa ficam num objeto do teste e entram como dado; os caminhos não
existem. O disco de verdade (ler o CLAUDE.md em cp1252, descer nas subpastas, pular arquivo ilegível, gravar e
zerar o "já mostrada") fica num teste só, numa pasta montada uma vez; o processo python, num teste só. A 2ª
conferência (`_comando_inteiro.py`) tem os testes dela; aqui ela entra calada.
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
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
MARCA = "<!-- mss-spec:regras-do-kit -->"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("regra_antes_de_gravar", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _conteudo(paths, corpo="Texto da regra.\n", frontmatter=None):
    if frontmatter is None:
        itens = "".join(f'  - "{p}"\n' for p in paths)
        frontmatter = f"---\npaths:\n{itens}---\n" if paths else "---\ndescription: sem paths\n---\n"
    return frontmatter + "\n" + corpo


class Maquina:
    """O que o hook lê e grava no disco, em memória: o `CLAUDE.md` e as regras de cada projeto e as regras já
    mostradas em cada conversa. `responder` chama a regra com isso como dado e faz o papel da casca."""

    def __init__(self, mod):
        self.mod, self.claude, self.regras, self.mostradas, self.anotacoes = mod, {}, {}, {}, []

    def projeto(self, nome="proj", marca=True):
        """Projeto do kit (CLAUDE.md com a marca); `marca=False` = projeto fora do kit."""
        raiz = BASE / nome
        self.claude[str(raiz)] = ("# Proj\n\n" + MARCA + "\n") if marca else "# Proj\n"
        self.regras[str(raiz)] = {}
        return raiz

    def regra(self, raiz, nome, paths, corpo="Texto da regra.\n", frontmatter=None):
        self.regras[str(raiz)][nome] = _conteudo(paths, corpo, frontmatter)

    def responder(self, evento, ambiente=None):
        saida, mudancas = self.mod.regra(
            evento, ambiente or {}, lambda raiz: self.claude.get(raiz), lambda raiz: dict(self.regras.get(raiz, {})),
            lambda sessao: self.mostradas.get(sessao, set()), lambda *_: None)
        if mudancas.get("mostradas"):
            sessao = evento.get("session_id")
            self.mostradas[sessao] = self.mostradas.get(sessao, set()) | set(mudancas["mostradas"])
        self.anotacoes += mudancas["anotacoes"]
        return saida


@pytest.fixture()
def maq(mod):
    return Maquina(mod)


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
def test_casa_glob_padroes_do_whats(mod, rel, padrao, esperado):
    assert mod.casa_glob(rel, padrao) is esperado


def test_casa_glob_barra_invertida_e_maiusculas(mod):
    assert mod.casa_glob("SQL\\Novo.SQL", "**/*.sql") is True
    assert mod.casa_glob("Web/Chat.html", "web/**") is True


def test_casa_glob_asterisco_simples_nao_atravessa_pasta_e_interrogacao_e_um_char(mod):
    assert mod.casa_glob("a/b.sql", "*.sql") is False
    assert mod.casa_glob("b.sql", "*.sql") is True
    assert mod.casa_glob("a1.py", "a?.py") is True
    assert mod.casa_glob("a12.py", "a?.py") is False
    assert mod.casa_glob("a.py", "a.py") is True and mod.casa_glob("axpy", "a.py") is False


# --- regras_de: nome, paths e texto -------------------------------------------------------------

def test_regras_le_nome_paths_e_texto_sem_frontmatter(mod):
    regras = mod.regras_de({"banco.md": _conteudo(["**/*.sql", "**/db/**"], corpo="# Banco\n\n- parametrizado\n"),
                            "sem-paths.md": _conteudo([])})
    assert [(n, p) for n, p, _ in regras] == [("banco.md", ["**/*.sql", "**/db/**"])]
    texto = regras[0][2]
    assert "# Banco" in texto and "parametrizado" in texto
    assert "---" not in texto and "paths:" not in texto


def test_regras_aceitam_crlf_e_bom(mod):
    regras = mod.regras_de({"a.md": "\ufeff---\r\npaths:\r\n  - \"**/*.sql\"\r\n---\r\n\r\n# A\r\n\r\n- corpo da regra\r\n"})
    assert regras and regras[0][1] == ["**/*.sql"] and "# A" in regras[0][2]


def test_sem_regras_devolve_vazio(mod):
    assert mod.regras_de({}) == []


def test_regras_em_ordem_de_nome_com_subpasta(mod):
    regras = mod.regras_de({"ui/telas.md": _conteudo(["**/*.html"], "REGRA-DE-TELA\n"),
                            "banco.md": _conteudo(["**/*.sql"])})
    assert [n for n, _, _ in regras] == ["banco.md", "ui/telas.md"]


def test_regra_em_subpasta_nega_com_o_caminho_da_regra(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "ui/telas.md", ["**/*.html"], corpo="REGRA-DE-TELA\n")
    motivo = _motivo(maq.responder(_evento(raiz, raiz / "a.html")))
    assert "REGRA-DE-TELA" in motivo and ".claude/rules/ui/telas.md" in motivo


def test_regra_so_com_titulo_e_comentario_nao_nega(maq):
    """Forma do `testes.md` do Whats depois da migração: título + comentário, o conteúdo voltou pro CLAUDE.md."""
    raiz = maq.projeto()
    maq.regra(raiz, "testes.md", ["**/test_*.py"],
              corpo="# Testes\n\n<!-- o conteúdo desta regra voltou pro `## Contexto` do CLAUDE.md -->\n")
    maq.regra(raiz, "multi.md", ["**/test_*.py"], corpo="## Vazia\n\n<!-- linha 1\nlinha 2 -->\n\n")
    assert maq.responder(_evento(raiz, raiz / "tests" / "test_a.py")) is None
    maq.regra(raiz, "real.md", ["**/test_*.py"], corpo="# Testes\n\n<!-- c -->\n- use fixtures\n")
    motivo = _motivo(maq.responder(_evento(raiz, raiz / "tests" / "test_a.py")))
    assert "use fixtures" in motivo and "testes.md" not in motivo and "multi.md" not in motivo


# --- decisão ----------------------------------------------------------------------------------

def test_projeto_sem_a_marca_nao_nega(maq):
    raiz = maq.projeto(marca=False)
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is None
    maq.claude[str(raiz)] = None                                     # sem CLAUDE.md
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is None


def test_marca_com_bom_e_crlf_vale(mod):
    assert mod.marca_no("\ufeff# Proj\r\n" + MARCA + "\r\n") is True
    assert mod.marca_no("# Proj\n<!-- outra marca -->\n") is False
    assert mod.marca_no(None) is False


def test_write_de_sql_novo_nega_com_o_texto_da_regra(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"], corpo="# Banco\n\n- SQL sempre parametrizado.\n")
    alvo = str(raiz) + "\\sql\\novo.sql"                  # barra invertida (Windows)
    motivo = _motivo(maq.responder(_evento(raiz, alvo)))
    assert "SQL sempre parametrizado." in motivo
    assert "repita a gravação" in motivo.lower()
    assert "sql/novo.sql" in motivo
    assert ".claude/rules/banco.md" in motivo
    assert "---" not in motivo and "paths:" not in motivo


def test_edit_e_multiedit_tambem_negam(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    for i, tool in enumerate(("Edit", "MultiEdit")):
        assert maq.responder(_evento(raiz, raiz / "a.sql", tool=tool, sessao=f"t{i}")) is not None, tool


def test_outras_ferramentas_passam(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "a.sql", tool="Read")) is None
    assert maq.responder(_evento(raiz, raiz / "a.sql", tool="Bash")) is None


def test_segunda_gravacao_na_mesma_sessao_passa(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    ev = _evento(raiz, raiz / "sql" / "novo.sql")
    assert maq.responder(ev) is not None
    assert maq.responder(ev) is None


def test_mesma_regra_em_outro_arquivo_da_mesma_sessao_tambem_passa(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is not None
    assert maq.responder(_evento(raiz, raiz / "b.sql")) is None


def test_outra_sessao_nega_de_novo(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "a.sql", sessao="A")) is not None
    assert maq.responder(_evento(raiz, raiz / "a.sql", sessao="A")) is None
    assert maq.responder(_evento(raiz, raiz / "a.sql", sessao="B")) is not None


def test_arquivo_que_nao_casa_passa(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "app.py")) is None


def test_regra_sem_paths_ignorada(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "geral.md", [])
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is None


def test_projeto_sem_rules_passa(maq):
    raiz = maq.projeto()
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is None


def test_arquivo_fora_da_raiz_passa(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, BASE / "outro" / "a.sql")) is None
    # prefixo parecido não é "dentro": proj-2 não está em proj
    assert maq.responder(_evento(raiz, BASE / "proj-2" / "a.sql")) is None


def test_caminho_relativo_resolve_contra_o_cwd(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, "sql/novo.sql")) is not None


def test_raiz_vem_do_claude_project_dir_antes_do_cwd(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    ev = _evento(BASE / "outro", raiz / "a.sql")
    assert maq.responder(ev, {"CLAUDE_PROJECT_DIR": str(raiz)}) is not None


def test_duas_regras_casam_nega_uma_vez_com_as_duas(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "logging.md", ["**/*.py"], corpo="REGRA-DE-LOG\n")
    maq.regra(raiz, "estrutura-em-camadas.md", ["**/*.py"], corpo="REGRA-DE-CAMADAS\n")
    ev = _evento(raiz, raiz / "servicos" / "a.py")
    motivo = _motivo(maq.responder(ev))
    assert "REGRA-DE-LOG" in motivo and "REGRA-DE-CAMADAS" in motivo
    assert maq.responder(ev) is None
    assert maq.responder(_evento(raiz, raiz / "b.py")) is None   # as duas já foram mostradas


def test_mostrada_e_por_regra(maq):
    """Outra regra que casa só em outro tipo de arquivo ainda nega."""
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    maq.regra(raiz, "frontend.md", ["**/*.html"])
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is not None
    assert maq.responder(_evento(raiz, raiz / "a.html")) is not None
    assert maq.responder(_evento(raiz, raiz / "b.html")) is None


def test_comando_cortado_entra_no_mesmo_deny(mod):
    """A 2ª conferência (`_comando_inteiro.py`, testada nos arquivos dela) soma o motivo dela ao deny, com escape
    e falha próprios: uma conferência não liga nem desliga a outra."""
    ev = _evento(BASE / "proj", BASE / "proj" / "memory" / "x.md")
    saida, mudancas = mod.regra(ev, {"MSS_REGRA_OFF": "1"}, lambda r: MARCA, lambda r: {}, lambda s: set(),
                                lambda *_: "COMANDO-CORTADO")
    assert _motivo(saida) == "COMANDO-CORTADO" and mudancas["anotacoes"] == [("negou", "comando-inteiro")]
    saida, _ = mod.regra(ev, {}, lambda r: MARCA, lambda r: {}, lambda s: set(), lambda *_: 1 / 0)
    assert saida is None, "a 2ª conferência quebrada travou a gravação"


# --- escape e falha aberta --------------------------------------------------------------------

def test_escape_MSS_REGRA_OFF(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "a.sql"), {"MSS_REGRA_OFF": "1"}) is None


def test_defeito_libera(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "quebrada.md", ["**/*.sql"], frontmatter='---\npaths:\n  - "**/*.sql"\n')   # sem o fecha-frontmatter
    assert maq.responder(_evento(raiz, raiz / "a.sql")) is None


def test_evento_malformado_libera(maq):
    for ev in ({}, {"tool_name": "Write"}, {"tool_name": "Write", "tool_input": None},
               {"tool_name": "Write", "tool_input": {"file_path": 7}, "cwd": str(BASE)}, None, "x"):
        assert maq.responder(ev) is None


def test_registra_negou_com_o_nome_da_regra_e_sem_caminho(maq):
    raiz = maq.projeto()
    maq.regra(raiz, "banco.md", ["**/*.sql"])
    assert maq.responder(_evento(raiz, raiz / "sql" / "segredo.sql")) is not None
    assert maq.anotacoes == [("negou", "banco.md")]


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("regra_antes")
    raiz, temp = base / "proj", base / "temp"
    regras = raiz / ".claude" / "rules"
    (regras / "ui").mkdir(parents=True)
    temp.mkdir()
    (raiz / "CLAUDE.md").write_bytes(("# São Paulo\n" + MARCA + "\n").encode("cp1252"))   # fora de UTF-8
    (regras / "banco.md").write_text(_conteudo(["**/*.sql"], "Acentuação: não concatene.\n"), encoding="utf-8")
    (regras / "ui" / "telas.md").write_text(_conteudo(["**/*.html"], "REGRA-DE-TELA\n"), encoding="utf-8")
    (regras / "binaria.md").write_bytes(b"\xff\xfe\x00\x01---\n")                            # ilegível
    return raiz, temp


def test_casca_le_marca_e_regras_e_grava_e_zera_o_ja_mostrada(mod, pasta, monkeypatch):
    raiz, temp = pasta
    monkeypatch.setattr(tempfile, "tempdir", str(temp))           # o "já mostrada" vai pro temp do SO
    assert [n for n, _, _ in mod.regras_do_projeto(str(raiz))] == ["banco.md", "ui/telas.md"], \
        "não desceu na subpasta ou não pulou o arquivo ilegível"
    ev = _evento(raiz, raiz / "a.sql", sessao="disco")
    assert "não concatene" in _motivo(mod.responder(ev, {})), "o CLAUDE.md em cp1252 perdeu a marca"
    assert mod.responder(ev, {}) is None, "o já mostrada gravado no disco não foi lido"
    mod.zerar("disco")
    assert mod.responder(ev, {}) is not None, "depois do /compact a regra volta a valer"
    mod.zerar("nunca-existiu")                                    # sem estado: não levanta


def test_processo_nega_em_json_e_sai_zero(pasta):
    raiz, temp = pasta
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(raiz), "MSS_REGISTRO_OFF": "1",
           "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento(raiz, raiz / "b.sql", sessao="proc")),
                          capture_output=True, text=True, encoding="utf-8", env=env)
    assert proc.returncode == 0
    assert "não concatene" in _motivo(json.loads(proc.stdout))


# --- fiação -----------------------------------------------------------------------------------

def test_hooks_json_session_start_compact_zera_o_estado():
    grupos = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["SessionStart"]
    achados = [g for g in grupos if any("regra_antes_de_gravar.py" in h["command"] for h in g["hooks"])]
    assert len(achados) == 1 and achados[0].get("matcher") == "compact"
    assert all("--zerar" in h["command"] and "CLAUDE_PLUGIN_ROOT" in h["command"] for h in achados[0]["hooks"])


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
    assert "Dezoito hooks" in doc
