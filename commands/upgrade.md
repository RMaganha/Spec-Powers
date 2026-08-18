---
description: Sincroniza os arquivos do kit no projeto com a versão atual dos templates — atualiza os de referência sozinho e MESCLA CLAUDE.md/AMBIENTE.md sem perder o seu (só conflito real pergunta)
argument-hint: "[--dry-run]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Traz o projeto pra versão atual do kit: compara cada arquivo que veio do kit com o template correspondente em `${CLAUDE_PLUGIN_ROOT}/templates/` e reconcilia com **o mínimo de interação** — só **conflito real** chama o owner.

**Antes de mexer:** confirme que o working tree está limpo (ou avise o owner pra revisar depois pelo `git diff`), porque o upgrade **modifica arquivos**. **Não** faça `git add`/commit — deixe as mudanças no working tree pro owner revisar e commitar.

## Modo `--dry-run` (preview, não toca em arquivo)

Se `$ARGUMENTS` contém `--dry-run`, rode em modo **preview**: mostre exatamente o que o upgrade *faria*, mas **não escreve nenhum arquivo** — o working tree fica intacto. É opt-in (a flag é aditiva; sem ela, o upgrade aplica como sempre). Serve pra prevenir o merge silencioso da categoria 1, que hoje é aplicado sozinho sem o owner ver o que mudou.

No preview:
- **Categoria 1 (referência):** para cada arquivo desatualizado, mostre o **diff unificado** (git-style, template novo × arquivo atual) do que *seria* sobrescrito. Este é o passo hoje silencioso — o alvo da prevenção.
- **Categorias 2 e 3 (`CLAUDE.md`/`AMBIENTE.md` e código):** o mesmo relatório descritivo de sempre (o que seria mesclado · conflitos que dependeriam do owner · código a revisar à mão), sem escrever nada.

Ao fim, **deixe explícito que foi só preview** e diga como aplicar de verdade: rode `/mss-spec:upgrade` **sem a flag**. Não faça nenhuma edição, `git add` nem commit no dry-run.

Três categorias:

1. **Arquivos só-do-kit (referência) — atualiza sozinho, sem perguntar.** São iguais em todo projeto; substitua pela versão nova do template:
   - `docs/SEGURANCA.md` ← `templates/SEGURANCA.md`
   - `docs/ESTRUTURA.md` ← `templates/ESTRUTURA.md`
   - `.claude/rules/*.md` ← `templates/rules/` (regras path-scoped; **acrescente as que faltam**, e não recrie a que o projeto apagou de propósito por não se aplicar)
   - `docs/FRONTEND.md` ← `templates/FRONTEND.md` (só se o projeto tem UI web)
   - `docker-compose.yml` · `docker-compose.office.yml` · `Dockerfile` · `.dockerignore` ← `templates/docker/` (só se o projeto usa Docker)
   - `.gitignore` ← `templates/gitignore` (acrescente o que o kit passou a ignorar; **não remova** entradas que o projeto adicionou)

   **Freio da infra própria — o que é MSIG não entra em projeto que não é MSIG.** Leia a linha `**Infra:**` do Contexto do `CLAUDE.md` antes desta categoria. Se for **infra própria**, os arquivos da infra corporativa **não são criados nem atualizados**: `docker-compose.office.yml`, `certs/corp-ca.pem` e o proxy no `.env`; e o `docker-compose.yml` base, se existir, **não** ganha a rede externa `mitiai_network`. Sem esse freio o upgrade **reintroduz** sozinho, a cada rodada, exatamente o que o `kickoff` deixou de fora (a categoria 1 sobrescreve sem perguntar).

   **Freio do brownfield — arquivo que "não nasceu do kit" PERGUNTA, não é sobrescrito.** Antes de aplicar esta categoria, leia a tabela **"Pré-existente — não nasceu do kit"** do `docs/ARQUITETURA.md` (se existir; ela é gravada pelo `/mss-spec:analise`). Arquivo listado lá é do **projeto**, não uma cópia velha do molde: **mostre o diff e pergunte** ao owner em vez de atualizar sozinho — o padrão é **manter o do projeto**. Sem esse freio, um projeto **brownfield** que já tinha `docker-compose.yml`/`Dockerfile` próprios teria a infra que roda substituída pelo molde do kit, parando o projeto. Vale o mesmo julgamento quando não há dossiê e o arquivo claramente não veio do kit (conteúdo sem parentesco com o template): na dúvida, **pergunte**. O próprio `docs/ARQUITETURA.md` é **conteúdo do projeto** (levantamento do código, sem template a sincronizar) — o upgrade **nunca** o toca; quem o regenera é o `/mss-spec:analise`.

2. **`CLAUDE.md`, `docs/AMBIENTE.md` e `docs/superpowers/MAPA.md` — MESCLA (nunca sobrescreve o do owner).** O kit dá o esqueleto, o owner preenche/edita. Compare **seção por seção / regra por regra** com o template:
   - Seção/regra do template que **falta** no projeto → **acrescente** (novidade do kit).
   - Conteúdo que o owner escreveu (contexto preenchido, regra específica do projeto — a última das "Regras críticas", que no molde é só um placeholder) → **mantenha intacto**. Atenção à **numeração**: quando o molde ganha uma regra nova, ela entra **antes** da regra do projeto; acrescente a nova e **renumere**, sem sobrescrever a do owner.
   - Mesma seção/regra nos dois mas **divergiu** (kit diz A, owner editou pra B) → **CONFLITO**: mostre os dois lados e **pergunte** ao owner qual fica. Só isso interage.
   - **Limite honesto:** o upgrade não guarda a versão *antiga* do template que o projeto nasceu, então a reconciliação é por seção/regra (não é 3-way merge). Na dúvida entre mexer ou não, **erre pro lado de manter o do owner**.
   - **Caso da linha `**Infra:**` (novidade da 0.18.0):** ela é o que faz o kit parar de assumir a infra MSIG, e num projeto anterior a esta versão **não existe**. Ao mesclar o `CLAUDE.md`, acrescente-a no Contexto — mas **não escolha por ele**: mostre as duas opções e **pergunte** (*"este projeto roda na infra MSIG — rede `mitiai_network`, proxy, CA do FortiGate, SQL Server corporativo — ou tem infra própria?"*). Enquanto ele não responder, deixe `<MSIG | própria — a confirmar>`; **assumir MSIG em silêncio é justamente o erro** que a versão conserta.
   - **Caso do `MAPA.md`:** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/MAPA.md` (novidade do kit num projeto que nasceu antes dela — senão a regra de partida no `CLAUDE.md` apontaria pra um arquivo inexistente). Se **já existe**, **mescle a ESTRUTURA** do template que faltar — as 3 seções fixas (`Onde estamos`, `Próximo passo`, `Conexões`) e o **comentário-guia do formato de Conexões** (o `/mss-spec:mapa-neural` depende dele pra parsear) — **mantendo intacto** o conteúdo que o owner preencheu (branch/próximo passo/conexões declaradas). O conteúdo é volátil/regenerável (`/mss-spec:mapa` reconcilia), então **não trate divergência de conteúdo como conflito** — erre pro lado de manter o do owner e só garanta que a estrutura nova está presente.

   - **Caso do `docs/EVALS.md` (novidade da 0.19.0):** se **falta**, crie de `${CLAUDE_PLUGIN_ROOT}/templates/EVALS.md` — **vazio de casos** (o corpus é do projeto; nunca invente falha que não aconteceu). Se **já existe**, **não toque**: os casos são conteúdo do owner, jamais sobrescritos pela categoria 1. Mesma coisa pro `memory/MEMORY.md`: se o índice ainda não estiver agrupado por **gatilho**, **proponha** a migração (mostrando o antes/depois) em vez de reescrever sozinho.

3. **Código do projeto (ex.: `utils/get_connection.py`) — só avisa.** Mexer em código sozinho é arriscado. Se `templates/get_connection.py` evoluiu, **mostre o diff** e diga "o molde do kit mudou — revise à mão"; **não** aplique.

**No fim, um relatório curto:** (a) o que atualizou sozinho · (b) o que mesclou no `CLAUDE.md`/`AMBIENTE.md` · (c) os conflitos que dependem do owner · (d) o código a revisar à mão. Lembre o owner de conferir tudo pelo `git diff` antes de commitar.

**Rollback: o git é o rollback.** Não há comando de "desfazer" — não precisa. Como o upgrade só mexe em arquivos versionados (e você começou com a árvore de trabalho limpa), `git restore .` reverte tudo que ele mudou antes de commitar; se já commitou, `git revert`/descartar a branch desfaz. Sem comando dedicado de propósito (YAGNI).
