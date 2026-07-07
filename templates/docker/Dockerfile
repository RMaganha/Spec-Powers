# Imagem standalone. Conecta em serviços existentes via .env (não sobe banco próprio).
# Se usar Tailwind: compile static/css/app.css e comite (sem Node aqui). Ajuste os COPY do app.
FROM python:3.14-slim

WORKDIR /app

# Proxy do pip só no build (não fica no runtime). Vem do build-arg (office.yml / ${HTTP_PROXY} do .env).
ARG PIP_PROXY=

# --- CA corporativa MSIG (proxy FortiGate intercepta TLS) — confiar no certificado ---
# certs/corp-ca.pem = bundle de raízes do Windows (inclui a CA da MSIG). Inofensivo fora da empresa
# (só adiciona CAs confiáveis) e não quebra o build se o arquivo não existir. Entra no store do
# sistema, usado por Python/requests/curl/ODBC.
RUN if [ -f certs/corp-ca.pem ]; then \
      cp certs/corp-ca.pem /usr/local/share/ca-certificates/corp-ca.crt && \
      (update-ca-certificates || true) && \
      cat certs/corp-ca.pem >> /etc/ssl/certs/ca-certificates.crt; \
    fi
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# (OPCIONAL — só se o projeto roda Chrome/Selenium headless: o Chrome no Linux NÃO lê o store do
#  sistema, valida pela base NSS. Descomente pra registrar a CA em /root/.pki/nssdb também.)
# RUN apt-get update && apt-get install -y --no-install-recommends libnss3-tools && rm -rf /var/lib/apt/lists/* \
#  && if [ -f certs/corp-ca.pem ]; then mkdir -p /root/.pki/nssdb \
#     && (certutil -d sql:/root/.pki/nssdb -N --empty-password || true) \
#     && awk 'BEGIN{n=0} /BEGIN CERTIFICATE/{n++} {print >> ("/tmp/ca-"n".pem")}' certs/corp-ca.pem \
#     && for f in /tmp/ca-*.pem; do certutil -d sql:/root/.pki/nssdb -A -t "C,," -n "msig-$(basename "$f" .pem)" -i "$f" || true; done \
#     && rm -f /tmp/ca-*.pem; fi

# Sem o corp-ca.pem em mãos, o pip confiaria nos hosts do PyPI (--trusted-host). Com o CA embutido
# acima, o TLS já é confiável; mantemos os trusted-host como rede de segurança pro proxy.
COPY requirements.txt .
RUN pip install --no-cache-dir ${PIP_PROXY:+--proxy $PIP_PROXY} \
        --trusted-host pypi.org \
        --trusted-host files.pythonhosted.org \
        --trusted-host pypi.python.org \
        -r requirements.txt

COPY app ./app
# COPY templates ./templates      # descomente se tiver UI (Jinja)
# COPY static ./static            # descomente se tiver UI (assets)

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
