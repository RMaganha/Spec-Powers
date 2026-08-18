---
paths:
  - "**/*.sql"
  - "**/db/**"
  - "**/*banco*.py"
  - "**/*conn*.py"
  - "**/*repositor*.py"
---

# Banco e segredo

- **SQL sempre parametrizado.** Nada de concatenar valor em string de query.
- **DDL não passa pelo app**: vai versionada em `sql/NN_*.sql`, revisada pelo owner e rodada **fora**
  da aplicação. O app não cria nem altera esquema.
- **Credencial só por variável de ambiente** (`.env` no dev → App Settings no deploy). Nunca no
  código, nunca no commit, nunca pedida digitada no chat. Fernet-no-código é ofuscação, não
  segurança — só entra como opção de continuidade, decidida no `/mss-spec:banco`.
- A conexão respeita a linha `**Infra:**` do `CLAUDE.md` — não presuma SQL Server corporativo.

Memória de origem: `memory/feedback_credencial_reusar_env_precedente.md` ·
`memory/project_kit_nao_assume_ambiente_de_origem.md`
