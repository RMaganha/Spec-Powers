---
description: Cria os ambientes Azure do projeto em 6 etapas — a homologação (se ainda não existe) e a produção espelho dela — por uma receita Bicep + todas as variáveis de ambiente (senha vira *****), simuladas e aplicadas pelo pipeline, produção com botão de aprovação
argument-hint: ""
disable-model-invocation: true
---

Você vai criar os ambientes Azure do projeto sem ninguém montar nada à mão a partir de documentação: a
**homologação**, se ainda não existe, e a **produção**, espelho da homologação que funciona. Ferramenta:
**Bicep** (nativo do Azure), a partir da receita-base do kit (`templates/azure-ambiente/main.bicep`, tirada
do MSS-UTILS, em produção desde 2026-10-20). Fatos fixos de homologação e produção (grupos, plano, rede,
DNS, registro, permissões já feitas): `docs/AMBIENTE.md` §5. Spec do kit: `docs/specs/azure-ambiente.md`.

## Como conduzir a conversa (regra — vale em TODA mensagem)

O owner não é especialista em Azure e acompanha pelo chat. Caso F-038: sem mapa, ele se perdeu.

1. **Na 1ª mensagem**, mostre a tabela do caminho inteiro (abaixo), o que já está definido em até 2
   linhas **sem a fonte** (arquivo e linha só se o owner perguntar) e a pergunta da etapa 1 (a
   homologação já existe). **Peça o export uma vez só**, e só se a homologação existe.
2. **Toda mensagem termina com o mesmo bloco**, nesta forma:
   **Etapa X de 6 — <nome da etapa>**
   **O que preciso de você agora:** <UMA coisa, em passos numerados> — ou "nada, sigo sozinho".
3. **Um pedido por vez.** Nunca dois pedidos abertos ao mesmo tempo; nunca "depois faço isso ou aquilo".
4. **Uma aprovação por etapa:** liste todos os arquivos que a etapa vai gravar, 1 linha cada (o que é,
   em palavras simples), e peça **um** OK pra lista inteira. Nada de pedir arquivo por arquivo.
5. **Sem detalhe interno.** Teste vira uma linha — "proteção: N verdes" —, sem descrever o que cada teste
   confere. Nome técnico só o que o owner vai digitar ou ver na tela.
6. Passo que o owner executa: **numerado, título em negrito**, dizendo **onde** (portal, Azure DevOps, chat).
7. **Mensagem curta, sem linguagem técnica:** só o que mudou desde a última mensagem (até 3 linhas) +
   o bloco final. Nada de explicar o que não foi perguntado, de premissa que o owner não precisa decidir,
   nem de assunto que não é do desenvolvedor (capacidade do plano, rede, permissões — é da infra).
8. **Antes de enviar a branch, avise em uma linha:** "Vou enviar a branch `feature/azure-ambiente` pro Azure
   DevOps, pra o pipeline enxergar os arquivos novos. Isso não publica nada na homologação nem em
   produção. Vai aparecer um pedido de aprovação; aprove." Só depois envie.
9. **Valor que falta tem um nome só:** "falta preencher" (e, em produção, `*****`). Nunca `?` num valor,
   nunca trocar o símbolo no meio da conversa.
10. **Valor pra trocar num comando ou texto:** diga de onde tirar, clique a clique, com um exemplo de
    como fica preenchido.

| Etapa | O que é | Quem faz | Onde |
|---|---|---|---|
| 1 | Ponto de partida: a homologação já existe? Se sim, baixar a receita dela | owner | chat + portal do Azure |
| 2 | Montar os arquivos (receita, nomes por ambiente, variáveis, pipeline) | assistente — um OK do owner | este projeto |
| 3 | Criar a homologação (se não existe) ou simular contra ela | owner clica **Run pipeline** (hml) e cola o log | Azure DevOps |
| 4 | Revisar as variáveis de ambiente, até a simulação dar "nada muda" | os dois | chat + Azure DevOps |
| 5 | Preparar produção: aprovadores e pedido ao prestador | owner | Azure DevOps + chamado |
| 6 | Rodar em produção e aprovar | owner clica **Run pipeline** (prd) e **Approve** | Azure DevOps |

## Limites (nunca violar)

- **Nada roda na máquina do owner contra o Azure** — nem Azure CLI, nem login, nem simulação local. Tudo
  que fala com o Azure roda **no pipeline** (caso F-036).
- **Você nunca aplica a receita.** `az deployment group create` (e qualquer `az deployment … create`) é
  negado pelo hook `git_publicacao.py`: quem cria em produção é o **pipeline**, depois da aprovação do owner.
- **Variáveis de ambiente vão TODAS** — senha/chave vai como `*****` — mas **fora do Bicep** (etapa 2).
- **Fora da receita:** liberação de rede (a receita só **aponta** pra subnet já liberada) e recurso
  **compartilhado** entre projetos (plano, VNet, registro `mssaicontainerregistry`): já existe, só é referenciado.
- **Dúvida se algo existe ou vale em produção? Não conclua pelo documento de outro projeto** — peça ao
  owner pra conferir no portal (caso F-037).

## Antes da 1ª mensagem: ler o projeto (sozinho, sem perguntar)

Abra o pipeline de código que existe (`azure-pipelines*.yml`) e a documentação de deploy: nome do Web App
de homologação, imagem, plano, subnet, como a imagem é puxada do registro, comando de inicialização.
**Plano, grupo do plano, VNet/subnet e DNS de produção já estão mapeados** em `docs/AMBIENTE.md` §5 — use
de lá com a fonte, **não pergunte**. O projeto é anterior e o `docs/AMBIENTE.md` dele não tem essas
linhas? Leia do `${CLAUDE_PLUGIN_ROOT}/templates/AMBIENTE.md`.

**Pipeline de código de produção:** procure um pipeline com `trigger` na `main` que atualiza o Web App de
produção. **Não existe → é pendência**, dita ao owner exatamente assim: "Hoje, publicar na `main` ainda
não atualiza produção. Criar isso é tarefa à parte." (Como fazer — duplicar o pipeline de homologação
trocando nome da imagem, do Web App e do grupo — só quando ele pedir essa tarefa.) Produção sobe mesmo
assim: na 1ª criação ela usa a imagem da homologação (etapa 2).

## Etapa 1 de 6 — Ponto de partida

Pergunta ao owner (na 1ª mensagem, junto da tabela): **"A homologação deste projeto já existe no Azure
(`mss-miti-ai-<projeto>-dev-br`)?"**
- **Não existe** → nada a baixar: a receita sai da receita-base do kit e o pipeline cria a homologação na
  etapa 3. Siga pra etapa 2.
- **Já existe** → o export dela vira conferência da receita. Pedido ao owner, na mensagem seguinte:

1. **Abrir o grupo de recursos:** Portal do Azure → **Grupos de recursos** → `RG-MSSAI-DEV`.
2. **Marcar só o Web App deste projeto:** a caixinha de `mss-miti-ai-<projeto>-dev-br` (não o plano, a
   VNet nem o registro de imagens).
3. **Abrir a exportação:** no botão **⋯** (à direita de **Exportar para CSV**) → **Exportar modelo** →
   **Exportar como Bicep**.
4. **Baixar:** na tela que abre, **Download**. Se aparecer um aviso amarelo (`ExportTemplateCompletedWithErrors`),
   é esperado — siga.
5. **Colar aqui no chat** o caminho do arquivo baixado (ex.: `C:\Users\<você>\Downloads\main.bicep`).

Enquanto ele baixa, a etapa 2 já pode ser preparada — mas sem pedir nada novo a ele.

## Etapa 2 de 6 — Montar os arquivos

Liste ao owner **todos** os arquivos de uma vez e peça **um** OK. A receita parte **sempre** da receita-base
(`${CLAUDE_PLUGIN_ROOT}/templates/azure-ambiente/main.bicep` → `infra/main.bicep`), preenchendo nos dois
`.bicepparam`: `comandoInicial` (o mesmo do pipeline de código ou do `Dockerfile`), `caminhoSaude` (nunca
`/`), `ipsPermitidos` (os IPs de acesso, ex.: o escritório — copie de um projeto que já tem, só leitura, ou
pergunte uma vez ao owner) e, no pipeline, a variável `porta`. Com homologação existente, o export é
**conferência**: o que o projeto tem a mais entra na receita, seguindo a tabela abaixo.

| Arquivo | O que é |
|---|---|
| `.gitignore` | ganha `/infra/export-*` — o export traz valores da homologação e nunca entra no git |
| `.dockerignore` | ganha `/infra/` e `/azure-pipelines*.yml` — o `Dockerfile` costuma copiar a pasta inteira (`COPY . .`) e a receita não deve ir pra dentro da imagem do sistema |
| `infra/main.bicep` | a receita, a partir da receita-base do kit (e conferida com o export, se a homologação existe) |
| `infra/hml.bicepparam` / `infra/prd.bicepparam` | os nomes de cada ambiente |
| `infra/app_settings.py` | leva as variáveis de ambiente |
| `azure-pipelines-infra.yml` | o pipeline com a escolha hml/prd e o botão |

Cópias dos modelos (troque `<projeto>` pelos nomes reais):
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-ambiente/hml.bicepparam` → `infra/hml.bicepparam`
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-ambiente/prd.bicepparam` → `infra/prd.bicepparam` (modelo `templates/azure-ambiente/prd.bicepparam`)
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-ambiente/app_settings.py` → `infra/app_settings.py` (modelo `templates/azure-ambiente/app_settings.py`)
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-ambiente/azure-pipelines-infra.yml` → `azure-pipelines-infra.yml` (modelo `templates/azure-ambiente/azure-pipelines-infra.yml`)

Regras da receita `infra/main.bicep` (montada do export):
- Tudo que **muda entre ambientes** vira `param`: `nomeWebApp`, `nomePlano`, `grupoPlano`, `subnetId` e
  **`imagem`**. Renomeie os parâmetros longos do export (`sites_mss_miti_ai_..._name`) pros curtos.
- O plano é apontado **pelo grupo dele**, nunca suposto no mesmo grupo do Web App:
  `serverFarmId: resourceId(grupoPlano, 'Microsoft.Web/serverfarms', nomePlano)`.
- **Imagem nunca fixa** (`siteConfig.linuxFxVersion: imagem`): o pipeline passa em `IMAGEM` a que está
  rodando no Web App; **na 1ª criação de produção**, a que está rodando na **homologação** (já testada,
  mesmo registro) — produção nasce espelho e sobe sem esperar o pipeline de código de produção. Sem
  imagem, o pipeline falha em vez de criar.
- **Tire TODAS as variáveis de ambiente** (`siteConfig.appSettings` e qualquer recurso
  `config 'appsettings'`): no Bicep, `appSettings` **substitui** a coleção inteira — uma 2ª execução
  apagaria a senha que o prestador colocou à mão. Quem leva as variáveis é o `infra/app_settings.py`.
- **Sempre** aparece no export (mesmo com o aviso `ExportTemplateCompletedWithErrors`), e não pode ir pra
  produção como veio:

  | No export | O que fazer |
  |---|---|
  | `hostNameSslStates`, recurso `hostNameBindings`, `customDomainVerificationId` | **remover**: é o endereço gerado do Web App de homologação (`…-<código>.azurewebsites.net`); produção ganha o dela sozinha |
  | recurso `virtualNetworkConnections` e `vnetName` | **remover**: o nome carrega um código da rede de homologação; a ligação com a rede fica só em `virtualNetworkSubnetId: subnetId` — **nunca `networkConfig`**, que exige a permissão de alterar a subnet (erro real no MSS-UTILS) |
  | `location` nas partes internas do Web App (`basicPublishingCredentialsPolicies`, `config`) | deixe essas partes **sem `location`** — o Bicep avisa `BCP187` |
  | `vnetRouteAllEnabled` (dentro do `config 'web'`) | **remover**; quem manda é `outboundVnetRouting` com `allTraffic: false` — "rotear todo o tráfego" **desligado**, regra da casa (com ele ligado, a imagem e as chamadas externas passam pela rede e o Web App cai) |
  | `ipSecurityRestrictions` (regras de acesso) | **manter**; a regra que aponta pra subnet de homologação passa a usar `subnetId`. IPs fixos das regras (escritório) ficam como estão |
  | `publishingUsername` | **remover** (vem `REDACTED`) |
  | `linuxFxVersion` (aparece duas vezes: no site e no `config 'web'`) | as duas usam `imagem` |
  | ids e nomes da homologação escritos direto | viram `param` |

- **Confira a receita contra o roteiro de deploy de homologação do projeto** (ex.: `docs/deploy-azure-dev.md`):
  comando de inicialização, verificação de saúde, rede, "rotear todo o tráfego", HTTPS e TLS, regras de
  acesso. O aviso amarelo do export não diz o que ficou de fora — o roteiro diz. Item do roteiro que não
  está na receita (fora as variáveis, que vão pelo `app_settings.py`) **entra à mão** na receita, e vai
  na lista da aprovação da etapa como "completado do roteiro".

Pode escrever um teste de proteção no projeto (nomes batem, sem variável nem imagem fixa na receita);
ao owner, só "proteção: N verdes". Depois do OK e dos arquivos gravados: commit na branch da feature e
envio da branch, com o aviso da regra 8 antes (o hook pede a aprovação do owner).

## Etapa 3 de 6 — Criar a homologação (se não existe) ou simular contra ela

**Homologação nova — antes de rodar:** confira na seção 5 do `docs/AMBIENTE.md` se as permissões na rede
de **homologação** (`SNET-WEB-AI-DEVQA`) estão registradas como feitas. Não estão → entregue ao owner a
seção 4 do `templates/azure-ambiente/permissoes-infra.md`, com o código da identidade registrado na mesma
seção 5. Com a homologação nova, a opção **hml** cria o Web App com uma imagem provisória e as variáveis de
plataforma (registro, porta, fuso, DNS); depois o pedido ao owner é, numa mensagem: criar no portal as
variáveis **do sistema** (as do `.env.example` do projeto) e fazer o 1º push na `dev`, que troca a imagem
provisória pela real. Rodar **hml** de novo → a homologação já existe → vira simulação, como abaixo.

Antes do pedido, diga ao owner em uma linha cada:
- é um **pipeline novo**, o **terceiro**, separado do de homologação (`<PROJETO>-DEV`) e do futuro de
  produção do código (`<PROJETO>-PROD`): chama `<PROJETO>-INFRA` e só roda quando ele clica;
- **não precisa de nenhum comando git**: a branch já foi enviada na etapa 2;
- a 1ª simulação **vai dar erro de propósito**: ela para nas variáveis e imprime a lista de todas as da
  homologação — é o que a etapa 4 usa.

Pedido ao owner, numa mensagem:
1. **Criar o pipeline** (Azure DevOps): **Pipelines** → **New pipeline** → **Azure Repos Git** → este
   repositório → **Existing Azure Pipelines YAML file** → branch `feature/azure-ambiente` →
   `/azure-pipelines-infra.yml` → **Save** (não **Run** ainda).
2. **Dar o nome:** **Pipelines** → na linha do pipeline novo (vem com o nome do repositório, ex.:
   `MSS-UTILS (1)`) → **⋯** → **Rename/move** → `<PROJETO>-INFRA` → **Save**.
3. **Rodar a simulação:** **Pipelines** → `<PROJETO>-INFRA` → **Run pipeline** → em **Select pipeline
   version by branch/tag**, `feature/azure-ambiente` (os arquivos estão só nela; vão pra `main` no fecho) → em
   **Parameters → Ambiente**, **hml** → **Next: Resources** → não mexer → **Run**.
4. **Se aparecer "Permission needed":** é a permissão de uma vez só pra usar a conexão com o Azure →
   **View** → **Permit** → **Permit**.
5. **Copiar o log:** estágio **Simular** → item **Receita + variáveis: o que mudaria** → **View raw log** →
   **Ctrl+A** → **Ctrl+C** → colar aqui no chat.

Guarde do log a linha `Identidade do pipeline (object id, …): <código>` — é o código da etapa 5.

## Etapa 4 de 6 — Revisar as variáveis de ambiente

Grave `infra/app-settings.json` (versionado, **sem valor nenhum**) a partir da lista impressa, e mostre ao
owner **numa tabela só** — nome e o que acontece em produção — pra ele corrigir de uma vez:

| Marca | O que o pipeline faz em produção |
|---|---|
| `"copiar"` | copia o valor da homologação. A `DOCKER_REGISTRY_SERVER_PASSWORD` o Azure não entrega na leitura: o pipeline lê direto do registro de imagens. Valor que vier vazio não é gravado: vira "falta preencher" |
| `"senha"` | grava `*****` **só se ainda não existe** em produção; se já existe, não mexe |
| `{"prd": "<valor>"}` | grava o valor de produção escrito ali (URL, servidor, ambiente — nunca senha). Serve também pra variável que **só existe em produção**: acrescente sempre `"WEBSITE_DNS_ALT_SERVER": {"prd": "168.63.129.16"}` (`docs/AMBIENTE.md` §5) |

Iguais nos dois ambientes, sempre `"copiar"` (`docs/AMBIENTE.md` §5): `WEBSITE_DNS_SERVER` (`10.170.210.2`)
e as `DOCKER_REGISTRY_SERVER_*`. Liga/desliga (`…_ATIVO`, `…_ATIVA`) é `"copiar"`, mesmo com TOKEN no nome.
Endereço de produção que o owner não sabe: marque `"senha"` e diga "falta preencher" — o mesmo nome da
regra 9, do começo ao fim.

Com o OK do owner na tabela: commit, aviso da regra 8, envio da branch. Depois o pedido é **um**, dizendo
**o que mudou** desde a última execução (ex.: "a lista de variáveis foi enviada") e o que esperar:
**Run pipeline** → branch `feature/azure-ambiente` → **hml** → **Next: Resources** → **Run** → colar o log do
item **Receita + variáveis: o que mudaria**. Leia com ele:
- **Receita:** critério **"nada muda"** — recursos em `NoChange` (ou `Ignore`). Cada `Modify`/`Create`/
  `Delete` é diferença entre a receita e a homologação → ajuste o `main.bicep` e repita. Propriedade que
  o Azure preenche sozinho pode aparecer como mudança sem diferença real: mostre e deixe **o owner** decidir.
- **Variáveis:** nenhuma faltando. Variável nova na homologação que não esteja no arquivo **trava** o
  pipeline com o nome dela — nenhuma fica pra trás.

Só avance quando o owner disser que o resultado está limpo.

## Etapa 5 de 6 — Preparar produção (uma vez só, pra todos os projetos)

**Primeiro confira** a seção 5 do `docs/AMBIENTE.md` (ou do `${CLAUDE_PLUGIN_ROOT}/templates/AMBIENTE.md`):
se registra as **permissões da conexão do pipeline em produção** e o ambiente `producao` com aprovadores
como já feitos, diga "já está pronto desde <data>, seguimos" e vá pra etapa 6.

Se não estão feitos, entregue ao owner **o chamado pronto**: copie o `templates/azure-ambiente/permissoes-infra.md`
(`${CLAUDE_PLUGIN_ROOT}/templates/azure-ambiente/permissoes-infra.md`), trocando `<PROJETO>` pelo nome real.
Os comandos já vêm com o código da conexão (`ecab5b96-…`); confira com a linha `Identidade do pipeline` do
log da etapa 3 — se for outro código, troque pelo do log. Nunca peça o código pelo
"Manage App registration" — no MSS-UTILS ele levou as permissões pra outra identidade (caso F-039).
Pedido ao owner: mandar esse texto pra infra e avisar aqui quando estiver feito.

Se o owner tentar cadastrar os aprovadores e aparecer `You do not have permissions to manage checks`: só
um administrador do Azure DevOps faz — é a seção 2 do mesmo chamado. **Não rode prd** até o ambiente
`producao` mostrar **Approvals** com os nomes em **Approvals and checks**: sem aprovador, o estágio Criar
roda sem parar. O nome do ambiente é `producao`, **minúsculo e sem acento**, igual ao pipeline.

## Etapa 6 de 6 — Rodar em produção e aprovar

Pedido ao owner:
1. **Rodar:** **Pipelines** → `<PROJETO>-INFRA` → **Run pipeline** → branch `feature/azure-ambiente` → **prd** →
   **Next: Resources** → **Run**. Se aparecer "Permission needed" (agora pro ambiente `producao`) →
   **View** → **Permit**.
2. **Copiar o log da simulação:** estágio **Simular** → item **Receita + variáveis: o que mudaria** →
   **View raw log** → colar aqui. Você confere a lista do `what-if` (só `Create` na 1ª vez) e diz em
   palavras simples o que vai ser criado, qual imagem e o que vai faltar preencher.
3. **Pedir a aprovação** — texto pronto pro aprovador (o owner só copia):
   > Preciso da sua aprovação para criar o Web App de produção do `<projeto>` (`mss-miti-ai-<projeto>-prod`).
   > A simulação já foi conferida. Por favor:
   > 1. Abra: `<endereço do pipeline <PROJETO>-INFRA no Azure DevOps>`
   > 2. Clique na execução `<número>` (branch `feature/azure-ambiente`).
   > 3. No aviso no topo, ou no estágio "Criar em produção", clique em **Review**.
   > 4. Clique em **Approve**.
4. **Depois de aprovado:** estágio **Criar em produção** → item **Aplicar a receita e as variáveis em
   RG-MSSAI-PRD** → **View raw log** → colar aqui.

Se o Criar falhar com `AuthorizationFailed`/`LinkedAuthorizationFailed`: nada é criado. Leia no erro o
`object id` e a permissão que falta — o Azure diz os dois. Object id diferente do da linha `Identidade do
pipeline` = a permissão foi pra identidade errada; permissão que falta e que não está no chamado = mostre
ao owner, sem chute (caso F-039).

**Depois de criado, conferir com o owner** (portal → Web App de produção):
- **Visão geral** → **Verificação de Integridade** subindo de 0%; endereço `…/health` responde
  `{"status":"ok"}` (a raiz `/` dar `Not Found` é normal);
- **Fluxo de log** → aparece a subida do sistema. Vazio = a imagem não foi baixada: confira a
  `DOCKER_REGISTRY_SERVER_PASSWORD`;
- **não** clicar no aviso laranja do padrão sidecar.

**De onde vem cada valor que falta preencher** (Web App de produção → **Variáveis de ambiente** → clicar no
nome → colar no **Valor** → **OK** → no fim, **Aplicar**):

| Variável | De onde tirar |
|---|---|
| `DOCKER_REGISTRY_SERVER_PASSWORD` (se ainda vazia) | Portal → **Registros de contêiner** → `mssaicontainerregistry` → **Chaves de acesso** → **password**. Nunca clicar em **Regenerar**: troca a senha e derruba todos os Web Apps que usam o registro |
| chaves de IA, tokens do próprio sistema | Web App de homologação → **Variáveis de ambiente** → **Mostrar valores** (ou o `.env` do projeto) |
| conexão de banco, credencial de sistema externo, endereços de produção | quem cuida daquele sistema — o valor da homologação aponta pro ambiente de teste |

Fecho: commit dos arquivos na branch da feature, stage nominal. **Push em `main` é do owner** (o hook nega)
— rode `/mss-spec:release` e entregue o passo a passo.
