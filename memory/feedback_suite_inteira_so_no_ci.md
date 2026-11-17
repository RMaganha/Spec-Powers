---
name: feedback_suite_inteira_so_no_ci
description: na máquina do owner roda só o teste do que mudou, escolhido pelo templates/testes_do_que_mudou.py; a suíte inteira e os testes ainda não reescritos rodam só no CI
gatilho: quando for rodar pytest na máquina do owner
gatilho_comando: pytest(?:\s+-[\w-]+(?:=\S+)?)*(?:\s+tests/?)?(?:\s+-[\w-]+(?:=\S+)?)*(?:\s+\d?>\S*)*\s*(?:$|[;&|])
metadata:
  type: feedback
---

Regra 9 do kit desde a 0.65.0 (`docs/decisoes.md`, 2026-11-17). Na máquina do owner:

```
python templates/testes_do_que_mudou.py --rodar
```

O script lê o que mudou na branch e roda só os testes que citam ou importam a peça mudada. A suíte inteira roda no
GitHub Actions (`.github/workflows/testes.yml`) a cada push do owner; para ler as falhas, ver
[[reference_ci_do_kit_sem_login]].

**Why:** rodar o teste do bpmn quando a mudança foi na memória não pega nada e só pesa (owner, 2026-11-17). E teste
ainda não reescrito cria uma pasta por teste: rodá-lo na máquina para conferir uma troca de uma linha encheu a pasta
temporária de novo (caso F-073 do `docs/EVALS.md`).

**How to apply:** o gatilho de comando casa a suíte inteira (`python -m pytest tests/ -q`, `python -m pytest -q`) e
não casa um arquivo só, `arquivo::teste` nem o script. Teste ainda não reescrito que precisa ser conferido: deixe para o
CI. Relacionado: [[feedback_teste_nao_cria_pasta]], [[project_pytest_pasta_temporaria_por_projeto]].
