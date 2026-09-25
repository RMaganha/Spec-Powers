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

**(2) `hooks/um_item_por_janela.py`** — `UserPromptSubmit`, **por chat** (0.34.0). Só age em
`/mss-spec:nova-feature <nome>` (ou `/nova-feature`); o nome é o resto da linha do comando. Guarda
`session_id + projeto → feature` (+ quantas linhas estavam fechadas) em `~/.claude/mss-spec/um-item-janelas.json`
(por máquina, fora do repo; parado há mais de 30 dias sai, retomar renova; `MSS_UM_ITEM_ESTADO` troca o
caminho). Ligação chat → linha: a linha do chat é achada **só pelo nome**, por palavra inteira (`ui` não casa com `guia`; nome de 1 palavra só casa igual), e **encerrada** só se toda linha que casa estiver `fechada`/`pausada` (a `v1` fechada não encerra a `v2` nem a `busca vetorial hibrida` abertas). Linha nova em que nenhum nome contém o outro **não** é atribuída ao chat — o INDEX não diz qual chat a escreveu. Sem linha pelo nome, a feature do chat só conta como encerrada se nada está aberto no INDEX e alguma linha fechou desde a abertura; senão bloqueia dizendo que não achou a linha (custo aceito: título do passo 3 sem que um nome contenha o outro + outra feature aberta → o chat sai por chat novo). **Bloqueia o prompt** quando **este chat** já abriu a feature Y,
Y não está `fechada`/`pausada: <motivo>` (no INDEX ou no `INDEX-historico.md`; Y fora do INDEX segue
valendo — a linha nasce no passo 3) e o pedido é outra: manda abrir **chat novo**, continuar Y, o
owner marcar Y `pausada` à mão ou `to-dolist adicionar`. **Chat novo** com feature `aberta`/`em
andamento` de outro assunto no INDEX (fora de `## Backlog` e "Fora de escopo") → **passa com aviso**
(lista + worktree: duas features na mesma pasta trocam a branch uma da outra), via `systemMessage` +
`additionalContext`. A mesma (nome ou slug, sem acento/caixa), sem nome, sem `session_id`, sem INDEX →
passa calado. **Falha ABERTA** (estado ilegível → vazio). Escape só do owner: `MSS_UM_ITEM_OFF=1`.

**(3) Prosa que virou trava**: `templates/CLAUDE.md` (linha "Um assunto por janela" deixa de ser
"alerta, não trava": 2º assunto → **não aja**, anote no MAPA, `to-dolist`, janela nova; linha Git:
push em dev/homolog/prod e deploy "nunca você", merge/rebase/push de feature com aprovação) ·
`commands/nova-feature.md` **passo 0** (gate "um chat, uma feature" — 2ª camada do hook 2) e fecho (push
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
- 2026-09-24 — (2) passa a contar por CHAT (`session_id`), não por projeto (0.34.0) (motivo: o owner — *"novamente hook bloqueando os comandos, nunca sei quando devo usar ou se posso abrir um chat novo"*; no Whats, 6 features abertas em outros chats travavam o `nova-feature` do chat novo, e ele passou a tirar o comando do prompt — o ritual deixava de rodar, como no F-030). O dano do F-022 é a MESMA janela absorvendo outro assunto: isso segue bloqueado; feature aberta de outro chat vira aviso com worktree. Escolha do owner entre por chat, por projeto com mensagem melhor e deixar como está. Rejeitado: ler o transcript pra saber o que o chat abriu (o formato não é contrato) e bloquear quando outro chat tem feature na mesma pasta (fica aviso — premissa declarada, sem fonte).
- 2026-09-25 — (2) a ligação chat → linha do INDEX passa a ser só pelo nome, por palavra inteira, a que casa melhor vence (motivo: a revisão de código reproduziu 7 cenários — o chat seguia travado depois de fechar a própria feature quando o passo 3 gravava título diferente do digitado, e o casamento por pedaço de texto deixava a `v1` fechada ou um `UI` fechado encerrar a feature aberta do chat, soltando o F-022). Junto: comando sozinho na linha não grava o parágrafo como nome, chave `chat + projeto`, retomar renova a validade, `.tmp` órfão removido.
- 2026-09-25 — (2) sai a "foto do INDEX" que atribuía ao chat as linhas nascidas depois da abertura (motivo: a 2ª revisão reproduziu o chat preso pela linha aberta do vizinho na mesma pasta e o chat A "retomando" a feature do chat B — o INDEX não diz qual chat escreveu a linha). Fica o que dá pra afirmar: linha pelo nome; sem ela, encerrada só se nada está aberto e algo fechou desde a abertura. Brechas aceitas e declaradas: reabrir feature já `fechada` conta como encerrada até o passo 3 reabrir a linha; comando sem nome na linha passa calado; retomar por subconjunto aceita a feature vizinha (`exportar pdf` × `exportar pdf assinado`).
- 2026-09-25 — (2) "encerrada" passa a olhar toda linha que casa pelo nome, não só a que casa melhor (motivo: 3ª revisão — evoluir feature já fechada: a v1 `busca vetorial` fechada, nome exato, encerrava a `busca vetorial hibrida` aberta do próprio chat e o F-022 passava). Custo aceito: linha aberta do vizinho que case pelo nome segura o chat.
