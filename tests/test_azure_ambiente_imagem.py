"""Imagem do Web App no pipeline do /mss-spec:azure-ambiente — roda o trecho de bash real com um `az` falso.

Regra (spec docs/specs/azure-ambiente.md):
- Web App já existe → usa a imagem que está rodando nele (nova execução nunca volta pra versão velha).
- 1ª criação de produção (Web App de produção ainda não existe) → usa a imagem que está rodando na
  HOMOLOGAÇÃO: já testada, mesmo registro; produção nasce espelho e sobe sem esperar o pipeline de código
  de produção (que pode nem existir ainda — MSS-UTILS, 2026-10-15).
- Não deu pra ler nem a da homologação → o script FALHA (nunca cria produção com imagem inexistente).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parent.parent
PIPE = REPO / "templates" / "azure-ambiente" / "azure-pipelines-infra.yml"
VARS = {"$(rgHml)": "RG-MSSAI-DEV", "$(webAppHml)": "app-hml",
        "$(rgPrd)": "RG-MSSAI-PRD", "$(webAppPrd)": "app-prd"}
IMG_HML = "DOCKER|mssaicontainerregistry.azurecr.io/app-hml:123"
IMG_PRD = "DOCKER|mssaicontainerregistry.azurecr.io/app-prd:99"


def _bash():
    """O `bash` que funciona. No PowerShell do Windows o 1º do PATH é o do WSL (`System32\\bash.exe`), que
    sem distribuição instalada não roda — aí vale o que vem com o Git (`<Git>\\bin\\bash.exe`)."""
    candidatos = [shutil.which("bash")]
    git = shutil.which("git")
    if git:
        raiz = Path(git).resolve().parent.parent          # <Git>\cmd\git.exe → <Git>
        candidatos += [raiz / "bin" / "bash.exe", raiz / "usr" / "bin" / "bash.exe"]
    for b in candidatos:
        if not b or not Path(b).exists():
            continue
        try:
            ok = subprocess.run([str(b), "-c", "echo ok"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if ok.stdout.strip() == "ok":
            return str(b)
    pytest.skip("bash indisponível")


def _scripts():
    """{estágio: inlineScript} — inclusive o Criar, inserido por `${{ if ... }}`."""
    doc = yaml.safe_load(PIPE.read_text(encoding="utf-8"))
    out = {}
    for item in doc["stages"]:
        estagios = [item] if "stage" in item else next(iter(item.values()))
        for e in estagios:
            texto = yaml.safe_dump(e, allow_unicode=True)
            job = e["jobs"][0]
            steps = job.get("steps") or job["strategy"]["runOnce"]["deploy"]["steps"]
            out[e["stage"]] = next(s["inputs"]["inlineScript"] for s in steps if "inputs" in s)
            assert texto
    return out


def _bloco(script):
    ini, fim = script.index("# imagem: início"), script.index("# imagem: fim")
    bloco = script[ini:fim]
    for k, v in VARS.items():
        bloco = bloco.replace(k, v)
    return bloco


def _rodar(bloco, rg, app, hml=IMG_HML, prd=None):
    falso = f"""
az() {{
  case "$*" in
    *"-n app-prd"*) if [ -n "{prd or ''}" ]; then echo "{prd or ''}"; return 0; fi; return 3 ;;
    *"-n app-hml"*) if [ -n "{hml or ''}" ]; then echo "{hml or ''}"; return 0; fi; return 3 ;;
  esac
  return 9
}}
set -euo pipefail
RG='{rg}'; APP='{app}'
"""
    proc = subprocess.run([_bash(), "-c", falso + bloco + '\necho "IMAGEM=${IMAGEM:-<vazio>}"'],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""


def test_os_dois_estagios_tem_o_mesmo_bloco_de_imagem():
    s = _scripts()
    assert set(s) == {"Simular", "CriarHml", "Criar"}
    assert _bloco(s["Simular"]) == _bloco(s["Criar"]) == _bloco(s["CriarHml"]), "a regra da imagem divergiu entre os estagios"


@pytest.mark.parametrize("estagio", ["Simular", "Criar"])
def test_primeira_criacao_de_producao_usa_a_imagem_da_homologacao(estagio):
    code, saida = _rodar(_bloco(_scripts()[estagio]), "RG-MSSAI-PRD", "app-prd", prd=None)
    assert code == 0 and saida == f"IMAGEM={IMG_HML}"


@pytest.mark.parametrize("estagio", ["Simular", "Criar"])
def test_producao_existente_mantem_a_imagem_que_esta_rodando(estagio):
    code, saida = _rodar(_bloco(_scripts()[estagio]), "RG-MSSAI-PRD", "app-prd", prd=IMG_PRD)
    assert code == 0 and saida == f"IMAGEM={IMG_PRD}"


def test_simulacao_da_homologacao_usa_a_propria_imagem():
    code, saida = _rodar(_bloco(_scripts()["Simular"]), "RG-MSSAI-DEV", "app-hml")
    assert code == 0 and saida == f"IMAGEM={IMG_HML}"


def test_sem_imagem_nem_na_homologacao_falha_em_vez_de_criar():
    code, _ = _rodar(_bloco(_scripts()["Criar"]), "RG-MSSAI-PRD", "app-prd", hml=None, prd=None)
    assert code != 0, "criaria produção com uma imagem que não existe"


def _bloco_identidade(script):
    ini, fim = script.index("# identidade: início"), script.index("# identidade: fim")
    return script[ini:fim]


def test_simular_mostra_a_identidade_que_recebe_as_permissoes():
    """MSS-UTILS 2026-10-16: tres rodadas de permissao foram pra identidade errada (pegaram o codigo pelo
    'Manage App registration'). O Simular imprime o object id da identidade REAL do pipeline — e com ele
    que a infra da as permissoes (--assignee-object-id)."""
    import base64
    import json as _json
    corpo = base64.urlsafe_b64encode(_json.dumps({"oid": "ecab5b96-527b-415d-bc02-3a31cfea7fb0"}).encode()).decode().rstrip("=")
    token = f"cabecalho.{corpo}.assinatura"
    falso = f'az() {{ echo "{token}"; }}\nset -euo pipefail\n'
    import sys
    # no agente Linux é `python3`; aqui, o Python que roda a suíte (no Windows `python3` pode não existir)
    bloco = _bloco_identidade(_scripts()["Simular"]).replace("python3", f'"{Path(sys.executable).as_posix()}"')
    proc = subprocess.run([_bash(), "-c", falso + bloco],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "ecab5b96-527b-415d-bc02-3a31cfea7fb0" in proc.stdout
    assert "Identidade do pipeline" in proc.stdout
    assert token not in proc.stdout, "o token nunca vai pro log"


def test_homologacao_nova_nasce_com_imagem_provisoria():
    """Projeto novo: a imagem real nasce no 1o push na dev; a homologacao e criada com uma provisoria."""
    code, saida = _rodar(_bloco(_scripts()["CriarHml"]), "RG-MSSAI-DEV", "app-hml", hml=None)
    assert code == 0 and saida == "IMAGEM=DOCKER|mcr.microsoft.com/appsvc/staticsite:latest"


def test_criar_homologacao_nunca_mexe_numa_que_ja_existe(tmp_path):
    """A guarda roda o script INTEIRO do CriarHml com um az falso que registra cada chamada."""
    chamadas = tmp_path / "chamadas.txt"
    falso = f"""
az() {{
  echo "$*" >> "{chamadas.as_posix()}"
  case "$*" in *"webapp show"*) echo "DOCKER|x"; return 0 ;; esac
  return 0
}}
"""
    script = _scripts()["CriarHml"]
    for k, v in VARS.items():
        script = script.replace(k, v)
    proc = subprocess.run([_bash(), "-c", falso + script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "nada a criar" in proc.stdout
    feitas = chamadas.read_text(encoding="utf-8") if chamadas.exists() else ""
    assert "deployment" not in feitas and "appsettings" not in feitas, feitas
