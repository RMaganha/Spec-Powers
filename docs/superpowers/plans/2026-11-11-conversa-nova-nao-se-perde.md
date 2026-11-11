# Plano — conversa nova não se perde (0.59.0)

Spec: `docs/specs/conversa-nova-nao-se-perde.md`. Nível médio: execução na própria conversa, TDD, uma task por vez.

1. **Comando colado (critério 6)** — `hooks/_prompt.py` tira o `<pasted_content …>` do começo do pedido;
   `kit_primeiro.py` e `um_item_por_janela.py` passam a usar. Testes nos dois arquivos de teste dos hooks.
2. **Trava de branch (critérios 7 e 8)** — `hooks/_pasta_e_branch.py` (lê `.git/HEAD`, lembra as branches da
   conversa no temp) + 6ª cerca no `git_publicacao.py`. Teste `tests/test_hook_pasta_e_branch.py`.
3. **Quem recebe (critérios 1 a 3)** — `hooks/passagem_de_conversa.py`: no envio do pedido guarda os itens e
   entrega a regra; no fim da resposta devolve uma vez. Teste `tests/test_hook_passagem_de_conversa.py`, com a
   resposta real do caso F-058.
4. **Quem entrega (critério 5)** — mesma peça, conferência do texto pronto + molde.
5. **"O kit não aceita" (critério 4)** — mesma peça, em toda conversa.
6. **Medir nas respostas gravadas deste projeto** — quantas voltariam por conferência; ajustar; registrar na spec.
7. **Ligar** — `hooks/hooks.json`, `hooks/README.md`, textos que mandam "entregar o texto pronto"
   (`sem_worktree.py`, `um_item_por_janela.py`, `commands/nova-feature.md`), versão 0.59.0 nos dois manifestos.
8. **Fecho** — suíte inteira, EVALS (F-053, F-058, F-059), decisão, memória, INDEX, MAPA, release.
