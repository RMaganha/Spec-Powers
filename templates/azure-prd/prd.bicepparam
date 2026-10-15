// Nomes de PRODUÇÃO — gerado pelo /mss-spec:azure-prd.
// A receita (main.bicep) é a mesma da homologação; aqui mora SÓ o que muda entre os ambientes.
// Variáveis de ambiente NÃO entram aqui nem no main.bicep: quem cuida delas é o infra/app_settings.py.
// Troque <projeto> e os <...> pelos valores de produção (a subnet vem da infra, já liberada).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-prod'
param nomePlano = 'mss-ai-asp-prod-br'
// VNET-MSSD-PRD fica no grupo RG-MSSD-PRD (confirmado no portal em 2026-10-15) — docs/AMBIENTE.md §5.
param subnetId = '/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654/resourceGroups/RG-MSSD-PRD/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-PRD/subnets/SNET-WEB-AI-PRD'
// A imagem que está rodando: o pipeline lê do Web App e passa em IMAGEM, pra uma nova execução nunca
// voltar produção pra uma versão velha. O valor abaixo só vale na 1ª vez (Web App ainda não existe).
param imagem = readEnvironmentVariable('IMAGEM', 'DOCKER|mssaicontainerregistry.azurecr.io/<imagem de produção>:latest')
