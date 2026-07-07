---
description: Gera a infra Docker no padrão MSIG (compose base + office, Dockerfile, CA corporativa, .dockerignore) e explica casa-VPN vs escritório-proxy
argument-hint: ""
disable-model-invocation: true
---

Você vai montar a **infra Docker** deste projeto no padrão MSIG. Referência completa em `docs/AMBIENTE.md` (§1 rede, §2 proxy/TLS de 4 camadas). Mostre o que vai copiar/gerar e **confirme antes de gravar**.

1. Pergunte: **este projeto será containerizado?** Se não, oriente só o `.env` (proxy/SSL) + `pip config` no host e pare.
2. **`.env` / `.env.example`** — proxy e SSL vivem aqui (nunca no Docker Desktop nem em código):
   ```
   HTTP_PROXY=            # http://10.170.200.120:8080 no escritório; vazio em casa
   HTTPS_PROXY=
   NO_PROXY=localhost,127.0.0.1,::1,host.docker.internal,MSSQLD0,10.170.210.36,postgres-db,.ms-seg.com.br,.msig.com.br,.local
   SSL_VERIFY=true        # false atrás do proxy FortiGate
   ```
3. **Copie os arquivos padrão** de `${CLAUDE_PLUGIN_ROOT}/templates/` para o projeto e ajuste:
   - `templates/docker/docker-compose.yml`        → `docker-compose.yml` (troque `<servico>`)
   - `templates/docker/docker-compose.office.yml` → `docker-compose.office.yml` (troque `<servico>`)
   - `templates/docker/Dockerfile`                → `Dockerfile` (ajuste os `COPY app`/`templates`/`static`)
   - `templates/docker/dockerignore`              → `.dockerignore`
   - `templates/certs/corp-ca.pem`                → `certs/corp-ca.pem` (CA corporativa embutida na imagem)
4. **SSL no código:** garanta `app/config.py` com `ssl_verify: bool = True` (pydantic-settings) e **todo** `httpx.Client` de saída com `verify=settings.ssl_verify`. `SSL_VERIFY=false` + a CA embutida cobrem a interceptação TLS do FortiGate. Lembre: `psycopg`/TCP ignora proxy; mudar `SSL_VERIFY` pede restart (clients criados no import).
5. **Explique as 4 camadas** (pull da base = daemon/Docker Desktop · build = build.args/PIP_PROXY · runtime = `.env` · TLS = CA embutida + `SSL_VERIFY`) e **como subir**:
   - Casa (VPN): `docker compose up -d --build`
   - Escritório (proxy): `docker compose -f docker-compose.yml -f docker-compose.office.yml up -d --build`
   - Se der `load metadata ... i/o timeout` no build: proxy no Docker Desktop **ou** `docker pull python:3.14-slim` (cache por máquina — costuma resolver).
6. Lembre de criar a rede uma vez, se não existir: `docker network create mitiai_network`.
