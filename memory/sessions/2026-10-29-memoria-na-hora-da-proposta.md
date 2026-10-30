# 2026-10-29 — memória na hora da proposta · sintoma do owner é fato (0.49.0, F-047)

## Conversamos
1. "Como pedir uma melhoria ao plugin, se não é feature nem bug?" → `/mss-spec:nova-feature` no modo médio (o
   mínimo pula a spec).
2. O owner: o `nova-feature` "se perdeu todo" no Whats (conversa "V2 código fonte e histórico") — "toda vez os
   mesmos problemas se repetem".
3. Eu li a conversa até a 1ª resposta e escrevi "o assistente não se perdeu". O owner mandou reler a partir de
   "Você tem razão: propus o desenho sem abrir os subíndices…" e pediu para abrir a correção junto com esse erro.
4. Diagnóstico: 114 de 150 memórias do Whats sem `gatilho:`; o recall casa o pedido ("código fonte"), e a memória
   que vetava casa a proposta ("build", "arquivos novos"). Desenho aprovado ("Aprovo").
5. "Não entendi as opções deixar como está ou apertar" → expliquei o que a conferência faz, o custo de cada lado
   e recomendei; o owner: "pode deixar como está".

## Pivôs
- "O assistente não se perdeu" → o sintoma do owner é fato; virou o item 6 (memória com `gatilho_resposta` +
  passo 2 do `/mss-spec:bug`).
- Busca com o texto inteiro da proposta (não achava nenhuma das 3) → termo curto do tema (achou as duas).
- 1ª medição: 314 de 2.285 respostas voltariam (marca solta "plano"/"desenho", tema solto "arquivo") → marca forte
  de proposta + frase de mudança + todas as palavras do termo: 75 de 2.287.
- "Não se perdeu" sem sujeito pegava frase sem relação (3 de 6) → exige assistente/plugin/kit/ele…
- Texto real da proposta do Whats como fixture foi negado → amostra sintética.

## Rejeitado
- Contar só a resposta que pede o OK do owner (o owner escolheu deixar como está).
- Escrever o `gatilho:` nas 114 memórias do Whats agora (fica no to-dolist, `#fora-de-escopo`).
- Corrigir o `CLAUDE.md` do Whats ("não existe Python no host") daqui — é da conversa de lá.

## Fizemos
- 0.49.0, commit `fae5d91` na `feature/memoria-na-hora-da-proposta`: `confere_citacoes.py` (Stop) com a
  conferência da proposta; memória `feedback_sintoma_do_owner_e_fato`; passo 2 do `bug.md`;
  `tests/test_hook_memoria_da_proposta.py` (11); F-047 fechado. Suíte 1.031 verde.

## Próximo
- Owner: merge e push da 0.49.0 na `main`.
