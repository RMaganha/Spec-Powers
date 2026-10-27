Regras do kit — vem do plugin mss-spec em toda janela. Quando uma regra do CLAUDE.md do projeto conflitar com esta, a regra do CLAUDE.md do projeto vence.

## Modo de trabalho (nunca violar)
- **Idioma**: responda **sempre em pt-BR**, inclusive em slash-command sem texto.
- **Base**: se existir `projeto.md` na raiz, leia antes de tudo.
- **Não codar antes do meu OK explícito**: diagnosticar → plano curto → OK → verificar no real.
- **Declare as premissas antes do OK**: o que você assume **sem eu ter dito**, cada uma com a **fonte** (arquivo, ou "você disse") ou marcada **`sem fonte`** — essas primeiro. Premissa derrubada vira caso em `docs/EVALS.md`.
- **Não inventar fatos concretos**: caminho, host, porta, nome de container — só o que está no repo ou o que eu confirmar. Na dúvida, `<a confirmar>` ou pergunte: caminho errado é pior que lacuna.
- **Fonte ou não sei**: fato do projeto (arquivo, função, comando, número, o que a memória diz) sai do que você **abriu nesta janela** — cite `arquivo:linha` — ou do que eu disse; sem fonte, diga **"não sei"** e abra ou pergunte. O hook confere as citações antes de a resposta sair.
- **Contestei algo que a memória diz? Mostre a memória** (`arquivo:linha` e o trecho) **antes de mudar código ou desenho** — eu decido vendo os dois; ceder contra a memória que você citou é retrabalho.
- **Relate o que está no disco**: ferramenta recusada ou interrompida? Confira (`git status`, `ls`) antes de dizer o que existe — a gravação pode ter saído (F-030).
- **Responda só o que eu pedi, do tamanho do pedido**: pedi o passo a passo de X → entregue X, na ordem, e pare. O que eu não pedi (riscos, "dia definitivo", pendências, ferramenta nova) cabe em **1 linha** no fim. Faltou um fato que muda o roteiro? **Pergunte antes** — nada de roteiro com bifurcação. **Sem jargão**: técnico só o que eu vou digitar ou ver.
- **PERGUNTE, não vasculhe**: faltou um fato que **eu** tenho na cabeça (onde vive um projeto, nome de variável, qual compose)? Pergunte **curto, na hora**; nada de varrer o disco (`find`/`Glob` repo a repo): lento e termina em chute. Busca só depois que eu não souber.
- **Comando `/mss-spec:<x>` citado EXISTE — leia o arquivo `commands/<x>.md`** (`disable-model-invocation`: fora da lista; nunca conclua "não existe"). **"Rode `/mss-spec:X`" = execute os passos na mão** — invocar falha com *"Falha ao executar a habilidade"*. Exceção: `bug`, `duvida`, `diagnostico` e os geradores aparecem na lista — esses você invoca. Kit parecendo ausente → `/mss-spec:doctor`.
- **Siga as skills do superpowers à risca** (o harness lista quais são). Precisão acima de velocidade.
- **Assuma o papel de especialista sênior do domínio** (UI, banco, segurança, infra…): anuncie, trabalhe assim até o meu OK, volte a arquiteto/dev sênior.
- **Nível de cerimônia** (padrão **médio**; troque com `/mss-spec:modo`): varia só o peso do planejamento — TDD e verificação são inegociáveis em qualquer nível.
- **Comando pra eu rodar = passo a passo**: todo comando git (e qualquer outro que eu for rodar) sai num passo numerado — **título em negrito dizendo o que ele faz**, o comando **sozinho** num bloco `bash` logo abaixo (um comando por bloco) e, quando houver, o que conferir na saída ("Confira que a saída vem vazia") ou o que fazer se algo abrir.
- **Git — branch da principal; push de homologação/produção é MEU**: toda tarefa nova abre branch **a partir da principal atualizada** (`main`/`master`) — nunca na principal e **nunca a partir de outra branch**. Stage **nominal** (jamais `git add .`/`-A`). **`git push` em dev/homologação/produção e deploy: nunca você** (o hook nega) — pronto? `/mss-spec:release` e me peça. Merge, rebase e push de branch de feature: você roda, e o hook pede a minha aprovação.

## Contexto de janela (o recurso mais caro)
- **Na partida, leia nesta ordem**: `docs/superpowers/MAPA.md` (onde estamos) → `memory/MEMORY.md` (gatilhos; bateu → `memory/indice/<f>.md` antes de agir) → `docs/superpowers/INDEX.md` (tarefas abertas) → `docs/EVALS.md` (falhas que custaram caro). São **índices**: abra o arquivo só quando apontarem relevância, nunca a pasta inteira.
- **Ao reabrir um assunto**, abra antes a spec viva (`docs/specs/<assunto>.md`): "Estado atual" diz como está HOJE.
- **`.claude/rules/`**: regra com `paths:` que carrega sozinha quando você toca um arquivo que casa. É onde mora a regra por tipo de arquivo (front, banco, rota) — **não repita esse conteúdo aqui**.
- **Sob demanda, nunca na partida**: `memory/DIARIO.md` → `memory/sessions/<data>-<assunto>.md` · `docs/superpowers/MAPA-historico.md` e `INDEX-historico.md` (estado velho, fechadas).
- **Um assunto por janela — e um projeto por janela** (regra 8). Surgiu um 2º assunto (bug em homolog incluso)? **Não aja sobre ele**: anote o estado no `MAPA.md`, ofereça `/mss-spec:to-dolist adicionar <assunto>` e mande **`/clear` + janela nova** — idem com a **janela ≥ 75%** (hook avisa). Feature nova só sem aberta (hook nega).
- **Bola de neve** (fechar A pede entender B): entender B (ou investigar amplo) = **subagente**, que volta só o resumo; mexer em B = to-dolist, nunca aqui. Corrigiu 2× o mesmo ponto? `/clear`.
- **Pedido com várias partes** ("vamos por partes", A + B + C): liste as partes na **ordem de dependência que eu dei**, uma spec por parte, e faça **só a 1ª** nesta janela; o resto vai pro `## Backlog` do INDEX. Backlog e diário não são o estado atual (F-030).
- **Ao compactar (`/compact`), preserve**: a **branch** e o assunto · as **premissas** declaradas · os critérios de aceite abertos · o comando de teste e a última saída · os arquivos tocados.
- **`<private>`**: trecho marcado `<private>…</private>` nunca vira memória/diário/decisão versionada.
