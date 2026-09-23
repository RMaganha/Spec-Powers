"""Cerca de publicação por DESTINO — push em homologação/produção é do owner; o resto do git o
assistente roda, com a aprovação do owner.

Nasceu de um acidente real (2026-09, caso F-022): numa janela aberta pra UMA feature, o
assistente absorveu um 2º e um 3º assunto, mesclou branches e disparou `git push` — e o push
é o gatilho do deploy automático em homologação. A 1ª versão da cerca (0.26.0) negava TODO
push/merge/rebase; em uso, travou o dia a dia (merge local, push de feature, até `git merge-base`,
que só lê). O dano do F-022 veio do push que faz DEPLOY — é isso que continua negado.

Propriedades:
- **nega** push cujo destino é branch protegida (main, master, dev, develop, production,
  homolog*, hml*, prod*, release/*) — explícito, `HEAD:dev`, `--delete`, ou `git push` puro
  estando numa delas (ou com o `@{push}` apontando pra uma); nega push de destino indeterminável
  (`--all`, `--mirror`, `--tags`, `:`) e deploy (`docker push`, `az …`, `gh pr merge`);
- **pede aprovação** (`permissionDecision: "ask"`) pra merge, rebase e push de feature/fix;
- **libera calado** o resto (status, fetch, commit, `merge-base`, `merge-tree`, `--abort`, pull);
- **falha FECHADA**: avaliação estourada, ou git inconsultável num push sem destino explícito → nega;
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


def _evento(comando, tool="Bash", cwd=None):
    return {"hook_event_name": "PreToolUse", "cwd": str(cwd or REPO),
            "tool_name": tool, "tool_input": {"command": comando}}


def _git(atual="feature/x", push="feature/x"):
    """Stub do git: (branch atual, destino do `git push` sem refspec)."""
    chamadas = []

    def consultar(pasta):
        chamadas.append(pasta)
        return atual, push
    consultar.chamadas = chamadas
    return consultar


def _avaliar(comando, git=None, tool="Bash", ambiente=None):
    mod = _mod()
    return mod.avaliar(_evento(comando, tool=tool), ambiente={} if ambiente is None else ambiente,
                       git_destino=git or _git())


# --- AC1: push pra homologação/produção, destino indeterminável e deploy → NEGA -------------

@pytest.mark.parametrize("comando", [
    "git push origin main",
    "git push origin master",
    "git push origin dev",
    "git push -u origin develop",
    "git push origin production",
    "git push origin homologacao",
    "git push origin hml",
    "git push origin prod",
    "git push origin release/1.2",
    "git push origin HEAD:dev",
    "git push origin feature/x:main",
    "git push origin +feature/x:master",
    "git push origin refs/heads/feature/x:refs/heads/dev",
    "git push origin --delete main",
    "git push origin feature/x main",            # dois refspecs: um protegido basta
    "git push --force-with-lease origin dev",
    "git push --all",
    "git push --mirror origin",
    "git push --tags",
    "git push origin :",
    "cd /c/proj && git push origin main",
    "git add -A; git commit -m x; git push origin dev",
    "git status | cat && git push origin dev",
    "git -C /c/proj push origin main",
    "GIT_TRACE=1 git push origin main",
    "git\tpush origin main",
    "git push origin main\n",
    "gh pr merge 12 --squash",
    "docker push acr.azurecr.io/app:1.0",
    "az acr build -r acr -t app:1 .",
    "az webapp config appsettings set -g rg -n app --settings X=1",
    "az webapp restart -g rg -n app",
    "az containerapp update -n app -g rg --image x",
])
def test_nega_push_protegido_indeterminado_e_deploy(comando):
    tipo, motivo = _avaliar(comando)
    assert tipo == "deny", f"{comando!r} → {tipo} — a cerca não travou"
    assert "owner" in motivo.lower(), "motivo não diz que é ato do owner"
    assert "/mss-spec:release" in motivo, "motivo não aponta o gate de pré-publicação"


@pytest.mark.parametrize("atual,push", [
    ("main", "main"),
    ("dev", "dev"),
    ("homologacao", "homologacao"),
    ("feature/x", "dev"),          # a feature rastreia origin/dev: `git push` puro iria pra dev
    ("HEAD", None),                # HEAD destacado: destino indeterminado
    (None, None),
])
def test_push_sem_refspec_nega_quando_o_destino_e_protegido_ou_incerto(atual, push):
    for comando in ("git push", "git push origin"):
        tipo, _ = _avaliar(comando, git=_git(atual, push))
        assert tipo == "deny", f"{comando!r} em {atual!r}→{push!r} passou"


def test_git_inconsultavel_nega_push_sem_destino_explicito():
    def quebrado(_pasta):
        raise OSError("git não encontrado")
    tipo, motivo = _avaliar("git push", git=quebrado)
    assert tipo == "deny" and "não deu pra saber" in motivo.lower()


def test_nega_tambem_no_powershell():
    assert _avaliar("git push origin main", tool="PowerShell")[0] == "deny"
    assert _avaliar("git merge dev; git push origin dev", tool="PowerShell")[0] == "deny"


def test_negacao_vence_pedido_no_mesmo_comando():
    assert _avaliar("git merge feature/x && git push origin main")[0] == "deny"
    assert _avaliar("python -m pytest -q | tail -1 && git commit -m x && git push origin feature/x")[0] == "deny"


# --- AC2: merge, rebase e push de feature → PEDE APROVAÇÃO ---------------------------------

@pytest.mark.parametrize("comando", [
    "git merge feature/x",
    "git merge --no-ff dev",               # traz dev pra dentro da feature, local
    "git checkout main\ngit merge feature/x\n",
    "git rebase main",
    "git rebase -i HEAD~3",
    "git push origin feature/x",
    "git push -u origin fix/y",
    "git push --force-with-lease origin feature/x",
    "git push origin HEAD:feature/x",
    "git push",                            # stub: está em feature/x, @{push} = feature/x
    "git push -u origin HEAD",
    "cd /c/proj && git push",
])
def test_pede_aprovacao_pra_integrar_e_push_de_feature(comando):
    tipo, motivo = _avaliar(comando)
    assert tipo == "ask", f"{comando!r} → {tipo}"
    assert "aprova" in motivo.lower(), "motivo não pede a aprovação do owner"
    assert "homologação/produção" in motivo, "motivo não lembra o que segue bloqueado"


def test_consulta_o_git_na_pasta_do_comando():
    git = _git()
    _avaliar("git -C /c/outro push", git=git)
    assert git.chamadas[-1] == "/c/outro"
    git = _git()
    _avaliar('cd "/c/pasta com espaco" && git push', git=git)
    assert git.chamadas[-1] == "/c/pasta com espaco"
    git = _git()
    _avaliar("git push", git=git)
    assert git.chamadas[-1] == str(REPO)


def test_push_com_destino_explicito_nao_consulta_o_git():
    git = _git()
    _avaliar("git push origin feature/x", git=git)
    assert git.chamadas == []


# --- AC3: o resto passa, calado ------------------------------------------------------------

@pytest.mark.parametrize("comando", [
    "git status --short",
    "git log --oneline -5",
    "git diff --stat main..HEAD",
    "git fetch origin",
    "git fetch --all --prune",
    "git pull",
    "git add tests/test_x.py hooks/x.py",
    "git commit -m 'feat: x'",
    "git checkout main && git checkout -b feature/nova",
    "git switch -c fix/y",
    "git branch --show-current",
    "git merge --abort",
    "git rebase --abort",
    "git merge-base main feature/x",       # só lê — era falso positivo na 0.30.0
    "git merge-tree --write-tree main feature/x",
    "git merge-file a b c",
    "git stash && git stash pop",
    "git remote -v",
    "git rev-parse --git-common-dir",
    "python -m pytest -q",
    "docker build -t app .",
    "docker ps",
    "az account show",
    "az webapp log tail -g rg -n app",
    "echo pushing",
    "grep -rn 'git push origin main' docs/",
])
def test_libera_o_resto(comando):
    tipo, motivo = _avaliar(comando)
    assert tipo is None and motivo is None, f"{comando!r} → {tipo}"


def test_outro_tool_nao_e_avaliado():
    mod = _mod()
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Write",
          "tool_input": {"file_path": "x.md", "content": "git push origin main"}}
    assert mod.avaliar(ev, ambiente={}, git_destino=_git()) == (None, None)


# --- AC4: escape do owner e modos de falha -------------------------------------------------

def test_escape_do_owner():
    assert _avaliar("git push origin main", ambiente={"MSS_PUBLICACAO_OFF": "1"}) == (None, None)
    assert _avaliar("git merge x", ambiente={"MSS_PUBLICACAO_OFF": "1"}) == (None, None)
    # vazio/branco não conta como escape
    assert _avaliar("git push origin main", ambiente={"MSS_PUBLICACAO_OFF": " "})[0] == "deny"


def test_evento_sem_comando_libera_calado():
    mod = _mod()
    for ev in ({"tool_name": "Bash", "tool_input": {}}, {"tool_name": "Bash"}, {}):
        assert mod.avaliar(ev, ambiente={}, git_destino=_git()) == (None, None)


def test_bug_na_avaliacao_falha_fechada(monkeypatch):
    """Cerca com defeito NÃO pode abrir sozinha: se há comando e a avaliação estoura, nega."""
    mod = _mod()
    monkeypatch.setattr(mod, "publica_ou_integra", lambda *_a, **_k: 1 / 0)
    tipo, motivo = mod.avaliar(_evento("git status"), ambiente={}, git_destino=_git())
    assert tipo == "deny" and "defeito" in motivo.lower()


def test_decidir_segue_devolvendo_o_motivo():
    """Compatibilidade: `decidir` devolve o motivo de qualquer ação (negar ou perguntar), ou None."""
    mod = _mod()
    assert mod.decidir(_evento("git status"), ambiente={}) is None
    assert "owner" in mod.decidir(_evento("git push origin main"), ambiente={}).lower()


# --- AC5: protocolo de processo, como o Claude Code roda -----------------------------------

def _rodar(evento, raw=None):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_PUBLICACAO_OFF", "MSS_PIPE_TESTE_OFF")}
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


def test_processo_pede_aprovacao_com_exit_zero():
    """`ask` só vale com exit 0 — exit 2 é bloqueio e ignoraria o JSON (doc do Claude Code)."""
    proc = _rodar(_evento("git merge feature/x"))
    assert proc.returncode == 0, proc.stderr
    hook = json.loads(proc.stdout)["hookSpecificOutput"]
    assert hook["permissionDecision"] == "ask"
    assert "git merge" in hook["permissionDecisionReason"]
    assert proc.stderr.strip() == ""


def test_processo_libera_silencioso():
    proc = _rodar(_evento("git status"))
    assert proc.returncode == 0
    assert proc.stdout.strip() == "" and proc.stderr.strip() == ""


def test_processo_entrada_malformada_libera():
    proc = _rodar(None, raw="isto não é json")
    assert proc.returncode == 0


def test_processo_consulta_o_git_de_verdade(tmp_path):
    """Sem stub: repo real em `dev` → `git push` puro é negado; em feature → pede aprovação."""
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q", "-b", "dev")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x")
    assert json.loads(_rodar(_evento("git push", cwd=tmp_path)).stdout)["hookSpecificOutput"][
        "permissionDecision"] == "deny"
    git("checkout", "-q", "-b", "feature/y")
    assert json.loads(_rodar(_evento("git push", cwd=tmp_path)).stdout)["hookSpecificOutput"][
        "permissionDecision"] == "ask"


# --- AC6: registrado e documentado ---------------------------------------------------------

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
    assert "aprovação" in readme and "release/*" in readme, "README não explica o destino protegido e o ask"
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").lower()
    assert "git push" in claude and "hook" in claude, \
        "CLAUDE.md não diz que o push de homologação/produção é do owner com cerca por hook"
    assert "aprova" in claude, "CLAUDE.md não diz que o resto do git roda com a aprovação do owner"
