# Azure produção — receita da homologação levada pra produção (`/mss-spec:azure-prd`)

## Estado atual
**`/mss-spec:azure-prd`** (`commands/azure-prd.md`) leva a homologação que funciona pra produção sem
nada rodar na máquina do owner contra o Azure, em **6 etapas** (baixar · montar · simular · revisar
variáveis · preparar produção · rodar e aprovar): a 1ª mensagem mostra a tabela do caminho inteiro, toda
mensagem termina com "Etapa X de 6" + UMA coisa que precisa do owner, uma aprovação por etapa, teste vira
"proteção: N verdes". A etapa 2 também põe `/infra/` e `/azure-pipelines*.yml` no `.dockerignore`, e a
receita aponta o plano pelo grupo dele (`grupoPlano`). Na janela do projeto: lê o que o projeto já tem (e avisa,
como pendência, se não existe pipeline de código de produção) → o owner exporta o Web App da homologação
pelo portal ("Exportar modelo", Bicep) → o assistente monta `infra/main.bicep` (nomes, plano, subnet e
**imagem** como parâmetros; **sem nenhuma variável de ambiente**), `infra/hml.bicepparam`,
`infra/prd.bicepparam`, `infra/app_settings.py`, `infra/app-settings.json` e o pipeline
`azure-pipelines-infra-prd.yml` (modelo `templates/azure-prd/azure-pipelines-prd.yml`).

O pipeline roda à mão com a escolha **hml** ou **prd**. `hml`: só o estágio Simular — `az bicep build` +
`what-if` contra `RG-MSSAI-DEV` (tem de dar "nada muda") + conferência das variáveis. `prd`: Simular
contra `RG-MSSAI-PRD`, depois o estágio Criar — que só existe no `prd` (inserido na compilação) e para no
botão de aprovação do environment `producao` — cria a receita e grava as variáveis. A imagem que está
rodando é lida do Web App e passada em `IMAGEM` (`readEnvironmentVariable` sem valor padrão nos
`.bicepparam`); na 1ª criação de produção é a que está rodando na homologação (produção nasce espelho e
sobe sem o pipeline de código de produção); sem nenhuma das duas, o pipeline falha em vez de criar.

**Variáveis de ambiente** (`templates/azure-prd/app_settings.py`, fora do Bicep porque `appSettings`
substitui a coleção inteira): todas as da homologação vão; o `infra/app-settings.json` (só nomes) marca
cada uma `"copiar"`, `"senha"` (grava `*****` só se ainda não existe em produção — nunca sobrescreve a
verdadeira) ou `{"prd": "<valor>"}` (que também cria variável só de produção, como a
`WEBSITE_DNS_ALT_SERVER=168.63.129.16`). Plano, VNet/subnet e DNS de produção vêm do `docs/AMBIENTE.md` §5,
sem perguntar. Variável da homologação fora do arquivo trava o pipeline com o nome
dela; sem arquivo, a 1ª simulação imprime a proposta. Gravação por mescla; valor nunca vai pro log; o fim
lista as senhas ainda `*****` em produção. O `hooks/git_publicacao.py` nega ao assistente
`az deployment … create` e `az stack … create`.

Critérios de aceite:
- DADO o projeto em homologação, QUANDO o owner roda `/mss-spec:azure-prd`, ENTÃO saem a receita, os dois
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
