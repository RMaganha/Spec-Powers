---
name: reference_ci_do_kit_sem_login
description: o resultado e as falhas do CI do kit no GitHub se leem pela API pública (rodada, job, anotações), sem login — o gh não está instalado e o log do job pede administrador
gatilho: quando precisar ler o resultado ou as falhas do CI do kit no GitHub
metadata:
  type: reference
---

Visto em 2026-11-17: o `gh` não está instalado nesta máquina; o log do job pela API devolve "Must have admin rights to
Repository"; a página do job pede login, e o navegador embutido não ficou logado. O que funciona, sem login:

1. A rodada mais recente da branch (troque a branch):
```
curl -s "https://api.github.com/repos/RMaganha/Spec-Powers/actions/runs?branch=main&per_page=1" | python -c "import json,sys; r=json.load(sys.stdin)['workflow_runs'][0]; print(r['id'], r['head_sha'][:7], r['status'], r['conclusion'])"
```
2. O job da rodada (troque `<run>` pelo id do passo 1):
```
curl -s "https://api.github.com/repos/RMaganha/Spec-Powers/actions/runs/<run>/jobs" | python -c "import json,sys; print(json.load(sys.stdin)['jobs'][0]['id'])"
```
3. As falhas (troque `<job>` pelo id do passo 2) — o `.github/workflows/testes.yml` publica a lista numa anotação de
título "testes que falharam":
```
curl -s "https://api.github.com/repos/RMaganha/Spec-Powers/check-runs/<job>/annotations" | python -c "import json,sys; [print(a.get('title'), a.get('message','')) for a in json.load(sys.stdin) if a.get('annotation_level')=='failure']"
```

Quem escreve a anotação é o `conftest.py` da raiz (cópia do molde `templates/pytest/conftest.py`, função
`linha_de_falhas`), no fim da rodada, quando `GITHUB_ACTIONS=true`; o passo do YAML é só `python -m pytest -q -rfE`.
Nos projetos no Azure DevOps a mesma lista sai como `##vso[task.logissue type=error]`, mas a rodada só abre logado:
quem lê é o owner, que cola a linha na conversa (decisão de 2026-11-18, `docs/specs/molde-de-ci.md`).

substituiu: "o passo da suíte roda com `set +e` e monta a anotação em bash" (0.66.0, 2026-11-18).
Relacionado: [[feedback_suite_inteira_so_no_ci]].
