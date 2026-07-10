---
name: docker-build-fortigate
description: 3 armadilhas do build Docker com ODBC atrás do FortiGate — base bookworm, apt via HTTPS, linha do repo MS sem duplo colchete (validado build real MSS-SSC)
metadata:
  type: project
---

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
