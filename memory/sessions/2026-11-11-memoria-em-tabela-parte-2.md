# 2026-11-11 — memória em tabela, parte 2: a busca usa a tabela e a tabela se atualiza sozinha

Branch `feature/memoria-em-tabela-parte-2` (da `main` em `5366d66`, mais o commit `77cd688` do item CRÍTICO do
to-dolist). Spec: `docs/specs/memoria-em-tabela.md`. Plano:
`docs/superpowers/plans/2026-11-11-memoria-em-tabela-parte-2.md`. Conversa nova, aberta com o texto pronto do
dossiê. Diário em andamento: a sessão ainda não fechou (ver "Próximo").

## Conversamos
- O owner abriu com 6 itens **já decididos** e a ordem de leitura (spec → dossiê → diário da parte 1 → F-054 a
  F-057). Pediu: se alguma regra parecer proibir, mostrar a regra com arquivo e linha e perguntar.
- Conferi as regras: nada proíbe. A mais próxima (`docs/decisoes.md`, 2026-11-03) permite hook Python do app.
- Entreguei a lista única das minhas escolhas (20 linhas, cada uma com o motivo) e ele respondeu "Ok".

## Pivôs
- **Tópico por tópico → lista única.** Comecei a fechar de novo, um por um, o que ele já tinha decidido. Ele
  cortou: *"Os itens de 1 a 6 do meu texto já estão decididos. Não me peça para confirmar de novo, tópico por
  tópico."* Pediu: lista só das escolhas do assistente, o que só ele decide perguntado de uma vez no fim, e
  seguir. Virou nota em `feedback_decidir_por_topicos_um_de_cada_vez` e o item CRÍTICO do to-dolist
  ("conversa nova se perde").
- **Branch aberta sem ler em que branch a pasta estava.** Encadeei `git status -sb && git switch -c`: a pasta
  estava na `chore/todo-conversa-nova-se-perde` de outra conversa, e o commit dela (`77cd688`) caiu na minha
  branch. Nada se perdeu; devolvi a pasta, relatei, e o owner mandou seguir com o commit na minha branch e apagar
  a chore. Reincidência do "quase reincidiu" de 2026-10-21 (`feedback_feature_a_partir_da_master`).
- **Conferência completa → conferência por nome, tamanho e data.** A conferência de antes levava 1,9 a 2,6 s no
  kit (quase tudo em chamadas ao git); passou a comparar só o que está no disco com uma linha de controle do
  projeto, dentro da mesma tabela. Medido: 0,5 a 0,8 s quando nada mudou.
- **Texto colado é pedido do owner.** O filtro do teste de mesa jogava fora o pedido colado (vem embrulhado numa
  marca); o filtro entregue mantém, e ignora corpo de comando e de skill.

## Rejeitado
- Tabela de controle separada (segue a escolha da parte 1: uma tabela só — a linha de controle mora nela).
- Processo solto ou tarefa agendada pra atualizar depois de gravar (decisão de 2026-11-03).
- Trocar agora o motor do aviso automático de 3 anotações: a troca é decisão do owner, com os números.
- Reservar vagas pra anotações nas 30 linhas (só foi medido com 10).
- Contexto dos pedidos anteriores quando o owner digita um termo no `/mss-spec:memory buscar` (não medido).

## Fizemos
- `templates/memoria_tabela.py`: `assinatura_do_disco`, `atualizar`, `buscar`, `formatar`,
  `pedidos_da_conversa`, `arquivo_da_conversa`, modo `buscar` na linha de comando.
- `hooks/memoria_tabela_em_dia.py` (abertura da conversa e depois de gravar), ainda **não** ligado no
  `hooks/hooks.json`.
- `commands/tarefa.md`, `bug.md`, `duvida.md` (passo 1a) e `commands/memory.md` (`buscar` na tabela; `tabela`
  virou uso interno).
- Testes: `tests/test_memoria_tabela_busca.py`, `tests/test_hook_memoria_tabela_em_dia.py`, desvio da tabela
  real no `tests/conftest.py`.
- Régua com o código entregue (`docs/analise/2026-11-10-teste-de-mesa/regua_parte2.py`; dados fora do
  repositório): pedido real → arquivo entre os 10 em 43,8% (664 casos) e 47,7% (675, com o filtro entregue),
  contra 10,7% e 12,0% do jeito de hoje; situação → regra 89,1% (hoje 78,1%); descrição → anotação 91,8%.
  Estável nas duas metades. Aviso entre os 3 primeiros: kit e Whats a tabela ganha; MSS-UTILS empata e em
  primeiro lugar o jeito de hoje ganha.

## Próximo
- Suíte inteira, documentação (README dos hooks, LEIA-ME, CHANGELOG, decisão), 0.56.0 nos dois manifestos,
  F-057 fechado, hook ligado no `hooks/hooks.json`, revisão, `plano-teste`, `release`.
- Captura completa com o OK do owner: caso novo no `docs/EVALS.md` pelo erro da branch e pelo tópico a tópico.
- Do owner: decidir, com os números, se o aviso automático troca de motor; merge e `git push`.
- Avisos dados a ele: a saída de 30 linhas deu 8,6 KB nesta conversa (o dossiê estimava 4,7 KB); o teste do
  hook foi escrito junto com o código.
