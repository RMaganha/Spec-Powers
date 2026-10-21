// Receita-base do Web App (container Linux) — gerada pelo /mss-spec:azure-ambiente.
// Tirada da receita do MSS-UTILS, em produção desde 2026-10-20. A MESMA receita serve aos dois
// ambientes: o que muda mora em hml.bicepparam / prd.bicepparam.
//
// Projeto SEM homologação: o pipeline (opção hml) cria a homologação com esta receita.
// Projeto COM homologação: o export do portal vira conferência — o que o projeto tem a mais entra aqui.
//
// Fora daqui, de propósito:
//  - variáveis de ambiente: no Bicep, `appSettings` SUBSTITUI a coleção inteira — a 2ª execução apagaria
//    a senha preenchida à mão. Quem leva é o infra/app_settings.py.
//  - plano, VNet e registro de imagens: compartilhados entre projetos — já existem, só são apontados.
//  - a ligação com a rede é `virtualNetworkSubnetId` — nunca `networkConfig`, que exige a permissão de
//    alterar a subnet.

param nomeWebApp string
param nomePlano string
// O plano é apontado pelo grupo DELE — nunca suposto no mesmo grupo do Web App.
param grupoPlano string
param subnetId string
// Imagem nunca fixa: o pipeline passa a que está rodando (1ª criação de produção: a da homologação;
// 1ª criação de homologação: uma provisória, trocada pelo pipeline de código no 1º push na dev).
param imagem string
// Comando de inicialização do container (ex.: 'uvicorn main:app --host 0.0.0.0 --port 8000 --workers 6').
param comandoInicial string
// Caminho que a plataforma consulta pra saber se o sistema está de pé (nunca '/').
param caminhoSaude string
// Regras de acesso por IP (ex.: o escritório): [{ ip: '<ip>/32', nome: '<nome>' }]. A rede do próprio
// ambiente já entra sozinha; o resto é negado.
param ipsPermitidos array

var regrasIp = [for (regra, i) in ipsPermitidos: {
  ipAddress: regra.ip
  action: 'Allow'
  tag: 'Default'
  priority: 200 + i
  name: regra.nome
}]
var regraRede = [
  {
    vnetSubnetResourceId: subnetId
    action: 'Allow'
    tag: 'Default'
    priority: 300
    name: 'rede-do-ambiente'
  }
]
var negarResto = [
  {
    ipAddress: 'Any'
    action: 'Deny'
    priority: 2147483647
    name: 'Deny all'
    description: 'Deny all access'
  }
]

resource site 'Microsoft.Web/sites@2024-11-01' = {
  name: nomeWebApp
  location: 'Brazil South'
  kind: 'app,linux,container'
  properties: {
    enabled: true
    serverFarmId: resourceId(grupoPlano, 'Microsoft.Web/serverfarms', nomePlano)
    reserved: true
    isXenon: false
    hyperV: false
    // "Rotear todo o tráfego" DESLIGADO (regra da casa): ligado, o pull da imagem e as chamadas
    // externas passam pela rede e o Web App cai com 503.
    outboundVnetRouting: {
      allTraffic: false
      applicationTraffic: true
      contentShareTraffic: false
      imagePullTraffic: false
      backupRestoreTraffic: false
    }
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: imagem
      acrUseManagedIdentityCreds: false
      alwaysOn: false
      http20Enabled: false
    }
    clientAffinityEnabled: false
    clientCertEnabled: false
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    virtualNetworkSubnetId: subnetId
    keyVaultReferenceIdentity: 'SystemAssigned'
  }
}

// FTP e publicação básica desligados (como na homologação do MSS-UTILS).
resource ftp 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-11-01' = {
  parent: site
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource scm 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-11-01' = {
  parent: site
  name: 'scm'
  properties: {
    allow: false
  }
}

resource web 'Microsoft.Web/sites/config@2024-11-01' = {
  parent: site
  name: 'web'
  properties: {
    numberOfWorkers: 1
    linuxFxVersion: imagem
    acrUseManagedIdentityCreds: false
    alwaysOn: false
    appCommandLine: comandoInicial
    healthCheckPath: caminhoSaude
    httpLoggingEnabled: false
    detailedErrorLoggingEnabled: false
    scmType: 'None'
    webSocketsEnabled: false
    publicNetworkAccess: 'Enabled'
    ipSecurityRestrictions: concat(regrasIp, regraRede, negarResto)
    ipSecurityRestrictionsDefaultAction: 'Deny'
    scmIpSecurityRestrictionsUseMain: false
    scmIpSecurityRestrictionsDefaultAction: 'Allow'
    http20Enabled: false
    minTlsVersion: '1.2'
    scmMinTlsVersion: '1.2'
    ftpsState: 'FtpsOnly'
  }
}
