---
description: Porta de entrada do kit pra BUG — use quando o owner relatar erro, falha, incidente, algo que parou de funcionar ou que funciona diferente do esperado (homologação ou produção inclusas). Lê a memória do projeto antes da 1ª hipótese, chama a superpowers:systematic-debugging e escala pro /mss-spec:diagnostico se não fechar
argument-hint: "[sintoma: ex. botões aparecem pra corretor fora da lista, conversa some do painel]"
---

**Responda sempre em português (pt-BR).**

Bug em foco: **$ARGUMENTS** (sem argumento → o sintoma é o que o owner acabou de descrever).

Por que existe: nas 4 conversas do Whats analisadas em 2026-10-27, os 3 incidentes foram direto pra
`superpowers:systematic-debugging` (a regra 11 mandava isso), e o kit ficou de fora: o
`/mss-spec:diagnostico` nunca entrou, nem com o owner dizendo *"novamente perdido"*. Este comando é a
porta: o kit entra primeiro, com a memória do projeto, e chama o superpowers por baixo.

## O trilho (na ordem)

**0. Um assunto por janela.** Esta janela já tem feature aberta de outro assunto? **Não aja sobre o
bug aqui**: anote o estado no `docs/superpowers/MAPA.md`, ofereça `/mss-spec:to-dolist adicionar
<bug>` e mande abrir janela nova.

**1. O que a memória já diz — antes da 1ª hipótese.** Leia o destilado nesta ordem:
`docs/superpowers/MAPA.md` → `memory/MEMORY.md` (o gatilho que bate → `memory/indice/<família>.md` →
a memória) → `docs/EVALS.md` (a falha já aconteceu?) → `docs/decisoes.md` e a spec viva do assunto
(`docs/specs/<assunto>.md`) → **`memory/DIARIO.md`** (as entradas dos **últimos 7 dias**: o que já foi
conversado e o que ficou aberto; abra o `memory/sessions/<data>-<assunto>.md` só se o assunto bater) → e,
se o sintoma cita **local, homologação, produção, servidor, variável ou App Setting**, a seção daquele
ambiente em **`docs/AMBIENTES.md`** (nomes, valores, quem acessa o quê — nunca chute nome de servidor nem
proponha passo num ambiente que o owner não acessa). Abra só o que o gatilho apontar, nunca a pasta
inteira. Mostre ao owner
**em até 5 linhas**, cada uma com `arquivo:linha`, o que já está escrito sobre esse sintoma: como o
sistema funciona ali, casos parecidos, decisões que valem. Nada achado? Diga isso em uma linha. Só
depois disso vem hipótese.

**2. Diagnóstico.** Invoque **`superpowers:systematic-debugging`** e siga a disciplina dela. Fato que
o owner afirmou não se re-litiga — inclusive o próprio sintoma: se o que você leu (conversa, log, código)
não mostra o erro que ele relatou, **falta leitura**, não erro. Diga o que já leu, onde ainda não achou, e
pergunte o que ele viu; nunca "não se perdeu" / "não errou" (caso F-047). Precisa de evidência dele (print,
log, consulta)? Cada pedido traz **um teste que discrimina** — nunca uma lista de hipóteses pra ele testar
uma a uma.

**3. Não fechou em 2 rodadas** — ou o owner disse que você está perdido, teimoso ou repetindo? **Pare e
invoque `mss-spec:diagnostico`** (o trilho completo: tabela de fatos do owner, diff contra o que
funciona, condição real). Não espere ele pedir.

**4. Owner contesta algo que a memória diz?** **Mostre a memória** (`arquivo:linha` e o trecho)
**antes de mudar o código ou o desenho**. Ou ela está velha (aí ela é corrigida junto), ou o owner
lembrou diferente — quem decide é ele, vendo os dois. Mudar o código pra agradar, contra a memória
que você mesmo citou, foi o retrabalho do nova-feature no Whats (26/10).

**5. Causa fechada → correção.** Apresente a causa e a correção em poucas linhas e **espere o OK**.
Depois:
- branch `fix/<nome>` a partir da principal atualizada (regras de git do projeto valem: se o git é
  do owner, entregue os comandos em passo a passo);
- **teste que reproduz o bug** primeiro (vermelho pelo motivo certo) → correção → verde → suíte
  inteira do `docs/superpowers/PLANO-TESTE.md`, com a saída colada;
- a correção mudou um comportamento descrito numa spec? Atualize o "Estado atual" dela (regra 6).

**6. Virou feature?** Se a correção pede comportamento novo (tabela nova, regra de negócio nova, tela
nova), **pare**: isso não é bug. Diga ao owner e siga pelo **`/mss-spec:nova-feature`**.

**7. Fecho — só o que o owner pedir.** Ofereça em 1 linha, sem rodar sozinho: registrar a armadilha
(sintoma → causa → correção) na memória pelo `/mss-spec:memory capturar` e, se o assistente alongou
o diagnóstico (hipótese repetida, fato do owner contestado, memória ignorada), o caso no
`docs/EVALS.md`. Testar em homologação antes de fechar é escolha dele.
