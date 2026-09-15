---
name: feedback_pipe_mascara_o_exit_do_teste
description: `pytest … | tail -1 && git commit` commita com suíte vermelha — o exit do pipe é o do tail; use set -o pipefail ou rode o pytest em passo próprio
gatilho: quando encadear o comando de teste com git commit (ou qualquer ação) no mesmo comando de shell
metadata:
  type: feedback
---

2026-09-15, commit `edc0ab9` do kit: `python -m pytest tests/... -q 2>&1 | tail -1 && git add … && git commit`
commitou com **2 testes vermelhos**. O `&&` viu o exit do `tail` (0), não o do pytest. Só apareceu duas
tarefas depois, ao rodar a suíte inteira sem pipe. Caso **F-025** em `docs/EVALS.md` (aberto).

**Why:** "rodou sem erro" era o `tail`. A regra 9 do `CLAUDE.md` (rode o teste e cole a saída) pressupõe
que o exit visto é o do teste — o pipe quebra essa premissa em silêncio.

**How to apply:** ou `set -o pipefail` no início do comando, ou pytest num passo próprio (ler a linha
`N passed` antes de commitar), ou `pytest … && git commit` sem pipe no meio. Nunca `| tail`/`| head`
antes de um `&&` que grava.
