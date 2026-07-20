# CI com artefatos de teste (design)

Data: 2026-07-20 · feature do próprio kit mss-spec (item 12 do INDEX; depende do item 9).

## Estado atual
O kit traz um `.gitlab-ci.yml` na raiz com um job `test` que instala `pytest pytest-cov`, roda a suíte e publica **artefatos** de teste que o GitLab renderiza nativamente: JUnit XML (`artifacts.reports.junit`) para resultados/tendência de duração e Cobertura XML (`artifacts.reports.coverage_report`) para cobertura. Os flags de artefato (`--junitxml`, `--cov --cov-report=xml`) vivem **no comando do job**, não no `addopts` do pytest — o `pytest -q` local segue limpo e sem exigir `pytest-cov`. As saídas de run (`report.xml`, `coverage.xml`, `htmlcov/`, `.coverage`) são ignoradas no `.gitignore` — run output nunca entra no repo (o anti-padrão que o item 12 evita). Como o item 9, o mecanismo está **preparado, não ativado**: `git remote` está vazio, então apontar/rodar num host real é passo manual do owner quando o host interno existir.

## Critérios de aceite
- DADO a raiz do repo, QUANDO valido o `.gitlab-ci.yml`, ENTÃO há um job que roda pytest e declara `artifacts.reports.junit` **e** `artifacts.reports.coverage_report` (formato `cobertura`).
- DADO o comando do job, QUANDO o inspeciono, ENTÃO ele gera JUnit XML (`--junitxml`) e cobertura Cobertura (`--cov` + `--cov-report=xml`), sem `addopts` que quebre o `pytest -q` local.
- DADO o `.gitignore`, QUANDO o verifico, ENTÃO `report.xml`, `coverage.xml`, `htmlcov/` e `.coverage` estão ignorados.
- DADO o `.gitlab-ci.yml`, QUANDO leio onde o host apareceria, ENTÃO não há host inventado; a ativação é passo do owner (placeholder), como no item 9.

## Fora de escopo
Apontar/rodar num host real · badge de cobertura · gate de % mínimo de cobertura · matrix de versões de Python · deploy/publish no pipeline · mover os flags de CI para o `addopts` do pytest.

## Histórico
- 2026-07-20 — criado: design da CI com artefatos de teste (item 12), aprovado no chat. Escolhas do owner: plataforma GitLab CI (renderiza JUnit + Cobertura + tendência de duração sem plugin); host como placeholder espelhando o item 9; flags de artefato no comando do job, não no `addopts` (mantém `pytest -q` local limpo).
