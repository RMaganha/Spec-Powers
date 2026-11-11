# 2026-11-11 — consultar a memória pela ação: gatilho de ação em toda anotação de regra (0.57.0)

Branch `feature/consultar-pela-acao` (da `main` em `52b347e`). Spec: `docs/specs/memoria-em-tabela.md` (decisão
24, parte 3). Conversa nova, aberta pelo owner com `/mss-spec:nova-feature` e as regras da conversa (lista única
das escolhas, pergunta de uma vez no fim, regra que parecer proibir se mostra com arquivo e linha).

## Conversamos
- O owner abriu o item 2 da fila de memória: antes de agir, o assistente busca na tabela pelo que VAI FAZER.
- Medi, só em leitura, buscar pelo texto do comando: regra certa entre as 3 em 46% a 51% de 713 casos, e 30 das
  75 anotações apareceriam por conversa. Pela frase da situação, 100% (otimista: eu escrevi as frases).
- Entreguei um desenho inteiro de hook novo (4 momentos, 10 escolhas, 6 critérios) com a decisão antiga que
  parecia proibir como pergunta 1, no fim.
- O owner: *"Antes de qualquer desenho: mostre em 3 linhas a decisão de docs/decisoes.md:43 (o que foi recusado e
  por quê), diga em 1 linha o que a sua medição mostrou, e me pergunte se eu mantenho ou revejo aquela decisão.
  Só depois siga."*
- Resposta dele: mantém a decisão de 25/09; o item passa a ser ampliar o que já existe — toda anotação que é
  regra sobre o que o assistente FAZ ganha o gatilho de ação, cobrado na captura; pras antigas, a lista pra ele
  aprovar de uma vez.
- Levei a lista: 21 deveriam ter (9 por comando, 12 pela resposta); 49 ficam fora, em 4 grupos. Ele: *"Aprovado,
  os 21. Siga até o fim sem me perguntar mais nada"*.

## Pivôs
- **Hook novo que busca por momento → ampliar o gatilho de ação.** O desenho do hook caiu inteiro: a decisão de
  2026-09-25 já tinha recusado "recall no `PreToolUse` por palavras em comum", e o owner a manteve. Eu só abri
  essa decisão quando o aviso automático a apontou, e mesmo assim a deixei pro fim da proposta (caso F-060).
- **Regex estreito → regex medido.** Na 1ª medição dos 21, seis gatilhos disparariam 0 ou 1 vez em 1.057
  respostas (eram a frase que eu imaginei, não a real). Refeitos e medidos em 270 conversas de todos os projetos.
- **Limite por resposta → por conversa.** Dois gatilhos passam de 3,3% das respostas contando toda ocorrência
  ("N verdes" 6,3%, "quer que eu…?" 5,1%); como cada um age uma vez por sessão, devolvem em 2,1% e 1,9%.
- **Teste antigo vermelho → evento sem sessão não age.** Com 26 gatilhos no kit, 3 casos do teste da cerca de
  publicação (`git checkout -b`, `git stash`, `docker build`) passaram a ser negados — e só na 1ª rodada, porque
  o estado "já mostrei" de evento sem número de sessão caía num arquivo único. Conserto no
  `hooks/_memoria_de_acao.py`, com teste antes.

## Rejeitado
- Buscar por palavras a cada comando (decisão de 2026-09-25, mantida pelo owner).
- Hook novo que reconhece o momento e busca pela situação (não chegou a ser implementado).
- Gatilho por arquivo gravado, pras 13 anotações em que a ação é gravar arquivo (o owner não respondeu a
  pergunta e mandou seguir: valeu a recomendação de deixar como estão).
- Corrigir sozinho as anotações antigas dos outros projetos: a lista sai na conversa de cada um.

## Fizemos
- `templates/memoria_indice.py`: `verificar` cobra o gatilho de ação da anotação `type: feedback` nova (sem
  commit) e acusa regex quebrado; as antigas viram aviso e saem no `fila`.
- `hooks/_memoria_de_acao.py`: evento sem número de sessão não dispara gatilho.
- `commands/memory.md` (captura) e `templates/MEMORY.md`: o gatilho de ação deixou de ser opcional.
- Memória do kit: 21 anotações com `gatilho_comando:`/`gatilho_resposta:` e 28 com `sem_gatilho_de_acao:`.
- Testes: `tests/test_memoria_gatilho_de_acao.py` (40) e um caso novo em `tests/test_hook_memoria_de_acao.py`.
- 0.57.0 nos dois manifestos, CHANGELOG, `docs/LEIA-ME.md`, spec (decisão 24, parte 3, critérios 20 a 24,
  medição), F-059 fechado, F-060 aberto.

## Próximo
- Do owner: aprovar o merge na `main` e fazer o `git push origin main`.
- Leituras da medição em 2026-11-25 e 2026-12-11: quantas vezes cada gatilho disparou (registro dos hooks) e,
  a cada falha nova do tipo "a regra existia e não foi usada", se a anotação tinha gatilho e se ele disparou.
- Nos outros projetos, na conversa de cada um: `memoria_indice.py fila` e a lista pro owner aprovar.
- Avisos dados a ele: nenhum dos 21 gatilhos foi visto disparar em uso real ainda; os do kit valem em todo
  projeto; revisão só do próprio assistente.
