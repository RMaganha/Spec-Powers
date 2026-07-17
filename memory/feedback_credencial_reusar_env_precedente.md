---
name: credencial-reusar-env-precedente
description: Segredo de conexão — env-var (recomendado pra web app Azure: .env dev → App Settings prod) OU Fernet-no-código (continuidade, é ofuscação); escolha por-projeto no /mss-spec:banco; nunca pedir credencial digitada nem pôr segredo no código/commit
metadata:
  type: feedback
---

Feedbacks do owner sobre onde mora a credencial de conexão (SQL Server).

**Origem (2026-07-08, MSS-SSC):**
1. O assistente criou `.env` e pediu usuário/senha digitados — mas a credencial já existia na
   máquina. "Lá já tem tudo!!!" → nunca pedir credencial digitada; reusar o que já conecta.
2. Padrão canônico da casa era o `get_connection.py` multi-ambiente do Transportes V2: par Fernet
   KEY/CIPHERTEXT por base e ambiente (DEV/D0 · HML/HI · PROD) embutido no arquivo; `.env` só com
   `CONEXAO_SQL` (D0|HML|PRD) + `CONEXAO_SQL_PORTA` (opcional). Comentário no `.env` SEMPRE em linha
   própria (inline o Docker Compose passa junto do valor e quebra).

**Evolução (2026-07-16) — feature "regra de senhas":** pra **projeto novo** (web app Azure, a
maioria), o recomendado passou a ser a credencial como **variável de ambiente** — `.env` gitignored
em dev → **Azure App Settings** em prod; o código lê via `os.getenv`. Motivo: o Fernet com a chave
junto no repo é só **ofuscação** (quem tem o repo decifra), não segurança. O **Fernet vira OPÇÃO de
continuidade** (projetos que já usam), não o padrão. A escolha é **por-projeto** no `/mss-spec:banco`.
Ou seja, o "no `.env` no máximo o ambiente" **relaxou**: segredo em `.env` **gitignored** (dev) agora
é aceito — o que NÃO pode é segredo no **código/commit**. Projetos atuais ficam intactos (o kit não
reescreve `get_connection.py` existente; o `/mss-spec:upgrade` trata código como advisory).

**How to apply:** conexão SQL nova → `/mss-spec:banco` oferece (a) **variável de ambiente
[recomendado]** — conn string no `.env`/App Settings, lida via `os.getenv`, sem `cryptography`; ou
(b) **Fernet [continuidade]** — copiar `templates/get_connection.py`, pares por base/ambiente no
código. Base MSIG conhecida (SSC, MS10=`tkgs_corp`, TRP, OnBase) → apontar constantes no Transportes
V2 pro owner colar (copiar credencial entre projetos é decisão DELE); base nova → gerar par
localmente, sem ecoar segredo. Nunca conn string em texto plano no chat (usar `mask_password`).
Portas verificadas (2026-07-08): SSC dev `10.170.210.36,1435`; `tkgs_corp`/`MSS_TRP` dev sem porta;
SSC prod `10.170.210.48`. Erro 53/timeout fora da rede corporativa é rede, não credencial.
Relacionado: [[nao-inventar-fatos-concretos]].
