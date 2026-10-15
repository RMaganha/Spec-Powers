"""Imagem do Web App no pipeline do /mss-spec:azure-prd — roda o trecho de bash real com um `az` falso.

Regra (spec docs/specs/azure-prd.md):
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
PIPE = REPO / "templates" / "azure-prd" / "azure-pipelines-prd.yml"
VARS = {"$(rgHml)": "RG-MSSAI-DEV", "$(webAppHml)": "app-hml",
        "$(rgPrd)": "RG-MSSAI-PRD", "$(webAppPrd)": "app-prd"}
IMG_HML = "DOCKER|mssaicontainerregistry.azurecr.io/app-hml:123"
IMG_PRD = "DOCKER|mssaicontainerregistry.azurecr.io/app-prd:99"


def _bash():
    b = shutil.which("bash")
    if not b or subprocess.run([b, "-c", "echo ok"], capture_output=True, text=True).stdout.strip() != "ok":
        pytest.skip("bash indisponível")
    return b


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
    assert set(s) == {"Simular", "Criar"}
    assert _bloco(s["Simular"]) == _bloco(s["Criar"]), "a regra da imagem divergiu entre Simular e Criar"


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
