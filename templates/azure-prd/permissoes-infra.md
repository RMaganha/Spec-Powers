# Pedido à infra — permissões do pipeline de criação de produção

Gerado pelo `/mss-spec:azure-prd`. Feito **uma vez só**: vale pra todos os projetos que usam a mesma
conexão do pipeline e a mesma rede de produção. Se a seção 5 do `docs/AMBIENTE.md` já registra que foi
feito, não refaça.

**Riscos:** os papéis abaixo só deixam **ler** e **ligar** um Web App na subnet de produção. Nenhum
altera nem apaga a rede. NÃO dar `subnets/write` nem o papel pronto "Network Contributor", que permitem
alterar e apagar a rede. Nota: qualquer pipeline do projeto MSS-AI que use essa mesma conexão passa a
poder ligar um Web App nessa subnet.

## 1. O código da identidade do pipeline

Use o código que o **próprio pipeline** mostra. Não use o do "Manage App registration": no MSS-UTILS
(2026-10-16) três rodadas de permissão foram pra uma identidade que não era a do pipeline.

Onde está: Azure DevOps → **Pipelines** → `<PROJETO>-INFRA` → a última execução → estágio **Simular** →
item **Receita + variáveis: o que mudaria** → a linha
`Identidade do pipeline (object id, é este que recebe as permissões): <código>`.

Nos comandos abaixo, troque `OBJECT_ID` por esse código, mantendo as aspas. Exemplo de como fica:
`--assignee-object-id "ecab5b96-527b-415d-bc02-3a31cfea7fb0"`.

## 2. Ambiente `producao` com aprovadores (Azure DevOps — administrador do projeto MSS-AI)

1. **Pipelines** → **Environments** → **New environment** → nome `producao` (minúsculo, sem acento) →
   **Resource: None** → **Create**.
2. Dentro de `producao` → **⋮** → **Approvals and checks** → **+** → **Approvals** (não o "Pre-check" nem o
   "Post-check") → **Next** → em **Approvers**, quem aprova → em **Advanced**, deixar marcado "Allow
   approvers to approve their own runs" se quem roda também aprova → **Create**.
3. Opcional: em **⋮** → **Security**, dar o papel **Administrator** nesse ambiente ao responsável pelo
   projeto, pra ele manter os aprovadores sem novo chamado.

## 3. Permissões na rede de produção (terminal da infra, ex.: Cloud Shell)

3.1. **Conferir se os papéis já existem** (só leitura):
```bash
az role definition list --custom-role-only true --query "[?roleName=='MSIG-VNet-Join-Subnet' || roleName=='MSIG-VNet-ServiceEndpoint-Subnet'].roleName" -o tsv
```
Os dois nomes aparecem → pule para o 3.3.

3.2. **Criar os papéis que faltam:**
```bash
az role definition create --role-definition '{"Name":"MSIG-VNet-Join-Subnet","Description":"Permite ligar Web Apps numa subnet, sem alterar a rede.","Actions":["Microsoft.Network/virtualNetworks/subnets/join/action","Microsoft.Network/virtualNetworks/subnets/read"],"AssignableScopes":["/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654"]}'
```
```bash
az role definition create --role-definition '{"Name":"MSIG-VNet-ServiceEndpoint-Subnet","Description":"Permite regra de acesso de Web App apontando para a subnet, sem alterar a rede.","Actions":["Microsoft.Network/virtualNetworks/subnets/joinViaServiceEndpoint/action"],"AssignableScopes":["/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654"]}'
```
Depois de criar, espere uns 2 minutos.

3.3. **Dar os três papéis à identidade do pipeline:**
```bash
az role assignment create --assignee-object-id "OBJECT_ID" --assignee-principal-type ServicePrincipal --role "MSIG-VNet-Join-Subnet" --scope "/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654/resourceGroups/RG-MSSD-PRD/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-PRD/subnets/SNET-WEB-AI-PRD"
```
```bash
az role assignment create --assignee-object-id "OBJECT_ID" --assignee-principal-type ServicePrincipal --role "Reader" --scope "/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654/resourceGroups/RG-MSSD-PRD/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-PRD"
```
```bash
az role assignment create --assignee-object-id "OBJECT_ID" --assignee-principal-type ServicePrincipal --role "MSIG-VNet-ServiceEndpoint-Subnet" --scope "/subscriptions/e87b4af3-ce34-4c44-8c64-0151ca959654/resourceGroups/RG-MSSD-PRD/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-PRD/subnets/SNET-WEB-AI-PRD"
```
Confira em cada saída: `"principalId": "OBJECT_ID"` (o mesmo código do item 1).

| Papel | Pra quê | Fonte |
|---|---|---|
| `MSIG-VNet-Join-Subnet` (na subnet) | ligar o Web App na rede de produção | Microsoft Learn — *Integrate your app with an Azure virtual network*, seção Permissions |
| `Reader` (na rede `VNET-MSSD-PRD`) | ler a rede (`virtualNetworks/read`, exigida pela mesma seção) | idem |
| `MSIG-VNet-ServiceEndpoint-Subnet` (na subnet) | a regra de acesso do Web App que aponta pra subnet (ex.: n8n) | erro real do Azure: `LinkedAuthorizationFailed … joinViaServiceEndpoint/action` |

A subnet `SNET-WEB-AI-PRD` já está delegada para `Microsoft.Web/serverFarms` (conferido no portal em
2026-10-16), por isso a permissão de alterar a subnet não é necessária.
