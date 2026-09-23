# Travas de publicação e um item por janela — cercas mecânicas contra a janela sequestrada

## Estado atual
Três cercas **mecânicas** (hooks ligados por padrão; a (4), do F-025, veio depois, registrados em `hooks/hooks.json`) e uma regra
dura de conduta, nascidas do caso **F-022** (`docs/EVALS.md`): a janela de UMA feature absorveu dois
outros assuntos, mesclou branches e o assistente disparou `git push` — o gatilho do deploy
automático — várias vezes; a homologação quebrou inteira.

**(1) `hooks/git_publicacao.py`** — `PreToolUse` em `Bash|PowerShell`, **por destino** (0.31.0).
**Nega** `git push` pra branch **protegida** (`main`, `master`, `dev`, `develop`, `production`,
`homolog*`, `hml*`, `prod*`, `release/*`) — por refspec (`origin dev`, `HEAD:dev`, `x:main`,
`--delete main`) ou, sem refspec, pela branch atual e pelo `@{push}` que o git da pasta do comando
responde (`-C` › último `cd` › `cwd`); nega push de destino indeterminável (`--all`, `--mirror`,
`--tags`, `:`, HEAD destacado, git que não responde) e deploy/integração remota (`gh pr merge`,
`docker push`, `az acr build`, `az webapp <escrita>`, `az containerapp update|create|revision`).
**Pede aprovação** (`permissionDecision: "ask"`, exit 0 — o owner vê o comando e aprova) pra
`git merge`, `git rebase` (menos `--abort`) e push de feature/fix. **Libera calado** o resto
(`merge-base`, `merge-tree`, `pull`, status, commit…). Casa o **verbo inteiro no início de um comando
simples** (após `;` `&&` `|` `(` quebra de linha ou prefixo `VAR=x`); negar vence perguntar. **Falha
FECHADA**. Escape só do owner: `MSS_PUBLICACAO_OFF=1`. No push protegido o assistente roda
`/mss-spec:release` e **pede**; o owner publica do terminal dele.

**(2) `hooks/um_item_por_janela.py`** — `UserPromptSubmit`. Só age em `/mss-spec:nova-feature <nome>`
(ou `/nova-feature`). Lê `<cwd>/docs/superpowers/INDEX.md`; linha de item com status `aberta` ou
`em andamento` conta como aberta (`fechada`/`pausada: <motivo>` não; seção "Fora de escopo" ignorada).
Outra aberta → **bloqueia o prompt** listando-as e as três saídas (terminar a aberta; o owner marcar
`pausada` à mão; `to-dolist adicionar`). A mesma (nome ou slug da spec, sem acento/caixa) → passa.
Sem INDEX → passa. **Falha ABERTA**. Escape só do owner: `MSS_UM_ITEM_OFF=1`.

**(3) Prosa que virou trava**: `templates/CLAUDE.md` (linha "Um assunto por janela" deixa de ser
"alerta, não trava": 2º assunto → **não aja**, anote no MAPA, `to-dolist`, janela nova; linha Git:
push em dev/homolog/prod e deploy "nunca você", merge/rebase/push de feature com aprovação) ·
`commands/nova-feature.md` **passo 0** (gate de feature aberta — 2ª camada do hook 2) e fecho (push
protegido é do owner; merge local e push da feature com aprovação) · `commands/diagnostico.md`
passo 3 (**F-023**: saúde de endpoint só com a matriz de variantes do chamador; diff do deploy
inteiro). O molde ficou em **7.991/8.000 bytes** via compressão de prosa (mover/encurtar, nunca apagar).

**(4) Cerca do pipe, no mesmo processo do `git_publicacao.py`** (caso **F-025**): nega o comando que
tem o **pytest como comando** (`pytest`, `py.test`, `<python> -m pytest`) com a saída num `|` e um
`git commit` depois, sem `pipefail` — o exit do pipe é o do último comando, e o commit sairia com a
suíte vermelha. Passam: `pytest && git commit`, `pytest | tail` sem commit, `set -o pipefail; …`,
`pytest` como texto (`grep pytest`) e teste depois do commit. Mora no mesmo hook porque é o mesmo
evento (hook separado = ~190 ms a mais em todo comando de shell), mas com **modo de falha próprio —
ABERTA** (commit vermelho se reverte) e **escape próprio** `MSS_PIPE_TESTE_OFF=1`; a cerca de
publicação é avaliada primeiro e segue FECHADA. Não é "hook de pre-commit bloqueante" (fora de
escopo no INDEX): não roda teste nem trava commit, só recusa o comando que esconde o resultado.

**Custo aceito:** cada merge/rebase/push de feature custa um clique de aprovação do owner; push em
homologação/produção e deploy seguem só dele (o `finishing-a-development-branch` apresenta as
opções e o owner faz esse push). Falso bloqueio conhecido: branch que **começa** com
`prod`/`hml`/`homolog` (ex.: `produto-x`) conta como protegida — use o prefixo `feature/`.

Fora de escopo: detectar mecanicamente "2º assunto no meio da conversa" (não há assinatura de tool;
fica na prosa + no gate de abertura) · tirar a credencial git do assistente (configuração da máquina,
não do kit — complemento opcional do owner) · escape por argumento do assistente (só env do owner).

## Histórico
- 2026-09-14 — criado: análise da sessão "lixo" do projeto MITI (feature de formatação do WhatsApp
  que virou diagnóstico de 400 pra .Blip + flags + merge + pushes). Casos F-022 e F-023. Decisão do
  owner: "regra extremamente dura, 1 item por janela, nova feature somente quando não tiver mais
  features abertas" e "tem que ter outra trava que funcione" — por isso hook, não prosa (F-014 e
  F-015 já eram prosa e não seguraram).
- 2026-09-23 — (4) cerca do pipe no processo do `git_publicacao.py` (motivo: F-025 reincidiu — `edc0ab9` commitou com 2 vermelhos, `f9388e5` repetiu o atalho com a memória já escrita; a própria linha do EVALS pedia cerca). Nasceu da avaliação de duas análises externas do kit: o "release em script" que elas sugeriam não teria pego nenhum dos dois commits (o F-025 acontece na hora do commit, não no release).
- 2026-09-23 — (1) passa a ser por DESTINO (0.31.0) (motivo: o owner — *"a atualização minha no merge está impactando o dia a dia"*; negar todo merge/rebase/push travou o trabalho, inclusive `git merge-base`, que só lê e o registro gravou como `negou · git merge`). O dano do F-022 foi o push que faz deploy: push pra branch protegida, push de destino incerto e deploy seguem negados; merge/rebase/push de feature viram pedido de aprovação (`ask` — escolha do owner entre pedir aprovação e só avisar). Lista de protegidas = regra única, sem configuração (escolha do owner).
