// Nomes de HOMOLOGAÇÃO — gerado pelo /mss-spec:azure-prd.
// Serve pra SIMULAR: o what-if da receita com estes nomes contra RG-MSSAI-DEV tem de responder "nada muda".
// Os valores aqui são os que JÁ existem na homologação (copie do portal ou do export).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-dev-br'
param nomePlano = '<plano do App Service de homologação>'
param subnetId = '<id da subnet de homologação>'
