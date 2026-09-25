# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.36.0 publicada** (`6443e45`, em dia com o `origin/main`). Depois da 0.34.1: **0.35.0** — regra "Fonte ou não sei" no molde e `confere_citacoes.py` (Stop, sem LLM): citação de arquivo/`:linha`, `/mss-spec:<x>` ou `F-0NN` que não existe devolve a resposta uma vez (F-035); **0.36.0** — memória com gatilho de ação (`gatilho_comando:` nega o comando uma vez por sessão; `gatilho_resposta:` devolve a resposta uma vez; F-034 fechado) e resposta com rotas alternativas não pedidas volta uma vez (F-033). Tudo medido em sessões reais antes de ligar. Suíte 731.

<!-- histórico do estado anterior -->
`main` — **v0.34.1 publicada** (`215f75c`, em dia com o `origin/main`). Nesta leva (caso F-030 a F-034): a partida **não volta a crescer** — o `teto_ao_gravar.py` roda o `rodizio_partida.py enxugar` a cada gravação de MAPA/INDEX acima do teto, movendo e nunca apagando, e o `orcamento_partida.py` avisa na abertura; a trava do `nova-feature` ignora `## Backlog`; **um projeto não grava em outro** pelo shell (3ª cerca do `git_publicacao.py`, por identidade de repositório, com o comando pronto pra colar na janela de lá); o recall não injeta diário nem linha `pausada:`/`obsoleta:` e lê o `FORA-DE-ESCOPO.md`; no molde, "Comando pra eu rodar = passo a passo" e "Responda só o que eu pedi". Suíte 676.

## Próximo passo
**Observar** o F-033 (tamanho e jargão seguem só na regra) e o F-035 (afirmação sem citação segue só na regra) — reincidiu, vira caso novo ou mecanismo; o `python hooks/_registro.py resumo` mostra quantas vezes o `confere_citacoes` devolveu. **No Whats (janela de lá, não aqui):** as regras "Comando pra eu rodar = passo a passo", "Responda só o que eu pedi" e "Fonte ou não sei" no `CLAUDE.md` de lá (9.899 bytes — mover um bloco se passar de 10 KB).

<!-- histórico do próximo passo anterior -->
**Canário da 0.34.0** (pendência da outra sessão): no mesmo chat `/mss-spec:nova-feature canario-a` e depois `canario-b` — o 2º bloqueia; num chat novo passa. **Observar** o F-033 (resposta do tamanho do pedido) e o F-034 (memória que não chega na hora da ação) — reincidiu, vira mecanismo. **Regra "não alucinar"**: o owner vai trazer. **No Whats (janela de lá, não aqui):** as regras "Comando pra eu rodar = passo a passo" e "Responda só o que eu pedi" no `CLAUDE.md` de lá (está em 9.899 bytes — mover um bloco se passar de 10 KB).

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-25 (captura da janela afogada) · regenerável com /mss-spec:mapa -->
