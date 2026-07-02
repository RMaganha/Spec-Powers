<!-- Prompt avulso — não é copiado pra projeto novo, fica aqui como referência versionada.
     Uso: cole o conteúdo entre as linhas "-----" numa sessão do CLAUDE CODE (CLI, com acesso a
     arquivo) com o terminal já aberto NA RAIZ do projeto que você quer investigar. NÃO funciona
     num chat do claude.ai / Claude Projects (web) — lá não há acesso ao sistema de arquivos do
     projeto, só a uploads/integrações, e o resultado sai inventado ou vazio. Testado e confirmado
     esse erro em 2026-07-02: rodado num chat sem acesso a arquivo, caiu num diretório vazio. -->

# Prompt: Mapeamento de Ambiente — Padrão Corporativo MSIG

Origem: levantamento feito em 2026-07-02 sobre IA Jeday Cosseguro, FunilVendas, IA Bot Agent
(antigo e `_opcao4`), IA Corretor, Chatwoot, Docker n8n e Docker postgres. Ver `modelo/AMBIENTE.md.modelo`
para o mesmo conteúdo já formatado como referência de projeto (esse prompt é a versão "peça pra
investigar e comparar").

-----

PRÉ-REQUISITO DE AMBIENTE: isto só funciona com acesso direto ao sistema de arquivos do projeto
(Claude Code / CLI com terminal já na raiz do repositório). Se você não tem ferramentas de
arquivo (Read/Glob/Grep) ou o diretório de trabalho não é a raiz de um projeto de código real —
por exemplo, está rodando num chat web sem acesso a arquivo, ou só vê uploads/memória de
conversa — PARE AQUI. Não invente um relatório. Diga isso ao usuário e peça pra: (a) rodar este
prompt no Claude Code com o terminal na raiz do projeto certo, ou (b) anexar os arquivos-chave
(docker-compose*.yml, Dockerfile, azure-pipelines*.yml, módulo de conexão SQL, .env.example).

Você vai investigar ESTE projeto (a raiz do repositório atual) e comparar suas convenções de
infraestrutura com o padrão corporativo já conhecido em outros projetos MSIG. É só investigação e
relatório — não altere nenhum arquivo.

REGRA DE SEGURANÇA CRÍTICA: nunca inclua no relatório valores reais de senha, connection string
completa, API key, token ou qualquer segredo. Reporte só estrutura/padrão (nomes de variáveis de
ambiente, nomes de serviço/rede, caminhos de arquivo). Se achar um .env ou config com segredo, diga
que existe e onde, sem copiar o valor.

## Padrão corporativo conhecido (referência para comparação)

- **Rede Docker**: `mitiai_network` — externa, compartilhada entre projetos (criada uma vez com
  `docker network create mitiai_network`, nunca criada dentro de um compose específico).
- **Proxy corporativo**: `HTTP_PROXY`/`HTTPS_PROXY=http://10.170.200.120:8080`, com `NO_PROXY`
  cobrindo localhost/host.docker.internal/hosts internos, e certificado `corp-ca.pem` injetado no
  Dockerfile (`REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`/`PIP_CERT`/`CURL_CA_BUNDLE`). Normalmente vem num
  arquivo de override separado (`docker-compose.office.yml`), não no compose principal.
- **Postgres compartilhado**: container `postgres-db` na rede `mitiai_network`, porta 5432, imagem
  `pgvector/pgvector:pg15`, com backup automático (`postgres-backup`, pg_dump periódico). Host de
  conexão varia: `postgres-db` (mesma rede Docker), `mitiai-poc.msig.com.br` (fora da rede),
  `localhost`/`host.docker.internal` (dev sem compose). Nome de banco costuma seguir
  `miti_ai_<projeto>`.
- **SQL Server compartilhado**: host `MSSQLD0` = `10.170.210.36`, porta 1433. Acesso via `pyodbc`,
  normalmente encapsulado numa função/módulo tipo `get_connection()` — variações conhecidas: (a)
  múltiplas conexões por banco (uma função por banco, cache via `st.cache_resource` se for
  Streamlit), (b) conexão única com credencial simples em dev e connection string **criptografada
  com Fernet** (`ENCRYPTION_KEY`/`ENCRYPTED_CONN`) em produção.
- **Azure DevOps / deploy**: service connection `Mitsui Sumitomo Seguros S.A. - Azure Subscriptions`,
  ACR `mssaicontainerregistry`, convenção de nome de recurso `mss-miti-ai-<projeto>-<ambiente>[-br]`,
  resource group `RG-MSSAI-DEV` (branch `dev`, homologação) / `RG-MSSAI-PRD` (branch `main`,
  produção). Pipeline em 3 estágios: build+push pro ACR → verificar tags → atualizar Web App.
- **Timezone**: `America/Sao_Paulo` em todo serviço Docker.

## O que investigar neste projeto (reporte tópico a tópico)

0. **Identificação do projeto** — antes de tudo, diga: nome do projeto, a que ele se destina (1
   frase de objetivo/negócio) e stack principal. Infira de `README.md`, `CLAUDE.md`, docstring do
   entrypoint (`main.py`/`app.py`), `pyproject.toml`/`package.json`, ou nome da pasta. Se depois de
   olhar esses lugares ainda não der pra saber pra que serve, **pergunte ao usuário** em vez de
   chutar — não continue pros tópicos de infra sem isso, porque o relatório final precisa desse
   contexto pra ser útil (e pra alimentar o catálogo de precedentes com o "pra quê", não só o
   "como").
1. **Docker Compose / rede** — existe? usa `mitiai_network`? Se não, por quê (projeto standalone,
   não precisa falar com outros containers)? Cole a seção `networks:`.
2. **Postgres** — conecta em algum? Segue o padrão acima (host/porta/nome de banco)? Ou tem lógica
   própria?
3. **SQL Server / getconnection.py** — existe? Qual das duas variantes conhecidas (ou uma terceira)?
   Usa o host `MSSQLD0`/`10.170.210.36`?
4. **Azure (homolog/prod)** — tem pipeline de deploy? Segue a convenção de nome/RG acima? Alguma
   divergência?
5. **Proxy corporativo** — tem override tipo `docker-compose.office.yml`? Usa o mesmo IP e
   certificado?
6. **Padrões de aplicação reutilizáveis** — este projeto faz algo que já existe em outro lugar
   (busca vetorial/RAG, extração de documento com LLM, integração com Chatwoot/WhatsApp, etc.)?
   Se sim, qual biblioteca/abordagem usa? (Isso alimenta o catálogo de precedentes entre projetos —
   ex.: RAG deve preferir `pgvector` no Postgres compartilhado, não um índice vetorial local tipo
   Chromadb, que é uma abordagem já superada.)

## Saída esperada

Abra o relatório com a identificação do projeto (item 0). Depois, para cada tópico de infra (itens
1-6): "conforme o padrão" ou "diverge: <explique e avalie se é problema ou decisão intencional>".
Feche com uma lista de recomendações (se houver divergências que valha a pena corrigir) e, se
aplicável, uma lista de padrões de aplicação novos dignos de virar entrada no catálogo de
precedentes entre projetos (skill `precedentes-msig`) — nesse caso, inclua também o nome/propósito
do projeto do item 0, não só o caminho.

-----
