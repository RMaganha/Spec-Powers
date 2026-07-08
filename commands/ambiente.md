---
description: Gera a infra Docker no padrão MSIG (compose base + office, Dockerfile, CA corporativa, .dockerignore) e explica casa-VPN vs escritório-proxy
argument-hint: ""
disable-model-invocation: true
---

Você vai montar a **infra Docker** deste projeto no padrão MSIG. Referência completa em `docs/AMBIENTE.md` (§1 rede, §2 proxy/TLS de 4 camadas). Mostre o que vai copiar/gerar e **confirme antes de gravar**.

1. Pergunte: **este projeto será containerizado?** Se não, oriente só o `.env` (proxy/SSL) + `pip config` no host e pare.
2. **`.env` / `.env.example`** — proxy e SSL vivem aqui (nunca no Docker Desktop; em arquivo versionado, só o override explícito do `docker-compose.office.yml`):
   ```
   HTTP_PROXY=            # http://10.170.200.120:8080 no escritório; vazio em casa
   HTTPS_PROXY=
   NO_PROXY=localhost,127.0.0.1,::1,host.docker.internal,MSSQLD0,10.170.210.36,postgres-db,.ms-seg.com.br,.msig.com.br,.local
   SSL_VERIFY=true        # padrão SEMPRE true — a CA embutida na imagem cobre o FortiGate; false só como fallback temporário de diagnóstico
   ```
3. **Copie os arquivos padrão** de `${CLAUDE_PLUGIN_ROOT}/templates/` para o projeto e ajuste:
   - `templates/docker/docker-compose.yml`        → `docker-compose.yml` (troque `<servico>`)
   - `templates/docker/docker-compose.office.yml` → `docker-compose.office.yml` (troque `<servico>`)
   - `templates/docker/Dockerfile`                → `Dockerfile` (ajuste os `COPY` às camadas do projeto — ver `docs/ESTRUTURA.md`)
   - `templates/docker/dockerignore`              → `.dockerignore`
   - `templates/certs/corp-ca.pem`                → `certs/corp-ca.pem` (CA corporativa embutida na imagem)
4. **SSL no código:** garanta `config/settings.py` com `ssl_verify: bool = True` (pydantic-settings; ver `docs/ESTRUTURA.md`) e **todo** `httpx.Client` de saída com `verify=settings.ssl_verify`. Quem cobre a interceptação TLS do FortiGate é a **CA embutida na imagem** (Dockerfile: `COPY certs` + store do sistema) — com ela, `SSL_VERIFY=true` funciona inclusive no escritório. `SSL_VERIFY=false` é só fallback temporário de diagnóstico (desliga a validação TLS de TODA saída, não só do proxy — não deixe assim). Lembre: `psycopg`/TCP ignora proxy; mudar `SSL_VERIFY` pede restart (clients criados no import).
5. **Explique as 4 camadas** (pull da base = daemon/Docker Desktop · build = build.args/PIP_PROXY · runtime = `.env` · TLS = CA embutida + `SSL_VERIFY`) e **como subir**:
   - Casa (VPN): `docker compose up -d --build`
   - Escritório (proxy): `docker compose -f docker-compose.yml -f docker-compose.office.yml up -d --build`
   - Se der `load metadata ... i/o timeout` no build: proxy no Docker Desktop **ou** `docker pull python:3.14-slim` (cache por máquina — costuma resolver).
6. Lembre de criar a rede uma vez, se não existir: `docker network create mitiai_network`.
