// Nomes de HOMOLOGAÇÃO — gerado pelo /mss-spec:azure-prd.
// Serve pra SIMULAR: o pipeline com ambiente hml roda o what-if da receita com estes nomes contra
// RG-MSSAI-DEV, e o resultado tem de ser "nada muda".
// Os valores aqui são os que JÁ existem na homologação (copie do portal ou do export).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-dev-br'
param nomePlano = 'mss-ai-asp-dev-br'
// Confira no export: o serverFarmId do Web App traz o grupo do plano (…/resourceGroups/<grupo>/…).
param grupoPlano = 'RG-MSSAI-DEV'
// O id completo vem do export (…/virtualNetworks/VNET-MSSD-DEVQA/subnets/SNET-WEB-AI-DEVQA).
param subnetId = '<id da subnet de homologação, copiado do export>'
// A imagem muda a cada push na dev: o pipeline lê a que está rodando e passa em IMAGEM (sem valor
// padrão de propósito — faltou IMAGEM, a simulação falha em vez de comparar com uma imagem inventada).
param imagem = readEnvironmentVariable('IMAGEM')
