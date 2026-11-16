---
name: project_pytest_em_paralelo_estoura_nesta_maquina
description: duas rodadas de pytest ao mesmo tempo nesta máquina dão falha falsa nos testes que sobem o hook como processo e multiplicam o tempo — rode uma de cada vez
gatilho: quando for rodar a suíte do kit com outra rodada de pytest ainda em andamento
metadata:
  type: project
---

Em 2026-11-13, a suíte inteira do kit rodou ao mesmo tempo que outra rodada de 2 testes. Resultado: 2 falhas falsas
em testes que sobem o hook como processo (`tests/test_hook_alerta_contexto.py::test_processo_nunca_bloqueia` e
`tests/test_hook_banco_producao.py::test_processo_post_carimba_e_libera_o_proximo`), e os 2 testes levaram 57 min.
Rodados sozinhos, os dois arquivos deram `55 passed in 100.83s`; a suíte inteira, sozinha, `1617 passed in
1020.51s (0:17:00)`.

**Why:** os testes de processo têm prazo; com a máquina dividida entre duas rodadas, estouram sem defeito no código —
e a falha falsa custa uma rodada inteira de diagnóstico ou de suíte.

**How to apply:** uma rodada de pytest por vez. Falhou só teste que sobe processo, e havia outra rodada em paralelo?
Rode o arquivo dele sozinho antes de procurar defeito. Relacionado: [[feedback_pipe_mascara_o_exit_do_teste]].
