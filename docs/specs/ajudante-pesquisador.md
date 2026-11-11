# Ajudante pesquisador — lê muito na janela dele e devolve só o resumo

## Estado atual
**Entregue na 0.58.0 (2026-11-11).** Falta uma prova que só o owner vê: o ajudante aparecer na lista de uma
conversa nova (critério 1).

- **O ajudante** é o arquivo `agents/pesquisador.md` do kit (aparece como `mss-spec:pesquisador`). Só tem as
  ferramentas de leitura (ler arquivo, procurar texto, listar arquivos): não grava, não roda comando e não chama
  outro ajudante. Usa o mesmo modelo da conversa. Se ele não aparecer na lista, as portas mandam fazer a mesma
  leitura com o ajudante genérico.
- **Quando é chamado** — só nestes três casos, nunca em toda tarefa: ler **outra conversa**, ler **muitos
  arquivos** (mais de 10 para abrir sem saber quais importam, ou documento grande que não vai ser editado nesta
  conversa) ou entender **outro assunto** que não é o desta conversa.
- **O que devolve:** resultado na primeira linha; cada fato com `arquivo:linha`; o que não achou e o que não leu;
  até 3.000 letras; nunca o arquivo colado.
- **Outra conversa:** a conversa gravada é um `.jsonl` que não dá para ler direto. O script
  `templates/conversa_texto.py` lista as conversas do projeto (`listar`) e grava uma delas em texto (`texto <começo
  do id | caminho | palavras do primeiro pedido>`): só as falas do owner e do assistente, numeradas, em linhas de
  até 160 letras, em `~/mss-spec/conversas/` (`MSS_CONVERSAS_DIR` troca). O ajudante lê esse texto. Quem roda o
  script é a conversa principal, antes de chamar o ajudante.
- **O que entra no texto da conversa:** as falas do owner — inclusive a que ele digitou enquanto o assistente
  trabalhava, que o app grava à parte — e o turno do assistente, com os arquivos que ele gravou. Ficam de fora:
  resultado de ferramenta, raciocínio, fala de ajudante, aviso do app (notificação de tarefa, resumo de
  compactação, "interrompido", erro de API), retorno de hook e trecho `<private>` (fechado ou não).
- **Onde a regra aparece:** na linha "Bola de neve" das regras do kit, nas portas `tarefa` e `duvida` (passo 1b)
  e `bug` (passo 1c), com o comando do script; no `to-dolist`, no `nova-feature` e no aviso de janela cheia.

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

## Conferido no real (2026-11-11)
- **Script:** `listar` mostrou as conversas deste projeto; `texto be490360` transformou uma conversa de 3,8 MB em
  22.273 letras (8 falas) em `~/mss-spec/conversas/`.
- **Três pesquisas, uma por caso — aproximação:** nesta conversa o `mss-spec:pesquisador` ainda não estava
  carregado, então o texto de `agents/pesquisador.md` foi entregue a um ajudante genérico (que tem mais
  ferramentas do que o pesquisador terá). As três respostas vieram certas no que dava para conferir e no formato
  pedido (resultado na primeira linha, fatos com `arquivo:linha`, "Não achei", "Não li").

  | Caso | Leu | Devolveu |
  |---|---|---|
  | Outra conversa (o texto da `be490360`) | 28.561 letras, 6 leituras | 3.391 letras |
  | Muitos arquivos (hooks que tratam evento de subagente) | 60.447 letras, 20 leituras | 3.385 letras |
  | Outro assunto (conferência antes de entregar) | 54.913 letras, 42 leituras | 3.999 letras |

- **O teto de 3.000 letras não foi cumprido em nenhuma das três** (13% a 33% acima). Depois disso o texto do
  ajudante ganhou a medida em linhas ("umas 35 linhas"); não foi medido de novo.
- **Revisão independente do código** (um ajudante, só leitura, rodou o script sobre as 62 conversas reais):
  9 achados, todos corrigidos com teste — fala do owner digitada no meio do trabalho era perdida (4 de 6 casos
  reais); `<private>` escapava com tag dentro ou sem fechar; o filtro da busca cortava fala legítima; 41
  registros que não são fala entravam ("interrompido", erro de API, "No response requested."); dois passos "1b"
  no `bug.md`; o caminho do arquivo não bastava sem a pasta; testes frouxos. Depois da correção, a conversa
  `5f0cefc5` traz a fala "Eu quero uma análise não é para sair desenvolvendo…" (fala 028).
- **Visto na revisão, fora desta entrega:** o filtro da busca na memória (`templates/memoria_tabela.py`,
  `_pedido_do_owner`) tem o mesmo corte por `<tag>…</tag>`; lá o texto só vira palavra de busca, não é gravado.
- **Não conferido:** o ajudante aparecer na lista de uma conversa nova com o kit carregado pela junção
  (critério 1). A documentação do Claude Code diz que plugin carrega `agents/` sozinho, mas não fala desse tipo
  de instalação; o comando `claude` não está no caminho desta máquina para conferir por fora.
- **Visto na lista de conversas:** existe uma conversa deste projeto que começa com "olhe a conversa do chat …
  da pasta" de outro projeto. O script só procura sozinho nas conversas deste projeto; a de outro projeto só com
  `--pasta`.

## Escolhas do assistente (o owner pode trocar)
- Arquivo de ajudante no plugin, em vez de texto pronto nos comandos ou de comando para o owner chamar.
- Só leitura; mesmo modelo da conversa; resposta de até 3.000 letras; "muitos arquivos" = mais de 10.
- Só conversas deste projeto; o script também lista as conversas (data, tamanho, primeiro pedido).
- **Trocada durante o plano:** a lista mostrada ao owner dizia "não ligo o ajudante dentro de `tarefa`, `bug` e
  `duvida`". Entrou um passo nas três, porque é só no texto de um comando que o caminho do script
  (`${CLAUDE_PLUGIN_ROOT}`) chega resolvido ao assistente.
- **Trocada depois da revisão:** a lista dizia "reaproveito a leitura de conversa de `templates/memoria_tabela.py`".
  Ficou só o caminho da conversa em curso (`arquivo_da_conversa`), o padrão do `<private>` e a lista de começos
  que não são pedido. O filtro da fala é próprio: o da busca corta qualquer `<tag>…</tag>`, o que serve pra
  buscar mas apagava o que o owner escreveu e deixava escapar `<private>` com tag dentro.
- Palavra que também é começo de id (`cafe`) traz as conversas dos dois jeitos; mais de uma → o script lista e
  pede o começo do id.

## Histórico
- 2026-11-11 — criado: desenho aprovado pelo owner (motivo: decisão 25 da memória em tabela; a medição do dia
  mostrou que o que enche a conversa é a leitura direta, não o retorno dos ajudantes).
