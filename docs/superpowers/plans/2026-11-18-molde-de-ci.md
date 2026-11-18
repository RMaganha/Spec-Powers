# Molde de CI — plano (nível médio, execução inline)

**Spec:** `docs/specs/molde-de-ci.md` · **Branch:** `feature/molde-de-ci`

**Restrições globais:** máquina `ubuntu-latest`; Python do `.python-version`, senão `3.12`; título da lista
`testes que falharam` (o mesmo do kit hoje); marca `externo`; o `conftest.py` da raiz do kit é cópia byte a byte do
molde (`tests/test_pytest_mss.py::test_kit_usa_o_proprio_molde`); teste na máquina só pelo
`templates/testes_do_que_mudou.py --rodar`.

**Pontos de atenção (sem teste próprio, conferir na revisão):** id de teste com `]`, `;` ou `%` (parametrizado)
quebraria o comando do Azure → escapar; lista enorme → cortar em 200 linhas, como hoje; projeto cujo `conftest.py` da
raiz não é o do kit → sem lista, mas o código de saída continua falhando a rodada; o CI do kit passa a ter a lista
vinda do `conftest.py` → tirar o bash do `.github/workflows/testes.yml` pra não sair duas vezes.

## Task 1 — `templates/pytest/conftest.py`: lista de falhas e marca `externo` (AC 3 e 4)
- Teste (`tests/test_pytest_mss.py`), tudo em memória:
  - `plataforma_do_ci({"GITHUB_ACTIONS": "true"}) == "github"`, `({"TF_BUILD": "True"}) == "azure"`, `({}) is None`
  - `linha_de_falhas("github", ["t.py::a", "t.py::b"]) == "::error title=testes que falharam::t.py::a%0At.py::b"`
  - `linha_de_falhas("azure", ["t.py::a[x;y]"])` começa com `##vso[task.logissue type=error]`, traz `%3B` e `%5D`, uma linha só
  - `linha_de_falhas(_, [])` e `linha_de_falhas(None, [...])` → `None`; 250 falhas → 200 na linha
  - `linha_de_externos("github", 3)` → `::warning …3…`; `(_, 0)` → `None`
  - `pytest_collection_modifyitems` com itens falsos: no CI, o marcado `externo` ganha `skip`; fora do CI, não
  - `pytest_configure` registra a marca `externo` mesmo quando a rodada é de dentro (dono já setado)
  - `pytest_terminal_summary` com reporter falso escreve as duas linhas no CI e nada fora dele
- Código: as três funções sem disco + os hooks; `MOTIVO_EXTERNO` para contar os pulados.
- Copiar o molde para o `conftest.py` da raiz.

## Task 2 — os dois moldes de CI (AC 1, 2 e 5)
- Teste (`tests/test_ci.py`): os dois YAML abrem; 1ª linha `# CI do kit mss-spec`; GitHub com `push` e
  `pull_request`; Azure com `trigger.branches.include == ["*"]`, `vmImage: ubuntu-latest`, `UsePythonVersion@0` com
  `$(versaoPython)`, `PublishTestResults@2` JUnit com `condition: succeededOrFailed()`, sem `AzureCLI` nem
  `azureSubscription`; o script das dependências é o mesmo texto nos dois e cobre `.python-version`/3.12,
  `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` e `pytest`.
- Código: `templates/ci/github-testes.yml`, `templates/ci/azure-pipelines-testes.yml`.
- CI do kit: `.github/workflows/testes.yml` deixa o bash da lista (agora vem do `conftest.py`); ajustar
  `test_github_actions_roda_a_suite_inteira_a_cada_push`.

## Task 3 — `kickoff`, `upgrade` e a linha `Versionamento` (AC 1 e 2)
- `commands/kickoff.md` e `commands/upgrade.md`: qual plataforma (linha `**Versionamento:**` → remotos git → pergunta),
  qual molde copiar, a marca da 1ª linha (existe sem ela → diff e pergunta), passo do owner no Azure (Pipelines → New
  pipeline → Existing YAML → `azure-pipelines-testes.yml`).
- `templates/CLAUDE.md`: `**Versionamento:**` passa a dizer onde fica hospedado.
- Teste: o `test_smoke_kit.py::test_templates_citados_existem` já confere os caminhos citados; um teste curto no
  `test_ci.py` confere que kickoff e upgrade citam os dois moldes.

## Fecho
`testes_do_que_mudou.py --rodar` → revisão → spec "Estado atual" no presente → versão nos dois manifestos +
`CHANGELOG.md` → captura da memória (inclui `memory/reference_ci_do_kit_sem_login.md`, que fala do `set +e`).
