---
description: Porta de entrada do kit pra DÚVIDA — use quando o owner perguntar como algo funciona no projeto, onde está, por que foi feito assim, ou pedir uma explicação sem pedir mudança. Responde a partir da memória e do código do projeto, com fonte, ou diz "não sei"; não mexe em arquivo
argument-hint: "[pergunta: ex. de onde vem o código do corretor na /v2?]"
---

**Responda sempre em português (pt-BR).**

Pergunta: **$ARGUMENTS** (sem argumento → a pergunta é o que o owner acabou de escrever).

Por que existe: dúvida respondida "de cabeça" vira suposição, e o owner já disse *"não quero
suposições"* — o projeto tem a resposta escrita na memória e nas specs. Este comando garante que ela
seja lida antes.

## O trilho

**1. Leia o destilado antes de responder**, nesta ordem: `docs/superpowers/MAPA.md` →
`memory/MEMORY.md` (o gatilho que bate → `memory/indice/<família>.md` → a memória) →
`docs/specs/<assunto>.md` (o "Estado atual") → `docs/decisoes.md`. Faltou? Abra o código que responde.
Abra só o que o gatilho apontar, nunca a pasta inteira.

**2. Responda com fonte ou diga "não sei".** Cada fato sai de um arquivo aberto nesta janela
(`arquivo:linha`) ou do que o owner disse. Sem fonte, diga **"não sei"** e diga o que abriria ou
perguntaria. Responda só o que foi perguntado, do tamanho da pergunta, na língua do owner.

**3. Não edite nada.** Dúvida não muda arquivo, não roda migração, não abre branch. Consulta só de
leitura (banco, log, git) pode, se ajudar a responder.

**4. Owner contesta a resposta?** Mostre a memória ou o código que a sustenta (`arquivo:linha` e o
trecho) antes de recuar. Se a memória estiver velha, diga — corrigir é outra tarefa.

**5. Encaminhe quando a resposta revelar outra coisa** — em 1 linha, sem fazer:
- algo quebrado ou diferente do esperado → **`/mss-spec:bug`**;
- algo novo a construir ou mudar → **`/mss-spec:nova-feature`**;
- algo pra depois → `/mss-spec:to-dolist adicionar <assunto>`.
