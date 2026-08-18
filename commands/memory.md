---
description: Memória do projeto — `resgatar` a nativa pro repo · `capturar` a sessão em decisões + diário
argument-hint: "resgatar | capturar (sem argumento: pergunto qual)"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Comando de **memória do projeto**, com dois modos. **Sem argumento, pergunte qual** antes de agir:
- **`resgatar`** — traz pro repo a memória que ficou na pasta nativa (volátil) do Claude.
- **`capturar`** — destila **esta sessão** em decisões (inclusive as negativas) + **diário de sessão**, roteando pros lares duráveis certos.

---

## Modo: resgatar

Você vai **trazer pro repositório** a memória que porventura ficou na pasta nativa do Claude (volátil, fora do git). **Nada se perde**: primeiro copia tudo pro repo (passos 1-4) e só **depois**, com o meu OK, a nativa vira ponteiro pro índice do repo (passo 5) — em vez de ficar como segunda fonte desatualizada.

1. **Ache a pasta nativa deste projeto** em `~/.claude/projects/`. O nome dela é o caminho absoluto do projeto com os separadores virando `-` (ex.: `C:\projetos\MeuApp\Azure` → algo como `C--projetos-MeuApp-Azure`). Se não tiver certeza de qual é, **liste** `~/.claude/projects/*/memory/` e **confirme comigo** antes de copiar (não chute a pasta errada).
2. **Se ela existir e tiver arquivos:** copie os `*.md` (menos o `MEMORY.md`) para `<repo>/memory/`, criando a pasta se preciso. **Não sobrescreva** um arquivo de mesmo nome já existente no repo sem me avisar.
3. **Índice:** funda as linhas do `MEMORY.md` nativo no `memory/MEMORY.md` do repo (crie do template do plugin se não existir); não duplique linhas.
4. **Commit (fecha a durabilidade):** só a memória vira durável depois de commitada. Se for um repo git:
   - garanta que existe `.gitignore` protegendo `.env` (crie de `${CLAUDE_PLUGIN_ROOT}/templates/gitignore` se faltar);
   - stage **nominal** — `git add memory/` (e `docs/` se houver doc a versionar). **NUNCA** `git add .`/`-A` (varreria `.env`/segredos);
   - rode `git status` e confira que **nada sensível** entrou;
   - `git commit -m "chore: resgata memoria para o repo (versionada)"`. **Local, sem `git push`** (regra "Git local-only" do `CLAUDE.md`: push só a pedido do owner).
   - Se NÃO for repo git, avise e pergunte antes de `git init` (não inicialize sozinho).
5. **Deixe o ponteiro na nativa (o passo que faz a memória durável realmente carregar).** Só o `MEMORY.md` da pasta **nativa** (`~/.claude/projects/<proj>/memory/MEMORY.md`) é **auto-carregado** pelo Claude Code no início de toda sessão — o índice do repo, que é o durável, só entra se alguém abrir. Duas cópias = a que carrega sozinha desatualiza e a atualizada não carrega (foi assim que 27 das 33 memórias deste kit ficaram fora da sessão por semanas — caso **F-012** de `docs/EVALS.md`). Então, **depois** de confirmar que tudo já está no repo, **peça meu OK** e substitua o conteúdo da nativa por um ponteiro de uma linha, por exemplo:

   ```markdown
   - Índice durável deste projeto: leia `memory/MEMORY.md` no repo (agrupado por gatilho). Esta pasta nativa é volátil — não grave memória aqui.
   ```

   Nunca faça isso **antes** do merge do passo 2/3 (perderia conteúdo), e nunca sem o meu OK — é arquivo fora do repositório.

6. **Reporte** o que foi copiado, de onde, e o commit. Depois do ponteiro, a fonte durável é **uma só** (o repo); a nativa só aponta pra ela. Memórias **novas** já vão direto pro repo (regra no `CLAUDE.md`).
7. Se a pasta nativa não existir ou estiver vazia, diga que não há nada a resgatar — sem inventar.

---

## Modo: capturar

Você vai **destilar esta sessão** e gravar o que é durável, pra parar de depender de eu lembrar no fecho. **Destile do contexto atual da conversa** (o que foi conversado/decidido + o `git diff` da branch) — **não releia arquivos** (captura barata). O essencial é o **rastro do raciocínio**: as decisões e, sobretudo, os **pivôs** (o que se cogitou, por que foi repensado, pra onde ajustou) — não só o estado final.

**Nunca invente.** Só grave o que aconteceu de fato nesta sessão / está no diff. Na dúvida, deixe de fora.

1. **Filtre `<private>`.** Qualquer trecho marcado `<private>…</private>` (na conversa ou no rascunho) **nunca** entra em nada versionado — descarte antes de rascunhar.

2. **Monte os rascunhos, roteando cada achado pro lar durável certo** (não crie destino novo):
   - **decisão transversal** ("X em vez de Y porque Z", arquitetura/lib/padrão) → 1 linha em **`docs/decisoes.md`**;
   - **decisão de escopo** ("decidiu-se NÃO fazer W") → seção **"Fora de escopo"** do **`docs/superpowers/INDEX.md`** (é o insumo anti-re-litígio: semanas depois isso me impede de repropor o que já foi descartado);
   - **narrativa do assunto** ("tentou-se A, virou B") → **Histórico** da spec viva em `docs/superpowers/specs/`;
   - **falha que já aconteceu** (premissa **derrubada** pelo owner nesta sessão, reincidência de um erro antigo, bug silencioso que só apareceu no projeto real) → 1 caso em **`docs/EVALS.md`**: `id · data · gatilho · classe · guardrail · status`. **Sem guardrail, o caso entra `aberto`** — e aí ele ganha um bloco curto (`Falhou · Verdade · Guardrail · Teste`). Com guardrail **e teste**, entra `fechado` e vive só na linha da tabela. Nunca cite teste que não existe;
   - **o que DEU CERTO** (abordagem, ordem de ataque ou jeito de perguntar que o owner confirmou — não só correção) → mesma prateleira do aprendizado durável, abaixo. O acervo de acertos é metade do valor: sem ele, só sobra a lista do que evitar;
   - **aprendizado durável atemporal** (regra/gotcha que vale além deste assunto) → arquivo em **`memory/`** (schema de frontmatter: `user`|`feedback`|`project`|`reference`) + 1 linha no índice **`memory/MEMORY.md`**. **Todo arquivo leva `gatilho:` no frontmatter** — a condição observável em que ele deve ser aberto ("quando editar HTML de aplicação") — e a linha do índice **começa pelo gatilho**, no grupo certo. Gatilho que é **arquivo** merece virar também regra path-scoped em `.claude/rules/` (ver `templates/rules/`), que o Claude Code carrega sozinho;
   - **resumo compacto da sessão** → **`memory/sessions/<data>-<assunto>.md`** + 1 linha no índice **`memory/DIARIO.md`** (data + assunto + gist → aponta o arquivo). Estrutura do resumo (curto): **Conversamos · Pivôs · Rejeitado · Fizemos · Próximo** — os **Pivôs** são o coração.

3. **Não duplicar — e podar.** Antes de escrever, consulte os índices (`MEMORY.md` / `DIARIO.md` / `docs/EVALS.md` / seções do INDEX) — se o fato/entrada já está coberto, **atualize** o existente em vez de criar duplicata. E olhe o que ficou para trás: memória **superada** por esta sessão ganha `obsoleta: <data> — superada por [[slug]]` no frontmatter e **sai do índice** (o arquivo fica, pra não perder a narrativa). O índice tem teto de **200 linhas e 25 KB** — é o mesmo limite que o Claude Code aplica ao índice de auto-memory, e acima dele **o excedente nem carrega**. Estourou: funda linhas parecidas antes de acrescentar.

4. **Mostre TODOS os rascunhos pro meu OK** (o que vai pra cada lar) e **não grave nada antes de gravar** sem meu "ok". Aplicado o OK, grave com stage **nominal** (`git add memory/ docs/` — nunca `git add .`/`-A`), confira `git status` (nada sensível) e commit local (sem `git push`).

5. **Delegue o MAPA.** Ao final, **rode `/mss-spec:mapa`** pra reconciliar *Onde estamos* / *Próximo passo* — **não reimplemente** o MAPA aqui (é dono do outro comando).

6. **Reporte** o que foi gravado e onde. Se a sessão não produziu nada durável, diga isso — captura vazia é resposta válida, não force memória.
