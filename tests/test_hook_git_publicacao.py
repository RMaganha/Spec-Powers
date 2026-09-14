"""Trava de publicação — o assistente NUNCA publica nem integra; isso é ato do owner.

Nasceu de um acidente real (2026-09, caso F-022): numa janela aberta pra UMA feature, o
assistente absorveu um 2º e um 3º assunto, mesclou branches e disparou `git push` — e o push
é o gatilho do deploy automático em homologação. Quando o owner viu, já tinham ido vários.
O ambiente inteiro quebrou e custou "centenas de testes" pra entender o quê.

A frase "git push só quando eu pedir" JÁ estava no CLAUDE.md e foi ignorada. Prosa não
segura na hora 2 da sessão; este hook é a camada que não depende de o assistente se comportar:
PreToolUse em Bash|PowerShell, nega qualquer comando que publique (push) ou integre (merge,
rebase) ou faça deploy (docker push, az acr/webapp/containerapp, gh pr merge).

Propriedades:
- **nega publicação/integração** por qualquer caminho (encadeado, com -C, PowerShell);
- **libera o resto do git** (status, log, fetch, commit, checkout/branch pra abrir a feature);
- **falha FECHADA** quando há comando e a avaliação estoura (bug aqui não pode abrir a cerca);
  sem comando pra avaliar (evento malformado) libera calado — não há push num evento vazio;
- escape consciente só do owner: `MSS_PUBLICACAO_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "git_publicacao.py"


def _mod():
    spec = importlib.util.spec_from_file_location("git_publicacao", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evento(comando, tool="Bash"):
    return {"hook_event_name": "PreToolUse", "cwd": str(REPO),
            "tool_name": tool, "tool_input": {"command": comando}}


# --- AC1: publicar, integrar e fazer deploy é negado -------------------------------------

@pytest.mark.parametrize("comando", [
    "git push",
    "git push origin main",
    "git push --force-with-lease origin feature/x",
    "git push -u origin HEAD",
    "cd /c/proj && git push",
    "git add -A; git commit -m x; git push",
    "git status | cat && git push origin dev",
    "git -C /c/proj push origin main",
    "git merge feature/x",
    "git merge --no-ff dev",
    "git rebase main",
    "gh pr merge 12 --squash",
    "docker push acr.azurecr.io/app:1.0",
    "az acr build -r acr -t app:1 .",
    "az webapp config appsettings set -g rg -n app --settings X=1",
    "az webapp restart -g rg -n app",
    "az containerapp update -n app -g rg --image x",
    "GIT_TRACE=1 git push",
    "git\tpush origin main",
    "git push origin main\n",
])
def test_nega_publicacao_e_integracao(comando):
    mod = _mod()
    motivo = mod.decidir(_evento(comando), ambiente={})
    assert motivo is not None, f"passou: {comando!r} — a trava não travou"
    assert "owner" in motivo.lower(), "motivo não diz que publicar/integrar é ato do owner"
    assert "/mss-spec:release" in motivo, "motivo não aponta o gate de pré-publicação"


def test_nega_tambem_no_powershell():
    mod = _mod()
    assert mod.decidir(_evento("git push origin main", tool="PowerShell"), ambiente={}) is not None
    assert mod.decidir(_evento("git merge dev; git push", tool="PowerShell"), ambiente={}) is not None


def test_comando_em_varias_linhas_e_pego():
    mod = _mod()
    comando = "git checkout main\ngit merge feature/x\n"
    assert mod.decidir(_evento(comando), ambiente={}) is not None


# --- AC2: o resto do git passa, silencioso -----------------------------------------------

@pytest.mark.parametrize("comando", [
    "git status --short",
    "git log --oneline -5",
    "git diff --stat main..HEAD",
    "git fetch origin",
    "git fetch --all --prune",
    "git add tests/test_x.py hooks/x.py",
    "git commit -m 'feat: x'",
    "git checkout main && git checkout -b feature/nova",
    "git switch -c fix/y",
    "git branch --show-current",
    "git merge --abort",
    "git rebase --abort",
    "git stash && git stash pop",
    "git remote -v",
    "git rev-parse --git-common-dir",
    "python -m pytest -q",
    "docker build -t app .",
    "docker ps",
    "az account show",
    "az webapp log tail -g rg -n app",
    "echo pushing",                 # a palavra solta não é o verbo do git
    "grep -rn 'git push' docs/",    # citar a regra em texto não é executá-la
])
def test_libera_o_resto(comando):
    mod = _mod()
    assert mod.decidir(_evento(comando), ambiente={}) is None, f"barrou de graça: {comando!r}"


def test_outro_tool_nao_e_avaliado():
    mod = _mod()
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Write",
          "tool_input": {"file_path": "x.md", "content": "git push"}}
    assert mod.decidir(ev, ambiente={}) is None


# --- AC3: escape do owner e modos de falha -----------------------------------------------

def test_escape_do_owner():
    mod = _mod()
    assert mod.decidir(_evento("git push origin main"), ambiente={"MSS_PUBLICACAO_OFF": "1"}) is None
    # vazio/branco não conta como escape
    assert mod.decidir(_evento("git push origin main"), ambiente={"MSS_PUBLICACAO_OFF": " "}) is not None


def test_evento_sem_comando_libera_calado():
    mod = _mod()
    assert mod.decidir({"tool_name": "Bash", "tool_input": {}}, ambiente={}) is None
    assert mod.decidir({"tool_name": "Bash"}, ambiente={}) is None
    assert mod.decidir({}, ambiente={}) is None


def test_bug_na_avaliacao_falha_fechada(monkeypatch):
    """Cerca com defeito NÃO pode abrir sozinha: se há comando e a avaliação estoura, nega."""
    mod = _mod()
    monkeypatch.setattr(mod, "publica_ou_integra", lambda _c: 1 / 0)
    motivo = mod.decidir(_evento("git status"), ambiente={})
    assert motivo is not None and "defeito" in motivo.lower()


# --- AC4: protocolo de processo, como o Claude Code roda ---------------------------------

def _rodar(evento, raw=None):
    amb = {k: v for k, v in os.environ.items() if k != "MSS_PUBLICACAO_OFF"}
    return subprocess.run([sys.executable, str(HOOK)],
                          input=raw if raw is not None else json.dumps(evento),
                          capture_output=True, text=True, env=amb, timeout=30)


def test_processo_nega_pelos_dois_protocolos():
    proc = _rodar(_evento("git push origin main"))
    assert proc.returncode == 2, f"esperava exit 2; saiu {proc.returncode}: {proc.stderr}"
    hook = json.loads(proc.stdout)["hookSpecificOutput"]
    assert hook["hookEventName"] == "PreToolUse"
    assert hook["permissionDecision"] == "deny"
    assert "owner" in hook["permissionDecisionReason"].lower()
    assert proc.stderr.strip(), "stderr vazio — runtime que só lê stderr não veria o motivo"


def test_processo_libera_silencioso():
    proc = _rodar(_evento("git status"))
    assert proc.returncode == 0
    assert proc.stdout.strip() == "" and proc.stderr.strip() == ""


def test_processo_entrada_malformada_libera():
    proc = _rodar(None, raw="isto não é json")
    assert proc.returncode == 0


# --- AC5: registrado e ligado por padrão ------------------------------------------------

def test_hook_registrado_em_bash_e_powershell():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    grupos = [g for g in cfg["PreToolUse"]
              if any("git_publicacao.py" in h["command"] for h in g["hooks"])]
    assert grupos, "git_publicacao.py não está registrado no PreToolUse"
    matcher = grupos[0]["matcher"]
    assert "Bash" in matcher and "PowerShell" in matcher, f"matcher não cobre Bash e PowerShell: {matcher}"
    assert "CLAUDE_PLUGIN_ROOT" in grupos[0]["hooks"][0]["command"]
    # a cerca da âncora continua sendo o 1º grupo (o teste dela lê grupos[0])
    assert "projeto_ativo.py" in cfg["PreToolUse"][0]["hooks"][0]["command"]


def test_documentado_no_readme_e_no_molde():
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8").lower()
    assert "git_publicacao.py" in readme
    assert "mss_publicacao_off" in readme, "README não documenta o escape do owner"
    assert "falha fechada" in readme, "README não explica o fail-closed desta cerca"
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").lower()
    assert "git push" in claude and "hook" in claude, \
        "CLAUDE.md não diz que publicar/integrar é ato do owner com cerca por hook"
