"""Receita-base do /mss-spec:azure-ambiente — `templates/azure-ambiente/main.bicep`.

Tirada da receita do MSS-UTILS, que está em produção desde 2026-10-20. Serve pra projeto SEM homologação
(o pipeline cria) e é o ponto de partida também pra quem tem: o export vira conferência. Os arquivos de
nomes por ambiente declaram exatamente os parâmetros da receita — parâmetro sobrando ou faltando quebra
a compilação do Bicep no pipeline.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "templates" / "azure-ambiente"
RECEITA = (BASE / "main.bicep").read_text(encoding="utf-8")
PARAMS = ("nomeWebApp", "nomePlano", "grupoPlano", "subnetId", "imagem", "comandoInicial", "caminhoSaude",
          "ipsPermitidos")


def _sem_comentarios(texto):
    return "\n".join(linha.split("//")[0] if not linha.strip().startswith("//") else "" for linha in texto.splitlines())


def test_receita_declara_os_parametros_de_cada_ambiente():
    declarados = re.findall(r"^param (\w+) ", RECEITA, flags=re.M)
    assert tuple(declarados) == PARAMS, declarados


def test_arquivos_de_nomes_casam_com_a_receita():
    for nome in ("hml.bicepparam", "prd.bicepparam"):
        texto = (BASE / nome).read_text(encoding="utf-8")
        assert tuple(re.findall(r"^param (\w+) =", texto, flags=re.M)) == PARAMS, nome


def test_receita_sem_nada_fixo_de_ambiente_nem_variavel():
    corpo = _sem_comentarios(RECEITA)
    for proibido in ("appSettings", "networkConfig", "virtualNetworkConnections", "vnetName", "vnetRouteAllEnabled",
                     "hostNameBindings", "hostNameSslStates", "customDomainVerificationId", "publishingUsername",
                     "RG-MSSAI", "VNET-MSSD", "azurecr.io", "mss-miti-ai-"):
        assert proibido not in corpo, f"receita-base com {proibido!r}"
    assert not re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", corpo), "IP fixo na receita (vai em ipsPermitidos)"


def test_receita_segue_as_regras_da_casa():
    corpo = _sem_comentarios(RECEITA)
    assert "virtualNetworkSubnetId: subnetId" in corpo
    assert "serverFarmId: resourceId(grupoPlano, 'Microsoft.Web/serverfarms', nomePlano)" in corpo
    assert corpo.count("linuxFxVersion: imagem") == 2
    assert "appCommandLine: comandoInicial" in corpo and "healthCheckPath: caminhoSaude" in corpo
    assert re.search(r"allTraffic:\s*false", corpo), "rotear todo o trafego tem de ficar desligado"
    assert "httpsOnly: true" in corpo and "minTlsVersion: '1.2'" in corpo
    assert "vnetSubnetResourceId: subnetId" in corpo, "regra de acesso da rede do ambiente"


def test_partes_internas_sem_location():
    """Aviso BCP187 visto no MSS-UTILS: location só no Web App."""
    blocos = re.split(r"^resource ", _sem_comentarios(RECEITA), flags=re.M)[1:]
    for bloco in blocos:
        if "parent: site" in bloco:
            assert "location:" not in bloco, bloco.splitlines()[0]
