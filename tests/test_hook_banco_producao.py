"""Cerca de banco de PRODUÇÃO — leitura com o OK do owner (um OK vale a tarefa), escrita nunca pelo assistente.

Benchmark MSIG_Agentes (2026-11-06), item 5: lá o `guarda_producao.py` classifica alias/host de produção, responde
`ask` com o motivo, carimba a aprovação por tarefa (2 h) quando um comando de produção executa, libera rotinas
agendadas registradas e nega DML/DDL; o MCP só aceita SELECT. Aqui a fonte dos hosts é o `docs/AMBIENTES.md`
do projeto (seção Produção), que o owner já mantém.

Propriedades:
- sem `docs/AMBIENTES.md`/sem seção Produção/sem marcador → libera calado;
- comando ou consulta MCP que cita host/alias de produção num segmento executável: leitura → `ask` uma vez por
  tarefa (o `--post` carimba quando executou); escrita → `deny`; rotina autorizada → libera;
- `echo`/`grep`/`cat` que citam o host não contam; `.py` do projeto que cita o host conta (leitura);
- falha com comando presente → `ask`; escape `MSS_BANCO_PRD_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`, `regra_pos`) é testada em memória — o `AMBIENTES.md` e os scripts de cada
projeto e o carimbo de cada projeto ficam num objeto do teste e entram como dado; os caminhos não existem. O disco
de verdade (ler o AMBIENTES e um script, gravar e ler o carimbo) fica num teste só, numa pasta montada uma vez; o
processo python, num teste só.
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
HOOK = REPO / "hooks" / "banco_producao.py"
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
AGORA = 1000.0

AMBIENTES = """# Ambientes — Whats

## Local
- **O que é:** `docker compose` na máquina; banco `host.docker.internal:5432`
| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `BANCO_LOCAL` | `localhost` | `.env` | owner |

## Homologação
- **O que é:** Web App `mss-whats-dev-br`; banco `MSSQLD0`
| `BANCO_HML` | `MSSQLD0` | App Setting | owner |

## Produção
- **O que é:** Web App `mss-whats-prod` (grupo `RG-WHATS-PRD`); SQL Server `MS10PROSQL` (`TKGS_CORP`)
- **Como o assistente lê:** só leitura pelo túnel, chave `BANCO_PRD` do `sql/.env`; nunca Kudu/Portal
- **Quem acessa:** owner: Portal não, Kudu não · assistente: só leitura
- **Rotinas autorizadas em produção (só leitura):** `scripts/relatorio_diario.py`
| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `N8N_PUSH_URL` | `https://n8n.msig.com.br/webhook/x` | App Setting do Web App `mss-whats-prod` | owner |
| `SENHA` | `*****` | App Setting | owner |
"""

AMBIENTES_EXPLICITO = AMBIENTES.replace(
    "- **Rotinas autorizadas em produção (só leitura):**",
    "- **Hosts de produção (cerca):** `MS10PROSQL`, `prd`\n- **Rotinas autorizadas em produção (só leitura):**")

SCRIPTS = {
    "scripts/relatorio_diario.py": "conectar('MS10PROSQL')\n",
    "scripts/consulta.py": "# lê o MS10PROSQL\nSELECT 1\n",
    "scripts/local.py": "print('nada de producao')\n",
}


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("banco_producao", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _chave(caminho):
    return os.path.normcase(os.path.normpath(str(caminho)))


class Maquina:
    """O que o hook lê e grava no disco, em memória: o `AMBIENTES.md` e os scripts de cada projeto e o carimbo de
    cada projeto. `avaliar` e `pos` chamam a regra com isso como dado e fazem o papel da casca."""

    def __init__(self, mod):
        self.mod, self.ambientes, self.scripts, self.carimbos, self.anotacoes = mod, {}, {}, {}, []

    def projeto(self, nome, ambientes=AMBIENTES, scripts=SCRIPTS):
        raiz = BASE / nome
        if ambientes is not None:
            self.ambientes[_chave(raiz)] = ambientes
        for caminho, texto in scripts.items():
            self.scripts[_chave(raiz / caminho)] = texto
        return raiz

    def avaliar(self, evento, ambiente=None, agora=AGORA):
        tipo, motivo, anotacoes = self.mod.regra(
            evento, ambiente or {}, lambda raiz: self.ambientes.get(_chave(raiz), ""),
            lambda caminho: self.scripts.get(_chave(caminho)), lambda raiz: self.carimbos.get(_chave(raiz)), agora)
        self.anotacoes += anotacoes
        return tipo, motivo

    def pos(self, evento, ambiente=None, agora=AGORA):
        raiz = self.mod.regra_pos(evento, ambiente or {}, lambda r: self.ambientes.get(_chave(r), ""),
                                  lambda caminho: self.scripts.get(_chave(caminho)))
        if raiz is None:
            return False
        self.carimbos[_chave(raiz)] = agora
        return True


@pytest.fixture()
def maq(mod):
    return Maquina(mod)


def _ev(comando=None, tool="Bash", cwd=None, query=None):
    entrada = {"command": comando} if comando is not None else {"query": query}
    return {"hook_event_name": "PreToolUse", "cwd": str(cwd), "session_id": "s1", "tool_name": tool,
            "tool_input": entrada}


# --- marcadores: do AMBIENTES.md ---------------------------------------------------------------------

def test_marcadores_por_heuristica_so_da_secao_producao(mod):
    hosts, rotinas = mod.marcadores(AMBIENTES)
    assert "MS10PROSQL" in hosts and "BANCO_PRD" in hosts and "mss-whats-prod" in hosts and "RG-WHATS-PRD" in hosts
    assert "MSSQLD0" not in hosts and "BANCO_HML" not in hosts, "pegou host de homologação"
    assert "*****" not in hosts and "sql/.env" not in hosts and "owner" not in hosts
    assert rotinas == ["scripts/relatorio_diario.py"]


def test_marcadores_explicitos_vencem_a_heuristica(mod):
    hosts, _ = mod.marcadores(AMBIENTES_EXPLICITO)
    assert hosts == ["MS10PROSQL", "prd"]


def test_sem_secao_producao_nao_ha_marcador(mod):
    assert mod.marcadores("# x\n## Local\n`MS10PROSQL`\n") == ([], [])
    assert mod.marcadores("") == ([], [])


# --- decisões ---------------------------------------------------------------------------------------

def test_select_em_producao_pede_aprovacao_com_motivo(maq):
    proj = maq.projeto("proj")
    tipo, motivo = maq.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT TOP 5 * FROM ems_emissao"', cwd=proj))
    assert tipo == "ask" and "MS10PROSQL" in motivo and "PRODUÇÃO" in motivo and "120 min" in motivo
    assert "MSS_BANCO_PRD_OFF" in motivo and "Rotinas autorizadas" in motivo


@pytest.mark.parametrize("comando", [
    'sqlcmd -S MS10PROSQL -Q "UPDATE ems_emissao SET sts_emis=\'06\' WHERE cod_ctrt=1"',
    'sqlcmd -S MS10PROSQL -Q "SELECT 1; DELETE FROM x"',
    'psql -h ms10prosql -c "ALTER TABLE x ADD y int"',
    'sqlcmd -S MS10PROSQL -i cancelar.sql -Q "EXEC pr_cancela"',
])
def test_escrita_em_producao_e_negada(maq, comando):
    tipo, motivo = maq.avaliar(_ev(comando, cwd=maq.projeto("proj")))
    assert tipo == "deny" and "ato do owner" in motivo and ".sql" in motivo


@pytest.mark.parametrize("comando", [
    "echo MS10PROSQL",
    "grep -rn MS10PROSQL docs/",
    "cat docs/AMBIENTES.md",
    "git log --oneline | grep BANCO_PRD",
    'sqlcmd -S MSSQLD0 -Q "SELECT 1"',
    "python scripts/local.py",
    "python -m pytest tests/ -q",
])
def test_texto_homologacao_e_script_sem_producao_passam(maq, comando):
    assert maq.avaliar(_ev(comando, cwd=maq.projeto("proj"))) == (None, None)


def test_script_do_projeto_que_cita_producao_pede_aprovacao(maq):
    tipo, motivo = maq.avaliar(_ev("python scripts/consulta.py --mes 11", cwd=maq.projeto("proj")))
    assert tipo == "ask" and "MS10PROSQL" in motivo


def test_rotina_autorizada_passa_calada(maq):
    proj = maq.projeto("proj")
    assert maq.avaliar(_ev("python scripts/relatorio_diario.py", cwd=proj)) == (None, None)
    assert maq.avaliar(_ev("python scripts\\relatorio_diario.py --hoje", tool="PowerShell", cwd=proj)) == (None, None)
    assert maq.anotacoes == [("liberou-rotina", "scripts/relatorio_diario.py")] * 2


def test_mcp_de_sql_select_pergunta_e_dml_nega(maq):
    proj = maq.projeto("proj")
    tipo, _ = maq.avaliar(_ev(tool="mcp__prd__execute_sql", cwd=proj, query="SELECT 1"))
    assert tipo is None, "servidor `prd` não é marcador neste AMBIENTES (heurística)"
    maq.projeto("proj", ambientes=AMBIENTES_EXPLICITO)
    tipo, _ = maq.avaliar(_ev(tool="mcp__prd__execute_sql", cwd=proj, query="SELECT 1"))
    assert tipo == "ask"
    tipo, _ = maq.avaliar(_ev(tool="mcp__prd__execute_sql", cwd=proj, query="DELETE FROM x"))
    assert tipo == "deny"
    tipo, _ = maq.avaliar(_ev(tool="mcp__hml__execute_sql", cwd=proj, query="SELECT * FROM MS10PROSQL.dbo.x"))
    assert tipo == "ask", "consulta cross-server citando o host de produção conta"
    assert maq.avaliar(_ev(tool="mcp__hml__execute_sql", cwd=proj, query="SELECT 1")) == (None, None)


# --- carimbo: um OK vale a tarefa -----------------------------------------------------------------

def test_executou_carimba_e_os_seguintes_passam_ate_vencer(maq):
    ev = _ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=maq.projeto("proj"))
    assert maq.avaliar(ev)[0] == "ask"
    assert maq.pos({**ev, "hook_event_name": "PostToolUse"}) is True
    assert maq.avaliar(ev, agora=AGORA + 119 * 60) == (None, None)
    assert maq.avaliar(ev, agora=AGORA + 121 * 60)[0] == "ask", "a aprovação não venceu em 120 min"
    assert maq.avaliar(ev, {"MSS_BANCO_PRD_MINUTOS": "10"}, agora=AGORA + 11 * 60)[0] == "ask"


def test_escrita_nao_carimba_nem_usa_o_carimbo(maq):
    proj = maq.projeto("proj")
    ev_w = _ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=proj)
    assert maq.pos({**ev_w, "hook_event_name": "PostToolUse"}) is False
    maq.carimbos[_chave(proj)] = AGORA
    assert maq.avaliar(ev_w)[0] == "deny"


def test_carimbo_e_por_projeto(maq):
    proj, outro = maq.projeto("proj"), maq.projeto("outro")
    maq.carimbos[_chave(proj)] = AGORA
    assert maq.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=outro))[0] == "ask"


# --- bordas ---------------------------------------------------------------------------------------

def test_projeto_sem_ambientes_libera(maq):
    vazio = maq.projeto("vazio", ambientes=None, scripts={})
    assert maq.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=vazio)) == (None, None)


def test_escape_do_owner(maq):
    ev = _ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=maq.projeto("proj"))
    assert maq.avaliar(ev, {"MSS_BANCO_PRD_OFF": "1"}) == (None, None)


def test_claude_project_dir_vence_o_cwd(maq):
    proj, vazio = maq.projeto("proj"), maq.projeto("vazio", ambientes=None, scripts={})
    tipo, _ = maq.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=vazio), {"CLAUDE_PROJECT_DIR": str(proj)})
    assert tipo == "ask"


@pytest.mark.parametrize("ruim", [None, "x", {}, {"tool_name": "Read", "tool_input": {"file_path": "a"}},
                                  {"tool_name": "Bash", "tool_input": {}}, {"tool_name": "Bash", "tool_input": "x"}])
def test_entrada_malformada_libera(maq, ruim):
    assert maq.avaliar(ruim) == (None, None)


def test_defeito_na_avaliacao_pergunta_em_vez_de_decidir(maq, mod, monkeypatch):
    monkeypatch.setattr(mod, "classificar", lambda *a, **k: 1 / 0)
    tipo, motivo = maq.avaliar(_ev("python scripts/consulta.py", cwd=maq.projeto("proj")))
    assert tipo == "ask" and "estourou" in motivo


def test_registro_diz_o_que_fez_sem_o_comando(maq):
    proj = maq.projeto("proj")
    maq.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM ems_emissao"', cwd=proj))
    maq.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=proj))
    assert maq.anotacoes == [("negou", "escrita em MS10PROSQL"), ("perguntou", "leitura em MS10PROSQL")]


def test_saida_pelo_contrato_do_pre_tool_use(mod):
    """`ask` só vale com exit 0 (exit 2 = bloqueio); `deny` sai 2 com o motivo no stderr; libera: calado."""
    impresso, erro, codigo = mod.saida("ask", "lê produção")
    assert codigo == 0 and erro is None
    assert json.loads(impresso)["hookSpecificOutput"] == {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                                          "permissionDecisionReason": "lê produção"}
    impresso, erro, codigo = mod.saida("deny", "ato do owner")
    assert codigo == 2 and erro == "ato do owner" and json.loads(impresso)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert mod.saida(None, None) == (None, None, 0)


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("banco")
    raiz, temp = base / "proj", base / "temp"
    for caminho, texto in {"docs/AMBIENTES.md": AMBIENTES, **SCRIPTS}.items():
        (raiz / caminho).parent.mkdir(parents=True, exist_ok=True)
        (raiz / caminho).write_text(texto, encoding="utf-8")
    temp.mkdir()
    return raiz, temp


def test_casca_le_ambientes_e_script_e_grava_o_carimbo(mod, pasta):
    raiz, temp = pasta
    amb = {"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    assert mod.avaliar(_ev("python scripts/consulta.py", cwd=raiz), amb, agora=AGORA)[0] == "ask", \
        "o AMBIENTES.md ou o script do disco não foram lidos"
    ev = _ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=raiz)
    assert mod.pos({**ev, "hook_event_name": "PostToolUse"}, amb, agora=AGORA) is True
    assert mod.avaliar(ev, amb, agora=AGORA + 60) == (None, None), "o carimbo gravado no disco não foi lido"
    assert list(raiz.rglob("mss_banco_prd_*")) == [], "o carimbo sujou a pasta do projeto"


def test_processo_deny_sai_2_pelo_contrato(pasta):
    raiz, temp = pasta
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)})
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=raiz)),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=amb, timeout=30)
    assert r.returncode == 2 and '"deny"' in r.stdout and "ato do owner" in r.stderr


def test_fiacao_hooks_json_readme_regra_e_molde():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    pre = [(g.get("matcher"), h["command"]) for g in cfg["hooks"]["PreToolUse"] for h in g["hooks"]]
    assert any("banco_producao.py" in c and "mcp__" in (m or "") and "Bash" in (m or "") for m, c in pre), pre
    post = [(g.get("matcher"), h["command"]) for g in cfg["hooks"]["PostToolUse"] for h in g["hooks"]]
    assert any("banco_producao.py" in c and "--post" in c for _, c in post), post
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "`banco_producao.py` | `PreToolUse`" in readme and "MSS_BANCO_PRD_OFF" in readme
    regra = (REPO / "templates" / "rules" / "banco-e-segredo.md").read_text(encoding="utf-8")
    assert "🟥" in regra and "🟨" in regra and "banco_producao.py" in regra, "a regra de banco não traz o rótulo nem a cerca"
    molde = (REPO / "templates" / "AMBIENTES.md").read_text(encoding="utf-8")
    assert "Hosts de produção (cerca)" in molde and "Rotinas autorizadas em produção" in molde
