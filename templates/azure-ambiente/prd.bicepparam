// Nomes de PRODUÇÃO — gerado pelo /mss-spec:azure-ambiente.
// A receita (main.bicep) é a mesma da homologação; aqui mora SÓ o que muda entre os ambientes.
// Variáveis de ambiente NÃO entram aqui nem no main.bicep: quem cuida delas é o infra/app_settings.py.
// A trocar: <projeto>, <porta>/<processos> e os IPs — os mesmos da homologação. O resto é fixo de
// produção (docs/AMBIENTE.md §5).
using './main.bicep'

param nomeWebApp = 'mss-miti-ai-<projeto>-prod'
param nomePlano = 'mss-ai-asp-prod-br'
// O plano fica em RG-MSSAI-PRD (confirmado no portal em 2026-10-15); a receita aponta pelo grupo, não supõe.
param grupoPlano = 'RG-MSSAI-PRD'
// VNET-MSSD-PRD fica no grupo RG-MSSD-PRD (confirmado no portal em 2026-10-15) — docs/AMBIENTE.md §5.
param subnetId = '/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654/resourceGroups/RG-MSSD-PRD/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-PRD/subnets/SNET-WEB-AI-PRD'
// A imagem vem SEMPRE do pipeline, em IMAGEM: a que está rodando em produção (nova execução nunca volta
// pra versão velha) ou, na 1ª criação, a que está rodando na homologação (já testada, mesmo registro).
// Sem valor padrão de propósito: faltou IMAGEM, a receita falha em vez de criar com imagem inexistente.
param imagem = readEnvironmentVariable('IMAGEM')
// Iguais aos da homologação: produção é espelho.
param comandoInicial = 'uvicorn main:app --host 0.0.0.0 --port <porta> --workers <processos>'
param caminhoSaude = '/health'
param ipsPermitidos = [
  { ip: '<ip do escritório>/32', nome: 'escritorio' }
]
