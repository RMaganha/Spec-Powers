# Upgrade — trazer o projeto pra versão atual do kit sem refazer o que é do projeto

## Estado atual
`commands/upgrade.md` (prosa; o assistente executa). Ordem: projeto sem a marca `<!-- mss-spec:regras-do-kit -->` → só a
migração do `CLAUDE.md` (`templates/migrar_claude_md.py`); to-dolist no formato antigo → só a conversão
(`templates/converter_to_dolist.py`); com a marca → três categorias: **1** arquivos só-do-kit (atualiza sozinho),
**2** `CLAUDE.md` / `docs/AMBIENTE.md` / `MAPA.md` / `AMBIENTES.md` / `EVALS.md` (mescla, só conflito real pergunta),
**3** código do projeto (só mostra o diff). `--dry-run` não grava. Rollback é o git.

**Freios da categoria 1**, na ordem em que são lidos:
- **Infra própria** (linha `**Infra:**` do `CLAUDE.md`): `docker-compose.office.yml`, `certs/corp-ca.pem` e proxy não
  entram; o `docker-compose.yml` não ganha a rede `mitiai_network`.
- **Brownfield** (tabela "não nasceu do kit" do `docs/ARQUITETURA.md`): arquivo listado mostra o diff e pergunta.
- **Infra que já roda nunca é reescrita (0.52.0)**: `docker-compose.yml`, `docker-compose.office.yml`, `Dockerfile` e
  `.dockerignore` que **existem** não são tocados, em projeto nenhum — o upgrade só **cria** o que falta (respeitando o
  freio da infra própria); se o molde mudou, mostra o diff e diz "o molde do kit mudou — revise à mão", como na categoria 3.
  Vale pro projeto que nasceu do kit e foi pra homologação/produção, que não é brownfield nem infra própria e caía fora dos
  dois freios anteriores. `certs/corp-ca.pem` **não** está na categoria 1: quem o entrega é o `/mss-spec:ambiente`, e CA
  velha quebra o build (`memory/project_docker_build_fortigate.md`), então ele continua atualizável.

**Na categoria 2 (0.52.0)**: `docs/AMBIENTE.md` que já existe **não ganha seção** do molde — o upgrade diz em 1 linha quais
seções o molde tem e o projeto não, e para; `docs/AMBIENTES.md` que falta nasce do molde com `falta preencher` e **sem
questionário** — 1 linha com a contagem (o `doctor`, check 13, conta). O resto da categoria 2 segue: a linha `**Infra:**`
que falta é perguntada uma vez; o `MAPA.md` ganha só a estrutura; valores do owner nunca são tocados.

Fora de escopo: script pro upgrade (é prosa; a prova é o teste de texto em `tests/test_smoke_kit.py` e o dry-run) ·
3-way merge com a versão antiga do molde · rodar o upgrade nos outros projetos daqui (a conversa do kit só lê os outros,
`docs/decisoes.md:52`).

## Histórico
- 2026-11-03 — criado (0.52.0): o owner, sobre rodar o upgrade nos projetos em homologação e produção — *"ele tenta fazer
  toda a parte de infra novamente … e se perde, isso é irritante"*. A categoria 1 reescrevia os arquivos do Docker sem
  perguntar (`commands/upgrade.md`, linha dos arquivos do Docker); o freio da infra própria não vale em projeto MSIG e o do
  brownfield só com a tabela do `/mss-spec:analise`; o projeto nascido do kit e em produção caía nos dois. Na cópia do
  MSS-SSC: Dockerfile com 143 linhas diferentes do molde, que o upgrade de 0.51.1 reescreveria.
