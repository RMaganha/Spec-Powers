# 2026-11-11 — conferências das entregas e captura final da conversa da memória em tabela

Mesma conversa da análise (2026-11-10) e da parte 1 (0.55.0). Daqui em diante ela só **conferiu** o que outras
conversas entregaram (0.56.0 a 0.59.0) e fechou a captura. Branch `docs/captura-conferencias-2026-11-11`.

## Conversamos
- O owner passou a tocar cada item numa conversa nova e a voltar aqui pra conferir: parte 2 (0.56.0), consultar
  pela ação (0.57.0), ajudante pesquisador (0.58.0) e o item crítico "conversa nova não se perde" (0.59.0).
- Pediu a conferência da parte 2 e "os prompts das próximas tarefas"; depois explicações dos itens que não
  entendeu; depois como a base funciona nos outros projetos e se haveria "duas memórias".
- Testou num projeto que não é o kit (DeRe): conversa nova, sem `upgrade` — a tabela ganhou 54 linhas.
- Pediu a captura em detalhes: *"nada aqui deve ficar de fora, pois foi onde decidimos tudo!!"*.

## Pivôs
- **Conferir rodando → conferir lendo.** Rodei a suíte na pasta em que a outra conversa fazia o merge (35 falhas
  falsas). Ele: *"interferiu na outra suite"*; *"não tem pq rodar aqui é gastar token a toa"*. Passou a valer: só
  leitura, e o resultado que a outra conversa registrou (F-064).
- **7 textos de uma vez → um por vez, com o item explicado.** *"O item 1 ,2 e 4 não entendi nada!!!"* (F-065).
- **Consultar pela ação mudou de forma.** A conversa do item 2 achou a decisão de 2026-09-25 (não buscar por
  palavras a cada comando) e mediu de novo: confirma o ruído. O owner manteve a decisão; o item virou "toda anotação
  de regra ganha o gatilho de ação, cobrado na captura" e ele aprovou os 21 gatilhos em bloco.
- **Ordem real:** ele pulou o comando guardado inteiro e fez busca → consultar pela ação → ajudante pesquisador →
  item crítico.
- **Captura por lembrança → captura por varredura.** O texto inteiro da conversa (122 falas) foi lido por um
  ajudante e cruzado com o repositório: 83 itens, 63 gravados, 8 pela metade, 12 faltando (F-066).

## Rejeitado
- Rodar a suíte aqui pra confirmar o que a outra conversa já rodou.
- Mexer no git com a pasta em uso por outra conversa (o commit do item crítico tinha caído na branch dela, F-059).
- Buscar por palavras a cada comando (decisão de 2026-09-25, mantida).

## Fizemos
- Conferências só de leitura das quatro entregas; régua refeita com os dados desta conversa (44,0% entre os 10,
  contra 10,4% do jeito de antes); prova ao vivo no DeRe conferida direto na tabela.
- Captura: casos F-064 a F-066; memória nova `feedback_conferir_entrega_de_outra_conversa_so_lendo`; notas datadas
  em `feedback_texto_pronto_pra_colar`, `feedback_resposta_do_tamanho_do_pedido` e
  `feedback_captura_varre_a_conversa_inteira`; spec da memória em tabela (ordem real, régua refeita, prova no DeRe,
  explicação em português simples, primeiro gatilho visto em uso); dossiê (linha defasada e os 4 textos prontos que
  faltavam, no molde novo); 3 linhas no `to-dolist.md`.
- Dois gatilhos de ação dispararam ao vivo aqui: "rode a peça com os padrões" devolveu uma resposta e a regra de
  branch barrou uma vez um `git switch -c`.

## Próximo
- Na ordem do owner: comando guardado inteiro → lista de conferência → ajudante revisor → teste automático do kit.
  Textos prontos na seção 9 do dossiê, um por vez.
- Do owner: GitLab ou GitHub; se o aviso automático de 3 anotações troca de motor; se as 31 decisões estão
  completas (ele tem anotações próprias que nunca foram comparadas).
- Pro kit tratar (`to-dolist.md`): captura aos poucos em conversa longa; o custo de uma conversa só pra conferir.
