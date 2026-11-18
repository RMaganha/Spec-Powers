# 2026-11-17 — suíte em camadas: a regra do hook testada em memória, sem pasta (em andamento)

## Conversamos
O owner abriu `/mss-spec:tarefa` com o texto pronto da conversa anterior (`2026-11-17-suite-lenta.md`): reescrever
a suíte do kit em camadas, na ordem das pastas que cada arquivo cria por rodada. Já decidido no pedido: teste não
cria pasta nem arquivo; disco só num teste por hook e processo python só num; o hook passa a receber o estado como
dado sem mudar o comportamento; na máquina só `templates/testes_do_que_mudou.py --rodar`; um commit por arquivo.

## Pivôs
- O nome da função sem disco começou como `decidir` no `passagem_de_conversa`; virou `regra` em todos porque
  `decidir` já era a casca pública em 7 hooks (commit separado, `ce25bd3`).
- No `confere_citacoes` a regra recebe o disco como objeto (`DiscoReal`, 6 métodos); em teste, um dicionário de
  arquivos com o pedaço do kit que os textos citam. O kit de verdade fica só no teste de disco.
- Uma rodada levou 13h03 de relógio: a máquina suspendeu no meio (a data virou). Rodada longa vai em segundo plano.

## Rejeitado
- Ler o kit de verdade nos testes em memória do `confere_citacoes` (seria disco fora do teste de disco).
- Ler `docs/specs` e o INDEX a cada pedido para passar como dado: a regra recebe funções que leem só quando
  precisa — hoje o hook só lê no 1º pedido ou só quando o comando casa.

## Fizemos
- Decisão em `docs/decisoes.md` (2026-11-17, hook = `regra` sem disco + casca), com o OK do owner.
- Reescritos, um commit cada: `passagem_de_conversa` (`1c19046`, `ce25bd3`), `um_item_por_janela` (`fb22400`),
  `confere_citacoes` (`1c78682`), `banco_producao` (`ac74dcc`). Em cada um, os testes antigos passaram com o hook
  novo antes da troca do teste.
- `regra_antes_de_gravar`: hook separado; teste novo pronto no scratchpad, esperando a rodada dos antigos.

## Próximo
Seguir a ordem do grupo 1 a partir de `regra_antes_de_gravar`. Aberto: o `testes_do_que_mudou.py` não escolhe teste
que carrega o hook pelo nome sem `.py` (`tests/test_hook_memoria_da_proposta.py` chama o `confere_citacoes` e não
rodou contra o código novo; roda no CI no push) — oferecido ao owner como item do `to-dolist.md`.
