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
- **Banco de produção: leitura só com o OK do owner, escrita nunca pelo assistente.** Um OK vale a tarefa
  inteira (janela de 2 h, carimbada pelo hook `banco_producao.py` quando o comando executa); DML/DDL de
  produção vira `.sql` entregue ao owner, com o SELECT das linhas afetadas antes e o do estado final depois.
  Os hosts/aliases de produção vêm do `docs/AMBIENTES.md`, seção Produção (linha **Hosts de produção (cerca)**);
  rotina agendada que lê produção se registra em **Rotinas autorizadas em produção (só leitura)**.
- **Rótulo em 100% das consultas a banco vivo:** o bloco de resultado abre com 🟨 **CONSULTA <ambiente>**
  (local/homologação, com o host) ou 🟥 **CONSULTA PRODUÇÃO**. Numa mesma investigação, não misture
  ambientes sem dizer por quê; tabela que não existe em produção se diz, nunca se completa com homologação.

Memória de origem: `memory/feedback_credencial_reusar_env_precedente.md` ·
`memory/project_kit_nao_assume_ambiente_de_origem.md`
