---
description: Porta de entrada do kit pra TAREFA do dia a dia — ajuste pequeno, operação (rodar script, carga, deploy), consulta, documentação, comando git: o que você já sabe o que quer e onde, cabe numa conversa e não muda o que uma spec promete. Não é bug, dúvida, feature nova nem análise. Lê só o que a tarefa toca, plano em até 5 linhas, OK, prova real antes de "pronto"
argument-hint: "[o que fazer: ex. trocar o texto do botão de adesão; passar os comandos git de dev e main]"
---

**Responda sempre em português (pt-BR).**

Tarefa: **$ARGUMENTS** (sem argumento → a tarefa é o que o owner acabou de pedir).

Por que existe: o kit tinha porta pra erro (`/mss-spec:bug`), pergunta (`/mss-spec:duvida`), coisa nova
(`/mss-spec:nova-feature`) e projeto existente (`/mss-spec:analise`) — e nenhuma pro **dia a dia**, que é a
maior parte do trabalho. Sem porta, a tarefa comum entrava direto pelo superpowers ou por nada, e a memória,
a spec e os ambientes ficavam de fora. Desde a 0.50.0 o hook `kit_primeiro.py` nega skill do superpowers sem
um comando do kit na conversa: esta é a porta do resto.

## O trilho (curto; é o comando mais usado)

**0. É tarefa mesmo?** Uma linha, antes de tudo:
- algo **quebrou** ou funciona diferente do esperado → **`/mss-spec:bug`**;
- é uma **pergunta** sobre o projeto, sem mudar nada → **`/mss-spec:duvida`**;
- é **comportamento novo**, ou muda o que o "Estado atual" de uma spec viva promete → **`/mss-spec:nova-feature`**;
- é projeto que **já existia** e o kit ainda não conhece → **`/mss-spec:analise`**.
Tarefa é o que sobra: você já sabe **o que** quer e **onde**, cabe numa conversa, e nenhuma spec passa a
mentir depois dela. Virou outra coisa no meio? Pare e troque de porta, dizendo em 1 linha.

**1. Leia só o que a tarefa toca** (destilado antes da fonte): `docs/superpowers/MAPA.md` (onde estamos) →
`memory/MEMORY.md` (o gatilho que bate → `memory/indice/<família>.md` → a memória) → a spec viva do assunto,
se existir (`docs/specs/<assunto>.md`, "Estado atual") → **`docs/AMBIENTES.md`**, se a tarefa cita local,
homologação, produção, servidor, variável ou App Setting (nome, valor, quem acessa o quê — nunca chute, nunca
proponha passo num ambiente que o owner não acessa) → **`memory/DIARIO.md`** (últimos 7 dias), se o assunto já
apareceu. Nunca a pasta inteira.

**2. Plano em até 5 linhas, e o OK do owner:** o que muda · em que arquivos · como você vai **provar** (teste,
consulta, tela, `git status`) · o que **não** muda. Fato que falta e muda o plano → **pergunte antes**, uma
pergunta. **Tarefa só de leitura** (consulta, relatório, `git log`, comparar arquivos) **não espera OK**:
execute e mostre. Mudança em arquivo, banco, ambiente ou git **espera**.

**3. Faça, no nível mínimo ou médio** (`/mss-spec:modo`; TDD e verificação não mudam de nível):
- muda código → branch **a partir da principal atualizada**, pelas regras de git do projeto (se o git é do
  owner, entregue os comandos em passo a passo, um por bloco, com o que conferir na saída);
- o teste que já cobre o trecho roda **antes e depois**; teste **novo** só se mudou comportamento;
- mudou o que o "Estado atual" de uma spec descreve → atualize a spec na mesma tarefa (regra crítica 6);
- operação em ambiente (carga, deploy, consulta a banco vivo) → **só pelo caminho que o `docs/AMBIENTES.md`
  diz** que você ou o owner acessam; banco de produção, só leitura; publicar é ato do owner (hook);
- documentação → o arquivo que já existe sobre o assunto, nunca um paralelo.

**4. Prova antes de dizer "pronto":** a saída **real**, colada — teste verde com o comando, resultado da
consulta, `git status --short`/`git log --oneline -3` depois do commit, a tela conferida. Não deu? Diga o que
falhou, com a saída; nunca "deve ter funcionado".

**5. Fecho em 1 linha** — o que mudou e onde — e pare. Apareceu assunto de fora? **Não faça**: ofereça
`/mss-spec:to-dolist adicionar <assunto>`. Houve decisão, aprendizado ou armadilha? Ofereça
`/mss-spec:memory capturar` (grava a memória **e** o diário da sessão juntos; o hook `diario_junto.py` cobra
se um sair sem o outro). O owner conduz o ritmo: nada de pergunta não pedida no fim.
