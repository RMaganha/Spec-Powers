---
description: Gera os arquivos de infra no padrão MSIG (docker-compose com rede mitiai_network; override de proxy do escritório se container)
argument-hint: ""
disable-model-invocation: true
---

Você vai gerar os **arquivos de infra** deste projeto no padrão MSIG. Consulte `docs/AMBIENTE.md` como referência dos valores fixos. Mostre o que vai gerar e **confirme com o owner antes de gravar**.

1. Pergunte: **este projeto será containerizado?** Se não, só oriente o setup de proxy no host (opção 1 do `docs/AMBIENTE.md`: `pip config`, `setx HTTP/HTTPS_PROXY`, Docker Desktop) e pare.
2. Se sim, gere `docker-compose.yml` com o serviço do projeto na rede externa compartilhada:
   ```yaml
   services:
     <servico>:
       build: .
       container_name: <nome>
       env_file: .env
       restart: unless-stopped
       networks:
         - mitiai_network
   networks:
     mitiai_network:
       name: mitiai_network
       external: true
   ```
3. Pergunte: **vai rodar no escritório (atrás do proxy corporativo)?** Se sim, gere `docker-compose.office.yml` como override, injetando `HTTP_PROXY`/`HTTPS_PROXY=http://10.170.200.120:8080` e `NO_PROXY` (localhost,127.0.0.1,::1,host.docker.internal,postgres-db,.ms-seg.com.br,.msig.com.br,.local) via `environment:`.
4. **Certificado corporativo está fora de escopo** — não injete `corp-ca.pem`. Se o container precisar de HTTPS externo atrás do proxy, avise que isso é tratado manualmente, fora do plugin.
5. Lembre o owner de criar a rede uma vez, se ainda não existir: `docker network create mitiai_network`.
