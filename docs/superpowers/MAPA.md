# Mapa de contexto — mss-spec

## Onde estamos
**0.66.0 (molde de CI) na `main`** — merge `--no-ff` em `b197f0e`; CI do kit verde na branch (`cfa2666`, run `44377466547`). Falta o push da `main` (owner). Spec: `docs/specs/molde-de-ci.md`; diário: `memory/sessions/2026-11-18-molde-de-ci.md`.

<!-- histórico do estado anterior -->
Branch `feature/molde-de-ci` — 0.66.0 feita, 1606 passed, CI verde; faltava o merge.
## Próximo passo
00. ⬜ **Owner: push da `main`** — `git push origin main` (merge `b197f0e`, 0.66.0); conferir o CI verde na `main`.
01. ⬜ **Provar o molde de CI num projeto de verdade** — `/mss-spec:upgrade` num projeto do Azure DevOps (o owner liga o pipeline no portal) e marcar `externo` o que a 1ª rodada mostrar.
02. ⬜ **Custo dos hooks num projeto grande** (conversa nova, o owner indica o projeto) — texto pronto em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)
0. ⬜ **Decidir o conflito `UserPromptSubmit` exit 0 × exit 2** (a 0.64.0 já foi publicada).
0a. ⬜ **Decidir como a regra 3 nova chega ao `.claude/rules/frontend.md` dos projetos** — o `upgrade` não sobrescreve o que existe; item no `to-dolist.md`.
1. ⬜ **Provar a 0.61.0 no real** — conversa pelo + só com uma frase do assunto; e o owner regrava o plano de teste base (`/mss-spec:plano-teste`: ainda diz 1564; a suíte mudou na 0.65.0).
1a. ⬜ **Provar a 0.60.0 no real** — a negação aparecendo numa captura de verdade (anotação ou diário com comando com reticências) e o aviso do `verificar` no Whats, na conversa dele.
1b. ⬜ **Provar a 0.59.0 no real** — falta o clique de aprovação ao trocar de branch numa branch que a conversa não abriu (a regra chegando numa conversa aberta com `Já decidido`: ✅ 2026-11-12).
1c. ✅ **`mss-spec:pesquisador` aparece na lista de ajudantes** de uma conversa nova (visto em 2026-11-16, na abertura da parte 2 do sono).
2. ⬜ **Medição do gatilho de ação — leituras em 2026-11-25 e 2026-12-11** — o que medir está na spec ("Conferido no real — parte 3").
3. ⬜ **Nos outros projetos, na conversa de cada um: lista das anotações antigas sem gatilho de ação** — `memoria_indice.py fila`; o owner aprova de uma vez. E o caso F-060 (aberto) espera o guardrail.
4. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
5. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md); só a partir daí o `marketplace update` passa a ser o passo pós-publicação.
6. ⬜ **`/mss-spec:upgrade` no Whats e no Energy, quando abrir cada um** — com a 0.54.0 é uma rodada só. **Transportes V2: ✅ feito em 2026-11-09** (`0190dfc` na `master` de lá, sem push; 1ª rodada real da 0.54.0). Detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)
7. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** e testar o `/mss-spec:bug` numa conversa nova (prova do `kit_primeiro.py`).
8. ⬜ **Autoria do MSIG_Agentes** (`<a confirmar>` no dossiê). As 40 citações mortas: ✅ 0 na 0.62.0.
9. ⬜ **Conversa nova por item — memória em tabela (passo 1) e conferência antes de entregar (passo 2)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)
10. ⬜ **Owner: decidir se o aviso automático de 3 anotações troca de motor** — números em `docs/specs/memoria-em-tabela.md` ("Conferido no real — parte 2").
11. ⬜ **Os 4 itens de 2026-11-12 no `to-dolist.md`** (o 1º é o guardrail do F-067) — cada um em conversa nova.
12. ⬜ **Próximo da fila do owner: lista de conferência antes de entregar** (item 13 do INDEX), em conversa nova.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
2. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md): instalar pelo app, conferir em conversa nova, só então tirar a junção, atualizar as memórias e o `doctor`.
3. ⬜ **Owner: push da `main`** — `git push origin main` (0.51.1 + esta nota).
4. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — nasce o `docs/AMBIENTES.md` em cada um; os valores só o owner preenche.
5. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** e testar o `/mss-spec:bug` numa conversa nova (prova do `kit_primeiro.py`).

## Conexões
<!-- FORMATO FIXO (o /mss-spec:mapa-neural parseia estas linhas pro grafo inter-projeto), uma por conexão:
       - → <outro-projeto>: o que ESTE envia/consome (<ponto: endpoint / fila / tabela compartilhada>)
       - ← <outro-projeto>: o que ESTE expõe/recebe   (<ponto>)
     Seta = DIREÇÃO do dado; o nome antes dos dois-pontos é o OUTRO projeto. Declare a partir do código real;
     NUNCA inventar — sem o ponto, marque <a confirmar>. "nenhuma" é válido. Guia completo: templates/MAPA.md. -->
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-11-18 (0.66.0 molde de CI na main, merge b197f0e; falta o push) · regenerável com /mss-spec:mapa -->
