# Mapa de contexto — mss-spec

## Onde estamos
`main` em `a77e708` — **0.51.0 mesclada e publicada** (`origin/main` igual à `main`, push das 21:28), árvore limpa, nenhuma branch aberta. 2026-10-30 fechou duas versões a partir da conversa do Whats "Validar mensagens WhatsApp em produção" (F-048): 0.50.0 (kit entra primeiro · Stop por JSON · diário junto da memória · lembrete ligado · `docs/AMBIENTES.md` · `/mss-spec:tarefa`) e 0.51.0 (guardião da junção, fora do kit). Suíte: 1.131 verdes. Pendente desta sessão: o OK da captura de memória (rascunhos prontos, nada gravado).

<!-- histórico do estado anterior -->
`feature/guardiao-da-juncao` (saiu da `main` em `ebd1a5c`) — 0.51.0 pronta na branch, por mesclar: o guardião da junção (`templates/guardiao-da-juncao.ps1`) recria `~/.claude/skills/mss-spec` quando some, com captura de evidência; hook `SessionStart` já gravado no `~/.claude/settings.json` do owner (cópia feita); a tarefa agendada (logon + hora em hora) **falta o owner registrar** — o sandbox do Claude não consegue. A 0.50.0 está mesclada e publicada (`8a6feaf`).

<!-- histórico do estado anterior (2) -->
`feature/kit-entra-primeiro` (saiu da `main` em `755ba99`) — 0.50.0 pronta na branch, por mesclar (owner): hooks `kit_primeiro.py` (superpowers só por dentro do kit) e `diario_junto.py` (memória sem diário não sai), `confere_citacoes.py` devolvendo por JSON (a devolução do Stop nunca chegava nesta máquina), lembrete de captura ligado por sessão, `templates/AMBIENTES.md` + recall por seção, diário (7 dias) e ambiente no passo 1 de `bug`/`duvida`/`diagnostico`, `doctor` 12-13, porta `/mss-spec:tarefa` pro dia a dia. Caso F-048 fechado; suíte inteira: 1.122 verdes.

## Próximo passo
1. ⬜ **Owner: OK da captura desta sessão** — 3 memórias novas, 2 atualizadas, caso F-049, 2 linhas fora de escopo e o fecho do diário; grava e commita local depois do OK.
2. ⬜ **Owner: registrar a tarefa agendada do guardião** — na sua janela do PowerShell, receita em `hooks/README.md` ("Fora do kit"); conferir com `Get-ScheduledTask "mss-spec guardiao da juncao"`.
3. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — cada um na conversa daquele projeto; nasce o `docs/AMBIENTES.md` com os nomes que o projeto já tem; os valores só o owner preenche.
4. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** — a tarde de 30/10 (token sem `MITI_DEV_AUTH`, push do n8n em produção) não tem diário.
5. ⬜ **No Whats: testar o `/mss-spec:bug`** — conversa nova, descrever um erro sem digitar o comando; o `kit_primeiro.py` deve negar o superpowers e apontar a porta.

<!-- histórico do próximo passo anterior -->
1. ⬜ **Owner: merge e push da 0.51.0** — `git switch main` · `git merge --no-ff feature/guardiao-da-juncao` · `git push origin main`.
2. ⬜ **Owner: registrar a tarefa agendada do guardião** na sua janela do PowerShell (receita em `hooks/README.md`, seção "Fora do kit") e conferir com `Get-ScheduledTask "mss-spec guardiao da juncao"`; o log fica em `~/.claude/mss-spec/guardiao-juncao.log`.
3. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; nasce o `docs/AMBIENTES.md` com os nomes que o projeto já tem e `falta preencher` no resto — os valores só o owner tem.
4. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** — a tarde de 30/10 (token sem `MITI_DEV_AUTH`, push do n8n em produção não resolvido) não tem diário.
5. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando: o hook `kit_primeiro.py` deve negar o superpowers e apontar a porta.

<!-- histórico do próximo passo anterior (2) -->
1. ⬜ **Owner: merge e push da 0.50.0** — `git switch main` · `git merge --no-ff feature/kit-entra-primeiro` · `git push origin main`.
2. ⬜ **Owner: tirar `LC_ALL=enu` das variáveis de ambiente do Windows** (ou pôr `C.UTF-8`) e reabrir o app — o `doctor` (check 12) avisa enquanto estiver assim.
3. ⬜ **`/mss-spec:upgrade` no Whats, no Transportes e no Energy** — o owner roda, cada um na conversa daquele projeto; nasce o `docs/AMBIENTES.md` com os nomes que o projeto já tem e `falta preencher` no resto — os valores só o owner tem.
4. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** — a tarde de 30/10 (token sem `MITI_DEV_AUTH`, push do n8n em produção não resolvido) não tem diário.
5. ⬜ **No Whats: testar o `/mss-spec:bug`** — janela nova, descrever um erro sem digitar o comando: o hook deve negar o superpowers e apontar a porta.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-30 (0.51.0 mesclada e publicada; captura da sessão aguardando OK) · regenerável com /mss-spec:mapa -->
