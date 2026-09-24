---
name: feedback_publicacao_e_ato_do_owner
description: Push em dev/homologação/produção e deploy (docker push, az, gh pr merge) é ato do OWNER — o assistente roda /mss-spec:release e PEDE; merge/rebase/push de feature rodam com a aprovação do owner; e feature nova só quando não há feature aberta (um item por janela é trava, não alerta)
gatilho: quando for publicar/integrar/fazer deploy (git push, merge, rebase, docker/az) ou quando surgir um 2º assunto na janela de uma feature
metadata:
  type: feedback
---

**Push em homologação/produção e deploy são ato do owner, nunca do assistente.** `git push` pra
`main`/`master`/`dev`/`develop`/`production`/`homolog*`/`hml*`/`prod*`/`release/*` (ou de destino
incerto), `gh pr merge`, `docker push`, `az acr build`, `az webapp <escrita>`, `az containerapp update`
são **negados** pelo hook `hooks/git_publicacao.py` (PreToolUse em Bash/PowerShell, ligado por
padrão, falha fechada). O caminho certo: `/mss-spec:release` → colar o veredito → **pedir**; o owner
executa do terminal dele. **Desde a 0.31.0** `git merge`, `git rebase` e push da branch de feature
**pedem aprovação** (o owner vê o comando e aprova) em vez de serem negados — a versão que negava tudo
travou o dia a dia (*"a atualização minha no merge está impactando o dia a dia"*, 2026-09-23); o
dano do F-022 foi o push que faz deploy, e só esse segue travado. **E um item por janela é trava — por CHAT:** o hook `hooks/um_item_por_janela.py`
bloqueia `/mss-spec:nova-feature` quando **este chat** já abriu outra feature que não está `fechada`
nem `pausada: <motivo>` (retomar a mesma passa). **Chat novo sempre abre**: feature aberta de outro
chat no `docs/superpowers/INDEX.md` só gera aviso + worktree (desde a 0.34.0 — contar por projeto
travou o chat novo e o owner passou a tirar o comando do prompt, 2026-09-24). Surgiu 2º assunto no meio (bug em homologação incluso)? **Não aja sobre ele**:
anote o estado da feature no `MAPA.md`, `to-dolist adicionar`, janela nova.

**Why:** 2026-09 (caso F-022 em `docs/EVALS.md`): uma janela aberta pra UMA feature (formatação da
resposta no WhatsApp) absorveu um 2º assunto (400 pra .Blip) e um 3º (flags em homologação),
mesclou branches no meio de um fix e **o assistente disparou `git push` várias vezes** — e o push
era o deploy automático em homologação. Quando o owner viu, já tinham ido; a homologação quebrou
inteira e custou "centenas de testes" pra entender o quê. A frase *"`git push` só quando eu pedir"*
e a regra *"um assunto por janela"* **já estavam** no `CLAUDE.md` — como prosa e como "alerta, não
trava" — e ficaram mudas na hora 2 da sessão. Nas palavras do owner: *"tem que ter outra trava que
funcione também! regra extremamente dura, 1 item por janela, nova feature somente quando não tiver
mais features abertas"*.

**How to apply:** o guardrail é mecânico (os dois hooks), então a tua parte é não brigar com ele:
ao ver `[mss-spec] BLOQUEADO`, não procure caminho alternativo (`gh api`, script, PowerShell) —
pare, rode o `release` e peça. Instrumentação de diagnóstico não altera contrato de resposta nem faz
merge sem OK. Parente de [[feedback_feature_a_partir_da_master]] (branch nasce da main; integrar é
voltar pra ela — pelo owner), de [[feedback-diagnostico-disciplinado]] (o 2º assunto da sessão era um
diagnóstico que virou código) e de [[feedback_projeto_ativo_read_only]] (a outra cerca mecânica do kit).
