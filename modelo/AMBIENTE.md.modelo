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
(Se já existe na máquina, o comando falha silenciosamente avisando que já existe — sem problema.)

Adicione seu(s) serviço(s) a essa rede no `docker-compose.yml`:
```yaml
services:
  <seu-servico>:
    networks:
      - mitiai_network
```

## 2. Proxy corporativo MSIG

Necessário pra `pip`, Docker Desktop e qualquer chamada HTTP saindo da rede da empresa.

**Pip:**
```
pip config set global.proxy http://10.170.200.120:8080
```

**Variáveis de ambiente globais (Windows, usuário):**
```
setx HTTP_PROXY "http://10.170.200.120:8080"
setx HTTPS_PROXY "http://10.170.200.120:8080"
```
Precisa fechar e abrir um terminal novo depois — `setx` só afeta janelas abertas depois do comando.

**Docker Desktop** (via interface, não tem comando): Settings → Resources → Proxies → Manual proxy
configuration → Web Server (HTTP) e Secure Web Server (HTTPS) = `http://10.170.200.120:8080` →
Apply & Restart. Se não pegar mesmo com "Apply & Restart": o backend (`com.docker.backend`) pode já
estar rodando desde antes da config ser salva — dê Quit completo no Docker Desktop (botão direito no
ícone da bandeja → Quit, não só fechar a janela), abra de novo, confirme a config e rode o build de novo.

**Dentro de um container** (build args + env, normalmente num `docker-compose.office.yml` separado do
compose principal, pra só ativar quando rodando na rede da empresa):
```yaml
services:
  <seu-servico>:
    build:
      args:
        HTTP_PROXY: http://10.170.200.120:8080
        HTTPS_PROXY: http://10.170.200.120:8080
    environment:
      - HTTP_PROXY=http://10.170.200.120:8080
      - HTTPS_PROXY=http://10.170.200.120:8080
      - NO_PROXY=localhost,127.0.0.1,::1,host.docker.internal,postgres-db,<outros-hosts-internos>,.ms-seg.com.br,.msig.com.br,.local
```

**Certificado corporativo (interceptação TLS do proxy)** — se o container faz chamadas HTTPS pra fora
(ex.: API da OpenAI/Gemini), precisa confiar na CA da empresa, senão dá erro de SSL:
```dockerfile
COPY certs/corp-ca.pem /usr/local/share/ca-certificates/corp-ca.crt
RUN update-ca-certificates || true \
    && cat /usr/local/share/ca-certificates/corp-ca.crt >> /etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```
Peça o arquivo `corp-ca.pem` (mesmo de todos os projetos) se ainda não tiver.

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

Host interno compartilhado: `MSSQLD0` (`10.170.210.36`), porta 1433. Acesso via `pyodbc`. Duas
variantes conhecidas — escolha uma:

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

**Variante endurecida** (credencial criptografada — recomendada pra produção):
```python
import os
import pyodbc
from cryptography.fernet import Fernet

def get_connection() -> pyodbc.Connection:
    key = os.getenv("ENCRYPTION_KEY").encode()
    ciphertext = os.getenv("ENCRYPTED_CONN").encode()
    connection_string = Fernet(key).decrypt(ciphertext).decode()
    return pyodbc.connect(connection_string, autocommit=True)
```
Em dev, pode cair pra credencial simples (`DB_SERVER`, `DB_USER`, `DB_PASS`, `DB_DATABASE`); em
produção, usar sempre `ENCRYPTION_KEY`/`ENCRYPTED_CONN`.

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
