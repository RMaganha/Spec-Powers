# Conversa nova não se perde — o que está decidido chega como decidido

## Estado atual
**Entregue na 0.59.0 (2026-11-11), branch `feature/conversa-nova-nao-se-perde`.** Vale para todos os projetos,
porque é hook do plugin — nenhum projeto precisa de upgrade. Falta provar no real, com o owner: o clique de
aprovação da troca de branch no app. Provado no real em 2026-11-12: a regra chegou numa conversa nova aberta com
`Ja decidido - nao reabrir` (2 itens), a da 0.61.0.

- **A conversa nova acha sozinha** (0.61.0, 2026-11-12, mesclada na `main` em `7e641b9` e publicada): o owner abre
  a conversa com uma frase comum — sem colar texto e sem comando. No **1º pedido** da conversa, se ele não traz
  `Já decidido` colado, o kit casa a frase com o assunto e entrega os itens decididos ao assistente, com a regra de
  não reabrir. De onde vêm os itens, nesta ordem: (a) o texto pronto que outra conversa entregou — o bloco no molde
  fica guardado sozinho na pasta temporária do sistema, um arquivo por projeto, 7 dias, os 10 últimos, nada no git;
  (b) a seção `## O que o owner decidiu` da spec do assunto. Casa quando a frase traz o nome inteiro do assunto, ou
  3 palavras do nome e do título e pelo menos metade do menor lado — nunca pelo texto dos itens. Dois assuntos
  empatados: chegam só os nomes, e o assistente pergunta qual. Entrega até 2.000 bytes de itens, sempre inteiros; o
  que não couber vira `arquivo:linha`. **Só informa:** o que foi achado sozinho não faz resposta voltar. Nada casa,
  2º pedido, outro projeto, texto vencido ou qualquer defeito: o pedido passa igual a antes. Falta provar no real:
  uma conversa nova de verdade aberta com uma frase, depois de outra conversa ter entregado o texto pronto.
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
6. 2026-11-12: conversa nova tem de achar sozinha o que o owner já decidiu — ele abre a conversa com uma frase
   comum, o kit acha o assunto e traz o que já foi decidido; sem colar texto e sem digitar comando.
7. 2026-11-12: não é comando novo no plugin e não pode ser uma coisa que trave.
8. 2026-11-12: "OK, implementa" no desenho e nas escolhas do assistente da 0.61.0 (abaixo).

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

Da 0.61.0 (a conversa nova acha sozinha), aprovadas em 2026-11-12:
1. Dentro do `hooks/passagem_de_conversa.py`, sem hook novo: as duas pontas já moram lá e não soma um sexto processo
   por pedido.
2. Duas fontes, nesta ordem: o texto pronto guardado (cobre assunto ainda sem spec) e a seção da spec (o durável).
3. O texto guardado fica na pasta temporária do sistema, onde o estado de cada conversa já fica; não suja a pasta
   do projeto. Se a pasta temporária for limpa, vale a spec; sem spec, o owner cola como antes.
4. Só procura no 1º pedido da conversa, e só se ele não trouxer `Já decidido` colado.
5. Só informa: o que foi achado sozinho não entra na devolução de resposta — o casamento pode errar de assunto.
   É a leitura do assistente para "não pode travar"; o owner pode trocar.
6. Teto de 2.000 bytes entregues. Item que não cabe inteiro não é cortado: vira `arquivo:linha` (cortar frase no
   meio pode inverter o sentido — visto na prova real, com o item 1 desta lista do owner).
7. Casa pelo termo curto do tema, nunca pelo texto dos itens (lição de `docs/decisoes.md:54`). Provado nos 21
   nomes de spec do repo: cada um acha a sua, nenhum acha a do vizinho.
8. Texto guardado vale 7 dias e ficam os 10 últimos por projeto; bloco com `<private>` e o molde do próprio hook
   não são guardados. Não estava na lista aprovada — escolha feita na construção, o owner confere.
9. Guarda o bloco no molde mesmo que a resposta não fale em "colar" — escolha feita na construção, o owner confere.

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
- Testes: `tests/test_hook_passagem_de_conversa.py`, `tests/test_hook_conversa_nova_acha_sozinha.py` (0.61.0),
  `tests/test_hook_pasta_e_branch.py`, e os do comando colado em
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
9. DADO uma conversa que entregou texto pronto no molde, QUANDO outra do mesmo projeto abre com uma frase do
   assunto, ENTÃO recebe os itens decididos e a regra de não reabrir.
10. DADO uma spec com `## O que o owner decidiu` e nenhum texto guardado, QUANDO a frase casa com ela, ENTÃO recebe
    os itens com `arquivo:linha`.
11. DADO frase que não casa, 2º pedido, pedido com `Já decidido`, outro projeto ou qualquer defeito, ENTÃO o pedido
    passa igual a antes; DADO dois assuntos empatados, ENTÃO chegam só os nomes.

## Histórico
- 2026-11-11 — criado: desenho aprovado pelo owner (lista única + duas respostas); branch aberta da `main`.
- 2026-11-11 — entregue (0.59.0): hook da passagem por HOOK em vez de comando ou anotação (o owner recusou comando
  para lembrar e pediu cobrança mecânica); trava de branch com clique de aprovação na pasta limpa em vez de negar
  sempre (decisão do owner); gatilhos calibrados nas conversas reais (motivo: as frases originais do "plugin não
  aceita" não estavam mais gravadas, e a medição tirou um falso positivo — "nunca bloqueou").
- 2026-11-12 — a conversa nova acha sozinha o que o owner já decidiu (0.61.0): o texto pronto no molde fica
  guardado e, no 1º pedido, a frase é casada com ele e com a seção `## O que o owner decidiu` da spec (motivo: o
  owner não quer colar texto nem digitar comando; decidiu que não é comando novo e que não trava).
- 2026-11-12 — dois pivôs da construção da 0.61.0: a régua "2 de 3 palavras do nome do assunto" foi rejeitada antes
  de ser escrita (motivo: "abri conversa nova pra ver o bug do login" casaria com esta spec); e o item, que saía
  cortado em 300 caracteres, passou a ir inteiro ou virar `arquivo:linha` (motivo: na prova com a frase real do
  owner o item 1 desta spec chegou cortado no meio da frase). Mesclada na `main` (`7e641b9`) e publicada pelo owner.
