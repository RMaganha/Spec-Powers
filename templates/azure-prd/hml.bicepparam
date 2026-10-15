// Nomes de HOMOLOGAÇÃO — gerado pelo /mss-spec:azure-prd.
// Serve pra SIMULAR: o pipeline com ambiente hml roda o what-if da receita com estes nomes contra
// RG-MSSAI-DEV, e o resultado tem de ser "nada muda".
// Os valores aqui são os que JÁ existem na homologação (copie do portal ou do export).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-dev-br'
param nomePlano = '<plano do App Service de homologação>'
param subnetId = '<id da subnet de homologação>'
// A imagem muda a cada push na dev: o pipeline lê a que está rodando e passa em IMAGEM.
param imagem = readEnvironmentVariable('IMAGEM', 'DOCKER|mssaicontainerregistry.azurecr.io/<imagem de homologação>:latest')
