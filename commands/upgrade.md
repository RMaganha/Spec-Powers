---
description: Sincroniza os arquivos do kit no projeto com a versão atual dos templates — atualiza os de referência sozinho e MESCLA CLAUDE.md/AMBIENTE.md sem perder o seu (só conflito real pergunta); projeto ainda com as regras do kit copiadas no CLAUDE.md é migrado antes, sozinho
argument-hint: "[--dry-run]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Traz o projeto pra versão atual do kit: compara cada arquivo que veio do kit com o template correspondente em `${CLAUDE_PLUGIN_ROOT}/templates/` e reconcilia com **o mínimo de interação** — só **conflito real** chama o owner.

**Antes de mexer:** confirme que o working tree está limpo (ou avise o owner pra revisar depois pelo `git diff`), porque o upgrade **modifica arquivos**. **Não** faça `git add`/commit — deixe as mudanças no working tree pro owner revisar e commitar. **Única exceção:** o git da migração do `CLAUDE.md` (próxima seção), que segue a regra de git do projeto.

## Modo `--dry-run` (preview, não toca em arquivo)

Se `$ARGUMENTS` contém `--dry-run`, rode em modo **preview**: mostre exatamente o que o upgrade *faria*, mas **não escreve nenhum arquivo** — o working tree fica intacto. É opt-in (a flag é aditiva; sem ela, o upgrade aplica como sempre). Serve pra prevenir o merge silencioso da categoria 1, que hoje é aplicado sozinho sem o owner ver o que mudou.

No preview:
- **Categoria 1 (referência):** para cada arquivo desatualizado, mostre o **diff unificado** (git-style, template novo × arquivo atual) do que *seria* sobrescrito. Este é o passo hoje silencioso — o alvo da prevenção.
- **Categorias 2 e 3 (`CLAUDE.md`/`AMBIENTE.md` e código):** o mesmo relatório descritivo de sempre (o que seria mesclado · conflitos que dependeriam do owner · código a revisar à mão), sem escrever nada.

Ao fim, **deixe explícito que foi só preview** e diga como aplicar de verdade: rode `/mss-spec:upgrade` **sem a flag**. Não faça nenhuma edição, `git add` nem commit no dry-run.

## Primeiro: projeto sem a marca → migração do `CLAUDE.md`, sozinha

Abra o `CLAUDE.md` da raiz e procure a linha `<!-- mss-spec:regras-do-kit -->` (a marca: é ela que faz o plugin entregar as regras do kit em toda janela).

- **Tem a marca** → o projeto já migrou; pule esta seção e siga pras categorias.
- **Não tem** → as regras do kit ainda estão copiadas no `CLAUDE.md`. Faça a migração **primeiro e sozinha**: **nenhuma outra categoria** (1, 2 ou 3) roda na mesma rodada — o `CLAUDE.md` muda de formato, e misturar esconderia a mudança no `git diff`.
  0. **A branch, antes de tudo** (árvore limpa; com `--dry-run` no `$ARGUMENTS` pule este passo — preview não mexe em git): vá pra branch principal, atualize-a e crie `chore/migrar-claude-md` a partir dela, pra o `--aplicar` já gravar na branch certa. Quem executa segue a **regra de git do projeto** (a linha `Versionamento` do `## Contexto`, ou o documento que ela aponta):
     - **Padrão do kit** — o assistente roda: trocar pra principal, atualizá-la (`git pull --ff-only`) e `git switch -c chore/migrar-claude-md`.
     - **Projeto que reserva o git ao owner** — o assistente **não escreve no git**: entregue esses comandos **um por bloco** (principal · atualizar · `git switch -c chore/migrar-claude-md`) e, **antes de continuar**, confirme rodando `git branch --show-current` (só leitura) que a resposta é `chore/migrar-claude-md`; se não for, não siga.
  1. Rode `python "${CLAUDE_PLUGIN_ROOT}/templates/migrar_claude_md.py" --proj "<raiz do projeto>"` (dry-run, com a raiz do projeto por extenso: não depende da pasta em que o shell está; a saída começa com "Prévia"). Mostre o relatório ao owner: quantas linhas saíram por serem do kit, quantas mudaram de lugar, quais ficaram por dúvida, e o aviso de teto se houver.
  2. Saiu com falha (a saída lista o que não fechou; árvore suja nos arquivos que ele toca também é falha) → **nada foi gravado**: repasse a lista e pare (a branch criada fica; o owner a descarta se quiser). Com `--dry-run` no `$ARGUMENTS`, pare aqui de qualquer jeito.
  3. Sem falha → rode `python "${CLAUDE_PLUGIN_ROOT}/templates/migrar_claude_md.py" --aplicar --proj "<raiz do projeto>"`. Ele grava e para: **não mexe no git**.
  4. Commit, pela mesma regra de git do projeto: `git add` **pelo nome** de cada arquivo que o script gravou (nunca `-A` nem `.`) e `git commit` — o assistente roda no padrão do kit; no projeto que reserva o git ao owner, entregue os dois comandos um por bloco. Push só como a regra do projeto permitir. Desfazer, antes de commitar: `git restore <os arquivos que o script gravou>`.
  5. **Termine aqui** — commit feito (padrão do kit) ou pedido ao owner (git reservado a ele). As outras categorias ficam pra próxima rodada do `/mss-spec:upgrade`, já com a marca.

## Segundo: to-dolist e fora de escopo no formato antigo → conversão, sozinha

Desde a 0.47.0, "fora de escopo" quer dizer **"não agora"** e é uma linha do `to-dolist.md` com a tag `#fora-de-escopo`; o to-dolist vai pro git (`docs/decisoes.md`, 2026-10-28). Rode `python "${CLAUDE_PLUGIN_ROOT}/templates/converter_to_dolist.py" checar --proj "<raiz do projeto>"` (só lê).

- **"no desenho do kit"** → pule esta seção e siga pras categorias.
- **Achou formato antigo** (seção "Fora de escopo" no INDEX, `docs/superpowers/FORA-DE-ESCOPO.md`, `.gitignore` ignorando o to-dolist, to-dolist fora do formato) → converta **primeiro e sozinha**: nenhuma categoria roda na mesma rodada. **Nunca perder nada** é a regra: em dois tempos, cada um com o seu commit.
  0. **A branch** (árvore limpa; com `--dry-run` pule): principal atualizada → `chore/to-dolist-desenho-do-kit`, pela **regra de git do projeto**, igual ao passo 0 da migração acima (no projeto que reserva o git ao owner, entregue os comandos um por bloco e confira com `git branch --show-current`).
  1. **Tempo 1 — o to-dolist entra no git como está.** `converter_to_dolist.py liberar --proj "<raiz>"` (prévia) mostra as linhas que saem do `.gitignore`; com `--aplicar` ele grava. Commit **só** de `.gitignore` e `to-dolist.md`, pelo nome, com o arquivo **exatamente como estava**: é o "antes" que o git guarda — o upgrade promete voltar atrás pelo git (fim deste comando), e o to-dolist estava fora dele. Sem to-dolist no projeto, só o `.gitignore`.
  2. **Tempo 2 — prévia.** `converter_to_dolist.py converter --proj "<raiz>"` (não grava). Mostre ao owner o que a saída traz: a **soma** (linhas de origem = recados convertidos + títulos usados + lista do fim + marcação) e **3 linhas reais** como estão e como vão ficar. O que a conversão faz: recado (item com as linhas que continuam embaixo) vira **uma linha**, com o título da seção na frente e a data dele; fora de escopo vira `- <item> #fora-de-escopo (decidido: <data>, <texto inteiro>)`; sem data → a data de hoje; `DD/MM/AAAA` → `AAAA-MM-DD`; ordem pela data, a mais antiga em cima; riscado/FEITA/CONCLUÍDO, data sem ano, parágrafo solto, citação, tabela e código vão **sem mudar uma letra** pra uma lista no fim, pro owner decidir. A seção do INDEX e o `FORA-DE-ESCOPO.md` saem. Saiu `PROBLEMA` → nada é gravado: repasse e pare. Com `--dry-run`, pare aqui.
  3. **Só com o OK do owner** nas 3 linhas: `converter … --aplicar`. Ele confere de novo (to-dolist já no git, arquivos limpos, soma) e só então grava; não mexe no git.
  4. Commit dos arquivos que ele gravou/apagou (`to-dolist.md`, `docs/superpowers/INDEX.md`, `docs/superpowers/FORA-DE-ESCOPO.md`), pelo nome e pela regra de git do projeto. Diga ao owner quantas linhas ficaram na **lista do fim** (abaixo do comentário `<!-- upgrade: linhas que a conversão não soube converter … -->`): ele decide cada uma — reescrever no formato, `/mss-spec:to-dolist feito <n>` ou deixar. Desfazer: `git revert` do commit do tempo 2 (o tempo 1 tem o original).
  5. **Termine aqui.** As categorias ficam pra próxima rodada do `/mss-spec:upgrade`.

Três categorias (projeto **com** a marca):

1. **Arquivos só-do-kit (referência) — atualiza sozinho, sem perguntar.** São iguais em todo projeto; substitua pela versão nova do template:
   - `docs/SEGURANCA.md` ← `templates/SEGURANCA.md`
   - `docs/ESTRUTURA.md` ← `templates/ESTRUTURA.md`
   - `.claude/rules/*.md` ← `templates/rules/` (regras path-scoped; **só acrescente as que faltam** — **nunca sobrescreva** a que existe, ela é do projeto — e não recrie a que o projeto apagou de propósito por não se aplicar)
   - `docs/FRONTEND.md` ← `templates/FRONTEND.md` (só se o projeto tem UI web)
   - `docker-compose.yml` · `docker-compose.office.yml` · `Dockerfile` · `.dockerignore` ← `templates/docker/` (só se o projeto usa Docker)
   - `.gitignore` ← `templates/gitignore` (acrescente o que o kit passou a ignorar; **não remova** entradas que o projeto adicionou — a única saída é a do `/to-dolist.md`, e só pelo `liberar` da seção acima)
   - **Índice de memória plano** (`memory/MEMORY.md` com linhas `- [Título](arquivo.md)` e sem `memory/indice/`): **não sobrescreva**; mostre `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_indice.py" dividir` em dry-run (tabela família × bytes) e peça OK antes do `--aplicar` — move, não apaga

   **Freio da infra própria — o que é MSIG não entra em projeto que não é MSIG.** Leia a linha `**Infra:**` do Contexto do `CLAUDE.md` antes desta categoria. Se for **infra própria**, os arquivos da infra corporativa **não são criados nem atualizados**: `docker-compose.office.yml`, `certs/corp-ca.pem` e o proxy no `.env`; e o `docker-compose.yml` base, se existir, **não** ganha a rede externa `mitiai_network`. Sem esse freio o upgrade **reintroduz** sozinho, a cada rodada, exatamente o que o `kickoff` deixou de fora (a categoria 1 sobrescreve sem perguntar).

   **Freio do brownfield — arquivo que "não nasceu do kit" PERGUNTA, não é sobrescrito.** Antes de aplicar esta categoria, leia a tabela **"Pré-existente — não nasceu do kit"** do `docs/ARQUITETURA.md` (se existir; ela é gravada pelo `/mss-spec:analise`). Arquivo listado lá é do **projeto**, não uma cópia velha do molde: **mostre o diff e pergunte** ao owner em vez de atualizar sozinho — o padrão é **manter o do projeto**. Sem esse freio, um projeto **brownfield** que já tinha `docker-compose.yml`/`Dockerfile` próprios teria a infra que roda substituída pelo molde do kit, parando o projeto. Vale o mesmo julgamento quando não há dossiê e o arquivo claramente não veio do kit (conteúdo sem parentesco com o template): na dúvida, **pergunte**. O próprio `docs/ARQUITETURA.md` é **conteúdo do projeto** (levantamento do código, sem template a sincronizar) — o upgrade **nunca** o toca; quem o regenera é o `/mss-spec:analise`.

2. **`CLAUDE.md`, `docs/AMBIENTE.md` e `docs/superpowers/MAPA.md` — MESCLA (nunca sobrescreve o do owner).** O kit dá o esqueleto, o owner preenche/edita. Compare **seção por seção / regra por regra** com o template:
   - **O `CLAUDE.md` com a marca é só do projeto: a categoria 2 não reacrescenta seção do kit** (Modo de trabalho, Contexto de janela, Regras críticas — vêm do plugin, não voltam pro arquivo). Do `CLAUDE.md` ela só confere as seções do projeto (`## Regras obrigatórias do projeto`, `## Contexto`, `## Mapa de arquivos`, `## Índice de regras por tipo de arquivo`) e acrescenta a que **faltar**. Vale a regra por seção abaixo pro `AMBIENTE.md` e o `MAPA.md`.
   - Seção/regra do template que **falta** no projeto → **acrescente** (novidade do kit).
   - Conteúdo que o owner escreveu (contexto preenchido, regras de `## Regras obrigatórias do projeto`) → **mantenha intacto**.
   - Mesma seção/regra nos dois mas **divergiu** (kit diz A, owner editou pra B) → **CONFLITO**: mostre os dois lados e **pergunte** ao owner qual fica. Só isso interage.
   - **Limite honesto:** o upgrade não guarda a versão *antiga* do template que o projeto nasceu, então a reconciliação é por seção/regra (não é 3-way merge). Na dúvida entre mexer ou não, **erre pro lado de manter o do owner**.
   - **Caso da linha `**Infra:**` (novidade da 0.18.0):** ela é o que faz o kit parar de assumir a infra MSIG, e num projeto anterior a esta versão **não existe**. Ao mesclar o `CLAUDE.md`, acrescente-a no Contexto — mas **não escolha por ele**: mostre as duas opções e **pergunte** (*"este projeto roda na infra MSIG — rede `mitiai_network`, proxy, CA do FortiGate, SQL Server corporativo — ou tem infra própria?"*). Enquanto ele não responder, deixe `<MSIG | própria — a confirmar>`; **assumir MSIG em silêncio é justamente o erro** que a versão conserta.
   - **Caso do `MAPA.md`:** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/MAPA.md` (novidade do kit num projeto que nasceu antes dela — senão a regra de partida no `CLAUDE.md` apontaria pra um arquivo inexistente). Se **já existe**, **mescle a ESTRUTURA** do template que faltar — as 3 seções fixas (`Onde estamos`, `Próximo passo`, `Conexões`) e o **comentário-guia do formato de Conexões** (o `/mss-spec:mapa-neural` depende dele pra parsear) — **mantendo intacto** o conteúdo que o owner preencheu (branch/próximo passo/conexões declaradas). O conteúdo é volátil/regenerável (`/mss-spec:mapa` reconcilia), então **não trate divergência de conteúdo como conflito** — erre pro lado de manter o do owner e só garanta que a estrutura nova está presente.

   - **Caso do `docs/AMBIENTES.md` (novidade da 0.50.0, F-048):** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/AMBIENTES.md` e **pré-preencha só o que o projeto já tem escrito** — nomes de ambiente, Web App, servidor e branch do `CLAUDE.md`/`docs/AMBIENTE.md`/`docs/specs/deploy-*.md`, e os **nomes** das variáveis do `.env.example` e do `infra/app-settings.json` (quando existem); todo **valor** que você não leu de um arquivo do projeto fica `falta preencher`, e segredo é `*****` + onde vive. Mostre o esqueleto e diga ao owner o que falta ele conferir. Se **já existe**, **não toque nos valores** (são leitura do owner); acrescente só seção de ambiente ou coluna que o modelo ganhou.
   - **Caso do `docs/EVALS.md` (novidade da 0.19.0):** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/EVALS.md` — **vazio de casos** (o corpus é do projeto; nunca invente falha que não aconteceu). Se **já existe**, **não toque**: os casos são conteúdo do owner, jamais sobrescritos pela categoria 1. Mesma coisa pro `memory/MEMORY.md`: se o índice ainda não estiver agrupado por **gatilho**, **proponha** a migração (mostrando o antes/depois) em vez de reescrever sozinho.

3. **Código do projeto (ex.: `utils/get_connection.py`) — só avisa.** Mexer em código sozinho é arriscado. Se `templates/get_connection.py` evoluiu, **mostre o diff** e diga "o molde do kit mudou — revise à mão"; **não** aplique.

**No fim, um relatório curto:** (a) o que atualizou sozinho · (b) o que mesclou no `CLAUDE.md`/`AMBIENTE.md` · (c) os conflitos que dependem do owner · (d) o código a revisar à mão. Lembre o owner de conferir tudo pelo `git diff` antes de commitar.

**Rollback: o git é o rollback.** Não há comando de "desfazer" — não precisa. Como o upgrade só mexe em arquivos versionados (e você começou com a árvore de trabalho limpa), `git restore .` reverte tudo que ele mudou antes de commitar; se já commitou, `git revert`/descartar a branch desfaz. Sem comando dedicado de propósito (YAGNI).
