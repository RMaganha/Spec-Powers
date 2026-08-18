---
name: feedback_consultar_destilado_antes_da_fonte
description: consultar mapa/índice/memória (o destilado) ANTES de reabrir arquivos-fonte; RE-ler tudo a cada pergunta é a amnésia que o mapa de contexto existe pra matar
gatilho: quando precisar de contexto do projeto — na partida ou ao reabrir um assunto
metadata:
  type: feedback
---

Antes de abrir um arquivo-fonte pra responder uma pergunta, **consulte primeiro o destilado**:
`docs/superpowers/MAPA.md`, o `mapa-neural.md` (índice do mapa mental, quando existir), `memory/MEMORY.md`,
`docs/superpowers/INDEX.md`, a tabela de comandos do `LEIA-ME.md`. Só abra a fonte quando o destilado
não cobrir — e, ao abrir, **destile o que aprendeu de volta** pro índice/memória, pra não reler na
próxima. O objetivo do mapa de contexto é reduzir a **RE-leitura**, não a 1ª leitura.

**Why:** o owner apontou (com um print) que, mesmo depois de eu construir o mapa mental, respondi uma
pergunta sobre o `upgrade` **relendo o `upgrade.md` inteiro** — exatamente o anti-padrão que o mapa
existe pra evitar ("faço uma pergunta e você lê o arquivo tudo de novo"). Reler a fonte a cada pergunta
é a amnésia de partida em ação, e mina a razão de ser do próprio kit.

**How to apply:** ordem de consulta = **destilado → fonte (só se faltar) → destilar de volta**. Detalhe
fino que não cabe num resumo ainda pode exigir a fonte (isso é honesto), mas RE-ler um arquivo já lido/
destilado é o erro. **O destilado é o TEXTO** — `docs/mapa-neural.md` (~15 KB), `memory/MEMORY.md` (índice por gatilho) e `docs/EVALS.md` (as falhas que já aconteceram) — que se
lê/`grep`a ao vivo; **NÃO** é a imagem/HTML do mapa (o `.html` de ~700 KB é **visual, pro humano**) **nem
o contexto inchado da conversa**. Erro real cometido: o owner colou o print do mapa e eu "consultei" a
IMAGEM — visual, pro humano — em vez de ler o `.md`. **Correção de 2026-08-18:** *numa sessão nova o `MEMORY.md` do repo NÃO vem carregado* — o que
auto-carrega é o índice da pasta **nativa**, que tinha 6 das 33 entradas. Por isso a nativa virou
**ponteiro** pro índice do repo e o índice passou a ser **agrupado por gatilho** (cada linha diz
*quando* abrir, não *o que é*). O `mapa-neural.md` está a um `grep` de distância; nenhum depende do
histórico gigante da janela. Sinal de alerta: pensar "deixa eu conferir o arquivo X" sem antes checar se o índice/
mapa já responde. Corolário de produto: o `mapa-neural.md` deve trazer **resumo de 1 linha por peça**
(da `description`/docstring), não só os nomes — senão ele não substitui a fonte. Relacionado:
[[feedback_visual_pro_humano_dados_pro_assistente]] (o índice de texto é o que me serve, não o desenho),
[[project_memoria_local_ao_repo]].
