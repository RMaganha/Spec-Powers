---
name: project_pytest_pasta_temporaria_por_projeto
description: sem configuração, todo projeto grava na mesma pasta temporária do pytest e a rodada interrompida deixa lixo travado por 3 dias — o molde templates/pytest/conftest.py dá uma pasta por projeto e uma rodada por vez
gatilho: quando o pytest deixar pastas acumulando na pasta temporária ou a máquina ficar lenta depois de interromper o pytest
metadata:
  type: project
---

Medido em 2026-11-17 (diário `memory/sessions/2026-11-17-suite-lenta.md`):

- Sem configuração, toda rodada de pytest, de qualquer projeto, grava em `<temp>/pytest-of-<usuário>`, uma pasta só
  para o usuário. No fim da rodada o pytest apaga as rodadas mais antigas que as 3 mais novas.
- Rodada interrompida (Ctrl+C, código 137, máquina travando) deixa um `.lock` na pasta dela, e o pytest só apaga pasta
  com `.lock` depois de 3 dias (`LOCK_TIMEOUT` no pathlib.py do pacote `_pytest`, no pytest instalado). A limpeza interrompida no
  meio também deixa a `garbage-*` com `.lock`. Havia 6 pastas travadas (cerca de 3 mil pastas); apagar levou 991 s.
- Conserto: o molde `templates/pytest/conftest.py` (raiz de cada projeto, pelo `kickoff` e pelo `upgrade`) usa
  `--basetemp` em `<temp>/pytest-<projeto>`, apagada no começo de cada rodada (sem `.lock`, nada acumula), e uma trava
  do sistema operacional para uma rodada de pytest por vez, que morre com o processo. O kit usa o próprio molde.
- A mesma suíte do kit leva de 517 a 2379 s na máquina do owner e 24 a 32 s no Linux do GitHub Actions: o custo é
  criar e apagar milhares de arquivos por rodada, não a quantidade de testes.

Relacionado: [[feedback_teste_nao_cria_pasta]], [[feedback_suite_inteira_so_no_ci]],
[[project_pytest_em_paralelo_estoura_nesta_maquina]].
