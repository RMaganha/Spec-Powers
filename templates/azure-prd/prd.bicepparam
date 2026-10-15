// Nomes de PRODUÇÃO — gerado pelo /mss-spec:azure-prd.
// A receita (main.bicep) é a mesma da homologação; aqui mora SÓ o que muda entre os ambientes.
// Sem senha: valor secreto vai nas App Settings do Web App, à parte.
// Troque <projeto> e os <...> pelos valores de produção (a subnet vem da infra, já liberada).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-prod'
param nomePlano = '<plano do App Service de produção>'
param subnetId = '<id da subnet de produção liberada pela infra>'
