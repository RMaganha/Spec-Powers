---
description: Leva a homologação Azure que já funciona pra produção — receita Bicep exportada da homologação + todas as variáveis de ambiente (senha vira *****), simuladas e aplicadas pelo pipeline com botão de aprovação
argument-hint: ""
disable-model-invocation: true
---

Você vai montar a **receita de produção** deste projeto a partir da **homologação que já funciona**, pra
que produção deixe de ser montada à mão a partir de documentação. Ferramenta: **Bicep** (nativo do
Azure, sem arquivo de estado pra guardar). Padrão de nomes e grupos de recursos em `docs/AMBIENTE.md` §5
(homologação `RG-MSSAI-DEV` · produção `RG-MSSAI-PRD`). Spec do kit: `docs/specs/azure-prd.md`.

**Limites (nunca violar):**
- **Nada roda na máquina do owner contra o Azure** — nem Azure CLI, nem login, nem simulação local. Tudo
  que fala com o Azure roda **no pipeline**, com a conexão dele; a parte do owner é clicar em
  **Run pipeline**, aprovar e colar o log (caso F-036).
- **Você nunca aplica a receita.** `az deployment group create` (e qualquer `az deployment … create`) é
  negado pelo hook `git_publicacao.py`: quem cria em produção é o **pipeline**, depois da aprovação do
  owner.
- **Variáveis de ambiente vão TODAS** — senha/chave vai como `*****` — mas **fora do Bicep** (passo 2).
- **Fora da receita:** liberação de rede (vnet/IP — segue com a infra; a receita só **aponta** pra subnet
  já liberada) e recurso **compartilhado** com outros projetos (plano usado por vários apps, vnet,
  registro de imagens `mssaicontainerregistry`): já existe, só é referenciado.
- Todo passo que o owner executa sai **numerado, com título em negrito** dizendo o que ele faz e onde
  (portal, Azure DevOps, chat) — sem jargão.
- Mostre o que vai gravar e **confirme antes de gravar** cada arquivo.

## 0. Ler o que o projeto já tem (você, sem perguntar o que está no repo)

Abra o pipeline de código que existe (`azure-pipelines*.yml`) e a documentação de deploy do projeto:
nome do Web App de homologação, nome da imagem, plano, subnet, como a imagem é puxada do registro.
Liste ao owner como **premissa com fonte** (`arquivo:linha`). **Plano, VNet/subnet e DNS de produção
já estão mapeados** em `docs/AMBIENTE.md` §5 (plano `mss-ai-asp-prod-br`, `VNET-MSSD-PRD` /
`SNET-WEB-AI-PRD`, `WEBSITE_DNS_ALT_SERVER=168.63.129.16` obrigatória) — use de lá com a fonte, **não
pergunte**. O projeto é anterior e o `docs/AMBIENTE.md` dele não tem essas linhas? Leia do
`${CLAUDE_PLUGIN_ROOT}/templates/AMBIENTE.md` — inclusive o **id completo da subnet de produção**
(`VNET-MSSD-PRD` no grupo `RG-MSSD-PRD`), que já vem preenchido no modelo `prd.bicepparam`.

**Pipeline de código de produção:** procure um pipeline com `trigger` na `main` que atualiza o Web App
de produção (padrão do `docs/AMBIENTE.md` §5). **Não existe → é pendência**, diga em uma linha: "o push
na `main` ainda não publica em produção; criar esse pipeline (duplicar o de homologação trocando
`imageName`, `webAppName` e `resourceGroup`) é tarefa à parte". Não suponha que existe.

## 1. Exportar a homologação (o owner, no portal)

Passos pro owner:
1. **Abrir o grupo de recursos da homologação:** Portal do Azure → **Grupos de recursos** → `RG-MSSAI-DEV`.
2. **Marcar só o Web App deste projeto** (`mss-miti-ai-<projeto>-dev-br`) — não marcar plano
   compartilhado, vnet nem o registro de imagens.
3. **Baixar a receita:** **Exportar modelo** → aba **Bicep** → **Baixar**.
4. **Salvar** em `infra/export-hml.bicep` (se vier `.zip`, ele te passa o caminho e você extrai).

Antes de ele salvar, acrescente `infra/export-*` ao `.gitignore` (o export traz valores da
homologação e nunca entra no git).

## 2. Montar os arquivos

A partir do export, grave `infra/main.bicep` (receita única, os dois ambientes) e copie os modelos:
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/hml.bicepparam` → `infra/hml.bicepparam` — nomes que **já existem** na homologação
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/prd.bicepparam` → `infra/prd.bicepparam` (modelo `templates/azure-prd/prd.bicepparam`) — nomes de produção
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/app_settings.py` → `infra/app_settings.py` (modelo `templates/azure-prd/app_settings.py`) — as variáveis de ambiente
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/azure-pipelines-prd.yml` → `azure-pipelines-infra-prd.yml` na raiz (modelo `templates/azure-prd/azure-pipelines-prd.yml`), trocando `<projeto>` nos nomes dos Web Apps

Na limpeza do `main.bicep`:
- Tudo que **muda entre ambientes** vira `param`: `nomeWebApp`, `nomePlano`, `subnetId` e **`imagem`**
  (vai em `siteConfig.linuxFxVersion`). O export cria parâmetros com nomes longos
  (`sites_mss_miti_ai_..._name`) — renomeie pros curtos.
- **Imagem nunca fixa:** ela muda a cada push. O pipeline lê a que está rodando no Web App e passa em
  `IMAGEM` (os `.bicepparam` usam `readEnvironmentVariable('IMAGEM')`, sem valor padrão); assim a
  simulação não acusa diferença à toa e uma nova execução nunca volta produção pra uma versão velha.
  **Na 1ª criação de produção** (o Web App de produção ainda não existe), o pipeline usa a imagem que
  está rodando na **homologação** — já testada, mesmo registro: produção nasce espelho e sobe sem esperar
  o pipeline de código de produção. Sem essa imagem, o pipeline falha em vez de criar.
- **Tire TODAS as variáveis de ambiente do `main.bicep`** (`siteConfig.appSettings` e qualquer recurso
  `config 'appsettings'`): no Bicep, `appSettings` **substitui** a coleção inteira — uma 2ª execução
  apagaria a senha que o prestador colocou à mão. Quem leva as variáveis é o `infra/app_settings.py`.
- **Remova** IP fixo, id de recurso e nome da homologação escritos direto na receita (viram `param` ou
  `resourceId(...)`) e propriedades só de leitura que o export copia (estado, datas, `hostNames` gerados).

**As variáveis de ambiente — `infra/app-settings.json`** (versionado, **sem valor nenhum**): lista
**todas** as variáveis da homologação, cada uma com uma marca:

| Marca | O que o pipeline faz em produção |
|---|---|
| `"copiar"` | copia o valor da homologação |
| `"senha"` | grava `*****` **só se ainda não existe** em produção; se já existe, não mexe |
| `{"prd": "<valor>"}` | grava o valor de produção escrito ali (URL, servidor, ambiente — nunca senha). Serve também pra variável que **só existe em produção**: acrescente sempre `"WEBSITE_DNS_ALT_SERVER": {"prd": "168.63.129.16"}` (`docs/AMBIENTE.md` §5) |

Iguais nos dois ambientes, sempre `"copiar"` (`docs/AMBIENTE.md` §5): `WEBSITE_DNS_SERVER` (`10.170.210.2`)
e as `DOCKER_REGISTRY_SERVER_*` — inclusive a senha: o registro é compartilhado, e com `*****` produção
não sobe até o prestador preencher. **Dúvida se uma variável existe ou vale em produção? Não conclua pelo
documento de outro projeto** — peça ao owner pra conferir no portal (Web App de produção → Variáveis de
ambiente) (caso F-037).

O arquivo nasce do passo 3: a 1ª simulação, sem ele, **para e imprime a proposta pronta** com os nomes
de todas as variáveis da homologação (senha marcada pelo nome). Você grava o arquivo a partir da
proposta e **revisa com o owner, uma a uma**, quais mudam em produção. Variável que aparecer depois na
homologação e não estiver no arquivo **trava** o pipeline com o nome dela — nenhuma fica pra trás.

## 3. Simular contra a homologação (prova que a receita é igual ao que funciona)

Commit na branch da feature e push da branch (o hook pede a aprovação do owner). Passos pro owner:
1. **Criar o pipeline no Azure DevOps:** **Pipelines** → **New pipeline** → **Azure Repos Git** → este
   repositório → **Existing Azure Pipelines YAML file** → branch da feature →
   `/azure-pipelines-infra-prd.yml` → **Save** (não **Run** ainda).
2. **Rodar a simulação:** abrir o pipeline → **Run pipeline** → branch da feature → ambiente **hml** → **Run**.
3. **Colar aqui** o log do estágio **Simular**.

Leia o log com o owner:
- **1ª vez:** falha nas variáveis com a proposta do `infra/app-settings.json` → grave o arquivo (passo 2),
  revise com o owner, commit, e ele roda **hml** de novo.
- **Receita:** o critério é **"nada muda"** — recursos em `NoChange` (ou `Ignore`). Cada
  `Modify`/`Create`/`Delete` é algo que a receita descreve diferente da homologação → ajuste o
  `main.bicep`. Propriedade que o Azure preenche sozinho pode aparecer como mudança sem diferença real:
  mostre cada uma e deixe **o owner** decidir se é ruído.
- **Erro de permissão** (`AuthorizationFailed`): a conexão do pipeline não pode simular no grupo de
  recursos — entra no pedido ao prestador do passo 4.

Só avance com o owner dizendo que o resultado está limpo.

## 4. Produção (o owner, com o botão de aprovação)

Passos pro owner, **antes da 1ª execução em prd**:
1. **Criar o ambiente com o botão:** Azure DevOps → **Pipelines** → **Environments** → **New environment**
   → nome `producao` → **Resource: None** → **Create**.
2. **Cadastrar quem aprova:** dentro de `producao`, menu **⋮** → **Approvals and checks** → **+** →
   **Approvals** → **Next** → em **Approvers**, nome ou e-mail de cada pessoa (usuária da organização no
   DevOps) → **Create**. Se quem dispara também aprova, marque em **Advanced** a opção que permite
   aprovar a própria execução. Sem aprovador, o estágio Criar roda **sem parar**.
3. **Pedir ao prestador (uma vez só):** a conexão do pipeline (`azureServiceConnection` de
   `docs/AMBIENTE.md` §5) precisa poder **criar** recursos em `RG-MSSAI-PRD` (hoje ela só troca a
   imagem e reinicia o Web App), mais a subnet de produção liberada e o que o passo 0 anotou.

Depois:
4. **Rodar em produção:** **Run pipeline** → ambiente **prd** → **Run**.
5. **Conferir antes de aprovar:** no log do estágio **Simular**, a lista do `what-if` (só `Create` na
   1ª vez) e o plano das variáveis → **Review** → **Approve**.
6. **Preencher as senhas:** o fim do log lista as variáveis que estão `*****` em produção — é a lista
   exata pro prestador preencher no Web App (Configuração → Variáveis de ambiente). Numa nova execução,
   essas senhas **não** são sobrescritas.

Commit dos arquivos (`infra/main.bicep`, `infra/hml.bicepparam`, `infra/prd.bicepparam`,
`infra/app_settings.py`, `infra/app-settings.json`, `azure-pipelines-infra-prd.yml`, `.gitignore`) na
branch da feature, stage nominal. **Push em `main` é do owner** (o hook nega) — rode `/mss-spec:release`
e entregue o passo a passo.
