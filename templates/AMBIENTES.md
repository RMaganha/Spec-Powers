<!-- AMBIENTES do projeto — um lugar só para "onde roda, com que valores, quem acessa o quê".
     Copiado pelo /mss-spec:kickoff (e criado pelo /mss-spec:upgrade quando falta); o OWNER preenche e mantém.
     O kit lê quando a conversa cita local, homologação, produção, servidor, variável ou App Setting:
     o recall aponta a seção, e o passo 1 do /mss-spec:bug, /mss-spec:duvida e /mss-spec:diagnostico a abre.
     Regras do arquivo:
     - SEGREDO NUNCA ENTRA (senha, token, connection string com senha): valor `*****` + onde vive.
     - Valor não conferido: `falta preencher`. Toda linha de valor diz quem leu e quando.
     - Um ambiente por seção `## `; o nome da seção é o que o owner usa na conversa (local · homologação · produção).
     - Nada de documento paralelo: mudou o valor no ambiente, muda aqui na mesma tarefa. -->

# Ambientes — <projeto>

> Infra em geral (proxy, rede Docker, CA, Azure): `docs/AMBIENTE.md`. Aqui é só **cada ambiente**: o que é,
> como se chega, quem acessa, e as variáveis com os valores.

## Local

- **O que é:** <ex.: `docker compose` na máquina do owner; banco em `host.docker.internal:5432`>
- **Como o assistente lê/roda:** <ex.: `docker compose run --rm --no-deps -T <servico> …`; suítes com os bancos isolados>
- **Quem acessa:** owner: sim · assistente: sim (leitura e escrita local)
- **Lido por / quando:** <owner, AAAA-MM-DD>

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `<CHAVE>` | `<valor>` | `.env` | <owner, AAAA-MM-DD> |
| `<CHAVE_SECRETA>` | `*****` | `.env` | <owner, AAAA-MM-DD> |

## Homologação

- **O que é:** <ex.: Web App `<nome>-dev-br` (grupo `RG-…-DEV`); Postgres `<servidor>-dev-br…`; branch `dev` publica>
- **Como o assistente lê:** <ex.: banco pelo túnel, chave `BANCO_HML` do `sql/.env`, só leitura>
- **Quem acessa:** owner: Portal <sim/não>, Kudu <sim/não>, banco <como> · assistente: <só leitura pelo túnel>
- **Lido por / quando:** <owner, AAAA-MM-DD>

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `<CHAVE>` | `<valor>` | App Setting do Web App `<nome>` | <owner, AAAA-MM-DD> |
| `<CHAVE_SECRETA>` | `*****` | App Setting do Web App `<nome>` | <owner, AAAA-MM-DD> |

## Produção

- **O que é:** <ex.: Web App `<nome>-prod` (grupo `RG-…-PRD`, restrito à infra); Postgres `<servidor>-prod-br…`; branch `main` publica>
- **Como o assistente lê:** <ex.: banco pelo túnel, chave `BANCO_PRD` do `sql/.env`, só leitura; nunca Kudu/Portal>
- **Quem acessa:** owner: Portal <sim/não>, Kudu <sim/não>, banco <como> · infra: <o quê> · assistente: <só leitura pelo túnel>
- **Lido por / quando:** <owner, AAAA-MM-DD>

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `<CHAVE>` | `<valor>` | App Setting do Web App `<nome>` | <owner, AAAA-MM-DD> |
| `<CHAVE_SECRETA>` | `*****` | App Setting do Web App `<nome>` | <owner, AAAA-MM-DD> |

<!-- Exemplo real (Whats, 2026-10-30) do que uma linha evita: o assistente passou 20 min sem saber se
     `N8N_WHATSAPP_PUSH_URL` de produção era o host certo e mandou o owner abrir o Kudu de produção, que ele
     não acessa. Com a seção "Produção" preenchida:
     | `N8N_WHATSAPP_PUSH_URL` | `https://mitiai-n8n.msig.com.br/webhook/mitiai-push-especialista` | App Setting do Web App `mss-miti-ai-agent-bot-webwhats-prod` | owner, 2026-10-30 |
     e a linha "Quem acessa: owner: Portal não, Kudu não", a resposta é uma linha, com fonte. -->
