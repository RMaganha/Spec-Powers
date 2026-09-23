# Ao versionar, publicar e fechar

- **quando abrir branch de feature ou fix** → [Feature sempre a partir da `main`](../feedback_feature_a_partir_da_master.md) — nunca ramificar de outra branch
- **quando for publicar/integrar/fazer deploy (push, merge, rebase, docker/az) ou surgir 2º assunto na janela** → [Push em homologação/produção é ato do owner; um item por janela é trava](../feedback_publicacao_e_ato_do_owner.md) — push protegido/deploy: hook nega, `release` + pedir; merge/rebase/push de feature: hook pede aprovação; feature nova só sem aberta (F-022)
- **quando bumpar a versão do kit** → [Versão vive em dois manifestos](../project_versao_em_dois_manifestos.md) — `plugin.json` + `marketplace.json`, e re-rode a suíte
- **quando fechar mudança em gerador ou CLI** → [Dogfood com diff antes × depois](../project_dogfood_gerador_diff_antes_depois.md) — fixture não vê o que só o projeto real tem
- **quando publicar ou instalar o kit por marketplace** → [relative-path serve git E local](../project_marketplace_relative_path_serve_git_e_local.md) — o mesmo `marketplace.json` resolve os dois
- **quando mexer em dependências no `plugin.json`** → [Dep cross-marketplace quebra o load](../project_plugin_load_cross_marketplace.md) — some tudo enquanto carrega por symlink
- **quando encadear pytest e `git commit` no mesmo comando** → [Pipe mascara o exit do teste](../feedback_pipe_mascara_o_exit_do_teste.md) — `pytest | tail -1 && git commit` commitou com 2 vermelhos (F-025); `set -o pipefail` ou pytest em passo próprio
