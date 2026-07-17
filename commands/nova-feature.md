---
description: Abre/evolui uma feature (spec viva por assunto → tasks) e mantém o índice de tarefas; branch antes de codar
argument-hint: "[nome-da-feature]"
disable-model-invocation: true
---

Feature: **$ARGUMENTS**

> **Um assunto por janela:** esta janela é pra **esta** feature. Se, no meio dela, surgir um 2º assunto não relacionado, **não emende** — alerte, ofereça `/mss-spec:to-dolist adicionar <assunto>`, feche o escopo atual e abra **uma nova janela** pro outro assunto (ver a regra homônima no `CLAUDE.md`). É alerta, não trava.

Conduza no **nível de cerimônia atual** (padrão **médio**; troque com `/mss-spec:modo`). Os passos abaixo descrevem o nível **alto**; ajuste ao nível ativo:
- **médio**: design curto (poucas frases, sem doc de spec grande) + plano curto em tópicos + execução **inline** — sem subagentes nem dupla revisão. Ainda: OK antes de codar, TDD, verificação.
- **mínimo**: pule spec/plano; alinhe em 1-2 perguntas e vá direto ao código com TDD leve.
- **alto**: siga os passos como estão (spec doc + `writing-plans` + `subagent-driven-development`).

1. **Localize a spec do assunto**: procure em `docs/specs/` e no `docs/superpowers/INDEX.md` uma spec do mesmo assunto de **$ARGUMENTS**. Achou → você vai **atualizá-la** (reescrever "Estado atual" + acrescentar 1 linha no "Histórico"). Não achou → vai **criá-la**. Se o casamento de assunto for **ambíguo**, pergunte ao owner antes de decidir.
2. Invoque **superpowers:brainstorming** para esta feature: objetivo (1 frase), **Critérios de Aceite testáveis** (formato "DADO… QUANDO… ENTÃO…") e fora de escopo. **Espere o OK do owner** antes de qualquer código.
3. **Grave/atualize a spec viva** `docs/specs/<assunto>.md` (kebab-case pelo tema), com as seções fixas **Estado atual** + **Histórico**:
   - **alto**: o design completo do brainstorming (objetivo, Critérios de Aceite, decisões, fora de escopo) **é** o "Estado atual".
   - **médio**: "Estado atual" enxuto (2-4 frases) + fora de escopo em 1 linha.
   - **mínimo**: pule este passo (sem spec).
   - Ao **criar**, a 1ª linha do Histórico é `- <data> — criado: <resumo>.`; ao **atualizar**, reescreva o "Estado atual" e acrescente `- <data> — <o que mudou> (motivo: <por quê>).`. O "Estado atual" **sempre** reflete como o comportamento está HOJE (o git guarda o diff; o Histórico, a narrativa legível).
   - **Atualize o índice** `docs/superpowers/INDEX.md`: 1 linha, link **sempre** pra spec viva — `- [<assunto>](../specs/<assunto>.md) — <objetivo em 1 frase> — aberta`. (nível mínimo, sem spec: `- <assunto> — <objetivo> — aberta`, sem link.)
4. Invoque **superpowers:writing-plans**: quebre em tasks pequenas e ordenadas, cada uma cobrindo ≥1 Critério de Aceite por teste. O plano é **datado/efêmero** em `docs/superpowers/plans/` — não é a spec.
5. Execute **uma task por vez** (superpowers:executing-plans / subagent-driven-development): TDD (teste do AC → vermelho → código → verde) e **rode e cole a saída** (verification-before-completion) antes da próxima. **Protocolo de log:** quando uma task for **gerar arquivos** e o projeto tiver o padrão de log montado (`config/logging.py`), antes de escrevê-los **liste os arquivos que vai criar com resumo de 1 linha cada** e **pergunte "logs em todos ou em quais?"** — instrumente com `logger = logging.getLogger(__name__)` só os escolhidos (regra de bolso: banco/API/regras de negócio sim, script simples não). Ver `/mss-spec:log`.
6. Ao concluir: `requesting-code-review` → **rode `/mss-spec:plano-teste`** (a suíte inteira; as validações desta feature dobram no baseline anti-regressão, que só é atualizado se passar 100%) → se a feature criou/alterou **rota ou endpoint** (ainda mais de **integração**, que outro sistema chama), revise contra `docs/SEGURANCA.md` (authz, entrada validada, `AUTH_TOKEN_ATIVO`/Bearer) — ou rode `/mss-spec:seguranca`. Confirme que o "Estado atual" da spec bate com o que foi entregue. Mude o status da linha no `INDEX.md` para `fechada`. Se surgiu regra durável, 1 linha em "Regras críticas" do `CLAUDE.md`; se surgiu aprendizado durável, grave em `memory/` (arquivo + linha no `MEMORY.md`); se houve **decisão transversal** (arquitetura/lib/padrão, não específica do assunto), 1 linha em `docs/decisoes.md`. **Antes de integrar, rode `/mss-spec:release`** — o gate de pré-publicação que confere testes/versão/CHANGELOG/segurança/specs num veredito só; verde → `finishing-a-development-branch` (merge/PR).

**Git/branch:** **abra a branch da feature ANTES de codar, a partir da principal atualizada** (`git checkout <principal> && git checkout -b feature/<nome>`; `<principal>` = `main`/`master`) — nunca code direto na principal e **nunca ramifique de outra branch** (a feature sempre nasce da principal; ao integrar, volte pra ela). Para isolamento maior, use worktree (`superpowers:using-git-worktrees`). `git push` só quando o owner pedir.

Mudanças que **não** são feature (não precisam deste comando): **bugfix** → teste que reproduz o bug é a spec → corrige → verifica; **refactor** → gate é "testes verdes"; **chore/docs** → sem spec. **Porém**, se um bugfix/refactor **alterar o comportamento descrito numa spec existente** em `docs/specs/`, atualize o "Estado atual" dela + 1 linha no "Histórico" — senão a spec passa a mentir e induz o assistente a codar errado (reintroduzir o bug) numa tarefa futura.
