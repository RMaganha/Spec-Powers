# 2026-11-09 — upgrade em uma rodada só (0.54.0)

Branch `feature/upgrade-em-uma-rodada` (da `main` em `eda9f62`). Spec:
`docs/superpowers/specs/2026-07-16-upgrade-design.md` ("Estado atual").

## Conversamos
- O owner abriu com `/mss-spec:nova-feature` colado: o `/mss-spec:upgrade` no Transportes V2 virou 3 conversas
  (migração do `CLAUDE.md` · conversão do to-dolist · categorias nem começaram), todas paradas na mesma pergunta
  sobre 3 arquivos modificados sem commit na `fix/atm-virada-outubro`. Pediu: status na abertura, árvore suja
  resolvida uma vez (guarda e devolve, nunca commita o trabalho dele), uma branch, um commit por passe,
  integração com OK + principal de volta pra branch dele, nunca conversa nova entre passes; testes em `tests/`.
- Lidas as 3 transcrições do Transportes (só leitura): o comportamento estava escrito na prosa ("primeiro e
  sozinha", "Termine aqui", "árvore limpa" em cada passe); o que destravou a 2ª e a 3ª foi o owner ditar o
  roteiro stash → branch → commit → merge → `--ff-only` → `stash pop`.

## Pivôs
- **Só prosa → script só-leitura + prosa.** A memória `feedback_comandos_prosa_nao_unit_test` diz que prosa não se
  testa como código; o owner pediu teste da ordem dos passes e da árvore suja. Saída: a decisão (ordem e situação
  do git) vira `templates/upgrade_plano.py checar` (código, 12 testes com repo git em `tmp_path`); a prosa ganha
  só testes-contrato no smoke.
- **Categorias passam a ter commit** (antes "não commita, deixa no working tree"): sem commit não há merge na
  principal (itens 3 e 4 do pedido). O to-dolist mantém os 2 commits (tempo 1 = original no git).
- **MAPA com 2 blocos de histórico** quebrou `test_mapa_carrega_um_estado_anterior`: o bloco do guardião foi
  **movido** pro `MAPA-historico.md` (nunca apagado).
- Dois testes do smoke codificavam o desenho antigo (branch `chore/migrar-claude-md`, "nenhuma outra categoria")
  → atualizados ao desenho novo, não apagados.

## Rejeitado
- Script que faz também o git (esconde o merge do owner; não serve ao projeto que reserva o git a ele).
- Só reescrever a prosa (foi a prosa que falhou 3×; o teste seria grep de frase).
- Varrer `apps/*` na conversão (`to-dolist.md`, linha 7): fica como item, fora desta feature.

## Fizemos
- `templates/upgrade_plano.py` + `tests/test_upgrade_plano.py` · `commands/upgrade.md` reescrito (abertura pelo
  script, seção Git, 3 passes, fecho com integração e conferência colada) · smoke `test_upgrade_em_uma_rodada_wiring`
  · spec, INDEX (fechada), LEIA-ME, CHANGELOG, 0.54.0 nos dois manifestos, baseline 1250 verdes.
- Hooks que agiram certo nesta sessão: `git_publicacao.py` (pipe de pytest antes do commit), memória do heredoc com
  acento (script foi pro scratchpad), `confere_citacoes.py` (2 devoluções por arquivo proposto citado como existente).
- Caso **F-053**: `kit_primeiro.py` não viu o comando colado e negou o brainstorming.

## Próximo
- Merge na `main` (aprovação do owner no hook) · `git push origin main` (owner) · `/mss-spec:upgrade` no Whats,
  Transportes (só faltam as categorias) e Energy · conserto do F-053 (item no to-dolist).
