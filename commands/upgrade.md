---
description: Sincroniza os arquivos do kit no projeto com a versão atual dos templates, TUDO NUMA RODADA e numa conversa — migração do CLAUDE.md, conversão do to-dolist e as 3 categorias, na ordem, uma branch e um commit por passe; atualiza os de referência sozinho e MESCLA CLAUDE.md/AMBIENTE.md sem perder o seu (só conflito real pergunta)
argument-hint: "[--dry-run]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Traz o projeto pra versão atual do kit: compara cada arquivo que veio do kit com o template correspondente em `${CLAUDE_PLUGIN_ROOT}/templates/` e reconcilia com **o mínimo de interação** — só **conflito real** chama o owner.

**Uma rodada, uma conversa (0.54.0).** O upgrade tem até três passes — **migração do `CLAUDE.md`** → **conversão do to-dolist** → **categorias 1-3** — e trata **todos os que se aplicam nesta mesma conversa, nesta ordem**, numa branch só, com **um commit por passe** (é o commit que mantém o `git diff` de cada passe separado, não uma conversa nova). **Nunca** peça conversa nova nem "próxima rodada" entre passes. Até a 0.53.0 cada passe terminava sozinho e exigia árvore limpa de novo: no Transportes V2 (2026-11-09) isso virou 3 conversas paradas na mesma pergunta sobre 3 arquivos modificados sem commit em outra branch.

## Abertura: o que o projeto precisa

Rode `python "${CLAUDE_PLUGIN_ROOT}/templates/upgrade_plano.py" checar --proj "<raiz do projeto>"` (só lê; a raiz por extenso, não depende da pasta em que o shell está). Ele imprime:

- a **1ª linha do status**, que você repete ao owner tal e qual — `migração do CLAUDE.md ✓/⬜ · to-dolist ✓/⬜ · categorias ⬜`;
- os **passes que se aplicam, na ordem** (migração só sem a marca `<!-- mss-spec:regras-do-kit -->`; to-dolist só com achado do `converter_to_dolist.py checar`; categorias sempre);
- a **situação do git**, num bloco só: branch atual, principal (`main`/`master`), se há remoto, arquivos **modificados** e **não rastreados**.

Abra a conversa com essas três coisas e o roteiro de git abaixo, e **peça um único OK** pra rodada inteira. Pergunta nova só em conflito real (categoria 2) e nos OKs que cada passe já pede (prévia da conversão do to-dolist; diff do que a categoria 1 vai sobrescrever, se o owner quiser ver). Nada de descrever o trabalho interno a cada item (caso **F-038**).

## Git: uma branch, trabalho pendente guardado uma vez

Quem executa segue a **regra de git do projeto** (a linha `Versionamento` do `## Contexto` do `CLAUDE.md`, ou o documento que ela aponta). **Padrão do kit**: o assistente roda os comandos. **Projeto que reserva o git ao owner**: o assistente **não escreve no git** — entrega cada comando **um por bloco**, na ordem, e confirma com leitura (`git branch --show-current`, `git status --short`) antes de seguir. O roteiro é o mesmo nos dois casos:

0. **Trabalho pendente do owner — guardar UMA vez, com o OK dele, nunca commitar.** Árvore suja (o `checar` listou modificados)? `git stash push -m "mss-spec upgrade: pendente de <branch atual>"` guarda os **modificados**; os **não rastreados** ficam no lugar (o upgrade não os toca; se um deles tiver o mesmo nome de um arquivo que o upgrade criaria, é o freio "do que já roda" — não é criado). Anote a branch em que o owner estava: é pra ela que tudo volta no fim. Árvore limpa → pule. **Não** proponha "commitar e seguir": o trabalho é dele, e o commit é dele.
1. **A branch, uma só.** Vá pra principal, atualize-a (`git pull --ff-only`, só se há remoto) e crie **`chore/upgrade-kit`** a partir dela. Toda gravação desta rodada é nela.
2. **Um commit por passe**, com `git add` **pelo nome** de cada arquivo que o passe gravou (nunca `-A` nem `.`): `chore(upgrade): migra o CLAUDE.md pras regras do kit no plugin` · `chore(upgrade): to-dolist no git como estava` + `chore(upgrade): to-dolist e fora de escopo no desenho do kit` (a conversão tem dois tempos, cada um com o seu commit — é a promessa de voltar atrás pelo git) · `chore(upgrade): arquivos do kit na versão <versão do plugin.json>` (categorias). O hook `teto_ao_gravar.py` moveu linhas do MAPA/INDEX ao gravar? Commit **à parte**, pra não misturar com o passe (aconteceu no Transportes: 34 linhas, `git revert` desfaz só ele).
3. **No fim, integrar e devolver** — seção "Fecho", abaixo.

## Modo `--dry-run` (preview, não toca em arquivo)

Se `$ARGUMENTS` contém `--dry-run`, rode em modo **preview**: a abertura inteira (status, passes, situação do git) e, pra cada passe, exatamente o que o upgrade *faria* — mas **não escreve nenhum arquivo** nem mexe no git (sem stash, sem branch, sem commit). O working tree fica intacto. É opt-in (a flag é aditiva; sem ela, o upgrade aplica como sempre). Serve pra prevenir o merge silencioso da categoria 1, que é aplicado sozinho sem o owner ver o que mudou.

No preview:
- **Migração do `CLAUDE.md`:** a prévia do `migrar_claude_md.py` (sem `--aplicar`).
- **To-dolist:** as prévias do `liberar` e do `converter` (sem `--aplicar`).
- **Categoria 1 (referência):** para cada arquivo desatualizado, mostre o **diff unificado** (git-style, template novo × arquivo atual) do que *seria* sobrescrito. Este é o passo hoje silencioso — o alvo da prevenção.
- **Categorias 2 e 3 (`CLAUDE.md`/`AMBIENTE.md` e código):** o mesmo relatório descritivo de sempre (o que seria mesclado · conflitos que dependeriam do owner · código a revisar à mão), sem escrever nada.

Ao fim, **deixe explícito que foi só preview** e diga como aplicar de verdade: rode `/mss-spec:upgrade` **sem a flag**. Não faça nenhuma edição, `git add` nem commit no dry-run.

## Passe 1 — projeto sem a marca → migração do `CLAUDE.md`

O `checar` disse `migração do CLAUDE.md ✓`? O projeto já migrou: pule pro passe 2. Disse `⬜`? As regras do kit ainda estão copiadas no `CLAUDE.md` (sem a marca `<!-- mss-spec:regras-do-kit -->`, o plugin não entrega regra nenhuma). Faça a migração **primeiro**, num commit só dela — o `CLAUDE.md` muda de formato, e misturar com as categorias esconderia a mudança no `git diff`.

  1. Rode `python "${CLAUDE_PLUGIN_ROOT}/templates/migrar_claude_md.py" --proj "<raiz do projeto>"` (dry-run; a saída começa com "Prévia"). Mostre o relatório ao owner: quantas linhas saíram por serem do kit, quantas mudaram de lugar, quais ficaram por dúvida, e o aviso de teto se houver.
  2. Saiu com falha (a saída lista o que não fechou; árvore suja nos arquivos que ele toca também é falha — por isso o stash vem antes) → **nada foi gravado**: repasse a lista e **siga pro passe 2** sem a migração; o relatório do fim diz que ela ficou pendente e por quê. Com `--dry-run`, pare neste passe de qualquer jeito.
  3. Sem falha → rode `python "${CLAUDE_PLUGIN_ROOT}/templates/migrar_claude_md.py" --aplicar --proj "<raiz do projeto>"`. Ele grava e para: **não mexe no git**.
  4. Commit do passe (regra de git do projeto): `git add` **pelo nome** de cada arquivo que o script gravou e `git commit`. Desfazer antes de commitar: `git restore <os arquivos que o script gravou>`.
  5. **Siga pro passe 2, nesta conversa.** A marca já está lá: as categorias vão achá-la.

## Passe 2 — to-dolist e fora de escopo no formato antigo → conversão

Desde a 0.47.0, "fora de escopo" quer dizer **"não agora"** e é uma linha do `to-dolist.md` com a tag `#fora-de-escopo`; o to-dolist vai pro git (`docs/decisoes.md`, 2026-10-28). O `checar` da abertura já rodou `python "${CLAUDE_PLUGIN_ROOT}/templates/converter_to_dolist.py" checar --proj "<raiz do projeto>"` (só lê) e trouxe os achados.

- **`to-dolist ✓`** ("no desenho do kit") → pule pro passe 3.
- **`to-dolist ⬜`** (seção "Fora de escopo" no INDEX, `docs/superpowers/FORA-DE-ESCOPO.md`, `.gitignore` ignorando o to-dolist, to-dolist fora do formato) → converta, ainda na `chore/upgrade-kit`. **Nunca perder nada** é a regra: em dois tempos, cada um com o seu commit.
  1. **Tempo 1 — o to-dolist entra no git como está.** `converter_to_dolist.py liberar --proj "<raiz>"` (prévia) mostra as linhas que saem do `.gitignore`; com `--aplicar` ele grava. Antes de commitar, confira que o to-dolist **não traz segredo nem dado pessoal** (só nomes de variável e host interno passam; valor de senha/token não). Commit **só** de `.gitignore` e `to-dolist.md`, pelo nome, com o arquivo **exatamente como estava**: é o "antes" que o git guarda — o upgrade promete voltar atrás pelo git (fim deste comando), e o to-dolist estava fora dele. Sem to-dolist no projeto, só o `.gitignore`.
  2. **Tempo 2 — prévia.** `converter_to_dolist.py converter --proj "<raiz>"` (não grava). Mostre ao owner o que a saída traz: a **soma** (linhas de origem = recados convertidos + títulos usados + lista do fim + marcação) e **3 linhas reais** como estão e como vão ficar. O que a conversão faz: recado (item com as linhas que continuam embaixo) vira **uma linha**, com o título da seção na frente e a data dele; fora de escopo vira `- <item> #fora-de-escopo (decidido: <data>, <texto inteiro>)`; sem data → a data de hoje; `DD/MM/AAAA` → `AAAA-MM-DD`; ordem pela data, a mais antiga em cima; riscado/FEITA/CONCLUÍDO, data sem ano, parágrafo solto, citação, tabela e código vão **sem mudar uma letra** pra uma lista no fim, pro owner decidir. A seção do INDEX e o `FORA-DE-ESCOPO.md` saem. Saiu `PROBLEMA` → nada é gravado: repasse e **siga pro passe 3** (o relatório do fim diz que a conversão ficou pendente). Com `--dry-run`, pare neste passe.
  3. **Só com o OK do owner** nas 3 linhas: `converter … --aplicar`. Ele confere de novo (to-dolist já no git, arquivos limpos, soma) e só então grava; não mexe no git.
  4. Commit dos arquivos que ele gravou/apagou (`to-dolist.md`, `docs/superpowers/INDEX.md`, `docs/superpowers/FORA-DE-ESCOPO.md`), pelo nome e pela regra de git do projeto. Diga ao owner quantas linhas ficaram na **lista do fim** (abaixo do comentário `<!-- upgrade: linhas que a conversão não soube converter … -->`): ele decide cada uma — reescrever no formato, `/mss-spec:to-dolist feito <n>` ou deixar. Desfazer: `git revert` do commit do tempo 2 (o tempo 1 tem o original).
  5. **Siga pro passe 3, nesta conversa.**

## Passe 3 — as três categorias (projeto **com** a marca)

1. **Arquivos só-do-kit (referência) — atualiza sozinho, sem perguntar.** São iguais em todo projeto; substitua pela versão nova do template:
   - `docs/SEGURANCA.md` ← `templates/SEGURANCA.md`
   - `docs/ESTRUTURA.md` ← `templates/ESTRUTURA.md`
   - `.claude/rules/*.md` ← `templates/rules/` (regras path-scoped; **só acrescente as que faltam** — **nunca sobrescreva** a que existe, ela é do projeto — e não recrie a que o projeto apagou de propósito por não se aplicar)
   - `docs/FRONTEND.md` ← `templates/FRONTEND.md` (só se o projeto tem UI web)
   - `docker-compose.yml` · `docker-compose.office.yml` · `Dockerfile` · `.dockerignore` ← `templates/docker/` (só se o projeto usa Docker, e **só o que falta**: o que existe nunca é reescrito — freio "do que já roda", abaixo)
   - `.gitignore` ← `templates/gitignore` (acrescente o que o kit passou a ignorar; **não remova** entradas que o projeto adicionou — a única saída é a do `/to-dolist.md`, e só pelo `liberar` do passe 2)
   - **Índice de memória plano** (`memory/MEMORY.md` com linhas `- [Título](arquivo.md)` e sem `memory/indice/`): **não sobrescreva**; mostre `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" dividir` em dry-run (tabela família × bytes) e peça OK antes do `--aplicar` — move, não apaga

   **Freio da infra própria — o que é MSIG não entra em projeto que não é MSIG.** Leia a linha `**Infra:**` do Contexto do `CLAUDE.md` antes desta categoria. Se for **infra própria**, os arquivos da infra corporativa **não são criados nem atualizados**: `docker-compose.office.yml`, `certs/corp-ca.pem` e o proxy no `.env`; e o `docker-compose.yml` base, se existir, **não** ganha a rede externa `mitiai_network`. Sem esse freio o upgrade **reintroduz** sozinho, a cada rodada, exatamente o que o `kickoff` deixou de fora (a categoria 1 sobrescreve sem perguntar).

   **Freio do que já roda — infra que existe NUNCA é reescrita, em projeto nenhum (0.52.0).** `docker-compose.yml`, `docker-compose.office.yml`, `Dockerfile` e `.dockerignore` que **já existem** (no git ou soltos na pasta, não rastreados) não são tocados: o upgrade só **cria** o que falta (respeitando o freio da infra própria). O molde mudou? **Mostre o diff** e diga "o molde do kit mudou — revise à mão", como na categoria 3; **nunca** sobrescreva. Motivo: o projeto que nasceu do kit e já está em homologação/produção não é brownfield (sem tabela no `ARQUITETURA.md`) nem infra própria — caía fora dos dois freios e tinha o Dockerfile que roda substituído pelo molde (MSS-SSC: 143 linhas diferentes só no Dockerfile). `certs/corp-ca.pem` **não** está nesta categoria e fica **fora** deste freio: quem o entrega é o `/mss-spec:ambiente`, e CA velha quebra o build (`memory/project_docker_build_fortigate.md`) — ele continua atualizável.

   **Freio do brownfield — arquivo que "não nasceu do kit" PERGUNTA, não é sobrescrito.** Antes de aplicar esta categoria, leia a tabela **"Pré-existente — não nasceu do kit"** do `docs/ARQUITETURA.md` (se existir; ela é gravada pelo `/mss-spec:analise`). Arquivo listado lá é do **projeto**, não uma cópia velha do molde: **mostre o diff e pergunte** ao owner em vez de atualizar sozinho — o padrão é **manter o do projeto**. Sem esse freio, um projeto **brownfield** que já tinha `docker-compose.yml`/`Dockerfile` próprios teria a infra que roda substituída pelo molde do kit, parando o projeto. Vale o mesmo julgamento quando não há dossiê e o arquivo claramente não veio do kit (conteúdo sem parentesco com o template): na dúvida, **pergunte**. O próprio `docs/ARQUITETURA.md` é **conteúdo do projeto** (levantamento do código, sem template a sincronizar) — o upgrade **nunca** o toca; quem o regenera é o `/mss-spec:analise`.

2. **`CLAUDE.md`, `docs/AMBIENTE.md` e `docs/superpowers/MAPA.md` — MESCLA (nunca sobrescreve o do owner).** O kit dá o esqueleto, o owner preenche/edita. Compare **seção por seção / regra por regra** com o template:
   - **O `CLAUDE.md` com a marca é só do projeto: a categoria 2 não reacrescenta seção do kit** (Modo de trabalho, Contexto de janela, Regras críticas — vêm do plugin, não voltam pro arquivo). Do `CLAUDE.md` ela só confere as seções do projeto (`## Regras obrigatórias do projeto`, `## Contexto`, `## Mapa de arquivos`, `## Índice de regras por tipo de arquivo`) e acrescenta a que **faltar**. Vale a regra por seção abaixo pro `AMBIENTE.md` e o `MAPA.md`.
   - Seção/regra do template que **falta** no projeto → **acrescente** (novidade do kit). **Exceção — `docs/AMBIENTE.md` que já existe (0.52.0): não acrescente seção** do molde; diga em 1 linha quais seções o molde tem e o projeto não, e pare — infra é do projeto, e seção reposta a cada rodada desfaz o que ele tirou de propósito.
   - Conteúdo que o owner escreveu (contexto preenchido, regras de `## Regras obrigatórias do projeto`) → **mantenha intacto**.
   - Mesma seção/regra nos dois mas **divergiu** (kit diz A, owner editou pra B) → **CONFLITO**: mostre os dois lados e **pergunte** ao owner qual fica. Só isso interage.
   - **Limite honesto:** o upgrade não guarda a versão *antiga* do template que o projeto nasceu, então a reconciliação é por seção/regra (não é 3-way merge). Na dúvida entre mexer ou não, **erre pro lado de manter o do owner**.
   - **Caso da linha `**Infra:**` (novidade da 0.18.0):** ela é o que faz o kit parar de assumir a infra MSIG, e num projeto anterior a esta versão **não existe**. Ao mesclar o `CLAUDE.md`, acrescente-a no Contexto — mas **não escolha por ele**: mostre as duas opções e **pergunte** (*"este projeto roda na infra MSIG — rede `mitiai_network`, proxy, CA do FortiGate, SQL Server corporativo — ou tem infra própria?"*). Enquanto ele não responder, deixe `<MSIG | própria — a confirmar>`; **assumir MSIG em silêncio é justamente o erro** que a versão conserta.
   - **Caso do `MAPA.md`:** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/MAPA.md` (novidade do kit num projeto que nasceu antes dela — senão a regra de partida no `CLAUDE.md` apontaria pra um arquivo inexistente). Se **já existe**, **mescle a ESTRUTURA** do template que faltar — as 3 seções fixas (`Onde estamos`, `Próximo passo`, `Conexões`) e o **comentário-guia do formato de Conexões** (o `/mss-spec:mapa-neural` depende dele pra parsear) — **mantendo intacto** o conteúdo que o owner preencheu (branch/próximo passo/conexões declaradas). O conteúdo é volátil/regenerável (`/mss-spec:mapa` reconcilia), então **não trate divergência de conteúdo como conflito** — erre pro lado de manter o do owner e só garanta que a estrutura nova está presente.

   - **Caso do `docs/AMBIENTES.md` (novidade da 0.50.0, F-048):** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/AMBIENTES.md` e **pré-preencha só o que o projeto já tem escrito** — nomes de ambiente, Web App, servidor e branch do `CLAUDE.md`/`docs/AMBIENTE.md`/`docs/specs/deploy-*.md`, e os **nomes** das variáveis do `.env.example` e do `infra/app-settings.json` (quando existem); todo **valor** que você não leu de um arquivo do projeto fica `falta preencher`, e segredo é `*****` + onde vive. Grave o esqueleto e diga em **1 linha** quantos valores ficaram `falta preencher` — **sem questionário** (0.52.0): o owner preenche quando precisar, e o `doctor` (check 13) conta. Se **já existe**, **não toque nos valores** (são leitura do owner); acrescente só seção de ambiente ou coluna que o modelo ganhou.
   - **Caso do `docs/EVALS.md` (novidade da 0.19.0):** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/EVALS.md` — **vazio de casos** (o corpus é do projeto; nunca invente falha que não aconteceu). Se **já existe**, **não toque**: os casos são conteúdo do owner, jamais sobrescritos pela categoria 1. Mesma coisa pro `memory/MEMORY.md`: se o índice ainda não estiver agrupado por **gatilho**, **proponha** a migração (mostrando o antes/depois) em vez de reescrever sozinho.

3. **Código do projeto (ex.: `utils/get_connection.py`) — só avisa.** Mexer em código sozinho é arriscado. Se `templates/get_connection.py` evoluiu, **mostre o diff** e diga "o molde do kit mudou — revise à mão"; **não** aplique.

**Commit do passe 3**, pela regra de git do projeto: mostre ao owner o `git status --short` e `git diff --stat` do que as categorias gravaram, e commite pelo nome (`chore(upgrade): arquivos do kit na versão <versão>`). Conflito da categoria 2 que o owner ainda não respondeu fica **fora** do commit (o arquivo fica como estava) e entra no relatório.

## Fecho: relatório, integração e devolução

**Relatório curto, um bloco por passe que rodou:** (a) o que atualizou sozinho · (b) o que mesclou no `CLAUDE.md`/`AMBIENTE.md` · (c) os conflitos que dependem do owner · (d) o código a revisar à mão · (e) o que ficou pendente (migração ou conversão que saiu com falha, linhas da lista do fim do to-dolist) e por quê. Mostre a lista dos commits da rodada: `git log --oneline <principal>..chore/upgrade-kit`.

**Integrar e devolver, com o OK do owner** (pela regra de git do projeto; no projeto que reserva o git ao owner, um comando por bloco e você confere por leitura):

1. `git switch <principal>` e `git merge chore/upgrade-kit` (o hook `git_publicacao.py` pede a aprovação do owner — é o OK dele; com remoto, `git merge --no-ff` se a regra do projeto pedir histórico de merge). **Push: nunca você** (`main`/`master` é negado pelo hook; o owner faz do terminal dele, quando quiser).
2. **Traz a principal pra branch em que o owner estava** — senão toda janela nova aberta nela acusa o `CLAUDE.md` antigo: `git switch <branch do owner>` e `git merge --ff-only <principal>`. O `--ff-only` falhou (a branch dele divergiu da principal)? **Pare e pergunte**: `git merge <principal>` (o hook pede aprovação) ou deixar pra ele — nunca rebase do trabalho dele.
3. **Devolve o trabalho pendente**: `git stash pop` (só se o passo 0 guardou). Conflito no pop? Pare, mostre `git status --short` e peça ao owner — o stash continua guardado até resolver.
4. **Conferência colada, antes de dizer "pronto"** (o owner disse "commitei"/"mesclei" e você não viu a saída? não está feito): `git branch --show-current` (a branch do owner) · `git log --oneline -5` (os commits da rodada aparecem) · `git status --short` (os mesmos arquivos modificados de antes, e só eles) · `git stash list` (vazio, ou sem a entrada `mss-spec upgrade`). Só com as quatro saídas na conversa a rodada está fechada. A `chore/upgrade-kit` pode ser apagada pelo owner (`git branch -d chore/upgrade-kit`); ela fica.

Owner sem tempo pra integrar agora? Tudo bem: a `chore/upgrade-kit` fica com os commits, você devolve o stash **na branch dele** (volte pra ela antes do `pop`) e o relatório diz que a integração (passos 1 e 2) ficou pra ele, com os comandos um por bloco.

**Rollback: o git é o rollback.** Não há comando de "desfazer" — não precisa. Como o upgrade só mexe em arquivos versionados, numa branch própria e com o trabalho do owner guardado fora: antes do commit, `git restore .` reverte o que o passe mudou; depois, `git revert` do commit do passe ou descartar a `chore/upgrade-kit` desfaz. Sem comando dedicado de propósito (YAGNI).
