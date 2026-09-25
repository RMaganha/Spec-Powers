# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.34.1 publicada** (`215f75c`, em dia com o `origin/main`). Nesta leva (caso F-030 a F-034): a partida **não volta a crescer** — o `teto_ao_gravar.py` roda o `rodizio_partida.py enxugar` a cada gravação de MAPA/INDEX acima do teto, movendo e nunca apagando, e o `orcamento_partida.py` avisa na abertura; a trava do `nova-feature` ignora `## Backlog`; **um projeto não grava em outro** pelo shell (3ª cerca do `git_publicacao.py`, por identidade de repositório, com o comando pronto pra colar na janela de lá); o recall não injeta diário nem linha `pausada:`/`obsoleta:` e lê o `FORA-DE-ESCOPO.md`; no molde, "Comando pra eu rodar = passo a passo" e "Responda só o que eu pedi". Suíte 676.

<!-- histórico do estado anterior -->
`main` — **v0.34.0 integrada localmente** (merge `76943b1` de `feature/um-item-por-chat`; **7 commits à frente do `origin/main` — `git push` pendente, ato do owner**). O `um_item_por_janela.py` conta **por chat**: chat novo sempre abre (outras abertas só geram aviso + worktree); o mesmo chat não abre 2ª feature enquanto a dele, achada só pelo nome, não está `fechada`/`pausada`. Três rodadas de revisão de código; suíte **676 verde** na `main`. Caso F-032 fechado; memória `feedback_nao_adivinhar_dono_do_dado`. Nenhuma feature aberta no INDEX.

## Próximo passo
**Canário da 0.34.0** (pendência da outra sessão): no mesmo chat `/mss-spec:nova-feature canario-a` e depois `canario-b` — o 2º bloqueia; num chat novo passa. **Observar** o F-033 (resposta do tamanho do pedido) e o F-034 (memória que não chega na hora da ação) — reincidiu, vira mecanismo. **Regra "não alucinar"**: o owner vai trazer. **No Whats (janela de lá, não aqui):** as regras "Comando pra eu rodar = passo a passo" e "Responda só o que eu pedi" no `CLAUDE.md` de lá (está em 9.899 bytes — mover um bloco se passar de 10 KB).

<!-- histórico do próximo passo anterior -->
**Publicar a 0.34.0:** release verde, captura gravada e merge local feitos → falta o **push da `main` pelo owner**. **Canário ao vivo** (depois de o kit novo carregar): no mesmo chat `/mss-spec:nova-feature canario-a` e depois `canario-b` — o 2º bloqueia dizendo que o chat já é da `canario-a`; num chat novo o `canario-b` passa. **No Whats (janela de lá):** das 6 abertas do INDEX, as paradas viram `pausada: <motivo>` à mão (não bloqueiam mais, só poluem o aviso). Custos aceitos pra observar no `python hooks/_registro.py resumo`: bloqueio "não achei a linha dela pelo nome" quando o passo 3 grava título sem que um nome contenha o outro.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-25 (captura da janela afogada) · regenerável com /mss-spec:mapa -->
