<!-- Índice de tarefas ABERTAS do próprio kit mss-spec (dogfood). 1 linha por tarefa, mantido à mão.
     Lido na PARTIDA — por isso só o que está vivo. O que ficou "pra depois" é linha do to-dolist.md com #fora-de-escopo.
     Tarefa fechada sai daqui pro docs/superpowers/INDEX-historico.md (lido sob demanda).
     Nomes em linguagem simples (os do owner) — nada de apelido-código. -->

# Índice de tarefas — mss-spec

## Em andamento
- [upgrade em uma rodada só](specs/2026-07-16-upgrade-design.md) — o `/mss-spec:upgrade` trata migração do `CLAUDE.md`, to-dolist e categorias numa conversa, uma branch, um commit por passe, stash único do pendente — aberta

## A fazer (ordem)
6. inventário do banco vivo — `/mss-spec:analise` inventaria o SQL Server sozinho (spec `docs/specs/inventario-banco.md`) — pausada: implementado na 0.28.0; falta dogfood no projeto C# real
7. cobertura C#/.NET na análise — `Program`/`Startup`, controllers, `.csproj`, rotas (o `bpmn` e o `mapa-neural` seguem só Python) — pausada: nasce depois do dogfood do item 6
