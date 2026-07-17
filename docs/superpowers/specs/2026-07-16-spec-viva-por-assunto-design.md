# Design — Spec viva por assunto no kit mss-spec

**Data:** 2026-07-16 · **Status:** aprovado (brainstorming) · **Branch:** plugin-v2

## Problema
Hoje o kit produz a spec como um **par datado** (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`),
congelado na criação. O `INDEX.md` já indexa por assunto e o `CLAUDE.md` já manda lê-lo — então
**descobrir** a spec ao voltar num assunto já funciona (no nível alto). O que **não** funciona é ela
**estar atualizada**:

1. No **nível médio (o default)**, o `nova-feature` não gera doc de spec nenhum — a maioria das
   features não tem spec pra reler; o estado vive só em código + `CLAUDE.md` + `memory/`.
2. No **nível alto**, existe o doc, mas ele é o **retrato de nascimento** da feature. Se ela evoluiu
   depois (via mudanças médias ou fixes), o doc datado ficou velho e ninguém reescreveu.

Consequência concreta: spec desatualizada faz o assistente **codar errado numa tarefa futura**
(lê o valor antigo na spec e reintroduz um bug já corrigido).

## Enquadramento (Böckeler)
Birgitta Böckeler distingue **spec-first** (spec antes, código depois, spec congela), **spec-anchored**
(spec continua viva e é atualizada na evolução) e **spec-as-source** (humano só edita a spec). O kit
hoje é spec-first. Esta mudança move a **spec** para **spec-anchored**, mantendo o **plano** como
spec-first (efêmero). Cada artefato no formato que combina com ele.

## Decisão
Substituir o par datado, **como spec**, por uma **spec viva por assunto**: um arquivo por tema,
nomeado pelo assunto, editado no próprio lugar, com seções fixas de **Estado atual** + **Histórico**.
O **plano/tasks continua datado e efêmero** em `docs/superpowers/plans/` (saída do `writing-plans`;
plano é retrato de uma rodada de trabalho, não tem "estado atual" a manter).

## Desenho

### 1. Artefato e local
- `docs/specs/<assunto>.md` — kebab-case pelo tema (ex.: `docs/specs/exportacao.md`). Pasta nova.
- O git guarda o diff completo de cada edição; o Histórico guarda a narrativa legível.

### 2. Formato do arquivo
```markdown
# Spec: <Assunto>

## Estado atual
<reescrito sempre pra refletir como o comportamento está HOJE>

## Histórico
- YYYY-MM-DD — criado: <resumo>.
- YYYY-MM-DD — <o que mudou> (motivo: <por quê>).
```
- **Estado atual** = a verdade de agora (o assistente lê isto pra saber como está, sem git).
- **Histórico** = 1 linha por mudança material.

### 3. Peso por nível de cerimônia
- **médio (default):** `Estado atual` enxuto (2-4 frases) + linha de Histórico. "Cartão do assunto".
- **alto:** o design completo do `brainstorming` (objetivo, Critérios de Aceite, decisões, fora de
  escopo) **é** o `Estado atual`, gravado direto em `docs/specs/<assunto>.md` (a skill do superpowers
  permite override do local da spec) — não mais no doc datado.
- **mínimo:** sem spec (igual hoje).

### 4. Criar vs. atualizar (lógica nova no `nova-feature`)
Ao rodar `/mss-spec:nova-feature <nome>`, o comando **procura em `docs/specs/` e no `INDEX.md` uma
spec do mesmo assunto**. Achou → **atualiza** (reescreve Estado atual + acrescenta linha no Histórico).
Não achou → **cria**. Se o casamento de assunto for ambíguo, **pergunta ao owner** antes de decidir.

### 5. Quem toca a spec, por tipo de mudança
| Tipo | Toca a spec? |
|---|---|
| **feat** | Sim — cria ou atualiza `docs/specs/<assunto>.md`. |
| **fix** | **Só se alterar o comportamento descrito numa spec existente** → atualiza Estado atual + 1 linha de Histórico. Se o fix só faz o código bater no que a spec já dizia, não toca. |
| **refactor** | Por definição não muda comportamento → quase nunca toca. Só se um "refactor" mudar sorrateiramente um default/limite descrito na spec. |
| **chore/docs/spike** | Não. |

Motivo do fix/refactor tocarem a spec (item "ligado"): sem isso a spec **mente** depois de um fix que
muda comportamento (ex.: limite de export baixado de 10k→5k no código, mas a spec ainda diz 10k), e o
assistente reintroduz o bug ao ler o valor velho numa tarefa futura.

### 6. INDEX.md e plano
- `docs/superpowers/INDEX.md` continua o índice de tarefas, mas o link **sempre existe** e aponta pro
  `docs/specs/<assunto>.md` (nome estável, sem data). Some o caso "linha sem link" do médio.
- O plano/tasks datado em `docs/superpowers/plans/` não muda.

## Arquivos do kit afetados
- `commands/nova-feature.md` — passos 1-3 e 5: gravar/atualizar `docs/specs/<assunto>.md`; lógica
  criar-vs-atualizar; médio passa a gerar spec enxuta; regra de fix/refactor tocarem a spec.
- `templates/CLAUDE.md` — mapa de arquivos (`docs/specs/`), instrução de leitura, e regra de que
  fix/refactor que mudam comportamento atualizam a spec do assunto.
- `templates/INDEX.md` — comentário de formato: link aponta pra `docs/specs/<assunto>.md`.
- `docs/ROTEIRO-SPEC-DRIVEN.md` — seção Fluxo + Tipos de mudança + justificativa spec-anchored.
- `docs/referencia-spec-driven.md` — nota curta da taxonomia (Böckeler) como decisão explícita.

## Fora de escopo (segue adiado, como já estava)
`docs/ESTADO.md`, dashboard de % de progresso, hooks (bloqueantes ou não), gate AC→teste no CI,
versionamento manual tipo `spec_v1/v2` (o git já versiona), e migração das specs datadas antigas
(a convenção vale só pra frente; nada no projeto atual muda).
