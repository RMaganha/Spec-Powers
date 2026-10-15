# Azure produção — receita da homologação levada pra produção (`/mss-spec:azure-prd`)

## Estado atual
**`/mss-spec:azure-prd`** (`commands/azure-prd.md`) guia, na janela do projeto, quatro etapas: exportar o
grupo de recursos da homologação pelo portal ("Exportar modelo", em Bicep) → limpar a receita em
`infra/main.bicep` + um arquivo de nomes por ambiente (`infra/hml.bicepparam`, `infra/prd.bicepparam`),
sem senha e sem IP fixo da homologação → **simular** com `what-if` contra `RG-MSSAI-DEV`, que tem de
responder "nada muda" → montar a etapa do pipeline do Azure DevOps (modelo em
`templates/azure-prd/azure-pipelines-prd.yml`): `what-if` contra `RG-MSSAI-PRD` → para no botão de
aprovação do ambiente `producao` (Pipelines → Environments → Approvals and checks) → só cria depois do
clique. O prestador libera, uma vez, a conexão do pipeline pra criar recursos em `RG-MSSAI-PRD`.
O `hooks/git_publicacao.py` nega ao assistente `az deployment ... create` (e `az stack ... create`);
`what-if`, `validate` e `show` seguem livres.

Critérios de aceite:
- DADO o projeto em homologação, QUANDO o owner roda `/mss-spec:azure-prd` na janela dele, ENTÃO saem
  `infra/main.bicep`, `infra/hml.bicepparam` e `infra/prd.bicepparam`, sem senha e sem IP fixo da homologação.
- DADO a receita, QUANDO roda `what-if` contra `RG-MSSAI-DEV`, ENTÃO o resultado é "nada muda".
- DADO o pipeline de produção, QUANDO dispara, ENTÃO mostra a lista do `what-if` e só cria depois da aprovação.
- DADO o assistente, QUANDO tenta `az deployment group create`, ENTÃO o hook nega; o `what-if` passa.

Fora de escopo: rede (vnet/IP — liberação segue com a infra), valores de senha (App Settings à parte),
Terraform (multi-nuvem já está fora de escopo do kit), rodar a simulação no MSS-UTILS por esta janela
(dogfood é na janela dele).

## Histórico
- 2026-10-15 — criado: produção é montada à mão por um prestador a partir de documentação, com rodadas
  de ajuste. Escolhido Bicep (nativo do Azure, sem arquivo de estado) em vez de Terraform; o owner
  preferiu o caminho do pipeline com botão de aprovação, que usa a mesma receita do "prestador roda um
  comando". Nome do comando: o owner pediu `AzurePrd`; ficou `azure-prd` pelo padrão minúsculo do kit.
