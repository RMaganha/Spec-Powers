# 2026-11-11 — conversa nova não se perde (0.59.0)

## Conversamos
- O owner abriu a conversa com o item CRÍTICO do `to-dolist.md`: a passagem de uma conversa para outra leva as
  decisões como decididas; a conversa nova nunca responde "o plugin não aceita" sem a regra com arquivo e linha e a
  pergunta; duas conversas na mesma pasta não trocam a branch uma da outra; tudo por comando ou hook, para todos os
  projetos. Regras da conversa: o que está decidido não se reabre; lista única das escolhas do assistente; perguntas
  de uma vez, no fim.
- Ele respondeu ao desenho em uma mensagem: "OK na lista. 1: fica o clique. 2: confirmo."

## Pivôs
- **O texto pronto era parte da causa.** Lendo o texto real da parte 2 da memória em tabela, ele pedia "um tópico por
  vez" e não dizia para não reabrir; a conversa que recebeu obedeceu. Por isso a entrega cobra também quem ENTREGA
  o texto (três partes de título fixo), não só quem recebe.
- **As frases originais do "plugin não aceita" não existem mais.** As duas conversas que se perderam não estão
  entre as gravadas. O gatilho saiu do relato do owner, das frases reais que NÃO podem disparar ("Nada no kit
  proíbe o que você decidiu") e da medição em 1.052 respostas — que tirou um falso positivo ("nunca bloqueou").
- **Trava de branch: clique em vez de negar sempre.** O hook não sabe se a outra conversa está viva; sabe o que
  esta abriu. Com mudança por commitar, nega; com a pasta limpa, o owner decide com um clique (escolha dele).
- **Criar branch dizendo que sai da principal** (`git switch -c x main`) numa branch de outra conversa não é
  "criar fora da principal": vale como troca.

- **A captura saiu incompleta e o owner pegou.** Ele perguntou "foi executado o /mss-spec:memory capturar"; eu
  tinha gravado os quatro rascunhos sem a varredura da conversa e sem reconciliar o MAPA. A varredura, feita
  depois, achou um item tirado do to-dolist como feito sem conferência (voltou, reescrito) — caso F-063.
- **MAPA com dois blocos de histórico.** Ao abrir a branch acrescentei um bloco sem tirar o anterior; a suíte pegou
  (`test_mapa_carrega_um_estado_anterior`) e o bloco mais antigo foi pro `MAPA-historico.md`.

## Rejeitado
- Comando para o owner digitar e gerar a passagem — ele já recusou comando para lembrar (F-057).
- Só anotação/prosa — é o que o item proíbe.
- Mexer no aviso de uma vez por conversa ao criar branch — fica como está.
- Negar sempre a troca de branch em branch que a conversa não abriu — o owner preferiu o clique.

## Fizemos
- `hooks/passagem_de_conversa.py` (pedido + fim da resposta), `hooks/_pasta_e_branch.py` (6ª cerca do
  `git_publicacao.py`), `hooks/_prompt.py` (comando colado, F-053); registro no `hooks/hooks.json` por último.
- Testes: 54 + 28 + 3. Medição antes de ligar: quem recebe 1 (a conversa do F-058), recusa 9 (0,9%), entrega 16
  (1,5%).
- Spec `docs/specs/conversa-nova-nao-se-perde.md`; casos F-053 e F-058 fechados, F-059 com trava; versão 0.59.0.
- O ajudante pesquisador foi chamado uma vez (ler outras conversas) e devolveu que faltava o texto delas: quem
  roda o `conversa_texto.py` é a conversa principal — rodei e li os trechos eu mesmo.

## Próximo
- Owner: aprovar o merge na `main` e publicar.
- Provar no real: o clique de aprovação ao trocar de branch e a regra chegando numa conversa nova aberta com
  `Já decidido`.
- Fora deste item: commit feito na branch errada; a ordem "regra antes do desenho" (F-060).
