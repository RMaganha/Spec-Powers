---
name: project_data_do_explorer_nao_e_data_de_gravacao
description: a "Data de modificação" do Explorer é reescrita por git checkout/merge e não diz quando o conteúdo foi gravado — a prova de gravação é o git log e a transcrição (Write/Edit no .jsonl); nunca afirmar nem negar "foi gravado" pela data do arquivo
gatilho: quando o owner disser que um arquivo não foi gravado ou não tem a data em que mexeu, ou ao conferir quando algo foi escrito no projeto
metadata:
  type: project
---

Em 2026-10-30 o owner disse: *"tenho quase certeza de que memória e muitas outras coisas ele não gravou na
pasta do projeto, pois vi algumas e não tem arquivos com as datas que mexi"*. Medido: desde 15/10, as conversas
do Whats fizeram **649 gravações, todas na pasta do projeto** (zero na pasta nativa do Claude, zero em outro
projeto), e 10 das 11 conversas com trabalho tinham diário em `memory/sessions/` e commit no mesmo dia. O que
enganava era a **data do Explorer**: um `git checkout dev` + `git merge main` do owner às 17:18 carimbou 31
arquivos de `memory/` e `docs/` com aquela hora, e **91 das 190 memórias** mostravam no Explorer uma data diferente
da do commit. Exemplo: `memory/sessions/2026-10-29-codigo-fonte-v2.md`, commit de 29/10, "modificado em" 30/10.

**Why:** afirmar ou negar "foi gravado" pela data do arquivo erra nos dois sentidos — e aqui quase levou o
owner a apagar tudo.

**How to apply:** a prova de gravação é dupla e barata: `git log --since=<data> --date=short --format="%ad %h %s"
-- memory docs` (o commit diz o dia de verdade) e, para o que ainda não foi commitado, os `Write`/`Edit` na
transcrição (`~/.claude/projects/<proj>/*.jsonl`, [[reference-historico-mostra-o-que-carregou]]). Mostre as duas
ao owner e diga por que a data do Explorer mudou. O que **faltou** se acha pela diferença: conversa com trabalho e
sem `memory/sessions/` do dia (foi assim que apareceu a conversa da tarde de 30/10 sem diário, que virou o hook
`diario_junto.py`). Relacionado: [[feedback_sintoma_do_owner_e_fato]] (o relato é o sintoma; a leitura explica, não
contesta).
