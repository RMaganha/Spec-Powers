# 2026-10-28 — fora de escopo vira item do to-dolist (0.47.0)

## Conversamos
1. O owner abriu a feature com a opção escolhida em 2026-10-28 (`docs/decisoes.md:51`): "não agora", um lugar (to-dolist com `#fora-de-escopo`), uma linha por item, to-dolist no git, o assistente nunca cita sozinho.
2. Desenho mostrado com um item real antes/depois (`release` em script, de bloco `> ` ilegível pela busca para linha do to-dolist) e a tabela do que muda por arquivo.
3. Pergunta única: os outros projetos ainda não convertidos (Transportes e Energy com a seção no INDEX; Whats com `FORA-DE-ESCOPO.md`) — o kit segue lendo o formato antigo? Owner: *"Sim, até o upgrade"*.

## Pivôs
- Formato antigo não sai de uma vez: `rodizio_partida.py`, `um_item_por_janela.py` e `doctor` continuam tratando a seção antiga, marcados como provisórios até a feature do upgrade.
- O item "`.bpmn` importável no Bizagi" saiu da conversão: foi entregue depois (`docs/decisoes.md:31`), não é mais "pra depois".
- O teste "sem seção no INDEX" passou a olhar só títulos: a própria linha desta feature no INDEX contém "fora de escopo".

## Rejeitado
- Inventar motivo para os 7 itens de 2026-07-17 que nunca tiveram: ficam com "motivo não registrado".

## Fizemos
- `f57e08e` na `feature/fora-de-escopo-no-to-dolist`: busca sem fora de escopo, to-dolist no git, comandos/moldes/hooks/docs com o texto novo, 61 itens convertidos (data da decisão em `docs/decisoes.md` ou do 1º commit), spec `docs/specs/fora-de-escopo-no-to-dolist.md`, 999 testes.

## Próximo
- Owner: push da captura (a 0.47.0 já foi mesclada e enviada em `44fb347`).
- Padronizar os projetos com o desenho do kit (doctor aponta, upgrade converte) — INDEX item 3.
