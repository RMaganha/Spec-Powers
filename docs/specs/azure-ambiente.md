# Ambientes Azure — homologação e produção pela mesma receita (`/mss-spec:azure-ambiente`)

## Estado atual
Desde a 0.41.0 o comando chama **`/mss-spec:azure-ambiente`** (era `azure-prd`) e cria, nos projetos, a
branch **`feature/azure-ambiente`**. A receita parte sempre da receita-base do kit
(`templates/azure-ambiente/main.bicep`, tirada do MSS-UTILS; parâmetros `comandoInicial`, `caminhoSaude`,
`ipsPermitidos`); com homologação existente, o export vira conferência. Homologação **nova**: a opção
**hml** do pipeline cria o Web App (estágio `CriarHml`, sem aprovação, só se ainda não existe — nunca altera
uma homologação que existe) com imagem provisória e as variáveis de plataforma (`app_settings.py
plataforma`); as do sistema o owner cria no portal; o 1º push na `dev` troca a imagem. Permissões na rede
de homologação: seção 4 do chamado-modelo (ainda não feitas).

**`/mss-spec:azure-ambiente`** (`commands/azure-ambiente.md`) leva a homologação que funciona pra produção sem
nada rodar na máquina do owner contra o Azure, em **6 etapas** (baixar · montar · simular · revisar
variáveis · preparar produção · rodar e aprovar): a 1ª mensagem mostra a tabela do caminho inteiro, toda
mensagem termina com "Etapa X de 6" + UMA coisa que precisa do owner, uma aprovação por etapa, teste vira
"proteção: N verdes". A etapa 2 também põe `/infra/` e `/azure-pipelines*.yml` no `.dockerignore`, e a
receita aponta o plano pelo grupo dele (`grupoPlano`). Na janela do projeto: lê o que o projeto já tem (e avisa,
como pendência, se não existe pipeline de código de produção) → o owner exporta o Web App da homologação
pelo portal ("Exportar modelo", Bicep) → o assistente monta `infra/main.bicep` (nomes, plano, subnet e
**imagem** como parâmetros; **sem nenhuma variável de ambiente**), `infra/hml.bicepparam`,
`infra/prd.bicepparam`, `infra/app_settings.py`, `infra/app-settings.json` e o pipeline
`azure-pipelines-infra.yml` (modelo `templates/azure-ambiente/azure-pipelines-infra.yml`).

O pipeline roda à mão com a escolha **hml** ou **prd**. `hml`: só o estágio Simular — `az bicep build` +
`what-if` contra `RG-MSSAI-DEV` (tem de dar "nada muda") + conferência das variáveis. `prd`: Simular
contra `RG-MSSAI-PRD`, depois o estágio Criar — que só existe no `prd` (inserido na compilação) e para no
botão de aprovação do environment `producao` — cria a receita e grava as variáveis. A imagem que está
rodando é lida do Web App e passada em `IMAGEM` (`readEnvironmentVariable` sem valor padrão nos
`.bicepparam`); na 1ª criação de produção é a que está rodando na homologação (produção nasce espelho e
sobe sem o pipeline de código de produção); sem nenhuma das duas, o pipeline falha em vez de criar.

**Variáveis de ambiente** (`templates/azure-ambiente/app_settings.py`, fora do Bicep porque `appSettings`
substitui a coleção inteira): todas as da homologação vão; o `infra/app-settings.json` (só nomes) marca
cada uma `"copiar"`, `"senha"` (grava `*****` só se ainda não existe em produção — nunca sobrescreve a
verdadeira) ou `{"prd": "<valor>"}` (que também cria variável só de produção, como a
`WEBSITE_DNS_ALT_SERVER=168.63.129.16`). Plano, VNet/subnet e DNS de produção vêm do `docs/AMBIENTE.md` §5,
sem perguntar. Variável da homologação fora do arquivo trava o pipeline com o nome
dela; sem arquivo, a 1ª simulação imprime a proposta. Gravação por mescla; valor nunca vai pro log; o fim
lista as senhas ainda `*****` em produção. O `hooks/git_publicacao.py` nega ao assistente
`az deployment … create` e `az stack … create`.

Desde a 0.40.0 (lições da 1ª produção real, MSS-UTILS, no ar em 2026-10-20): o Simular imprime a
`Identidade do pipeline (object id)`, e é com ela que o chamado `templates/azure-ambiente/permissoes-infra.md`
pede as permissões mínimas na rede de produção — já feitas e registradas no `templates/AMBIENTE.md` §5, então
a etapa 5 vira "já está pronto". A `DOCKER_REGISTRY_SERVER_PASSWORD` vem do próprio registro de imagens;
valor copiado vazio vira "falta preencher". A rede fica em `virtualNetworkSubnetId`, nunca `networkConfig`.

Critérios de aceite:
- DADO a 1ª simulação, QUANDO roda, ENTÃO o log mostra a identidade do pipeline, e o chamado à infra usa
  esse código (nunca o do "Manage App registration").
- DADO a senha do registro de imagens marcada `copiar`, QUANDO o pipeline grava produção, ENTÃO ela vem do
  registro; se não der, vira "falta preencher" — nunca é gravada vazia.
- DADO o projeto em homologação, QUANDO o owner roda `/mss-spec:azure-ambiente`, ENTÃO saem a receita, os dois
  `.bicepparam`, o `app_settings.py`, o `app-settings.json` e o pipeline — e nenhum passo pede comando
  local contra o Azure.
- DADO o pipeline com ambiente `hml`, QUANDO roda, ENTÃO o `what-if` contra `RG-MSSAI-DEV` dá "nada muda"
  e nenhuma variável da homologação fica fora do `app-settings.json`.
- DADO o pipeline com ambiente `prd`, QUANDO roda, ENTÃO para no botão e só cria depois da aprovação.
- DADO uma senha já preenchida em produção, QUANDO o pipeline `prd` roda de novo, ENTÃO ela não muda.
- DADO o assistente, QUANDO tenta `az deployment group create`, ENTÃO o hook nega; o `what-if` passa.

Fora de escopo: liberação de rede (vnet/IP), recurso compartilhado entre projetos, Terraform, criar o
pipeline de código de produção (é pendência avisada, tarefa à parte).

## Histórico
- 2026-10-15 — criado: produção é montada à mão por um prestador a partir de documentação, com rodadas
  de ajuste. Escolhido Bicep (nativo do Azure, sem arquivo de estado) em vez de Terraform; o owner
  preferiu o caminho do pipeline com botão de aprovação, que usa a mesma receita do "prestador roda um
  comando". Nome do comando: o owner pediu `AzurePrd`; ficou `azure-prd` pelo padrão minúsculo do kit.
- 2026-10-15 — simulação no pipeline (`hml`/`prd`), variáveis de ambiente pelo `app_settings.py`, imagem
  lida do Web App, pipeline de código de produção conferido (motivo: a 1ª execução real, no MSS-UTILS,
  achou quatro erros — Azure CLI local que não existe, nome de variável na receita apagaria a senha, imagem
  fixa, pipeline suposto; caso F-036. O owner exigiu que todas as variáveis fossem, senha como `*****`).
- 2026-10-15 — plano, VNet/subnet e DNS de produção mapeados no `templates/AMBIENTE.md` §5 e usados sem
  perguntar; `{"prd": …}` passa a criar variável que só existe em produção (motivo: o comando perguntou
  ao owner o que o Whats, já em produção, tinha medido — e a `WEBSITE_DNS_ALT_SERVER` obrigatória lá não
  existe na homologação, então o script a ignoraria).
- 2026-10-15 — `WEBSITE_DNS_SERVER` e `DOCKER_REGISTRY_SERVER_*` registrados como iguais nos dois
  ambientes; a proposta sugere a senha do registro como `copiar` (motivo: o portal mostrou a
  `WEBSITE_DNS_SERVER` em produção, que eu tinha dado como ausente pelo documento — F-037; e o owner
  decidiu que a senha do registro compartilhado vai copiada).
- 2026-10-15 — 1ª criação de produção usa a imagem da homologação; `.bicepparam` sem imagem padrão
  (motivo: o MSS-UTILS apontou que a imagem padrão `…-prod:latest` só existiria depois do pipeline de
  código de produção, que o projeto não tem — produção seria criada sem subir. O owner pediu chegar o
  mais perto possível de 100%).
- 2026-10-16 — condução em 6 etapas, `.dockerignore`, `grupoPlano`, teste da imagem no PowerShell
  (motivo: o owner se perdeu no MSS-UTILS — pedidos aos pedaços e sem mapa, caso F-038; o MSS-UTILS achou
  a receita indo pra dentro da imagem pelo `COPY . .`; o grupo do plano de produção foi conferido no portal).
- 2026-10-16 — etapa 1 com o caminho real do portal e o aviso amarelo; etapa 2 com a tabela do que o export
  traz da homologação e não vai pra produção como veio, e a conferência contra o roteiro de deploy (motivo:
  o 1º export real, do MSS-UTILS, trouxe endereço gerado, ligação de rede com código da homologação e
  "rotear todo o tráfego" ligado, contra o roteiro).
- 2026-10-20 — 0.40.0, lições da 1ª produção real (motivo: o MSS-UTILS foi ao ar; no caminho, permissões
  dadas à identidade errada por três rodadas — F-039 —, a senha do registro chegou vazia em produção e o
  owner anotou 22 pontos de condução e de receita pra corrigir no fim).
- 2026-10-21 — 0.41.0: renomeado `azure-prd` → `azure-ambiente` (comando e branch dos projetos) e a opção
  hml passa a criar a homologação que ainda não existe, a partir da receita-base do kit (motivo: o owner
  monta a homologação à mão pra cada desenvolvedor, replicando a mesma receita, e isso leva tempo; os
  nomes são dele — o assistente leu errado duas vezes antes de acertar).
