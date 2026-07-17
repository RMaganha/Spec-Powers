# regras de branch e escopo — design

Data: 2026-07-17 · feature do próprio kit mss-spec (branch `feature/regras-branch-e-escopo`).

## Objetivo
Ensinar o kit a (1) sempre abrir a branch de uma tarefa **a partir da principal atualizada**, nunca de outra branch; e (2) **alertar — sem travar —** quando um 2º assunto não relacionado aparece na mesma janela, empurrando-o pro to-dolist antes de abrir uma nova janela.

## Estado atual
As duas regras estão escritas como convenção (doc/comandos), não como automação:
- **Branch da principal:** a regra Git do `templates/CLAUDE.md` e a seção Git/branch do `nova-feature` mandam `git checkout <principal> && git checkout -b <tipo>/<nome>` — a branch nasce sempre da principal atualizada, **nunca de outra branch**. Antes a redação só proibia codar direto na principal, mas não impedia ramificar de uma feature em andamento.
- **Um assunto por janela:** há uma regra crítica no `templates/CLAUDE.md` — ao detectar um 2º assunto não relacionado, o assistente **para e alerta**, oferece `/mss-spec:to-dolist adicionar <assunto>` e sugere fechar o escopo atual + abrir nova janela. É **alerta, não trava**: o owner pode mandar seguir mesmo assim. `nova-feature` e `to-dolist` apontam pra esse protocolo.

## Problema
Duas dores observadas: (a) a `feature/doctor` "inchou" e virou a linha principal de fato porque branches saíam de branches — ponto de partida imprevisível; (b) uma mesma janela acumulava assuntos diferentes, poluindo o contexto e a branch.

## Critérios de aceite
1. DADO o `templates/CLAUDE.md`, QUANDO leio a regra Git, ENTÃO ela manda abrir a branch **a partir da principal** (`git checkout <principal>` antes do `-b`) e diz explicitamente "nunca a partir de outra branch".
2. DADO o `commands/nova-feature.md`, QUANDO instrui abrir a branch, ENTÃO manda partir da principal (não só "não codar na principal").
3. DADO uma janela com tarefa em andamento, QUANDO surge um 2º assunto não relacionado, ENTÃO o assistente **alerta** (não trava): oferece `/mss-spec:to-dolist adicionar` e sugere fechar o escopo + abrir nova janela. A regra vive nas "Regras críticas" do `templates/CLAUDE.md`; `nova-feature` e `to-dolist` a apontam.
4. DADO a suíte, QUANDO rodo o smoke test, ENTÃO `test_regras_branch_e_escopo_wiring()` passa (afirma as strings de convenção nos arquivos certos).

## Design
- **Só doc/comandos + teste** — sem hook e sem checagem automática (é convenção autoaplicada pelo assistente, verificada por smoke test de strings, no mesmo padrão dos outros wirings do kit).
- **Regra 2 é alerta, não bloqueio:** a redação instrui o assistente a *parar e perguntar*, nunca a recusar. Detectar "assunto diferente" é julgamento semântico — nenhum hook faz bem, e hook bloqueante já é fora de escopo do kit.

## Fora de escopo
Hook (bloqueante ou não); checagem automática de branch/escopo no `doctor` ou `compliance`; mexer em `effortLevel`. Podem entrar depois, em outra janela.

## Arquivos tocados
- `templates/CLAUDE.md` — regra Git (partir da principal) + regra crítica "um assunto por janela"
- `commands/nova-feature.md` — seção Git/branch + ponteiro pro protocolo de escopo
- `commands/to-dolist.md` — 1 linha ligando ao protocolo do 2º assunto
- `tests/test_smoke_kit.py` — novo `test_regras_branch_e_escopo_wiring()`
- `docs/superpowers/INDEX.md` — 1 linha da tarefa

## Histórico
- 2026-07-17 — criado: design das regras de branch (partir da principal) e escopo (um assunto por janela), aprovado no chat.
