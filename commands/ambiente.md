---
description: Gera os arquivos de infra no padrão MSIG (docker-compose na rede mitiai_network; proxy e SSL via .env, sem Docker Desktop nem certificado)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar os **arquivos de infra** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` (§1 rede, §2 proxy/SSL) como referência. Mostre o que vai gerar e **confirme com o owner antes de gravar**.

1. Pergunte: **este projeto será containerizado?**
2. **Proxy e SSL vivem no `.env`** (nunca no Docker Desktop nem em código). Gere/atualize o `.env.example` com:
   ```
   HTTP_PROXY=http://10.170.200.120:8080
   HTTPS_PROXY=http://10.170.200.120:8080
   NO_PROXY=localhost,127.0.0.1,::1,host.docker.internal,postgres-db,.ms-seg.com.br,.msig.com.br,.local
   SSL_VERIFY=false
   ```
3. **Se containerizado**, gere `docker-compose.yml` — serviço na rede externa, `.env` no runtime, proxy como build-arg (interpolado do `.env`):
   ```yaml
   services:
     <servico>:
       build:
         context: .
         args:
           PIP_PROXY: ${HTTP_PROXY:-}
       container_name: <nome>
       env_file: [.env]
       restart: unless-stopped
       networks:
         - mitiai_network
   networks:
     mitiai_network:
       name: mitiai_network
       external: true
   ```
   E no `Dockerfile`, o proxy só no pip (não vaza pro runtime):
   ```dockerfile
   ARG PIP_PROXY
   RUN pip install ${PIP_PROXY:+--proxy $PIP_PROXY} --no-cache-dir -r requirements.txt
   ```
4. **SSL:** garanta que o código de saída respeita `SSL_VERIFY` — `app/config.py` com `ssl_verify: bool = True` (pydantic-settings) e **todo** `httpx.Client` de saída criado com `verify=settings.ssl_verify`. `SSL_VERIFY=false` aceita a interceptação TLS do FortiGate (substitui a injeção de `corp-ca.pem` — certificado fica fora de escopo). Avise o owner: `psycopg`/TCP ignora proxy; e mudar `SSL_VERIFY` exige **reiniciar o app** (clients criados no import).
5. Lembre o owner de criar a rede uma vez, se ainda não existir: `docker network create mitiai_network`.
