---
paths:
  - "**/api/**"
  - "**/routes/**"
  - "**/app.py"
  - "**/main.py"
  - "**/views.py"
---

# Rota e endpoint

- Toda rota nova passa pelo baseline de `docs/SEGURANCA.md`: **autorização**, **entrada validada**,
  e erro que não vaza stack nem caminho interno.
- Rota de **integração** (outro sistema chama) exige Bearer — `TOKEN_API` sob a chave
  `AUTH_TOKEN_ATIVO`. Obscuridade não é segurança: o front é público por definição.
- Rota nova ou alterada que outro projeto consome → atualize a seção **Conexões** do
  `docs/superpowers/MAPA.md`, declarando **do código real**.
- Não invente caminho, host ou nome de recurso: use o que está no repo ou pergunte ao owner.

Memória de origem: `memory/project_seguranca_appsec_kit.md` ·
`memory/feedback_nao_inventar_fatos_concretos.md`
