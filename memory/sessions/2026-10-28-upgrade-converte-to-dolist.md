# 2026-10-28 — o upgrade converte o to-dolist e o fora de escopo (0.48.0)

## Conversamos
1. Depois da 0.47.0: "o que seria esse padronizar os projetos?" — expliquei que falta ensinar o upgrade.
2. "em outro chat você disse uma coisa aqui diz outra" → respondi "não sei" sem ler (F-045); "está no projeto
   as outras conversas e memoria, como não sabe???" → li a 6eb8f8d0: divergência na busca (F-046).
3. O owner decidiu: a busca fica como está (decisoes.md:51); o to-dolist do Whats é convertido para o formato
   do kit, com 3 linhas reais e OK antes de gravar; linha que não converte vai para uma lista.
4. Apontamentos aceitos: versionar o to-dolist como está antes de converter; conferir a soma. Sem data → a data
   do upgrade, ordem pela data.
5. "por que em uma nova janela se é a mesma feature?" → não precisava; seguiu nesta conversa.
6. Leitura dos 3 projetos: o to-dolist do Whats tem 926 linhas, só 108 com "- " → o owner aprovou: recado =
   1 linha com o título; texto do fora de escopo inteiro; riscado/FEITO para a lista.

## Pivôs
- "linha por linha" → "um recado por linha", depois de ler o arquivo real.
- Motivo curto → texto inteiro (encurtar é reescrever e pode perder).
- Separador do "o que": só o negrito → negrito até o 1º " — " ou ": " (Energy e Transportes saíam cortados).
- Janela nova → mesma conversa (a trava passa com a feature anterior fechada).

## Rejeitado
- A busca voltar a ler o FORA-DE-ESCOPO.md antigo até o upgrade.
- Converter sem versionar o original.
- Encurtar o motivo do fora de escopo.

## Fizemos
- 0.47.0 (f57e08e, merge 44fb347) e a captura 41830b5.
- 0.48.0 (9425dc7, merge 6b8c34d): converter_to_dolist.py + upgrade (seção "Segundo") + doctor (check 10);
  1020 testes; prévia sem gravar: Whats 1.066 linhas (292 na lista), Energy 68 (5), Transportes 134 (19).

## Próximo
- Owner: /mss-spec:upgrade no Whats (árvore limpa antes), no Transportes e no Energy.
- Depois de todos: tirar do kit o código do formato antigo (#fora-de-escopo).
