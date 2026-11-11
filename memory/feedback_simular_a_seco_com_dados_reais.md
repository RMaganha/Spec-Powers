---
name: feedback_simular_a_seco_com_dados_reais
description: mecanismo novo que vai mexer em arquivos de um projeto real se prova primeiro numa simulação a seco sobre os arquivos reais (tabela antes/depois + teste de recall), no scratchpad, sem gravar nada
gatilho: quando propor mecanismo novo que vai mexer em arquivos de um projeto real (índice, MAPA, migração, rodízio)
gatilho_resposta: (?is)\b(?:proponho|minha proposta|o desenho (?:é|fica|proposto)|desenho proposto|sugiro)\b.{0,1500}\b(?:nos projetos|outros projetos|projeto real|projetos reais|no Whats|no Transportes|no Energy)\b
metadata:
  type: feedback
---

Em 2026-09-14 o owner aprovou a ideia do índice em dois níveis mas, antes de qualquer código, pediu:
*"consegue simular aqui com o projeto que passei como ficaria e se realmente funcionaria — algo na tela,
tabela"*. A simulação (script no scratchpad, lendo o índice real do Whats, sem gravar) mostrou a tabela de
bytes e um recall por palavra com sintomas reais — e **achou dois defeitos de estrutura que a spec teria
herdado**: as famílias eram por assunto, não por gatilho (a memória certa morava na família "errada"), e
palavra-chave raspada do texto vira lixo ("Esta", ".md", "GET"). O topo passou a usar frases do `gatilho:`.

**Why:** a sessão anterior tinha custado caro por mecanismo aprovado no papel. Tabela medida convence e
corrige; prosa só convence.

**How to apply:** antes da spec, rode o mecanismo em modo leitura sobre os arquivos reais do projeto-alvo,
com saída no scratchpad; mostre antes/depois em bytes e um teste com casos reais; diga o que a simulação
NÃO prova (casamento por palavra é mais burro que o modelo). Nunca grave no projeto — a âncora é a regra 8.
Relacionado: [[feedback_medir_antes_de_afirmar_ganho]], [[feedback_medir_a_partida_inteira_nao_o_arquivo_acusado]].

- Confirmado de novo em 2026-10-28 (0.48.0): ler o to-dolist real do Whats antes do desenho mostrou que "linha por linha" não servia (926 linhas, só 108 começam com "- "); o desenho virou "um recado por linha", e a prévia nos 3 projetos, sem gravar nada, conferiu a soma antes do código ir para a branch.
- Ampliado em 2026-11-10 (memória em tabela, F-055): a simulação tem de usar **todas as fontes** do que se mede — a 1ª rodada leu só `memory/*.md` e diários e deixou fora subíndices, specs, planos, MAPA, INDEX e documentos (incluí-los levou o acerto de 13% pra 32%) — e **dizer o defeito de cada gabarito** (o dos pedidos reais cobria 8% dos pedidos e quase nenhum questionamento do owner; o arquivo mais "certo" era o `to-dolist.md`, lido por rotina). Liste as fontes e o que ficou fora antes de mostrar número.
