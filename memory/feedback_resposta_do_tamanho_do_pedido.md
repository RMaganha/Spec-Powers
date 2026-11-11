---
name: feedback_resposta_do_tamanho_do_pedido
description: Resposta do tamanho do pedido — entregue só o que o owner pediu, na ordem, e pare; o não pedido cabe em 1 linha; fato que muda o roteiro se PERGUNTA antes (nada de roteiro com bifurcação); sem jargão
gatilho: quando o owner pedir uma entrega específica (passo a passo, comando, roteiro) ou quando a resposta começar a ganhar etapas, rotas e pendências que ele não pediu
sem_gatilho_de_acao: vale pra toda resposta — o caso medível (rotas não pedidas, F-033) já é conferido pelo `hooks/confere_citacoes.py`
metadata:
  type: feedback
---

O owner pediu, numa janela do Whats (2026-09-24): *"o passo-a-passo da 1ª tarefa… como fazer o backup no
mitiai-poc e restaurar no Azure de produção e depois a sequência de scripts"*. Veio uma resposta de 8 etapas com
"Rota 1 / Rota 2", "dia definitivo", "pendências que ainda podem travar o dia", limpeza, a proposta de criar um modo
novo no `rodar-via-proxy.py` e termos como "libpq ignora proxy" e "grupo EXT.DISP". O owner: *"insistiu em mandar um
retorno gigantesco cheio de jargões de IA não focando no que eu preciso"* — e ele já tinha dito que a tarefa era a 1.

**Why:** cada etapa a mais é o owner filtrando o que importa; a bifurcação existia porque dois fatos (usuário do
Postgres, se o servidor alcança o Azure) não foram perguntados; e jargão faz o owner depender do assistente pra
entender o próprio roteiro. É o caso **F-033** do `docs/EVALS.md`.

**How to apply:**
- o pedido define o **escopo** e a **ordem** da resposta: backup → restore → scripts, e pare;
- o que não foi pedido (riscos, dia definitivo, pendências, melhoria de ferramenta) vira **no máximo 1 linha** no fim;
- faltou fato que muda o roteiro → **1–2 perguntas curtas antes**, sem entregar o roteiro com rotas alternativas;
- palavra simples; termo técnico só o que o owner vai **digitar** ou **ver na tela** (e comando no formato
  [[feedback_comando_pro_owner_passo_a_passo]]).
Mora no `templates/CLAUDE.md` com a frase-chave travada. Relacionadas: [[feedback_estilo_resposta_direto]],
[[feedback_perguntar_em_vez_de_vasculhar]].

**Reincidiu 3× numa sessão (2026-11-10/11, F-056):** *"é muita coisa para eu absorver"*; *"voce fala em linguagem
de máquina"*; *"eu te pergunto uma coisa voce responde outras só confusão aqui, que desespero..."*. O que
consertou está em [[feedback_decidir_por_topicos_um_de_cada_vez]], [[feedback_resultado_primeiro_em_medicao]] e
[[feedback_pergunta_so_no_texto]]: pergunta direta → resposta direta, na ordem em que ele perguntou, e só.
