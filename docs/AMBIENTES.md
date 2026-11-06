<!-- AMBIENTES do projeto — um lugar só para "onde roda, com que valores, quem acessa o quê".
     Copiado pelo /mss-spec:kickoff (e criado pelo /mss-spec:upgrade quando falta); o OWNER preenche e mantém.
     O kit lê quando a conversa cita local, homologação, produção, servidor, variável ou App Setting:
     o recall aponta a seção, e o passo 1 do /mss-spec:bug, /mss-spec:duvida e /mss-spec:diagnostico a abre.
     Regras do arquivo:
     - SEGREDO NUNCA ENTRA (senha, token, connection string com senha): valor `*****` + onde vive.
     - Valor não conferido: `falta preencher`. Toda linha de valor diz quem leu e quando.
     - Um ambiente por seção `## `; o nome da seção é o que o owner usa na conversa (local · homologação · produção).
     - Nada de documento paralelo: mudou o valor no ambiente, muda aqui na mesma tarefa. -->

# Ambientes — mss-spec

> Infra em geral (proxy, rede Docker, CA, Azure): `docs/AMBIENTE.md` — este repo **não tem** (é o kit, não um
> serviço; `**Infra:** própria — nenhuma` no `CLAUDE.md`). Aqui é só **cada ambiente**: o que é,
> como se chega, quem acessa, e as variáveis com os valores.

## Local

- **O que é:** este clone em `C:\Ronaldo\_Mitsui\Python\Spec-Powers`, carregado pelo Claude Code pela junção
  `~/.claude/skills/mss-spec` → clone (`docs/LEIA-ME.md`, "Instalação"). O marketplace `mss-local` e
  `enabledPlugins["mss-spec@mss-local"]` já estão registrados no `~/.claude/settings.json`, mas sem entrada em
  `~/.claude/plugins/installed_plugins.json` (escolha A, `docs/superpowers/PROXIMO-PASSO.md`, passo 2 — conferido
  pelo `doctor` em 2026-11-03).
- **Como o assistente lê/roda:** suíte `python -m pytest tests/ -q` (`docs/LEIA-ME.md`); hooks registrados em
  `hooks/hooks.json`; scripts dos moldes em `templates/*.py`.
- **Como atualiza depois de uma mudança no clone:** pela junção a edição vale na janela seguinte (o app lê o clone);
  pelo marketplace local, `falta preencher` — conferir o comando no primeiro uso, não inventar
  (`docs/superpowers/PROXIMO-PASSO.md`, passo 4).
- **Quem acessa:** owner: sim · assistente: sim (leitura e escrita local; git: branch e commit sim, push não).
- **Lido por / quando:** assistente, 2026-11-03 (de `docs/LEIA-ME.md`, `hooks/hooks.json`, `docs/superpowers/PROXIMO-PASSO.md`).

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `LC_ALL` | `enu` — o bash não conhece; todo hook imprime `setlocale` no stderr (`doctor`, check 12: remover ou pôr `C.UTF-8`) | variável de ambiente do Windows | assistente, 2026-11-03 (`echo $LC_ALL`) |
| `HTTPS_PROXY` / `HTTP_PROXY` | `http://127.0.0.1:3128` | `~/.claude/settings.json`, bloco `env` | assistente, 2026-11-03 |
| `NO_PROXY` | `localhost,127.0.0.1` | `~/.claude/settings.json`, bloco `env` | assistente, 2026-11-03 |
| `MSS_TETO_OFF` | não definida — escape consciente, só do owner, do hook `hooks/teto_ao_gravar.py` | ambiente do shell | assistente, 2026-11-03 |

## Homologação

- **O que é:** não existe — o kit não tem ambiente intermediário. A prova antes de publicar é a suíte local
  e o dogfood nos projetos que usam o kit (`docs/EVALS.md`).
- **Como o assistente lê:** não se aplica.
- **Quem acessa:** não se aplica.
- **Lido por / quando:** assistente, 2026-11-03.

## Produção

- **O que é:** o repositório publicado no GitHub — `https://github.com/RMaganha/Spec-Powers.git`, branch `main`
  (`origin/main`). É de onde o time instala e atualiza o kit (`/plugin marketplace add …` ·
  `/plugin marketplace update mss-local`, `docs/LEIA-ME.md`, "Via git"). O `.gitlab-ci.yml` é só referência:
  não roda no GitHub (comentário no topo do próprio arquivo).
- **Como o assistente lê:** `git fetch` + `git show origin/main:…` (check 11 do `doctor`); nunca faz push.
- **Quem acessa:** owner: push sim (`git push origin main`, do terminal dele) · assistente: só leitura — `git push`
  pra `main` é negado pelo hook `hooks/git_publicacao.py` (`memory/feedback_publicacao_e_ato_do_owner.md`) ·
  time: instala por URL (leitura).
- **Hosts de produção (cerca):** nenhum — o kit não tem banco; o hook `hooks/banco_producao.py` fica calado aqui.
- **Rotinas autorizadas em produção (só leitura):** nenhuma.
- **Lido por / quando:** assistente, 2026-11-03 (de `docs/LEIA-ME.md`, `.gitlab-ci.yml`, `memory/feedback_publicacao_e_ato_do_owner.md`).

Variáveis: nenhuma — o kit publicado não tem configuração própria; a versão vive nos dois manifestos
`.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json` (`memory/project_versao_em_dois_manifestos.md`).

<!-- Exemplo real (Whats, 2026-10-30) do que uma linha evita: o assistente passou 20 min sem saber se
     `N8N_WHATSAPP_PUSH_URL` de produção era o host certo e mandou o owner abrir o Kudu de produção, que ele
     não acessa. Com a seção "Produção" preenchida:
     | `N8N_WHATSAPP_PUSH_URL` | `https://mitiai-n8n.msig.com.br/webhook/mitiai-push-especialista` | App Setting do Web App `mss-miti-ai-agent-bot-webwhats-prod` | owner, 2026-10-30 |
     e a linha "Quem acessa: owner: Portal não, Kudu não", a resposta é uma linha, com fonte. -->
