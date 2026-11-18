# Molde de CI — a suíte inteira do projeto roda no CI a cada push

## Estado atual
**Entregue na 0.66.0 (`feature/molde-de-ci`); ainda não rodou num projeto de verdade.**

Um molde por plataforma, com o mesmo funcionamento: `templates/ci/github-testes.yml` → `.github/workflows/testes.yml`
(GitHub Actions) e `templates/ci/azure-pipelines-testes.yml` → `azure-pipelines-testes.yml` (Azure DevOps). Os dois
rodam a suíte inteira a cada push em qualquer branch, numa máquina `ubuntu-latest` da Microsoft (fora da rede
corporativa: sem proxy, sem CA do FortiGate), com o Python do `.python-version` do projeto (3.12 se não houver) e as
dependências do que existir (requirements.txt + requirements-dev.txt, senão pyproject.toml; sempre `pytest`). O de
Azure não publica nada nem usa conexão com o Azure, e o nome nunca bate com um pipeline de publicação; ele também manda
o JUnit pra aba **Tests** da rodada.

A lista do que falhou e o tratamento do teste `externo` moram no `templates/pytest/conftest.py` (que já vai pra todo
projeto): no CI (`GITHUB_ACTIONS` ou `TF_BUILD`), o teste marcado `@pytest.mark.externo` (precisa de banco ou serviço
que o CI não alcança) é pulado, e no fim sai **uma** linha de erro com os testes que falharam — anotação `::error` no
GitHub, `##vso[task.logissue type=error]` no Azure — mais um aviso com quantos `externo` foram pulados. O código de
saída é o do pytest, exceto "nenhum teste coletado" (5), que no CI vira 0 — projeto recém-constituído ainda não tem
teste. Na máquina nada muda: o `externo` roda normalmente (quando o `testes_do_que_mudou.py` o escolhe). O CI do kit
(`.github/workflows/testes.yml`) usa a mesma lista, do `conftest.py` da raiz.

A plataforma vem da linha `**Versionamento:**` do `CLAUDE.md`; se ela não disser, dos endereços dos remotos git
(`github.com` → GitHub; `dev.azure.com`/`visualstudio.com` → Azure; todos os remotos, não só `origin`); sem decisão ou
com os dois, o `kickoff`/`upgrade` pergunta e grava a resposta nessa linha. Arquivo de CI que já existe e não começa
com a marca do kit: mostra a diferença e pergunta (como o `conftest.py`).

No Azure, quem lê a rodada é o owner (projeto privado, sem token pro assistente): ele cola a linha de erro na conversa.

### Critérios de aceite
1. DADO um projeto no GitHub, QUANDO o `kickoff`/`upgrade` roda, ENTÃO nasce `.github/workflows/testes.yml` do molde, com
   disparo em `push` e `pull_request`.
2. DADO um projeto no Azure DevOps, QUANDO o `kickoff`/`upgrade` roda, ENTÃO nasce `azure-pipelines-testes.yml`, com
   `trigger` explícito em todas as branches, `ubuntu-latest`, sem `AzureCLI`/conexão de serviço, e o JUnit publicado
   mesmo quando a suíte falha.
3. DADO uma rodada no CI com testes falhando, QUANDO o pytest termina, ENTÃO sai uma linha de erro só, no formato da
   plataforma, com um teste por linha (`%0A`), e o código de saída é o do pytest.
4. DADO um teste `@pytest.mark.externo`, QUANDO roda no CI, ENTÃO é pulado e o aviso diz quantos; QUANDO roda na
   máquina, ENTÃO roda.
5. DADO um projeto sem `.python-version` nem `requirements*.txt`, QUANDO o CI roda, ENTÃO usa 3.12 e instala pelo
   pyproject.toml (se houver) mais `pytest`.

**Fora de escopo:** Postgres descartável no CI, token de leitura pro assistente no Azure, pacote de repositório
privado, projeto C#/.NET, regra de branch do Azure pra pull request (opcional, passo do owner no portal).

## Histórico
- 2026-11-18 — criado: molde de CI por plataforma (GitHub e Azure DevOps); o owner aprovou as escolhas (teste
  `externo` pulado no CI, owner lê a rodada no Azure, sem passo de autenticação pra pacote privado). Implementação: a
  lista de falhas e o pulo do `externo` foram pro `conftest.py` do molde, em vez de bash no YAML — Python testável em
  memória, e o YAML fica igual nas duas plataformas.
- 2026-11-18 — entregue na 0.66.0; acrescentado "nenhum teste coletado não é falha no CI" (motivo: o kickoff leva o
  molde a projeto que ainda não tem teste, e o CI nasceria vermelho).
