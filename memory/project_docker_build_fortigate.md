---
name: docker-build-fortigate
description: Build Docker com ODBC atrás do FortiGate — 3 armadilhas (base bookworm, apt via HTTPS, repo MS sem duplo colchete) + rotação de proxy/appliance quebra por CA faltando no corp-ca.pem ("issuer unknown")
metadata:
  type: project
---

**Atualização 2026-07-14 — rotação de proxy/appliance quebra o build por CA, não por rota.**
Proxy MSIG mudou `10.170.200.120` → `10.170.200.1:8080`. Build do MSS-SSC passou a falhar com
`apt-get update` HTTPS: "certificate verification failed ... issuer is unknown [IP: 10.170.200.1]".
Causa: o FortiGate faz SSL-inspection assinando com a CA **do appliance** (`CN=FG…<serial>`); o proxy
novo é outro appliance (`CN=FG2H0GT924902724`) e essa CA **não estava** no `certs/corp-ca.pem` (bundle
antigo, 68 certs). Fix: atualizar `corp-ca.pem` (reexportar raízes do Windows) — o Transportes/V2 já
tinha (69 certs) e buildava OK; copiei o bundle dele pro MSS-SSC e pro template do plugin. Diagnóstico:
`openssl x509 -subject` em cada cert do bundle e `comm` contra o de um projeto que builda.
Dois fatos que reconciliam tudo: (1) **Docker Desktop `config.json` (`proxies.default`) injeta proxy em
TODO build** (pull do FROM E apt/pip) — logo o build é interceptado com ou sem overlay; a nota antiga
"config.json só cobre o FROM" estava errada. (2) "issuer unknown" = CA defasada, NÃO rota de proxy.
Codificado no plugin (AMBIENTE §2 pegadinhas + CHANGELOG 0.7.0).

Build do MSS-SSC no escritório (2026-07-08) quebrou em 3 pontos em série; todos corrigidos e
**validados com build real** (`docker build` OK, `pyodbc.drivers()` → `ODBC Driver 17 for SQL Server`).

1. **Base flutuou pra trixie**: `python:3.12-slim` (e `3.14-slim`) agora é **Debian 13 (trixie)**; o
   repo ODBC da Microsoft é `debian/12` (bookworm). Fix: `FROM python:3.x-slim-bookworm`.
2. **apt em HTTP puro apanha do FortiGate**: mirrors Debian usam porta 80; o proxy intercepta o
   cleartext e devolve `Bad header data ...:80` → `apt-get update` falha. Fix: trocar mirrors pra
   **HTTPS** (`sed http://deb.debian.org→https://` em `debian.sources` e `sources.list`). Em HTTPS o
   intercept é TLS e a CA embutida (`COPY certs`) o torna confiável — funciona **sem proxy explícito**.
3. **Linha do repo MS com duplo colchete**: `curl prod.list | sed 's|https://|[signed-by=...] https://|'`
   gera `deb [arch=...] [signed-by=...] ...` → apt: `Malformed entry (URI parse)`. Fix: escrever à
   mão `echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main"`.

Também: o **pull do FROM é do daemon** — no escritório sem proxy no Docker Desktop, só builda a
partir de imagem **em cache**. O MSS-SSC usa `python:3.14-slim-bookworm` (era o bookworm em cache na
máquina + é a versão do dev local). Ver [[credencial-reusar-env-precedente]] e AMBIENTE §2.
Codificado no plugin v0.5.1 (templates/docker/Dockerfile + AMBIENTE §2).
