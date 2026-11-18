# 2026-11-18 — molde de CI: a suíte inteira de cada projeto no CI, no GitHub ou no Azure DevOps (0.66.0)

## Conversamos
O owner abriu `/mss-spec:nova-feature` com o texto pronto do `PROXIMO-PASSO.md`. Já decidido: suíte inteira no CI a
cada push, na máquina só o teste do que mudou; o kit já faz assim (`.github/workflows/testes.yml`); o molde chega
pelo `kickoff` e pelo `upgrade`. Faltava decidir a plataforma (este no GitHub, a maioria no Azure DevOps, cada projeto
com a sua) e o que fazer com dependências e testes que precisam de banco ou serviço externo.

## Pivôs
- O item 00 do MAPA, que o pedido mandava tirar no 1º commit, já tinha saído num commit da `main` local de outra
  conversa (`8d28b7b`, 15:33, sem push): a `main` estava 2 à frente da `origin/main` quando a branch foi aberta. O 1º
  commit ficou só com o "Onde estamos".
- O Whats publica no Azure com o remoto chamado `azure`, não `origin`: a plataforma se lê de todos os remotos.
- A lista do que falhou ia ser bash no YAML, como no CI do kit; foi pro `conftest.py` do molde (Python testável em
  memória, YAML igual nas duas plataformas). Com isso o CI do kit perdeu o bash, pra anotação não sair duas vezes.
- Projeto recém-constituído pelo `kickoff` não tem teste: o pytest sai com 5 e o CI nasceria vermelho. No CI, 5 vira 0.
- A documentação da Microsoft diz que a organização pode desligar o disparo implícito: `trigger` vai explícito. Pull
  request no Azure Repos só por regra de branch no portal (opcional; o push já cobre).

## Rejeitado
- Rodar a suíte dentro da imagem Docker do projeto; gerar um YAML sob medida por projeto; um arquivo só pras duas
  plataformas (motivos em `docs/decisoes.md`, 2026-11-18).
- Postgres descartável no CI e token de leitura no Azure (linhas `#fora-de-escopo` no `to-dolist.md`).

## Fizemos
- `templates/ci/github-testes.yml` e `templates/ci/azure-pipelines-testes.yml`; `templates/pytest/conftest.py` com
  `plataforma_do_ci`, `linha_de_falhas`, `linha_de_externos`, o pulo do `externo` e o 5 → 0 no CI; `kickoff`,
  `upgrade` e a linha `Versionamento` do `templates/CLAUDE.md`. Conferido no pytest real numa pasta de rascunho.
- 0.66.0; teste do que mudou: 1606 passed. Spec `docs/specs/molde-de-ci.md`.

## Próximo
- Push da `main` e da `feature/molde-de-ci` (owner), CI do kit verde, merge.
- Provar num projeto do Azure DevOps pelo `upgrade`: o owner liga o pipeline no portal e marca `externo` o que a 1ª
  rodada mostrar.
