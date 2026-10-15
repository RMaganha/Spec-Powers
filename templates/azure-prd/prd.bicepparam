// Nomes de PRODUÇÃO — gerado pelo /mss-spec:azure-prd.
// A receita (main.bicep) é a mesma da homologação; aqui mora SÓ o que muda entre os ambientes.
// Variáveis de ambiente NÃO entram aqui nem no main.bicep: quem cuida delas é o infra/app_settings.py.
// Troque <projeto> e os <...> pelos valores de produção (a subnet vem da infra, já liberada).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-prod'
param nomePlano = '<plano do App Service de produção>'
param subnetId = '<id da subnet de produção liberada pela infra>'
// A imagem que está rodando: o pipeline lê do Web App e passa em IMAGEM, pra uma nova execução nunca
// voltar produção pra uma versão velha. O valor abaixo só vale na 1ª vez (Web App ainda não existe).
param imagem = readEnvironmentVariable('IMAGEM', 'DOCKER|mssaicontainerregistry.azurecr.io/<imagem de produção>:latest')
