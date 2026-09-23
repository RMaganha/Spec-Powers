---
name: feedback_pipe_mascara_o_exit_do_teste
description: `pytest … | tail -1 && git commit` commita com suíte vermelha — o exit do pipe é o do tail; use set -o pipefail ou rode o pytest em passo próprio
gatilho: quando encadear o comando de teste com git commit (ou qualquer ação) no mesmo comando de shell
metadata:
  type: feedback
---

2026-09-15, commit `edc0ab9` do kit: `python -m pytest tests/... -q 2>&1 | tail -1 && git add … && git commit`
commitou com **2 testes vermelhos**. O `&&` viu o exit do `tail` (0), não o do pytest. Só apareceu duas
tarefas depois, ao rodar a suíte inteira sem pipe. Caso **F-025** em `docs/EVALS.md` — reincidiu em
`f9388e5` com esta memória já escrita, e desde a 0.30.0 é **cerca**: o `hooks/git_publicacao.py` nega
pytest com saída em pipe antes do `git commit` no mesmo comando (escape do owner: `MSS_PIPE_TESTE_OFF=1`).
A memória segue valendo pra onde a cerca não olha (`dotnet test`, `npm test`, `;` sem pipe).

**Why:** "rodou sem erro" era o `tail`. A regra 9 do `CLAUDE.md` (rode o teste e cole a saída) pressupõe
que o exit visto é o do teste — o pipe quebra essa premissa em silêncio.

**How to apply:** ou `set -o pipefail` no início do comando, ou pytest num passo próprio (ler a linha
`N passed` antes de commitar), ou `pytest … && git commit` sem pipe no meio. Nunca `| tail`/`| head`
antes de um `&&` que grava.
