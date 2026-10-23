---
paths:
  - "apis/**"
  - "chat_server.py"
  - "services/**"
---

# Segurança

<!-- Movido do CLAUDE.md em 2026-09-23 (teto de 10 KB; F-029/F-030 do kit): texto VERBATIM. A regra continua valendo — o CLAUDE.md mantém a frase-chave e aponta pra cá. -->

5. **Segurança (secure-by-default)** — o app fica exposto na nuvem; trate como alvo. **Prod**: default-deny + autorização no **backend** por request (o front nunca autoriza). SQL **sempre** parametrizado; entrada validada (Pydantic); **upload** checado (tipo/tamanho). O **browser nunca** vê segredo nem URL interna (assuma leitura total do bundle) — segredo só via variável de ambiente em runtime (`.env` gitignored em dev, Azure App Settings em prod), nunca no código nem no commit. Sem stack trace/erro verboso pro cliente e sem PII/segredo em log. Headers de segurança + HTTPS-only (prod) + CORS fechado. **Obscuridade não é segurança** (não criptografar/ofuscar URL de asset). Deps sem CVE. Endpoints de **integração** (outro sistema chama) exigem `Authorization: Bearer` (`TOKEN_API` no `.env`, server-to-server), ligados por `AUTH_TOKEN_ATIVO` (false em dev, true em prod). **Detalhe e checklist em `docs/SEGURANCA.md`; auditoria com `/mss-spec:seguranca`.**
