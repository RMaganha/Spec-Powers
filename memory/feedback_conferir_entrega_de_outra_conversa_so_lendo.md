---
name: feedback-conferir-entrega-de-outra-conversa-so-lendo
description: Conferir a entrega que outra conversa fez na mesma pasta é só LER (git, spec, o resultado da suíte que ela registrou) — nunca rodar suíte nem git que troque estado com a pasta em uso
gatilho: quando o owner pedir pra ver se está OK o que outra conversa entregou ou está entregando neste mesmo projeto
sem_gatilho_de_acao: a condição (outra conversa usando a pasta) não aparece no texto do comando nem da resposta
metadata:
  type: feedback
---

Em 2026-11-11 o owner pediu, sobre a parte 2 da memória em tabela feita em outra conversa: *"consegue ver se está
OK, e se estiver qual o prompt para a próxima etapa"*. Rodei a suíte inteira na mesma pasta; a outra conversa trocou
de branch pra fazer o merge no meio e saíram 35 falhas falsas. Ele: *"eu pedi uma coisa vc fez outra NOVAMENTE,
interferiu na outra suite"* e, depois, *"lá mesmo rodou a suite inteira … não tem pq rodar aqui é gastar token a
toa"*. Nas conferências seguintes passou a pedir: *"seja breve não execute a suite novamente"*.

**Why:** duas conversas na mesma pasta trocam a branch uma da outra (F-059) e disputam a máquina; e a conversa que
entrega já rodou a suíte e gravou o resultado no `docs/superpowers/PLANO-TESTE.md`. Rodar de novo custa tempo, tokens
e pode derrubar o teste dela.

**How to apply:** conferência de entrega de outra conversa =
1. `git status -sb` e `git log --oneline -4`, **só leitura**: em que branch a pasta está, se entrou na `main`, se
   há arquivo solto, se foi publicado;
2. a entrega contra as decisões do owner (a seção "Tudo o que o owner decidiu" da spec), item por item;
3. o resultado da suíte **que ela registrou** (linha "Último 100% verde" do `PLANO-TESTE.md`), dito como "segundo
   ela";
4. resposta **breve**: uma tabela de conferência → resultado, e o que falta (merge, publicar, prova que só o owner vê).
Não rode suíte, não troque de branch, não grave nada enquanto a outra conversa estiver na pasta. Se ele pedir uma
prova a mais, rode **uma peça**, com os padrões, e só com a pasta parada. Casos F-064 e F-059; parente de
[[feedback_resposta_do_tamanho_do_pedido]] e [[feedback_feature_a_partir_da_master]].
