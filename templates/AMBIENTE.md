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
| **Pull da imagem base (`FROM`)** | **daemon** → Docker Desktop → Settings → Resources → Proxies | baixar `python:3.14-slim` do Docker Hub |
| **Build (pip/apt)** | `build.args` `HTTP_PROXY`/`PIP_PROXY` (no `docker-compose.office.yml`; o base pega `${HTTP_PROXY}` do `.env`) | instalar deps durante o build |
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

**Gotcha — `load metadata for python:3.14-slim ... i/o timeout`:** o pull do `FROM` é do **daemon** e NÃO usa `build.args`/`.env`. Resolva com **um** dos dois:
1. Proxy no **Docker Desktop** (Settings → Resources → Proxies → Manual → HTTP/HTTPS = `http://10.170.200.120:8080` → Apply & Restart; se persistir, **Quit** total pela bandeja + reabrir).
2. **Pré-baixar a base** numa rede que funcione: `docker pull python:3.14-slim`. O cache é **por máquina**, então o build reusa e não vai mais no Docker Hub. ← costuma ser o que resolve.

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

## 4. SQL Server (`get_connection.py`)

Host interno compartilhado: `MSSQLD0` (`10.170.210.36`). **Porta: confirme com um projeto que já
conecta** — o jedai usa `Server=10.170.210.36,1435` (instância na porta **1435**); não assuma 1433.
Fora da rede corporativa (sem VPN), o host não resolve nem responde — erro 53/timeout é rede, não
credencial. Acesso via `pyodbc`. **Credencial: se outro projeto MSIG já conecta no mesmo servidor,
copie do `.env` local dele (ajustando `Database=`) em vez de pedir ao owner — nunca ecoar/commitar.**
Duas variantes conhecidas — escolha uma:

**Variante simples** (um ou mais bancos, credencial em variável de ambiente comum — bom pra
dev/homolog ou quando a máquina já é protegida por outros meios):
```python
import os
import pyodbc

_CONN_STR = os.getenv("SQL_CONNECTION_STRING_<BANCO>")

def get_connection_<banco>() -> pyodbc.Connection:
    if not _CONN_STR:
        raise RuntimeError("SQL_CONNECTION_STRING_<BANCO> não definida no .env")
    return pyodbc.connect(_CONN_STR)
```
```
SQL_CONNECTION_STRING_<BANCO>=Driver={ODBC Driver 17 for SQL Server};Server=MSSQLD0;Database=<banco>;UID=<usuario>;PWD=<senha>;TrustServerCertificate=yes;
```
Se o app for Streamlit e a conexão for reaproveitada durante a sessão, cacheie com
`@st.cache_resource`.

**Variante com credencial cifrada** (Fernet):
```python
import os
import pyodbc
from cryptography.fernet import Fernet

def get_connection() -> pyodbc.Connection:
    key = os.getenv("ENCRYPTION_KEY")
    ciphertext = os.getenv("ENCRYPTED_CONN")
    if not key or not ciphertext:
        raise RuntimeError("ENCRYPTION_KEY/ENCRYPTED_CONN não definidas no ambiente")
    connection_string = Fernet(key.encode()).decrypt(ciphertext.encode()).decode()
    # autocommit=True: cada statement commita sozinho — sem rollback; cuidado em escrita multi-passo.
    return pyodbc.connect(connection_string, autocommit=True)
```
**Nota honesta:** se `ENCRYPTION_KEY` mora no **mesmo `.env`** que `ENCRYPTED_CONN`, isso é
**ofuscação, não segurança** — quem lê o arquivo decifra na hora. Só vira proteção real quando a
chave vem de **outro store** (Azure Key Vault, app settings do Web App, variável injetada pelo
pipeline). Em dev, credencial simples (`SQL_CONNECTION_STRING_*`) dá no mesmo com menos peça móvel.

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
