# Mapa de contexto — mss-spec

## Onde estamos
`feature/teto-avisa-uma-vez-e-upgrade-sem-refazer-infra` (saiu da `main` em `4d28026`) — 0.52.0 em andamento: o teto da partida deixa de falar com o owner (MAPA/INDEX só pro assistente, uma vez por sessão; linha de sistema só quando o ato é dele), o teto do MAPA/INDEX conta só conteúdo, e o `upgrade` nunca reescreve os 4 arquivos do Docker que existem. Prova nas cópias do Whats e do MSS-SSC (scratchpad `sim/`): antes do código feita; depois, no fecho.

<!-- histórico do estado anterior -->
`fix/guardiao-sem-script` (saiu da `main` em `a96c92f`) — 0.51.1 por mesclar: o guardião da junção (script `.ps1` + tarefa agendada) foi **retirado** — ao registrar a tarefa, o owner foi contactado pela infra e pela Segurança da Informação: não permitido. Hook do `settings.json` do owner removido (cópia feita), `.ps1` e testes fora do kit, memória vira política com `gatilho_comando` (F-050). A junção que some com a atualização do app segue sem guarda: a alternativa é decisão do owner (marketplace local sem junção × hook Python de conferência), e passa pela SI antes.

<!-- histórico do estado anterior (2) -->
`main` em `a77e708` — **0.51.0 mesclada e publicada** (`origin/main` igual à `main`, push das 21:28), árvore limpa, nenhuma branch aberta. 2026-10-30 fechou duas versões a partir da conversa do Whats "Validar mensagens WhatsApp em produção" (F-048): 0.50.0 (kit entra primeiro · Stop por JSON · diário junto da memória · lembrete ligado · `docs/AMBIENTES.md` · `/mss-spec:tarefa`) e 0.51.0 (guardião da junção, fora do kit). Suíte: 1.131 verdes. Pendente desta sessão: o OK da captura de memória (rascunhos prontos, nada gravado).

## Próximo passo
1. ⬜ **Owner: merge `--no-ff` da `feature/teto-avisa-uma-vez-e-upgrade-sem-refazer-infra` na `main` e push** — o assistente roda o merge com a sua aprovação (hook); `git push origin main` é seu.
2. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
3. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md).
4. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy, quando abrir cada um** — com a 0.52.0 ele não reescreve mais a infra que existe; nasce o `docs/AMBIENTES.md` sem questionário.
5. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** e testar o `/mss-spec:bug` numa conversa nova (prova do `kit_primeiro.py`).

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
2. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md): instalar pelo app, conferir em conversa nova, só então tirar a junção, atualizar as memórias e o `doctor`.
3. ✅ **Owner: push da `main`** — `git push origin main` (0.51.1 + esta nota) — feito em 2026-11-03.
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

<!-- Atualizado em 2026-11-03 (0.52.0 pronta na branch, por mesclar; escolha A: marketplace local sem junção, a executar em conversa nova) · regenerável com /mss-spec:mapa -->
