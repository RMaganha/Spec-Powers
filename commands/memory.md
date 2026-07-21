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

Você vai **trazer pro repositório** a memória que porventura ficou na pasta nativa do Claude (volátil, fora do git). **Não-destrutivo**: só copia — a nativa fica intacta como fallback.

1. **Ache a pasta nativa deste projeto** em `~/.claude/projects/`. O nome dela é o caminho absoluto do projeto com os separadores virando `-` (ex.: `C:\projetos\MeuApp\Azure` → algo como `C--projetos-MeuApp-Azure`). Se não tiver certeza de qual é, **liste** `~/.claude/projects/*/memory/` e **confirme comigo** antes de copiar (não chute a pasta errada).
2. **Se ela existir e tiver arquivos:** copie os `*.md` (menos o `MEMORY.md`) para `<repo>/memory/`, criando a pasta se preciso. **Não sobrescreva** um arquivo de mesmo nome já existente no repo sem me avisar.
3. **Índice:** funda as linhas do `MEMORY.md` nativo no `memory/MEMORY.md` do repo (crie do template do plugin se não existir); não duplique linhas.
4. **Commit (fecha a durabilidade):** só a memória vira durável depois de commitada. Se for um repo git:
   - garanta que existe `.gitignore` protegendo `.env` (crie de `${CLAUDE_PLUGIN_ROOT}/templates/gitignore` se faltar);
   - stage **nominal** — `git add memory/` (e `docs/` se houver doc a versionar). **NUNCA** `git add .`/`-A` (varreria `.env`/segredos);
   - rode `git status` e confira que **nada sensível** entrou;
   - `git commit -m "chore: resgata memoria para o repo (versionada)"`. **Local, sem `git push`** (regra "Git local-only" do `CLAUDE.md`: push só a pedido do owner).
   - Se NÃO for repo git, avise e pergunte antes de `git init` (não inicialize sozinho).
5. **Reporte** o que foi copiado, de onde, e o commit. Lembre: ficam **duas cópias** (repo = fonte durável; nativa = fallback intocado); memórias **novas** já vão direto pro repo (regra no `CLAUDE.md`).
6. Se a pasta nativa não existir ou estiver vazia, diga que não há nada a resgatar — sem inventar.

---

## Modo: capturar

Você vai **destilar esta sessão** e gravar o que é durável, pra parar de depender de eu lembrar no fecho. **Destile do contexto atual da conversa** (o que foi conversado/decidido + o `git diff` da branch) — **não releia arquivos** (captura barata). O essencial é o **rastro do raciocínio**: as decisões e, sobretudo, os **pivôs** (o que se cogitou, por que foi repensado, pra onde ajustou) — não só o estado final.

**Nunca invente.** Só grave o que aconteceu de fato nesta sessão / está no diff. Na dúvida, deixe de fora.

1. **Filtre `<private>`.** Qualquer trecho marcado `<private>…</private>` (na conversa ou no rascunho) **nunca** entra em nada versionado — descarte antes de rascunhar.

2. **Monte os rascunhos, roteando cada achado pro lar durável certo** (não crie destino novo):
   - **decisão transversal** ("X em vez de Y porque Z", arquitetura/lib/padrão) → 1 linha em **`docs/decisoes.md`**;
   - **decisão de escopo** ("decidiu-se NÃO fazer W") → seção **"Fora de escopo"** do **`docs/superpowers/INDEX.md`** (é o insumo anti-re-litígio: semanas depois isso me impede de repropor o que já foi descartado);
   - **narrativa do assunto** ("tentou-se A, virou B") → **Histórico** da spec viva em `docs/superpowers/specs/`;
   - **aprendizado durável atemporal** (regra/gotcha que vale além deste assunto) → arquivo em **`memory/`** (schema de frontmatter: `user`|`feedback`|`project`|`reference`) + 1 linha no índice **`memory/MEMORY.md`**;
   - **resumo compacto da sessão** → **`memory/sessions/<data>-<assunto>.md`** + 1 linha no índice **`memory/DIARIO.md`** (data + assunto + gist → aponta o arquivo). Estrutura do resumo (curto): **Conversamos · Pivôs · Rejeitado · Fizemos · Próximo** — os **Pivôs** são o coração.

3. **Não duplicar.** Antes de escrever, consulte os índices (`MEMORY.md` / `DIARIO.md` / seções do INDEX) — se o fato/entrada já está coberto, **atualize** o existente em vez de criar duplicata.

4. **Mostre TODOS os rascunhos pro meu OK** (o que vai pra cada lar) e **não grave nada antes de gravar** sem meu "ok". Aplicado o OK, grave com stage **nominal** (`git add memory/ docs/` — nunca `git add .`/`-A`), confira `git status` (nada sensível) e commit local (sem `git push`).

5. **Delegue o MAPA.** Ao final, **rode `/mss-spec:mapa`** pra reconciliar *Onde estamos* / *Próximo passo* — **não reimplemente** o MAPA aqui (é dono do outro comando).

6. **Reporte** o que foi gravado e onde. Se a sessão não produziu nada durável, diga isso — captura vazia é resposta válida, não force memória.
