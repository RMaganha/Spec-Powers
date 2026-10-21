// Nomes de HOMOLOGAÇÃO — gerado pelo /mss-spec:azure-ambiente.
// Homologação ainda não existe: o pipeline (opção hml) cria com estes valores.
// Homologação já existe: o pipeline (opção hml) só compara — o resultado tem de ser "nada muda".
// Troque <projeto>, <porta> e os IPs pelos valores do projeto (docs/AMBIENTE.md §5).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-dev-br'
param nomePlano = 'mss-ai-asp-dev-br'
// Grupo do plano conferido no export do MSS-UTILS (serverFarmId …/resourceGroups/RG-MSSAI-DEV/…).
param grupoPlano = 'RG-MSSAI-DEV'
// VNET-MSSD-DEVQA fica no grupo RG-MSSD-DEVQA (export do MSS-UTILS, 2026-10-16) — docs/AMBIENTE.md §5.
param subnetId = '/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654/resourceGroups/RG-MSSD-DEVQA/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-DEVQA/subnets/SNET-WEB-AI-DEVQA'
// A imagem vem SEMPRE do pipeline, em IMAGEM: a que está rodando ou, na 1ª criação, uma provisória.
// Sem valor padrão de propósito — faltou IMAGEM, o pipeline falha em vez de inventar.
param imagem = readEnvironmentVariable('IMAGEM')
// O mesmo comando que o pipeline de código (azure-pipelines.yml) usa.
param comandoInicial = 'uvicorn main:app --host 0.0.0.0 --port <porta> --workers <processos>'
param caminhoSaude = '/health'
// IPs com acesso (ex.: o escritório) — os mesmos nos dois ambientes. Copie de um projeto que já tem.
param ipsPermitidos = [
  { ip: '<ip do escritório>/32', nome: 'escritorio' }
]
