# 2026-08-18 — evals e context engineering: a falha vira caso, o caso vira guardrail (v0.19.0)

## Conversamos
Janela aberta pelo item **4** do to-dolist, anotado no mesmo dia a partir de um artigo da OpenAI sobre
evals: três peças — premissas explícitas no brainstorming, premissa derrubada virando memória
`feedback_*`, e o `capturar` colhendo também o que deu certo — com a nota "sem harness/plataforma de
eval, só prosa nos comandos".

## Pivôs
- **O owner cortou meu primeiro desenho por raso.** Eu tinha transcrito o item em 3 bullets e chamado
  de design. Ele: *"isso parece meio razo em cobrir o eval e context engenering"*. A nota do to-dolist
  delimitava o **mecanismo** (sem harness), não a **profundidade** — e eu não declarei que estava
  lendo assim. Virou o caso **F-011** e a memória [[feedback-item-de-backlog-nao-e-design]].
- **A pesquisa virou o eixo, e a fonte importava.** Ele mandou pesquisar *"na sua documentação do
  claude, não de terceiros"*. A doc da Anthropic destampou 4 mecanismos que o kit não usava:
  `.claude/rules/` com `paths:`, o teto de 200 linhas/25 KB do índice de auto-memory, o fato de que só
  o índice da pasta **nativa** auto-carrega, e "bloated CLAUDE.md files cause Claude to ignore your
  actual instructions". Sem isso o desenho resolvia o sintoma errado →
  [[feedback-pesquisar-fonte-primaria-antes-de-desenhar]].
- **O achado que mudou tudo:** varrendo o `memory/`, o índice **nativo** tinha **6** entradas e o do
  repo, **33**. Ou seja: 27 memórias duráveis nunca entravam na sessão sozinhas. Isso reposicionou a
  queixa dele (*"eu tenho que ficar te lembrando das coisas… se eu esquecer isso fica totalmente
  perdido"*) de "problema de armazenamento" para **problema de recall**, e a peça E deixou de ser
  "espelhar o índice na nativa" (8 KB duplicados, desatualizando) para **ponteiro de uma linha**.
- **Descobri uma memória que mentia.** A `feedback_consultar_destilado_antes_da_fonte` afirmava "numa
  sessão nova o `MEMORY.md` já vem carregado" — falso, e era exatamente a crença que sustentava o
  problema. Corrigida na captura.
- **Dogfood no meio da execução:** F-011 e F-012 entraram no corpus como `aberto` (guardrail ainda não
  existia) e só viraram `fechado` quando T3 e T6 pousaram com teste. Se eu tivesse marcado "fechado"
  na hora, o corpus já nasceria mentindo.

## Rejeitado
Harness de eval que roda modelo e julga resposta · tipo novo de memória para premissa/acerto (reusam
`feedback_*`) · premissas explícitas fora do `nova-feature` · embeddings sobre a memória · `release`
**bloquear** por caso aberto.

## Fizemos
8 tasks em TDD, suíte **136 verde** (era 116): premissa **com fonte** no `nova-feature` ·
`docs/EVALS.md` com 12 casos reais · `gatilho:` nas 34 memórias e índice agrupado (8.107 → 6.972
bytes) · 3 regras path-scoped em `.claude/rules/` + molde em `templates/rules/` · ponteiro na nativa +
check 8 do `doctor` · `capturar` colhendo o acerto e podando + check 7 do `release` · proteção do
corpus no `upgrade` (achada na revisão do próprio diff) · bump 0.19.0.

## Próximo
F-010 segue **aberto** (jargão inventado ao explicar desenho — sem guardrail). Item 5 do to-dolist
(garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho) continua na fila, em janela própria.
