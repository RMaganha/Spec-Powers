---
description: Leva a homologação Azure que já funciona pra produção — receita Bicep exportada da homologação, simulada com what-if e aplicada pelo pipeline com botão de aprovação
argument-hint: ""
disable-model-invocation: true
---

Você vai montar a **receita de produção** deste projeto a partir da **homologação que já funciona**, pra
que produção deixe de ser montada à mão a partir de documentação. Ferramenta: **Bicep** (nativo do
Azure, sem arquivo de estado pra guardar). Padrão de nomes e grupos de recursos em `docs/AMBIENTE.md` §5
(homologação `RG-MSSAI-DEV` · produção `RG-MSSAI-PRD`). Spec do kit: `docs/specs/azure-prd.md`.

**Limites (nunca violar):**
- **Você nunca aplica a receita.** `az deployment group create` (e qualquer `az deployment … create`) é
  negado pelo hook `git_publicacao.py`: quem cria em produção é o **pipeline**, depois da aprovação do
  owner. Você pode rodar `what-if`, `validate`, `show` e `az bicep build` — só leem.
- **Fora da receita:** liberação de rede (vnet/IP — segue com a infra; a receita só **aponta** pra subnet
  já liberada) e **valores de senha** (vão nas App Settings do Web App, à parte — nunca no `.bicep` nem
  no `.bicepparam`, que são versionados).
- Mostre o que vai gravar e **confirme antes de gravar** cada arquivo.

## 1. Exportar a homologação (o owner faz no portal)

Peça ao owner, em passo numerado:
1. Portal do Azure → **Grupos de recursos** → `RG-MSSAI-DEV`.
2. Marque **só** os recursos deste projeto (Web App `mss-miti-ai-<projeto>-dev-br`, o plano do App
   Service dele e o que mais for exclusivo dele) → **Exportar modelo** → aba **Bicep** → **Baixar**.
3. Salvar o arquivo baixado em `infra/export-hml.bicep` (fica **fora** do git: acrescente
   `infra/export-*` no `.gitignore` — o export pode trazer valores da homologação).

Recurso **compartilhado** com outros projetos (registro de imagens `mssaicontainerregistry`, vnet,
plano usado por vários apps) **não** entra na receita: ele já existe e é só referenciado.

## 2. Limpar a receita

A partir do export, grave `infra/main.bicep` (receita única, os dois ambientes) e os arquivos de nomes
por ambiente, copiando os modelos:
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/hml.bicepparam` → `infra/hml.bicepparam` — nomes que **já existem** na homologação
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/prd.bicepparam` → `infra/prd.bicepparam` (modelo `templates/azure-prd/prd.bicepparam`) — nomes de produção

Na limpeza do `main.bicep`:
- Tudo que **muda entre ambientes** vira `param`: no mínimo `nomeWebApp`, `nomePlano`, `subnetId` (os
  nomes dos modelos). O export cria parâmetros com nomes longos (`sites_mss_miti_ai_..._name`) —
  renomeie pros curtos.
- **Remova** valores de senha, chaves e connection strings que vieram no export; mantenha o **nome** da
  App Setting se ajudar, com o valor preenchido à parte.
- **Remova** IP fixo, id de recurso e nome da homologação escritos direto na receita — viram `param` ou
  `resourceId(...)`.
- **Remova** propriedades só de leitura que o export copia (estado, datas, `hostNames` gerados) — se o
  `az bicep build -f infra/main.bicep` reclamar, é por aí.
- Confira como a homologação **puxa a imagem** do registro: se for por identidade gerenciada, a
  permissão no `mssaicontainerregistry` pro Web App de produção é ato do prestador (anote no passo 4).

Valide sem tocar no Azure:
```bash
az bicep build -f infra/main.bicep
```

## 3. Simular contra a homologação (prova que a receita é igual ao que funciona)

O owner roda (precisa do `az login` dele), ou você roda e cola a saída — `what-if` não muda nada:
```bash
az deployment group what-if --resource-group RG-MSSAI-DEV --parameters infra/hml.bicepparam
```
**O critério é "nada muda":** recursos em `NoChange` (ou `Ignore`). Cada `Modify`/`Create`/`Delete` é
algo que a receita descreve diferente da homologação → volte ao passo 2 e ajuste. Propriedade que o
Azure preenche sozinho pode aparecer como mudança mesmo sem diferença real: mostre cada uma ao owner e
deixe **ele** decidir se é ruído. Só avance com o owner dizendo que o resultado está limpo.

## 4. Pipeline de produção com botão de aprovação

1. Copie `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/azure-pipelines-prd.yml` (modelo
   `templates/azure-prd/azure-pipelines-prd.yml`) → `azure-pipelines-infra-prd.yml` na raiz. Dois estágios:
   **Simular** (`what-if` contra `RG-MSSAI-PRD`, não muda nada) → **Criar** (`az deployment group create`
   em `RG-MSSAI-PRD`, **parado no botão** do environment `producao`). Roda à mão, não por push.
2. Entregue ao owner, em passos numerados, o que é dele no Azure DevOps:
   - **Pipelines → Environments → New environment** `producao` → **Approvals and checks** →
     **Approvals** → cadastrar quem aprova. **Antes da 1ª execução** — sem aprovador, o estágio Criar
     roda sem parar.
   - **Pipelines → New pipeline** apontando pro `azure-pipelines-infra-prd.yml`.
3. Entregue ao owner o pedido pro **prestador** (uma vez só): a conexão do pipeline
   (`azureServiceConnection` de `docs/AMBIENTE.md` §5) precisa poder **criar** recursos em
   `RG-MSSAI-PRD` (hoje ela só troca a imagem e reinicia o Web App), mais o que o passo 2 anotou
   (permissão de puxar imagem, subnet de produção liberada).
4. **Como aprovar:** abrir o log do estágio **Simular**, ler a lista do `what-if` (só `Create` na 1ª vez)
   e só então **Approve**. Depois que o Web App existir, o pipeline de código que já existe (branch
   `main`) segue trocando a imagem como hoje.

Commit dos arquivos (`infra/main.bicep`, `infra/hml.bicepparam`, `infra/prd.bicepparam`,
`azure-pipelines-infra-prd.yml`, `.gitignore`) na branch da feature, stage nominal. **Push em `main` é do
owner** (o hook nega) — rode `/mss-spec:release` e peça.
