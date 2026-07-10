# Imagem standalone. Conecta em serviços existentes via .env (não sobe banco próprio).
# Se usar Tailwind: compile static/css/app.css e comite (sem Node aqui).
# Base FIXADA em `-bookworm` (Debian 12): as tags `python:3.x-slim` migraram pra trixie/Debian 13,
# que NÃO casa com o repo ODBC `debian/12` da Microsoft. O sufixo `-bookworm` trava a base certa.
# Ajuste a versão (3.12/3.14) à que o dev usa e que já esteja em cache (o daemon no escritório não
# puxa do Docker Hub — ver AMBIENTE.md §2, camada 1).
FROM python:3.12-slim-bookworm

WORKDIR /app

# Proxy do BUILD (pip/apt). Vazio em casa; o docker-compose.office.yml injeta do .env no escritório.
# HTTP_PROXY/HTTPS_PROXY/NO_PROXY são ARGs predefinidos do Docker — apt e pip os usam sozinhos.
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG NO_PROXY=""
ENV HTTP_PROXY=${HTTP_PROXY} HTTPS_PROXY=${HTTPS_PROXY} NO_PROXY=${NO_PROXY}
ENV DEBIAN_FRONTEND=noninteractive

# --- CA corporativa MSIG (proxy FortiGate intercepta TLS) — confiar ANTES de apt/pip ---
# certs/corp-ca.pem = bundle de raízes do Windows (inclui a CA da MSIG). Inofensivo fora da empresa.
# COPY é obrigatório: RUN não enxerga o build context. Registrada aqui, cobre apt, pip e o runtime
# (chamadas HTTPS de saída do app). O `cat >>` funciona mesmo sem update-ca-certificates.
COPY certs ./certs
RUN if [ -f certs/corp-ca.pem ]; then \
      cp certs/corp-ca.pem /usr/local/share/ca-certificates/corp-ca.crt && \
      (update-ca-certificates || true) && \
      cat certs/corp-ca.pem >> /etc/ssl/certs/ca-certificates.crt; \
    fi
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# apt via HTTPS: no escritório o FortiGate intercepta a porta 80 em cleartext e devolve lixo
# ("Bad header data" → apt-get update falha). Em HTTPS o intercept é TLS e a CA acima o torna
# confiável. Troca os mirrors http→https (deb822 do bookworm e/ou sources.list clássico).
RUN for f in /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list; do \
      [ -f "$f" ] && sed -i 's|http://deb.debian.org|https://deb.debian.org|g; s|http://security.debian.org|https://security.debian.org|g' "$f"; \
    done; true

# --- ODBC Driver 17 for SQL Server (repo Microsoft, Debian 12/bookworm) ---
# Necessário pro pyodbc. REMOVA este bloco se o projeto não usa SQL Server (Postgres/sem banco).
# A linha do repo é escrita à mão (um único grupo [ ] com signed-by). NÃO usar o prod.list via sed:
# ele já traz [arch=...], e um segundo [signed-by=...] gera "Malformed entry (URI parse)".
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl gnupg2 apt-transport-https ca-certificates \
 && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
      > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 unixodbc-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Camadas na raiz (docs/ESTRUTURA.md) — um COPY por pasta; remova/adicione conforme o projeto.
COPY main.py ./
COPY config ./config
COPY models ./models
COPY services ./services
COPY routers ./routers
COPY utils ./utils
# COPY templates ./templates      # descomente se tiver UI (Jinja: base + partials)
# COPY pages ./pages              # descomente se tiver UI (telas que estendem o base)
# COPY static ./static            # descomente se tiver UI (assets)

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
