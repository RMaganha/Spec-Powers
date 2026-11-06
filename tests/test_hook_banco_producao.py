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
"""
import importlib.util
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "banco_producao.py"

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


def _mod():
    spec = importlib.util.spec_from_file_location("banco_producao", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def proj(tmp_path):
    raiz = tmp_path / "proj"
    (raiz / "docs").mkdir(parents=True)
    (raiz / "docs" / "AMBIENTES.md").write_text(AMBIENTES, encoding="utf-8")
    (raiz / "scripts").mkdir()
    (raiz / "scripts" / "relatorio_diario.py").write_text("conectar('MS10PROSQL')\n", encoding="utf-8")
    (raiz / "scripts" / "consulta.py").write_text("# lê o MS10PROSQL\nSELECT 1\n", encoding="utf-8")
    (raiz / "scripts" / "local.py").write_text("print('nada de producao')\n", encoding="utf-8")
    return raiz


@pytest.fixture()
def amb(tmp_path):
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)}


def _ev(comando=None, tool="Bash", cwd=None, query=None):
    entrada = {"command": comando} if comando is not None else {"query": query}
    return {"hook_event_name": "PreToolUse", "cwd": str(cwd), "session_id": "s-" + uuid.uuid4().hex[:6],
            "tool_name": tool, "tool_input": entrada}


# --- marcadores: do AMBIENTES.md ---------------------------------------------------------------------

def test_marcadores_por_heuristica_so_da_secao_producao():
    hosts, rotinas = _mod().marcadores(AMBIENTES)
    assert "MS10PROSQL" in hosts and "BANCO_PRD" in hosts and "mss-whats-prod" in hosts and "RG-WHATS-PRD" in hosts
    assert "MSSQLD0" not in hosts and "BANCO_HML" not in hosts, "pegou host de homologação"
    assert "*****" not in hosts and "sql/.env" not in hosts and "owner" not in hosts
    assert rotinas == ["scripts/relatorio_diario.py"]


def test_marcadores_explicitos_vencem_a_heuristica():
    hosts, _ = _mod().marcadores(AMBIENTES_EXPLICITO)
    assert hosts == ["MS10PROSQL", "prd"]


def test_sem_secao_producao_nao_ha_marcador():
    assert _mod().marcadores("# x\n## Local\n`MS10PROSQL`\n") == ([], [])
    assert _mod().marcadores("") == ([], [])


# --- decisões ---------------------------------------------------------------------------------------

def test_select_em_producao_pede_aprovacao_com_motivo(proj, amb):
    tipo, motivo = _mod().avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT TOP 5 * FROM ems_emissao"', cwd=proj), amb)
    assert tipo == "ask" and "MS10PROSQL" in motivo and "PRODUÇÃO" in motivo and "120 min" in motivo
    assert "MSS_BANCO_PRD_OFF" in motivo and "Rotinas autorizadas" in motivo


@pytest.mark.parametrize("comando", [
    'sqlcmd -S MS10PROSQL -Q "UPDATE ems_emissao SET sts_emis=\'06\' WHERE cod_ctrt=1"',
    'sqlcmd -S MS10PROSQL -Q "SELECT 1; DELETE FROM x"',
    'psql -h ms10prosql -c "ALTER TABLE x ADD y int"',
    'sqlcmd -S MS10PROSQL -i cancelar.sql -Q "EXEC pr_cancela"',
])
def test_escrita_em_producao_e_negada(proj, amb, comando):
    tipo, motivo = _mod().avaliar(_ev(comando, cwd=proj), amb)
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
def test_texto_homologacao_e_script_sem_producao_passam(proj, amb, comando):
    assert _mod().avaliar(_ev(comando, cwd=proj), amb) == (None, None)


def test_script_do_projeto_que_cita_producao_pede_aprovacao(proj, amb):
    tipo, motivo = _mod().avaliar(_ev("python scripts/consulta.py --mes 11", cwd=proj), amb)
    assert tipo == "ask" and "MS10PROSQL" in motivo


def test_rotina_autorizada_passa_calada(proj, amb):
    assert _mod().avaliar(_ev("python scripts/relatorio_diario.py", cwd=proj), amb) == (None, None)
    assert _mod().avaliar(_ev("python scripts\\relatorio_diario.py --hoje", tool="PowerShell", cwd=proj), amb) == (None, None)


def test_mcp_de_sql_select_pergunta_e_dml_nega(proj, amb):
    mod = _mod()
    tipo, _ = mod.avaliar(_ev(tool="mcp__prd__execute_sql", cwd=proj, query="SELECT 1"), amb)
    assert tipo is None, "servidor `prd` não é marcador neste AMBIENTES (heurística)"
    (proj / "docs" / "AMBIENTES.md").write_text(AMBIENTES_EXPLICITO, encoding="utf-8")
    tipo, _ = mod.avaliar(_ev(tool="mcp__prd__execute_sql", cwd=proj, query="SELECT 1"), amb)
    assert tipo == "ask"
    tipo, _ = mod.avaliar(_ev(tool="mcp__prd__execute_sql", cwd=proj, query="DELETE FROM x"), amb)
    assert tipo == "deny"
    tipo, _ = mod.avaliar(_ev(tool="mcp__hml__execute_sql", cwd=proj, query="SELECT * FROM MS10PROSQL.dbo.x"), amb)
    assert tipo == "ask", "consulta cross-server citando o host de produção conta"
    assert mod.avaliar(_ev(tool="mcp__hml__execute_sql", cwd=proj, query="SELECT 1"), amb) == (None, None)


# --- carimbo: um OK vale a tarefa -----------------------------------------------------------------

def test_executou_carimba_e_os_seguintes_passam_ate_vencer(proj, amb):
    mod = _mod()
    ev = _ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=proj)
    assert mod.avaliar(ev, amb, agora=1000)[0] == "ask"
    assert mod.pos({**ev, "hook_event_name": "PostToolUse"}, amb, agora=1000) is True
    assert mod.avaliar(ev, amb, agora=1000 + 119 * 60) == (None, None)
    assert mod.avaliar(ev, amb, agora=1000 + 121 * 60)[0] == "ask", "a aprovação não venceu em 120 min"
    assert mod.avaliar(ev, {**amb, "MSS_BANCO_PRD_MINUTOS": "10"}, agora=1000 + 11 * 60)[0] == "ask"


def test_escrita_nao_carimba_nem_usa_o_carimbo(proj, amb):
    mod = _mod()
    ev_w = _ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=proj)
    assert mod.pos({**ev_w, "hook_event_name": "PostToolUse"}, amb, agora=1000) is False
    mod.carimbar(str(proj), amb, agora=1000)
    assert mod.avaliar(ev_w, amb, agora=1000)[0] == "deny"


def test_carimbo_e_por_projeto(proj, amb, tmp_path):
    mod = _mod()
    outro = tmp_path / "outro"
    (outro / "docs").mkdir(parents=True)
    (outro / "docs" / "AMBIENTES.md").write_text(AMBIENTES, encoding="utf-8")
    mod.carimbar(str(proj), amb, agora=1000)
    assert mod.avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=outro), amb, agora=1000)[0] == "ask"


# --- bordas ---------------------------------------------------------------------------------------

def test_projeto_sem_ambientes_libera(tmp_path, amb):
    raiz = tmp_path / "vazio"
    raiz.mkdir()
    assert _mod().avaliar(_ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=raiz), amb) == (None, None)


def test_escape_do_owner(proj, amb):
    assert _mod().avaliar(_ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=proj),
                          {**amb, "MSS_BANCO_PRD_OFF": "1"}) == (None, None)


def test_claude_project_dir_vence_o_cwd(proj, amb, tmp_path):
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    tipo, _ = _mod().avaliar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=vazio),
                             {**amb, "CLAUDE_PROJECT_DIR": str(proj)})
    assert tipo == "ask"


@pytest.mark.parametrize("ruim", [None, "x", {}, {"tool_name": "Read", "tool_input": {"file_path": "a"}},
                                  {"tool_name": "Bash", "tool_input": {}}, {"tool_name": "Bash", "tool_input": "x"}])
def test_entrada_malformada_libera(amb, ruim):
    assert _mod().avaliar(ruim, amb) == (None, None)


def test_defeito_na_avaliacao_pergunta_em_vez_de_decidir(proj, amb, monkeypatch):
    mod = _mod()
    monkeypatch.setattr(mod, "classificar", lambda *a, **k: 1 / 0)
    tipo, motivo = mod.avaliar(_ev("python scripts/consulta.py", cwd=proj), amb)
    assert tipo == "ask" and "estourou" in motivo


# --- processo e fiação ----------------------------------------------------------------------------

def _rodar(ev, tmp_path, extra=None, args=()):
    amb = {k: v for k, v in os.environ.items() if not k.startswith("MSS_") and k != "CLAUDE_PROJECT_DIR"}
    amb.update({"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path), **(extra or {})})
    return subprocess.run([sys.executable, str(HOOK), *args], input=json.dumps(ev), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=amb, timeout=30)


def test_processo_ask_sai_0_e_deny_sai_2(proj, tmp_path):
    r = _rodar(_ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=proj), tmp_path)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])["hookSpecificOutput"]
    assert saida["permissionDecision"] == "ask" and saida["hookEventName"] == "PreToolUse"
    r = _rodar(_ev('sqlcmd -S MS10PROSQL -Q "DELETE FROM x"', cwd=proj), tmp_path)
    assert r.returncode == 2 and '"deny"' in r.stdout and "ato do owner" in r.stderr


def test_processo_post_carimba_e_libera_o_proximo(proj, tmp_path):
    ev = _ev('sqlcmd -S MS10PROSQL -Q "SELECT 1"', cwd=proj)
    r = _rodar({**ev, "hook_event_name": "PostToolUse"}, tmp_path, args=("--post",))
    assert r.returncode == 0 and r.stdout.strip() == ""
    r = _rodar(ev, tmp_path)
    assert r.returncode == 0 and r.stdout.strip() == "", "depois do carimbo o SELECT devia passar calado"


def test_processo_entrada_vazia_libera():
    r = subprocess.run([sys.executable, str(HOOK)], input="", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and r.stdout.strip() == ""


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
