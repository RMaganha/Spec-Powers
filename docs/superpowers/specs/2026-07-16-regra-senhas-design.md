# regra de senhas — segredo via variável de ambiente (design)

Data: 2026-07-16 · feature do próprio kit mss-spec.

## Objetivo
Regra clara de onde mora o segredo: **variável de ambiente** — `.env` gitignored em dev → **Azure App Settings** em prod; o código lê do ambiente, nunca do código/commit. Para SQL Server, é uma **escolha por-projeto** no `/mss-spec:banco` (env-var recomendado; Fernet como opção de continuidade).

## Problema
O padrão atual de SQL cifra a credencial NO CÓDIGO (Fernet, Transportes V2) — mas a chave viaja junto no repo, então é **ofuscação**, não segurança. Como a maioria dos projetos é web app Azure, o caminho óbvio e seguro é a variável de ambiente (App Settings). Precisava virar regra, **sem quebrar** os projetos que já usam Fernet.

## Critérios de aceite
- DADO um projeto novo de SQL Server, QUANDO rodo `/mss-spec:banco`, ENTÃO ele oferece **variável de ambiente (recomendado)** e Fernet (continuidade), e explica a diferença.
- DADO o modo variável de ambiente, ENTÃO a conn string fica em `.env` (dev, gitignored) / App Settings (prod) e o código lê via `os.getenv` — nada de `cryptography`.
- DADO qualquer modo, ENTÃO nenhum segredo entra no **código** nem no **commit**.
- DADO um projeto que já usa Fernet, ENTÃO nada muda nele (o kit não reescreve `get_connection.py` existente).

## Design
- **Regra** escrita em `SEGURANCA.md` §7 e `CLAUDE.md` regra 5: segredo via variável de ambiente (`.env` gitignored dev → App Settings prod); Fernet-no-código é ofuscação, reservado a continuidade.
- **Escolha por-projeto** no `commands/banco.md` (SQL Server): (a) variável de ambiente [recomendado] · (b) Fernet [continuidade].
- `AMBIENTE.md` §4 e a memória do padrão de conexão atualizados.
- **Não-quebra:** só afeta projeto novo / quem optar; existentes intactos.

## Fora de escopo
Migrar projetos existentes automaticamente · Key Vault (fica no checklist Azure como opção pro muito sensível) · Managed Identity (idem, checklist).

## Arquivos tocados
- novo `commands/... ` (não — regra + escolha): `commands/banco.md`, `templates/SEGURANCA.md`, `templates/CLAUDE.md`, `templates/AMBIENTE.md`, `memory/feedback_credencial_reusar_env_precedente.md`

## Histórico
- 2026-07-16 — criado: env-var vira o recomendado (Fernet = opção de continuidade); escolha no `/mss-spec:banco`. Relaxa o "nunca no `.env`" antigo: segredo em `.env` gitignored (dev) é aceito; proibido é no código/commit.
