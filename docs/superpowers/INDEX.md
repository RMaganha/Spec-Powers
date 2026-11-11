<!-- Índice de tarefas ABERTAS do próprio kit mss-spec (dogfood). 1 linha por tarefa, mantido à mão.
     Lido na PARTIDA — por isso só o que está vivo. O que ficou "pra depois" é linha do to-dolist.md com #fora-de-escopo.
     Tarefa fechada sai daqui pro docs/superpowers/INDEX-historico.md (lido sob demanda).
     Nomes em linguagem simples (os do owner) — nada de apelido-código. -->

# Índice de tarefas — mss-spec

## Em andamento

## A fazer (ordem)
6. inventário do banco vivo — `/mss-spec:analise` inventaria o SQL Server sozinho (spec `docs/specs/inventario-banco.md`) — pausada: implementado na 0.28.0; falta dogfood no projeto C# real
7. cobertura C#/.NET na análise — `Program`/`Startup`, controllers, `.csproj`, rotas (o `bpmn` e o `mapa-neural` seguem só Python) — pausada: nasce depois do dogfood do item 6
8. comando guardado inteiro na anotação — comando ou SQL que o owner vai rodar de novo é gravado completo (escopo, régua e textos prontos dos itens 8 a 15: `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`)
11. consultar a memória pela ação antes de agir — aguardando o sim do owner
12. ajudante pesquisador — lê muito e devolve só o resumo
13. conferência antes de entregar — lista do projeto alimentada pelos apontamentos do revisor (decisões do owner: `docs/specs/conferencia-antes-de-entregar.md`)
14. ajudante revisor — confere a mudança pela lista do item 13
15. teste automático do kit a cada publicação — aguardando o owner decidir entre GitLab (decisão de 2026-07-20) e GitHub
