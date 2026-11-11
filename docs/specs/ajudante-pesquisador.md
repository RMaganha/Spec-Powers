# Ajudante pesquisador — lê muito na janela dele e devolve só o resumo

## Estado atual
**Em construção na branch `feature/ajudante-pesquisador` (0.58.0).** O desenho aprovado pelo owner em 2026-11-11:

- **O ajudante** é o arquivo `agents/pesquisador.md` do kit (aparece como `mss-spec:pesquisador`). Só tem as
  ferramentas de leitura (ler arquivo, procurar texto, listar arquivos): não grava, não roda comando e não chama
  outro ajudante. Usa o mesmo modelo da conversa.
- **Quando é chamado** — só nestes três casos, nunca em toda tarefa: ler **outra conversa**, ler **muitos
  arquivos** (mais de 10 para abrir sem saber quais importam, ou documento grande que não vai ser editado nesta
  conversa) ou entender **outro assunto** que não é o desta conversa.
- **O que devolve:** resultado na primeira linha; cada fato com `arquivo:linha`; o que não achou e o que não leu;
  até 3.000 letras; nunca o arquivo colado.
- **Outra conversa:** a conversa gravada é um `.jsonl` que não dá para ler direto. O script
  `templates/conversa_texto.py` lista as conversas do projeto e grava uma delas em texto (só as falas do owner e
  do assistente) em `~/mss-spec/conversas/`; o ajudante lê esse texto.
- **Onde a regra aparece:** na linha "Bola de neve" das regras do kit, nas portas `tarefa`, `bug` e `duvida`
  (passo 1b, com o comando do script), no `to-dolist`, no `nova-feature` e no aviso de janela cheia.

Fora de escopo: ajudante revisor (`docs/specs/conferencia-antes-de-entregar.md`), ler conversa de outro projeto,
escolher modelo mais barato para o ajudante (não medido).

## O que o owner decidiu
1. Decisão 25 de `docs/specs/memoria-em-tabela.md`: um ajudante do kit que lê muito e devolve só o resumo, usado
   **só nesse papel** (outra conversa, muitos arquivos ou outro assunto), nunca em toda tarefa — o ritual completo
   com ajudantes é lento (`memory/feedback_nivel_cerimonia_velocidade.md`). Escrito do zero no kit.
2. **Nada do MSIG_Agentes é usado ou copiado.**
3. 2026-11-11: o owner aprovou o desenho e as escolhas abaixo ("Aprovo, siga"). As três perguntas feitas a ele
   (branch a partir da `main` local 3 commits à frente do GitHub; texto da conversa em `~/mss-spec/conversas/`;
   spec própria em vez de parte 4 da memória em tabela) ficaram sem resposta explícita — vale a recomendação.

## O que foi medido antes (2026-11-11, só neste projeto, uma medição)
62 conversas. Em 18 houve algum ajudante (95 chamadas: 55 genérico, 16 guia do Claude Code, 12 revisor, 9 de
busca). O que o ajudante devolve já é curto: mediana 1.060 letras, 6 de 95 acima de 6.000. O que enche a
conversa é a leitura direta: mediana 62.831 letras por conversa, 20 conversas acima de 100.000, a maior com
472.068. Por isso o desenho cuida de **quando chamar** e do **formato da resposta**, não só do tamanho.

## Critérios de aceite
1. DADO o kit carregado, QUANDO uma conversa nova abre, ENTÃO `mss-spec:pesquisador` aparece na lista de ajudantes
   (só se prova no real).
2. DADO o arquivo do ajudante, ENTÃO as ferramentas dele são só as três de leitura e ele não traz campo que o
   Claude Code ignora em ajudante de plugin.
3. DADO o arquivo do ajudante, ENTÃO o texto traz o formato da resposta (primeira linha, `arquivo:linha`, o que
   não leu, 3.000 letras, sem colar arquivo) e a descrição diz os três casos e que não é para toda tarefa.
4. DADA uma conversa gravada, QUANDO o script roda, ENTÃO sai um texto só com as falas do owner e do assistente —
   sem resultado de ferramenta, sem fala de ajudante e sem trecho `<private>`.
5. DADAS as regras do kit, as portas e os comandos que falavam em subagente, ENTÃO eles nomeiam o ajudante e os
   três casos.
6. No real: uma pesquisa por caso, com as letras lidas pelo ajudante e as devolvidas.

## Escolhas do assistente (o owner pode trocar)
- Arquivo de ajudante no plugin, em vez de texto pronto nos comandos ou de comando para o owner chamar.
- Só leitura; mesmo modelo da conversa; resposta de até 3.000 letras; "muitos arquivos" = mais de 10.
- Só conversas deste projeto; o script também lista as conversas (data, tamanho, primeiro pedido).
- Reaproveita a leitura de conversa de `templates/memoria_tabela.py` (`_pedido_do_owner`, `arquivo_da_conversa`).
- **Trocada durante o plano:** a lista mostrada ao owner dizia "não ligo o ajudante dentro de `tarefa`, `bug` e
  `duvida`". Entrou um passo 1b nas três, porque é só no texto de um comando que o caminho do script
  (`${CLAUDE_PLUGIN_ROOT}`) chega resolvido ao assistente.

## Histórico
- 2026-11-11 — criado: desenho aprovado pelo owner (motivo: decisão 25 da memória em tabela; a medição do dia
  mostrou que o que enche a conversa é a leitura direta, não o retorno dos ajudantes).
