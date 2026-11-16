# Ao mexer em banco, segredo ou rota

- **quando configurar conexão de banco ou segredo** → [Env-var (recomendado) ou Fernet](../feedback_credencial_reusar_env_precedente.md) — nunca no código nem no commit
- **quando criar/alterar rota ou revisar segurança** → [Segurança AppSec no kit](../project_seguranca_appsec_kit.md) — baseline `SEGURANCA.md`; integração = Bearer
- **quando a conexão com o SQL Server falhar com o erro 18456** → [18456 é autenticação, não rede](../reference_sql_18456_e_autenticacao.md) — a conexão chegou; confira usuário e senha, não a porta
