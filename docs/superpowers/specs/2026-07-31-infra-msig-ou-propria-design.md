# infra MSIG ou própria — design

Data: 2026-07-31 · feature do próprio kit mss-spec.

## Estado atual
O kit **pergunta**, na constituição do projeto, se ele roda na **infra MSIG** (rede Docker
`mitiai_network` · proxy do escritório · CA do FortiGate · SQL Server corporativo) ou tem **infra
própria** — e a resposta manda no scaffolding. Antes disso o kit **assumia** MSIG em todo projeto:
copiava a CA e o compose do escritório, punha proxy no `.env`, oferecia o `get_connection.py` das
bases corporativas, e o `/mss-spec:doctor` cobrava proxy/CA/rede que num projeto de fora não
existem — ruído que treina o owner a ignorar o doctor.

A resposta vive numa **linha do `CLAUDE.md`** (Contexto): `**Infra:** MSIG | própria`. Escolha
deliberada: é o arquivo que já está em contexto em toda sessão, então todo comando a lê sem
procurar e sem formato de configuração novo. Quem grava é o `/mss-spec:kickoff`; pra mudar depois,
edita-se a linha.

Com **infra própria**, cinco coisas mudam — e só elas:
1. **CA** — `certs/corp-ca.pem` não é copiado (`kickoff`, `ambiente`).
2. **docker office** — `docker-compose.office.yml` não é copiado; e o `docker-compose.yml` **base**
   sai **sem a rede externa `mitiai_network`** (consequência necessária: fora da MSIG essa rede não
   existe e o serviço não subiria).
3. **proxy** — sem `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` no `.env`/`.env.example` e sem a prosa das
   4 camadas de proxy/TLS (ela descreve a MSIG). O `SSL_VERIFY` fica: é genérico.
4. **conexão de banco** — o `/mss-spec:banco` vai direto ao caminho genérico (string em variável de
   ambiente), sem par Fernet do Transportes V2 e sem as bases corporativas (SSC/MS10/TRP/OnBase).
5. **doctor** — os checks de proxy, CA e rede `mitiai_network` são **pulados** ("pulado — infra
   própria"), não ✗ nem "a verificar": check inaplicável não é pendência.

O `/mss-spec:upgrade` respeita a declaração nas duas pontas: **não reintroduz** os arquivos MSIG num
projeto de infra própria (a categoria 1 sobrescreve sem perguntar — sem o freio, ela desfaria o
kickoff a cada rodada) e, ao mesclar o `CLAUDE.md` de um projeto anterior a esta versão,
**acrescenta a linha perguntando** ao owner, com `<MSIG | própria — a confirmar>` até ele responder
— assumir MSIG em silêncio é o erro que a feature conserta.

O `docs/AMBIENTE.md` continua sendo copiado em ambos os casos; em infra própria ele leva uma nota no
topo dizendo que as seções de rede/proxy/CA são **referência da MSIG** e não descrevem este projeto.

## Critérios de aceite
- **CA1** — DADO o `/mss-spec:kickoff`, QUANDO leio o comando, ENTÃO ele pergunta na entrevista se a
  infra é MSIG ou própria e grava a resposta na linha `**Infra:**` do `CLAUDE.md`, sem adivinhar.
- **CA2** — DADO `templates/CLAUDE.md`, ENTÃO a linha `**Infra:**` existe no Contexto, nomeia o que
  MSIG implica (`mitiai_network`, FortiGate) e o que **não** se aplica em infra própria (proxy,
  `docker-compose.office`, `get_connection`).
- **CA3** — DADO infra própria, QUANDO leio `kickoff`/`ambiente`, ENTÃO nenhum dos dois copia
  `corp-ca.pem` ou `docker-compose.office.yml`, e o compose base sai sem a rede externa.
- **CA4** — DADO infra própria, QUANDO leio `banco`, ENTÃO o padrão MSIG de conexão não é oferecido.
- **CA5** — DADO infra própria, QUANDO leio `doctor`, ENTÃO proxy/CA/rede são **pulados**, não ✗.
- **CA6** — DADO infra própria, QUANDO leio `upgrade`, ENTÃO a categoria 1 não reintroduz os
  arquivos MSIG, e a mescla do `CLAUDE.md` acrescenta a linha **perguntando**.
- **CA7** — DADO a suíte, QUANDO rodo `python -m pytest -q`, ENTÃO os 5 testes de wiring novos
  passam e a suíte fica 100% verde.

## Design
Comando-prosa não se testa como código (é markdown que o assistente executa) — o gate é **wiring no
smoke**, como no resto do kit. Nada de flag em código, nada de arquivo de config: **uma linha
declarada + os comandos obedecendo**.

## Fora de escopo
Transformar o `docs/AMBIENTE.md` em documento da infra própria (ele fica como referência MSIG, com
nota) · **detectar** a infra sozinho (é pergunta ao owner — adivinhar pelo nome do projeto é
exatamente o tipo de chute que o kit proíbe) · ODBC e Azure, já condicionais a "usa SQL Server" /
"é Azure", que não dependem da rede · `/mss-spec:compliance` deixar de cobrar itens MSIG (não veio
no escopo; entra se aparecer no uso real).

## Arquivos tocados
- `templates/CLAUDE.md` (linha `**Infra:**` no Contexto)
- `commands/kickoff.md` (pergunta na entrevista + o que muda no scaffolding)
- `commands/ambiente.md` (passo 0: lê a linha; sem CA/office/proxy/rede externa)
- `commands/banco.md` (passo 0: caminho genérico em infra própria)
- `commands/doctor.md` (checks 4/5/6 pulados)
- `commands/upgrade.md` (freio da categoria 1 + a linha nova entra perguntando)
- `tests/test_smoke_kit.py` (5 testes de wiring, CA1–CA6)

## Histórico
- 2026-07-31 — criado: nasceu de duas pontas que se encontraram. A anotação de 28/07 no to-dolist
  ("perguntar na constituição se o projeto segue a arquitetura de rede MSIG") e o comentário do
  owner ao fechar o mapa neural: *"tem 2 projetos que não são MSS, então não entra certs, compose
  office e algumas partes de arquitetura da MSS"*. Escopo cravado por ele — **proxy, CA, docker
  office e `get_connection`**; a rede externa `mitiai_network` no compose base entrou porque sem
  ela a entrega ficaria quebrada (o serviço não sobe), e foi declarada antes de implementar. Lugar
  da declaração: o `CLAUDE.md`, que já está sempre em contexto — sem formato de configuração novo,
  seguindo a preferência registrada do owner por regra única sobre mecanismo declarativo.
