# Conversa nova não se perde — o que está decidido chega como decidido

## Estado atual
**Entregue na 0.59.0 (2026-11-11), branch `feature/conversa-nova-nao-se-perde`.** Vale para todos os projetos,
porque é hook do plugin — nenhum projeto precisa de upgrade. Falta provar no real, com o owner: o clique de
aprovação da troca de branch no app e a regra chegando numa conversa nova aberta com `Já decidido`.

- **Quem entrega** (a conversa que passa o trabalho adiante): o texto pronto para outra conversa só sai com três
  partes de título fixo — `Já decidido — não reabrir:` (lista numerada), `Falta decidir:` (lista ou "nada") e
  `Regras desta conversa:`. Sem elas, ou com "um tópico por vez" dentro do texto, a resposta volta uma vez com o
  molde.
- **Quem recebe:** quando o pedido traz `Já decidido` (ou `O que eu já decidi`, a forma que o owner usou em
  2026-11-11) com itens, o kit guarda os itens daquela conversa e entrega a regra na hora: não reabrir, lista única
  só das escolhas do assistente, perguntas de uma vez no fim. Daí em diante, a resposta volta uma vez se anunciar
  tópico a tópico, se fizer pergunta que repete um item decidido, ou se espalhar perguntas pelo meio.
- **"O kit não aceita"** — em toda conversa: resposta que diz que o kit, o plugin ou uma trava não aceita, negou ou
  bloqueou algo só sai com a regra em `arquivo:linha` e com uma pergunta ao owner.
- **Comando do kit colado:** o comando no começo de um texto colado (`<pasted_content …>`) é reconhecido pelo
  `hooks/kit_primeiro.py` e pelo `hooks/um_item_por_janela.py` (caso F-053).
- **Branch:** criar branch com a pasta fora da principal é negado. Trocar de branch numa branch que esta conversa
  não abriu é negado se há mudança por commitar e, com a pasta limpa, vira pedido de aprovação do owner (um
  clique). Na principal, ou numa branch que a própria conversa abriu, passa calado.

Fora de escopo: commit feito na branch errada; a ordem "regra antes do desenho" (caso F-060); `git stash` de
mudança de outra conversa.

## O que o owner decidiu
1. Item CRÍTICO de `to-dolist.md` (2026-11-11): a passagem leva as decisões como DECIDIDAS; a conversa nova mostra
   só as escolhas dela e pergunta o que falta, de uma vez; nunca responde "o plugin não aceita" sem a regra com
   arquivo e linha e a pergunta; duas conversas na mesma pasta não trocam a branch uma da outra; tudo cobrado por
   comando ou hook, não por anotação.
2. 2026-11-11, nesta feature: "OK na lista" das escolhas do assistente (abaixo).
3. Troca de branch com a pasta limpa numa branch que a conversa não abriu: **fica o clique de aprovação** (não
   negar sempre).
4. O item é um só, com quatro exigências: as quatro nesta conversa, numa spec — a regra "pedido com várias partes"
   (`templates/regras-do-kit/1-modo-de-trabalho.md:30`) não se aplica aqui.
5. Nada do MSIG_Agentes é usado ou copiado.

## Escolhas do assistente (aprovadas em lista)
1. Tudo por hook, nenhum comando para o owner lembrar (caso F-057).
2. Um hook próprio para a passagem (`hooks/passagem_de_conversa.py`, no envio do pedido e no fim da resposta); a
   trava de branch dentro do `hooks/git_publicacao.py`, onde as outras travas de git já moram.
3. A conferência do "kit não aceita" vale em toda conversa.
4. Cada conversa lembra as branches que ela abriu num arquivo temporário por conversa, como o `kit_primeiro.py`.
5. Medir nas respostas gravadas antes de ligar; a conversa do caso F-058 tem de ser pega.
6. Ligar no `hooks/hooks.json` por último, com os testes verdes — o kit é carregado desta pasta.
7. Defeito no hook libera calado.
8. O aviso de uma vez por conversa ao criar branch (`memory/feedback_feature_a_partir_da_master.md`) continua.

## O que foi visto no real antes do desenho (2026-11-11)
- O texto pronto da parte 2 da memória em tabela pedia "um tópico por vez" e não dizia para não reabrir
  (`docs/analise/2026-11-10-memoria-em-tabela-e-ci.md:287`). A conversa que recebeu respondeu com "Os tópicos, na
  ordem em que quero fechar com você" e "Tópico 1 — …" (conversa `56ec3cd9`, lida em texto).
- O texto colado chega ao hook como `<pasted_content id="…">` + quebra de linha + `/mss-spec:nova-feature …`
  (conversa `a7089e86`, a do caso F-053).
- **Não achado:** as duas conversas que responderam "o plugin não aceita" não estão mais entre as gravadas; só há
  o relato do owner (`to-dolist.md:80`). A frase real que não pode disparar existe: "Nada no kit proíbe o que você
  decidiu" (conversa `56ec3cd9`). O gatilho dessa conferência é calibrado pela medição nas respostas reais.

## Medido antes de ligar (2026-11-11, só este projeto, uma medição)
1.052 respostas finais das conversas gravadas do kit, passadas pelas três conferências:

| Conferência | Voltariam | O que eram |
|---|---|---|
| Quem recebe (reabrir) | 1 (0,1%) | a resposta do caso F-058 — a única conversa com itens decididos no pedido |
| "O kit não aceita" | 9 (0,9%) | relatos de trava que negou ("foi negada pelo hook", "a cerca de git negou") e 2 descrições |
| Quem entrega (texto pronto) | 16 (1,5%) | os 16 eram textos para colar em outra conversa; 2, recados para conversa em curso |

Abaixo dos 3,3% que a decisão de 2026-10-29 já aceita (`docs/decisoes.md:54`). O que a medição **não** prova: a
conferência de pergunta que repete item decidido só teve uma conversa real para olhar; e nenhuma das frases
originais do "o plugin não aceita" foi vista. Roteiro da medição fora do repositório (pasta temporária).

## Onde mora
- `hooks/passagem_de_conversa.py` (pedido e fim da resposta) · `hooks/_prompt.py` (texto colado) ·
  `hooks/_pasta_e_branch.py` (dentro do `hooks/git_publicacao.py`) · registro em `hooks/hooks.json`.
- Testes: `tests/test_hook_passagem_de_conversa.py`, `tests/test_hook_pasta_e_branch.py`, e os do comando colado em
  `tests/test_hook_kit_primeiro.py` e `tests/test_hook_um_item_por_janela.py`.
- Texto que ensina o molde: `commands/nova-feature.md` (passo 2), aviso do `hooks/sem_worktree.py`, `docs/LEIA-ME.md`.

## Critérios de aceite
1. DADO um pedido com `O que eu já decidi` e 6 itens, QUANDO a resposta anuncia "Tópico 1", ENTÃO volta uma vez.
2. DADO o mesmo pedido, QUANDO a resposta traz lista única e perguntas só no fim, ENTÃO sai.
3. DADO o mesmo pedido, QUANDO uma pergunta repete um item decidido, ENTÃO a resposta volta apontando o item.
4. DADO uma resposta que diz que o kit não aceita algo, sem `arquivo:linha` ou sem pergunta, ENTÃO volta; com os
   dois, sai. "Nada no kit proíbe" não dispara.
5. DADO um texto pronto para outra conversa sem `Já decidido`, ENTÃO a resposta volta com o molde.
6. DADO o comando do kit dentro de `<pasted_content>`, ENTÃO o `superpowers:*` não é negado e o um-item-por-janela
   enxerga o `nova-feature`.
7. DADO a pasta numa branch que a conversa não abriu, QUANDO ela cria branch, ENTÃO é negado; QUANDO troca com
   mudança pendente, ENTÃO é negado; QUANDO troca com a pasta limpa, ENTÃO o owner é perguntado.
8. DADO a pasta na principal, ou numa branch que a conversa abriu, ENTÃO criar e trocar passam.

## Histórico
- 2026-11-11 — criado: desenho aprovado pelo owner (lista única + duas respostas); branch aberta da `main`.
- 2026-11-11 — entregue (0.59.0): hook da passagem por HOOK em vez de comando ou anotação (o owner recusou comando
  para lembrar e pediu cobrança mecânica); trava de branch com clique de aprovação na pasta limpa em vez de negar
  sempre (decisão do owner); gatilhos calibrados nas conversas reais (motivo: as frases originais do "plugin não
  aceita" não estavam mais gravadas, e a medição tirou um falso positivo — "nunca bloqueou").
