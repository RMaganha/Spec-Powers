# Mapa de contexto — mss-spec

## Onde estamos
`main` — **0.54.0 publicada** (`origin/main` em `6fd4e63`, push do owner em 2026-11-09): **o `/mss-spec:upgrade` trata tudo numa rodada e numa conversa.** Até a 0.53.0 o comando terminava depois de cada passe (migração do `CLAUDE.md` · to-dolist · categorias) e exigia árvore limpa em cada um; no Transportes V2 (2026-11-09) isso virou 3 conversas paradas na mesma pergunta sobre trabalho pendente em outra branch. Entregue: `templates/upgrade_plano.py` (só lê; abre com o status e a situação do git; 12 testes) e `commands/upgrade.md` com uma branch (`chore/upgrade-kit`), um commit por passe, stash único do pendente do owner, integração na principal + `--ff-only` de volta pra branch dele e conferência colada. Suíte: 1250 verdes. Spec: `docs/superpowers/specs/2026-07-16-upgrade-design.md`.

<!-- histórico do estado anterior -->
`main` — **0.53.0 publicada** (`origin/main` em `fd2d7fb`, push do owner em 2026-11-06): entraram a branch do teto (0.52.0 — o teto fala só com o assistente, mede só conteúdo, upgrade não reescreve infra) e a `feature/absorver-msig-agentes` (0.53.0 — benchmark do kit de agentes da equipe, `docs/analise/2026-11-06-benchmark-msig-agentes.md`, 12 melhorias, um commit por item — lista no `CHANGELOG.md`). A junção `~/.claude/skills/mss-spec` ainda aponta pro clone, então hooks e comandos da 0.53.0 já valem em todo projeto; o que cada projeto ainda não tem são os arquivos novos do molde (`/mss-spec:upgrade`, passo 4). A `main` local está à frente do `origin` (correções do MAPA e a captura desta sessão); `git push origin main` é do owner (passo 1).

## Próximo passo
1. ✅ **Owner: merge da `feature/upgrade-em-uma-rodada` na `main` (0.54.0) e `git push origin main`** — feito em 2026-11-09 (`6fd4e63`), levou junto a captura da sessão anterior (F-052, memórias, diário).
2. ⬜ **Owner: apagar a tarefa agendada, se chegou a ser criada** — Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir (sem comando).
3. ⬜ **Conversa nova — trocar a junção pelo marketplace local (escolha A, decisão 2026-11-03)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md); só a partir daí o `marketplace update` passa a ser o passo pós-publicação.
4. ⬜ **`/mss-spec:upgrade` no Whats e no Energy, quando abrir cada um** — com a 0.54.0 é uma rodada só. **Transportes V2: ✅ feito em 2026-11-09** (`0190dfc` na `master` de lá, sem push; 1ª rodada real da 0.54.0). Detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)
5. ⬜ **No Whats: `/mss-spec:memory capturar` na conversa "Validar mensagens WhatsApp em produção"** e testar o `/mss-spec:bug` numa conversa nova (prova do `kit_primeiro.py`).
6. ⬜ **Dogfood no kit: as 40 citações mortas** (`python templates/memoria_indice.py citacoes`) — corrigir o caminho ou marcar a memória `obsoleta:`; e a autoria do MSIG_Agentes (`<a confirmar>` no dossiê).
7. ⬜ **Conversa nova por item — memória em tabela (passo 1) e conferência antes de entregar (passo 2)** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)

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
