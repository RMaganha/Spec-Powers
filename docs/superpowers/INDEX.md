<!-- Índice de tarefas ABERTAS do próprio kit mss-spec (dogfood). 1 linha por tarefa, mantido à mão.
     Lido na PARTIDA — por isso só o que está vivo + a seção anti-re-litígio 'Fora de escopo'.
     Tarefa fechada sai daqui pro docs/superpowers/INDEX-historico.md (lido sob demanda).
     Nomes em linguagem simples (os do owner) — nada de apelido-código. -->

# Índice de tarefas — mss-spec

## Em andamento
- [partida em dois níveis](../specs/partida-no-orcamento.md) — MAPA e INDEX com topo curto e detalhe em arquivo próprio, em toda gravação — em andamento: 0.44.0 pronta na branch, falta o merge do owner
- [bug e dúvida pelo kit](../specs/bug-e-duvida.md) — bug e dúvida entram pelo kit (`/mss-spec:bug`, `/mss-spec:duvida`, `diagnostico` destravado), que chama o superpowers por baixo — aberta

## A fazer (ordem)
5. upgrade — sincroniza projeto existente com a evolução dos templates — pausada: sem commit, retomar em janela própria
6. inventário do banco vivo — `/mss-spec:analise` inventaria o SQL Server sozinho (spec `docs/specs/inventario-banco.md`) — pausada: implementado na 0.28.0; falta dogfood no projeto C# real
7. cobertura C#/.NET na análise — `Program`/`Startup`, controllers, `.csproj`, rotas (o `bpmn` e o `mapa-neural` seguem só Python) — pausada: nasce depois do dogfood do item 6

## Fora de escopo (não fazer)

- Movido para [FORA-DE-ESCOPO.md](FORA-DE-ESCOPO.md) em 2026-10-27 — decisões de NÃO fazer; consulte antes de propor algo novo (o recall também lê este arquivo).
