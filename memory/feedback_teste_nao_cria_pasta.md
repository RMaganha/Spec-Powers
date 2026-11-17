---
name: feedback_teste_nao_cria_pasta
description: teste do kit não cria pasta nem arquivo — a regra é testada em memória; disco, processo e git só no teste que prova a leitura de verdade
gatilho: quando escrever ou reescrever teste do kit
sem_gatilho_de_acao: a ação é gravar arquivo de teste, que o gatilho de comando e de resposta não enxerga
metadata:
  type: feedback
---

O owner, 2026-11-17: *"não faz sentido criar milhares de pastas e arquivos"*. A suíte do kit criava cerca de 900
pastas por rodada porque quase todo teste montava um projeto de mentira no disco para testar uma regra.

O modelo (3 camadas):
- **Regra** — quase todos os testes: entra dado (comando, branch, texto do arquivo, estado), sai a decisão. Sem disco.
  Onde o hook lê ou grava estado direto em arquivo, o código do hook passa a receber o estado como dado.
- **Conversa com o mundo** — 1 teste por pergunta: disco de verdade num teste por hook; git de verdade só no teste que
  conversa com o git, montado uma vez por arquivo (`scope="module"`) e com `git init --template=` (23 itens em vez
  de 41).
- **Ponta a ponta** — 1 processo python por hook.

**Why:** a pasta não é o que se testa; ela existia porque o código não aceitava o dado em memória, e cada pasta custa
caro na máquina do owner.

**How to apply:** modelo já aplicado em `tests/test_hook_outro_projeto_shell.py`. A fila dos arquivos a reescrever,
na ordem, está no `to-dolist.md`. Relacionado: [[feedback_suite_inteira_so_no_ci]],
[[project_pytest_pasta_temporaria_por_projeto]].
