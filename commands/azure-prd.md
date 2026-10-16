---
description: Leva a homologação Azure que já funciona pra produção, em 6 etapas — receita Bicep exportada da homologação + todas as variáveis de ambiente (senha vira *****), simuladas e aplicadas pelo pipeline com botão de aprovação
argument-hint: ""
disable-model-invocation: true
---

Você vai levar a **homologação que já funciona** pra **produção**, sem ninguém montar produção à mão a
partir de documentação. Ferramenta: **Bicep** (nativo do Azure). Fatos fixos de homologação e produção
(grupos, plano, rede, DNS, registro): `docs/AMBIENTE.md` §5. Spec do kit: `docs/specs/azure-prd.md`.

## Como conduzir a conversa (regra — vale em TODA mensagem)

O owner não é especialista em Azure e acompanha pelo chat. Caso F-038: sem mapa, ele se perdeu.

1. **Na 1ª mensagem**, mostre a tabela do caminho inteiro (abaixo), o que já está definido em até 2
   linhas **sem a fonte** (arquivo e linha só se o owner perguntar) e o pedido da etapa 1. **Peça o
   export uma vez só**, nessa mensagem.
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

| Etapa | O que é | Quem faz | Onde |
|---|---|---|---|
| 1 | Baixar a receita da homologação | owner | portal do Azure |
| 2 | Montar os arquivos (receita, nomes por ambiente, variáveis, pipeline) | assistente — um OK do owner | este projeto |
| 3 | Simular contra a homologação | owner clica **Run pipeline** (hml) e cola o log | Azure DevOps |
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

## Etapa 1 de 6 — Baixar a receita da homologação

Pedido ao owner (na 1ª mensagem, junto da tabela):
1. **Abrir o grupo de recursos:** Portal do Azure → **Grupos de recursos** → `RG-MSSAI-DEV`.
2. **Marcar só o Web App deste projeto:** a caixinha de `mss-miti-ai-<projeto>-dev-br` (não o plano, a
   VNet nem o registro de imagens).
3. **Baixar:** **Exportar modelo** → aba **Bicep** → **Baixar**.
4. **Colar aqui no chat** o caminho do arquivo baixado (ex.: `C:\Users\<você>\Downloads\ExportedTemplate.zip`).

Enquanto ele baixa, a etapa 2 já pode ser preparada — mas sem pedir nada novo a ele.

## Etapa 2 de 6 — Montar os arquivos

Com o export em mãos, liste ao owner **todos** os arquivos de uma vez e peça **um** OK:

| Arquivo | O que é |
|---|---|
| `.gitignore` | ganha `/infra/export-*` — o export traz valores da homologação e nunca entra no git |
| `.dockerignore` | ganha `/infra/` e `/azure-pipelines*.yml` — o `Dockerfile` costuma copiar a pasta inteira (`COPY . .`) e a receita não deve ir pra dentro da imagem do sistema |
| `infra/main.bicep` | a receita, montada do export |
| `infra/hml.bicepparam` / `infra/prd.bicepparam` | os nomes de cada ambiente |
| `infra/app_settings.py` | leva as variáveis de ambiente |
| `azure-pipelines-infra-prd.yml` | o pipeline com a escolha hml/prd e o botão |

Cópias dos modelos (troque `<projeto>` pelos nomes reais):
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/hml.bicepparam` → `infra/hml.bicepparam`
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/prd.bicepparam` → `infra/prd.bicepparam` (modelo `templates/azure-prd/prd.bicepparam`)
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/app_settings.py` → `infra/app_settings.py` (modelo `templates/azure-prd/app_settings.py`)
- `${CLAUDE_PLUGIN_ROOT}/templates/azure-prd/azure-pipelines-prd.yml` → `azure-pipelines-infra-prd.yml` (modelo `templates/azure-prd/azure-pipelines-prd.yml`)

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
- **Remova** IP fixo, id e nome da homologação escritos direto (viram `param`) e propriedades só de
  leitura que o export copia (estado, datas, `hostNames` gerados).

Pode escrever um teste de proteção no projeto (nomes batem, sem variável nem imagem fixa na receita);
ao owner, só "proteção: N verdes". Depois do OK e dos arquivos gravados: commit na branch da feature e
push da branch (o hook pede a aprovação do owner — esse clique é o pedido da próxima mensagem).

## Etapa 3 de 6 — Simular contra a homologação

Pedido ao owner, em uma mensagem:
1. **Criar o pipeline:** Azure DevOps → **Pipelines** → **New pipeline** → **Azure Repos Git** → este
   repositório → **Existing Azure Pipelines YAML file** → branch da feature → `/azure-pipelines-infra-prd.yml`
   → **Save** (não **Run** ainda).
2. **Rodar a simulação:** abrir o pipeline → **Run pipeline** → branch da feature → ambiente **hml** → **Run**.
3. **Colar aqui** o log do estágio **Simular**.

A 1ª simulação **para nas variáveis** de propósito e imprime a lista de todas as da homologação — é o
insumo da etapa 4. Diga isso ao owner antes, pra o "erro" não assustar. **Erro de permissão**
(`AuthorizationFailed`) = a conexão do pipeline não pode simular no grupo de recursos — entra no pedido
ao prestador da etapa 5.

## Etapa 4 de 6 — Revisar as variáveis de ambiente

Grave `infra/app-settings.json` (versionado, **sem valor nenhum**) a partir da lista impressa, e mostre
ao owner **numa tabela só** — nome e marca proposta — pra ele corrigir de uma vez:

| Marca | O que o pipeline faz em produção |
|---|---|
| `"copiar"` | copia o valor da homologação |
| `"senha"` | grava `*****` **só se ainda não existe** em produção; se já existe, não mexe |
| `{"prd": "<valor>"}` | grava o valor de produção escrito ali (URL, servidor, ambiente — nunca senha). Serve também pra variável que **só existe em produção**: acrescente sempre `"WEBSITE_DNS_ALT_SERVER": {"prd": "168.63.129.16"}` (`docs/AMBIENTE.md` §5) |

Iguais nos dois ambientes, sempre `"copiar"` (`docs/AMBIENTE.md` §5): `WEBSITE_DNS_SERVER` (`10.170.210.2`)
e as `DOCKER_REGISTRY_SERVER_*` — inclusive a senha: o registro é compartilhado, e com `*****` produção não
sobe até o prestador preencher.

Com o OK do owner na tabela: commit, push da branch, e o pedido é **um**: **Run pipeline** → **hml** →
colar o log. Leia com ele:
- **Receita:** critério **"nada muda"** — recursos em `NoChange` (ou `Ignore`). Cada `Modify`/`Create`/
  `Delete` é diferença entre a receita e a homologação → ajuste o `main.bicep` e repita. Propriedade que
  o Azure preenche sozinho pode aparecer como mudança sem diferença real: mostre e deixe **o owner** decidir.
- **Variáveis:** nenhuma faltando. Variável nova na homologação que não esteja no arquivo **trava** o
  pipeline com o nome dela — nenhuma fica pra trás.

Só avance quando o owner disser que o resultado está limpo.

## Etapa 5 de 6 — Preparar produção

Pedido ao owner, numa mensagem só (é uma lista de tarefas dele, uma vez por projeto):
1. **Criar o ambiente com o botão:** Azure DevOps → **Pipelines** → **Environments** → **New environment**
   → nome `producao` → **Resource: None** → **Create**.
2. **Cadastrar quem aprova:** dentro de `producao`, menu **⋮** → **Approvals and checks** → **+** →
   **Approvals** → **Next** → em **Approvers**, nome ou e-mail de cada pessoa → **Create**. Se quem dispara
   também aprova, marque em **Advanced** a opção que permite aprovar a própria execução. Sem aprovador, o
   estágio Criar roda **sem parar**.
3. **Pedir ao prestador:** a conexão do pipeline (`azureServiceConnection` de `docs/AMBIENTE.md` §5) precisa
   poder **criar** recursos em `RG-MSSAI-PRD` (hoje ela só troca a imagem e reinicia o Web App).
4. **Me avisar** quando os três estiverem feitos.

## Etapa 6 de 6 — Rodar em produção e aprovar

Pedido ao owner:
1. **Rodar:** **Run pipeline** → ambiente **prd** → **Run**.
2. **Conferir antes de aprovar:** no log do estágio **Simular**, a lista do `what-if` (só `Create` na 1ª vez)
   e o plano das variáveis → **Review** → **Approve**.
3. **Colar aqui** o fim do log do estágio **Criar**.

O fim do log lista as variáveis que estão `*****` em produção — entregue ao owner como a lista exata pro
prestador preencher (Web App de produção → **Variáveis de ambiente**). Numa nova execução, essas senhas
**não** são sobrescritas.

Fecho: commit dos arquivos na branch da feature, stage nominal. **Push em `main` é do owner** (o hook nega)
— rode `/mss-spec:release` e entregue o passo a passo.
