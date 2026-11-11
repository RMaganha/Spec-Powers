# Mapa de contexto — mss-spec

## Onde estamos
Branch `feature/consultar-pela-acao` (da `main` em `52b347e`, 0.56.0 já integrada) — **0.57.0 (consultar a memória pela ação, decisão 24) pronta em 2026-11-11; o merge na `main` depende da aprovação do owner e a publicação é dele** (confira com `git log --oneline -3` e `git status -sb`): o owner manteve a decisão de 2026-09-25 (não buscar por palavras a cada comando) e fechou a 24 como ampliar o gatilho de ação — a captura cobra `gatilho_comando:`/`gatilho_resposta:` (ou `sem_gatilho_de_acao:`) da anotação de regra nova, e 21 anotações do kit ganharam o gatilho (lista aprovada por ele; valem em todo projeto). Spec: `docs/specs/memoria-em-tabela.md` (parte 3). Diário: `memory/sessions/2026-11-11-consultar-pela-acao.md`.

<!-- histórico do estado anterior -->
Branch `feature/memoria-em-tabela-parte-2` (da `main` em `5366d66`, mais o commit `77cd688` do item CRÍTICO do to-dolist, que o owner mandou ficar) — **0.56.0 (memória em tabela, parte 2) pronta em 2026-11-11; o merge na `main` depende da aprovação do owner e a publicação é dele** (suíte 1341 verdes; se a `main` já tem o merge, confira com `git log --oneline -3` e `git status -sb`): a busca das portas `tarefa`, `bug`, `duvida` e do `/mss-spec:memory buscar` usa a tabela, e a tabela se atualiza sozinha (hook `memoria_tabela_em_dia.py` na abertura da conversa e depois de gravar; o `buscar` confere antes de procurar). O modo `tabela` saiu da vista do owner. Régua com o código entregue: 43,8% e 47,7% entre os 10 nos pedidos reais (meta 41%). O aviso automático de 3 anotações **não** foi trocado — decisão do owner, com os números. Spec: `docs/specs/memoria-em-tabela.md`. Plano: `docs/superpowers/plans/2026-11-11-memoria-em-tabela-parte-2.md`.

## Próximo passo
1. ⬜ **Owner: aprovar o merge da `feature/consultar-pela-acao` na `main` (0.57.0) e fazer o `git push origin main`**
2. ⬜ **Medição do gatilho de ação — leituras em 2026-11-25 e 2026-12-11** — o que medir está na spec ("Conferido no real — parte 3").
3. ⬜ **Nos outros projetos, na conversa de cada um: lista das anotações antigas sem gatilho de ação** — `memoria_indice.py fila`; o owner aprova de uma vez. E o caso F-060 (aberto) espera o guardrail.
4. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
5. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md); só a partir daí o `marketplace update` passa a ser o passo pós-publicação.
6. ⬜ **`/mss-spec:upgrade` no Whats e no Energy, quando abrir cada um** — com a 0.54.0 é uma rodada só. **Transportes V2: ✅ feito em 2026-11-09** (`0190dfc` na `master` de lá, sem push; 1ª rodada real da 0.54.0). Detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)
7. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** e testar o `/mss-spec:bug` numa conversa nova (prova do `kit_primeiro.py`).
8. ⬜ **Dogfood no kit: as 40 citações mortas** (`python templates/memoria_indice.py citacoes`) — corrigir o caminho ou marcar a memória `obsoleta:`; e a autoria do MSIG_Agentes (`<a confirmar>` no dossiê).
9. ⬜ **Conversa nova por item — memória em tabela (passo 1) e conferência antes de entregar (passo 2)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)
10. ⬜ **Owner: decidir se o aviso automático de 3 anotações troca de motor** — números em `docs/specs/memoria-em-tabela.md` ("Conferido no real — parte 2").
11. ⬜ **Próximo da fila de memória: comando guardado inteiro na anotação** (item 8 do INDEX), em conversa nova.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
2. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md): instalar pelo app, conferir em conversa nova, só então tirar a junção, atualizar as memórias e o `doctor`.
3. ⬜ **Owner: push da `main`** — `git push origin main` (0.51.1 + esta nota).
4. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — nasce o `docs/AMBIENTES.md` em cada um; os valores só o owner preenche.
5. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** e testar o `/mss-spec:bug` numa conversa nova (prova do `kit_primeiro.py`).

<!-- histórico do próximo passo anterior (2) -->
1. ⬜ **Owner: OK da captura desta sessão** — 3 memórias novas, 2 atualizadas, caso F-049, 2 linhas fora de escopo e o fecho do diário; grava e commita local depois do OK.
2. ⬜ **Owner: registrar a tarefa agendada do guardião** — na sua janela do PowerShell, receita em `hooks/README.md` ("Fora do kit"); conferir com `Get-ScheduledTask "mss-spec guardiao da juncao"`.
3. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — cada um na conversa daquele projeto; nasce o `docs/AMBIENTES.md` com os nomes que o projeto já tem; os valores só o owner preenche.
4. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** — a tarde de 30/10 (token sem `MITI_DEV_AUTH`, push do n8n em produção) não tem diário.
5. ⬜ **No Whats: testar o `/mss-spec:bug`** — conversa nova, descrever um erro sem digitar o comando; o `kit_primeiro.py` deve negar o superpowers e apontar a porta.

## Conexões
<!-- FORMATO FIXO (o /mss-spec:mapa-neural parseia estas linhas pro grafo inter-projeto), uma por conexão:
       - → <outro-projeto>: o que ESTE envia/consome (<ponto: endpoint / fila / tabela compartilhada>)
       - ← <outro-projeto>: o que ESTE expõe/recebe   (<ponto>)
     Seta = DIREÇÃO do dado; o nome antes dos dois-pontos é o OUTRO projeto. Declare a partir do código real;
     NUNCA inventar — sem o ponto, marque <a confirmar>. "nenhuma" é válido. Guia completo: templates/MAPA.md. -->
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-11-10 (0.54.0 publicada; upgrade do Transportes V2 feito) · regenerável com /mss-spec:mapa -->
