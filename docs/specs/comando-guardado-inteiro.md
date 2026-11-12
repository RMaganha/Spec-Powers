# Comando guardado inteiro — comando ou SQL citado em anotação ou diário é gravado completo

## Estado atual
**Pronto na branch `feature/comando-guardado-inteiro` (0.60.0, 2026-11-12), aguardando o owner aprovar o merge na
`main`.** Falta provar no real: a negação aparecendo numa captura de verdade.

- **Regra na captura:** o passo 2 do modo capturar de `commands/memory.md` manda gravar inteiro o comando ou SQL
  que o owner vai rodar de novo, na anotação e no diário; senha e token viram `*****` mais onde o valor vive; sem
  o comando inteiro na conversa, diz-se isso em vez de inventar.
- **Conferência na hora de gravar** (`hooks/_comando_inteiro.py`, chamado de dentro do
  `hooks/regra_antes_de_gravar.py`): gravação em `memory/<nome>.md` ou `memory/sessions/<nome>.md` que **traz**
  comando ou SQL com reticências (`...` ou `…`) é negada **uma vez** por arquivo e por conversa, com o trecho no
  motivo; repetir passa. Os índices (`MEMORY.md`, `DIARIO.md`, `memory/indice/`) e o resto do projeto não são
  conferidos.
  - Conta: bloco de código de SQL; bloco de terminal (a linha do comando e as de continuação); bloco sem língua,
    na linha que começa como SQL ou comando conhecido; trecho entre crases que começa assim.
  - Não conta: `*****`, intervalo do git (`main...HEAD`), marcador entre `<` e `>`, bloco de outra língua
    (python, text, json), saída de programa depois do comando e reticências em prosa.
  - No Edit e no MultiEdit confere-se o arquivo como vai ficar. O corte que já estava no arquivo não é cobrado de
    quem edita outro trecho.
  - Sem número de conversa não age; defeito → deixa gravar. Escape só do owner: `MSS_COMANDO_INTEIRO_OFF=1`.
- **Anotações antigas:** `templates/memoria_indice.py verificar` avisa quantas anotações e diários têm comando ou
  SQL com reticências, com os nomes; não altera nenhum e não muda o código de saída. A lista vai ao owner.

Fora de escopo: detector de senha (a regra de esconder segue como está) e `UPDATE`/`DELETE` sem `WHERE` que não
tem reticências.

## O que o owner decidiu
1. Decisão 23 de `docs/specs/memoria-em-tabela.md`: quando uma anotação ou diário citar um comando ou SQL que o
   owner vai rodar de novo, ele é gravado completo, nunca cortado com reticências.
2. Senha e credencial continuam escondidas.
3. Nada do MSIG_Agentes é usado ou copiado.
4. 2026-11-12: o owner aprovou o desenho e as escolhas abaixo ("ajustei o merge pode seguir com meu OK") e mesclou
   ele mesmo a captura de 2026-11-11 na `main` antes de a branch nascer.

## De onde veio
`docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`, seção 4.7: 8 das 35 anotações com SQL têm reticências; quase
todas legítimas (exemplo de sintaxe, senha escondida). Caso claro: 1, no Whats — a anotação guardou o começo de um
`UPDATE`, sem o `WHERE`, e o owner precisou reconstituir. Até aqui nada na captura mandava guardar o comando inteiro
e nada conferia.

## Critérios de aceite
1. DADO uma anotação ou diário com comando ou SQL com reticências, QUANDO gravo, ENTÃO a gravação é negada uma vez
   com o motivo, e a repetição passa.
2. DADO um comando com `*****`, intervalo do git (`main...HEAD`) ou marcador entre `<` e `>`, QUANDO gravo, ENTÃO
   passa calado.
3. DADO um arquivo fora de `memory/`, QUANDO gravo, ENTÃO a conferência não age.
4. DADO o `commands/memory.md`, QUANDO rodo a suíte, ENTÃO a frase da regra está no modo capturar.
5. DADO anotações antigas com comando com reticências, QUANDO rodo o `verificar`, ENTÃO ele diz quantas são e não
   altera nenhuma.

## O que foi medido antes de ligar (2026-11-12, só neste projeto, uma medição)
O detector rodou nas 77 anotações e nos 36 diários do kit: **4 anotações e nenhum diário** seriam pegos (6 trechos).
Conferidos à mão, os 6 descrevem o **formato** de um comando que deu errado (`pytest … && git commit`,
`git status -sb && git switch -c …`) — nenhum é comando cortado que o owner rodaria de novo. Bate com a seção 4.7
(7 das 8 reticências eram legítimas) e é o motivo de a conferência negar uma vez e deixar a repetição passar.
Neste projeto não há caso real de comando cortado; os 8 casos cortados da suíte foram escritos a partir da
descrição do caso do Whats. Nos outros projetos nada foi medido daqui.

## Escolhas do assistente (o owner pode trocar)
- Negar uma vez e deixar a repetição passar, em vez de travar sempre: 7 das 8 reticências medidas eram legítimas.
- A conferência mora num módulo chamado de dentro do `hooks/regra_antes_de_gravar.py`, que já roda em toda
  gravação, em vez de hook separado (cada hook a mais custa a partida do Python em toda gravação).
- Anotação antiga só é contada: o comando original se perdeu e o assistente não completa sozinho.
- Spec própria, com a decisão 23 apontando para cá (como a 25 fez com o ajudante pesquisador).
- O caso de teste do `UPDATE` cortado foi escrito a partir da descrição da seção 4.7; o texto da anotação do Whats
  não foi lido.
- Medição só neste projeto antes de ligar; nos outros, prova-se em uso.

## Histórico
- 2026-11-12 — criado: desenho aprovado pelo owner (motivo: decisão 23 da memória em tabela; o `UPDATE` cortado no
  Whats).
- 2026-11-12 — pronto na 0.60.0: decidimos negar uma vez a gravação com comando cortado em vez de travar sempre ou
  de deixar só a frase na captura (motivo: a medição no kit achou 4 anotações, todas legítimas; e só a frase já
  tinha falhado em outras regras do kit). Acrescentado durante a construção: só o corte que a gravação traz de novo
  é cobrado, para que editar uma anotação antiga não cobre um comando que já se perdeu.
