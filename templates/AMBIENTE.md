<!-- MODELO de referência de ambiente corporativo — copie para `docs/AMBIENTE.md` no projeto novo.
     Seções 1 e 2 são fatos fixos (iguais em todo projeto MSIG) — copie como está.
     Seções 3-5 são padrões (a estrutura se repete, os valores em <...> são deste projeto).
     Apague as seções que não se aplicarem a este projeto (ex.: sem SQL Server, sem Azure). -->

# Ambiente corporativo MSIG — referência de infraestrutura

## 1. Rede Docker compartilhada

Toda infra Docker da empresa compartilha uma única rede externa, usada pra containers de projetos
diferentes se enxergarem (ex.: uma API falando com o Postgres corporativo, ou com o n8n).

```yaml
networks:
  mitiai_network:
    name: mitiai_network
    external: true
```

A rede **não é criada pelo compose** — precisa existir antes:
```
docker network create mitiai_network
```
(Se já existe na máquina, o comando retorna um erro avisando que já existe — sem efeito colateral, pode ignorar.)

Adicione seu(s) serviço(s) a essa rede no `docker-compose.yml`:
```yaml
services:
  <seu-servico>:
    networks:
      - mitiai_network
```

## 2. Proxy e TLS corporativo — 4 camadas que NÃO se confundem

Atrás da rede MSIG, proxy e TLS aparecem em **4 pontos independentes**; cada um resolve uma coisa.
Confundi-los é a maior fonte de "funciona no build mas não no runtime" (e vice-versa).

| Camada | Onde se configura | Para quê |
|---|---|---|
| **Pull da imagem base (`FROM`)** | **daemon** → Docker Desktop → Settings → Resources → Proxies | baixar `python:3.12-slim` do Docker Hub |
| **Build (pip/apt)** | `build.args` `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` — ARGs predefinidos do Docker, usados sozinhos por pip/apt (o `docker-compose.office.yml` os injeta do `.env`) | instalar deps durante o build |
| **Runtime (saída do app: Graph, n8n, APIs)** | `.env` via `env_file` (`HTTP_PROXY/HTTPS_PROXY/NO_PROXY`) | chamadas HTTP de saída do container |
| **TLS interceptado (FortiGate)** | CA corporativa **embutida na imagem** (`Dockerfile`: `COPY certs` → `certs/corp-ca.pem` → store do sistema) com **`SSL_VERIFY=true`** | confiar no CA do proxy SEM desligar a validação TLS (`false` = só fallback temporário de diagnóstico) |

Notas que evitam pegadinha:
- O `httpx` lê `HTTP_PROXY/HTTPS_PROXY/NO_PROXY` sozinho (`trust_env=True`) — **não** passe `proxies=` no código nem use `trust_env=False`.
- `SSL_VERIFY` é lido no `config.py` (pydantic) e vira `verify=` de **todo** `httpx.Client` de saída. Clients criados no import → mudar `SSL_VERIFY` **pede restart**.
- **`psycopg`/Postgres é TCP puro: ignora o proxy** (por isso o banco não passa por ele).
- `corp-ca.pem` = bundle de raízes do Windows (inclui a CA da MSIG). Inofensivo fora da empresa e não quebra o build se faltar. Projetos com **Chrome/Selenium headless** precisam registrar a CA também no NSS (`/root/.pki/nssdb`) — ver bloco opcional no `Dockerfile`.

### Subir o Docker — casa (VPN) vs escritório (proxy)
- **Casa (VPN, sem proxy):** `docker compose up -d --build`
- **Escritório (proxy MSIG):** `docker compose -f docker-compose.yml -f docker-compose.office.yml up -d --build`

**Gotcha — `load metadata for python:3.12-slim ... i/o timeout`:** o pull do `FROM` é do **daemon** e NÃO usa `build.args`/`.env`. Resolva com **um** dos dois:
1. Proxy no **Docker Desktop** (Settings → Resources → Proxies → Manual → HTTP/HTTPS = `http://10.170.200.120:8080` → Apply & Restart; se persistir, **Quit** total pela bandeja + reabrir).
2. **Pré-baixar a base** numa rede que funcione: `docker pull python:3.12-slim`. O cache é **por máquina**, então o build reusa e não vai mais no Docker Hub. ← costuma ser o que resolve.

Os arquivos `docker-compose.yml`, `docker-compose.office.yml`, `Dockerfile`, `.dockerignore` e
`certs/corp-ca.pem` já vêm padronizados (o `/mss-spec:ambiente` os copia); ajuste só o nome do serviço
e os `COPY` do app.

### Dev na máquina host (fora de container)
Para `pip install` direto no Windows, uma vez: `pip config set global.proxy http://10.170.200.120:8080`.
O app rodando com `uvicorn` local lê proxy/SSL do mesmo `.env` (pydantic + `trust_env` do httpx).

## 3. Postgres compartilhado

Existe um Postgres corporativo único (container `postgres-db`, imagem `pgvector/pgvector:pg15`,
porta 5432, na rede `mitiai_network`), com backup automático (`postgres-backup`, dump a cada 6h).
Convenção de nome de banco: `miti_ai_<projeto>`.

**Connection string**, host varia conforme de onde você conecta:
```
postgresql://<usuario>:<senha>@<host>/miti_ai_<projeto>
```
- Mesma rede Docker (`mitiai_network`): host = `postgres-db`
- Fora da rede / máquina diferente: host = `mitiai-poc.msig.com.br`
- Dev local sem Docker: host = `localhost`; dev local com Docker (Windows/Mac): host =
  `host.docker.internal`

Peça ao owner do Postgres pra criar o banco `miti_ai_<projeto>` e as credenciais antes de usar.

## 4. SQL Server (`get_connection.py` multi-ambiente — padrão canônico da casa)

**Referência REAL** (com os pares das bases SSC · MS10=`tkgs_corp` · TRP · OnBase já prontos):
`C:\Ronaldo\_Mitsui\Python\Transportes\V2\get_connection.py`. O `/mss-spec:banco` copia o template
do plugin (`templates/get_connection.py`) pro projeto.

Regras do padrão:
- **Credencial NUNCA em `.env` nem em texto plano** (regra do owner: "no `.env` no máximo o
  ambiente"). Cada base tem par Fernet `KEY`/`CIPHERTEXT` **por ambiente** (DEV/D0 · HML/HI · PROD)
  embutido no próprio `get_connection.py`.
- **`.env` só carrega o seletor**: `CONEXAO_PRD` (vazio/ausente = DEV; qualquer valor = PROD) e
  `API_ENV=PRD` em produção.
- **Base já usada em outro projeto** → os pares prontos estão no arquivo de referência acima;
  **copiar par entre projetos é decisão do owner** (o assistente aponta o caminho/constantes, não
  cola). **Base nova** → gerar o par localmente por script (snippet no docstring do template), sem
  ecoar segredo.
- Helpers do padrão: `mask_password` (log sem senha), `_build_conn_str` (`Encrypt`/`timeout`
  automáticos), `_connect` (log + erro padronizados), `is_ambiente_prd()`; apps Streamlit têm cache
  de conexão por sessão (ver referência).

**Fatos verificados** (2026-07-08, decriptação local no Transportes V2): SSC dev =
`10.170.210.36,1435`; `tkgs_corp` (MS10) e `MSS_TRP` dev = `10.170.210.36` (sem porta explícita);
SSC prod = `10.170.210.48`. As instâncias corporativas usam portas **1434/1435** (owner) — onde
entra a 1434: `<a confirmar>`. Não assuma `MSSQLD0:1433`. Fora da rede corporativa (sem VPN), nada
resolve/responde — **erro 53/timeout do pyodbc é rede, não credencial**.

**Nota honesta:** chave+cifra no mesmo repo = quem tem o repo decripta. Aceito porque os repos são
privados/internos e isso evita credencial circulando em texto plano; segurança real (repo exposto)
exigiria a chave fora do repo (Azure Key Vault).

Se o container precisar resolver `MSSQLD0` por nome, adicione no `docker-compose.yml`:
```yaml
extra_hosts:
  - "MSSQLD0:10.170.210.36"
```

## 5. Azure — deploy homologação/produção

Pipeline padrão via Azure DevOps (ACR → Azure Web App), acionado por branch:

| | Homologação | Produção |
|---|---|---|
| Branch | `dev` | `main` |
| Resource Group | `RG-MSSAI-DEV` | `RG-MSSAI-PRD` |
| Nome do recurso | `mss-miti-ai-<projeto>-dev-br` | `mss-miti-ai-<projeto>-prod` |

Fixos em qualquer projeto:
```yaml
variables:
  azureServiceConnection: 'Mitsui Sumitomo Seguros S.A. - Azure Subscriptions (e87b4af3-ce34-4c44-8c64-0151ca959654)'
  acrName: 'mssaicontainerregistry'
  vmImageName: 'ubuntu-latest'
```

Estágios: **BuildAndPush** (`az acr build`, tag = `$(Build.BuildId)` + `latest`) → **Verify Image**
(`az acr repository show-tags`) → **Update Web App** (`az webapp config container set` +
`az webapp restart`). Duplique o pipeline (um YAML por branch/ambiente) trocando só `imageName`,
`webAppName` e `resourceGroup`.

## 6. Outras convenções

- **Timezone**: `America/Sao_Paulo` em toda variável `TZ`/`GENERIC_TIMEZONE` de container.
- **Restart policy** padrão: `unless-stopped` (serviços de aplicação) ou `always` (infra de base
  como Postgres/n8n).
