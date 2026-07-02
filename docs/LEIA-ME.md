# Spec-Powers — kit Spec-Driven mínimo + registro (NÃO são instruções do robô ATM)

> ⚠️ **Leia primeiro:** esta pasta é um **kit/referência isolado**. Não altera o ATM Robô V2 nem o
> `CLAUDE.md` do projeto. Nada desta conversa virou memória do assistente. Os templates ficam em
> `modelo/` com nomes **neutros** (ex.: `CLAUDE.md.modelo`) de propósito, para não serem carregados como
> instrução enquanto vivem dentro deste repositório.

## O que é
Um **kit mínimo** para começar **projetos novos** (ou adotar existentes) com fluxo Spec-Driven sobre o
plugin **superpowers**. A disciplina (não codar sem OK, TDD, verificação, review) **já vem do superpowers**;
o kit só adiciona o que falta: 2 comandos nomeados, um `CLAUDE.md` enxuto e o `settings.json` correto.

## Como usar (bootstrap de um projeto novo)
Copie os arquivos de `modelo/` para o projeto, renomeando para o destino:

| Arquivo no kit | Copie para (no projeto novo) | O que é |
|---|---|---|
| `modelo/CLAUDE.md.modelo` | `CLAUDE.md` (raiz) | constituição enxuta; preencha os `<...>` |
| `modelo/settings.json.modelo` | `.claude/settings.json` | liga o superpowers (formato **objeto**) + effort |
| `modelo/comando-kickoff.md` | `.claude/commands/kickoff.md` | comando `/kickoff` |
| `modelo/comando-nova-feature.md` | `.claude/commands/nova-feature.md` | comando `/nova-feature` |
| `modelo/MEMORY.md.modelo` | `memory/MEMORY.md` | índice da memória do projeto (vazio, só cabeçalho) |
| `modelo/AMBIENTE.md.modelo` | `docs/AMBIENTE.md` | referência de ambiente corporativo MSIG (rede, proxy, Postgres, SQL Server, Azure) — fatos fixos prontos + padrões com `<...>` a preencher |

Depois, **dentro do projeto**: rode **`/kickoff "sua ideia"`** (entrevista → gera o `CLAUDE.md`) e, por
feature, **`/nova-feature <nome>`** (spec com Critérios de Aceite → tasks → executa uma por vez com TDD + verificação).

## Como funciona (resumo)
- **`/kickoff`** te entrevista (1 pergunta por vez) e escreve o `CLAUDE.md`. Serve para projeto **novo e existente** (faz scan antes).
- **`/nova-feature`** define os **Critérios de Aceite** (suas validações), espera seu OK, gera as tasks e executa **uma por vez** (teste → código → roda e cola a saída).
- **Memória** = pasta `memory/` do **projeto** (dentro do repo, versionada, índice em `memory/MEMORY.md` — NÃO em `~/.claude/projects/<proj>/memory/`), nunca no `CLAUDE.md`. **Estado** = plan files do superpowers. **"O que não fazer"** = seção "Regras críticas" do `CLAUDE.md`.
- **Sem hooks bloqueantes** (quebravam no Windows e travavam o bootstrap); a orquestração vem das skills do superpowers + do `CLAUDE.md` sempre carregado.

## Arquivos desta pasta
- `modelo/` — os 6 templates a copiar (tabela acima).
- `ROTEIRO-SPEC-DRIVEN.md` — o **playbook** (manual do owner): princípio, fluxo, tipos de mudança, DoD, banco, memória/estado, ambiente corporativo, o que ficou adiado.
- `referencia-spec-driven.md` — o **porquê**: análise do CLI `@igoruehara/spec-driven` × superpowers, comparação, caminho recomendado e lições do ATM.
- `PROMPT-MAPEAR-AMBIENTE.md` — prompt avulso (não copiado pro projeto novo) pra rodar no Claude Code de **qualquer** projeto existente e comparar as convenções dele com o padrão MSIG documentado em `modelo/AMBIENTE.md.modelo`. Exige acesso a arquivo exato (Claude Code, ou configs anexados no chat).
- `PROMPT-CONHECER-PROJETO.md` — prompt avulso complementar: entender O QUE um projeto faz (propósito, arquitetura, funcionalidades, regras de negócio) em vez de infra/deploy. Funciona em qualquer chat, não só Claude Code.
- `LEIA-ME.md` — este guia.

## Além do kit: skill global de precedentes
Fora desta pasta, em `~/.claude/skills/precedentes-msig/`, existe uma skill do Claude Code (disponível em
**qualquer** projeto, não só os que usam este kit) que indica qual projeto MSIG já resolveu um problema
parecido (ex.: RAG/busca vetorial, extração de PDF com LLM) antes de desenhar do zero. Cresce por linha,
sem cerimônia — ver o próprio arquivo da skill para o formato.

## Limites (a pedido do owner)
- Nenhuma alteração no `CLAUDE.md` do projeto (V2 ou diretório pai), nem na memória do assistente.
- Nenhuma mudança de código ou no comportamento do ATM Robô.
