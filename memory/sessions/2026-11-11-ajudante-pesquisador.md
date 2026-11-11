# 2026-11-11 — ajudante pesquisador: lê muito na janela dele e devolve só o resumo (0.58.0)

Branch `feature/ajudante-pesquisador` (da `main` em `43b2eae`, 3 commits à frente do GitHub). Spec:
`docs/specs/ajudante-pesquisador.md` (decisão 25 de `docs/specs/memoria-em-tabela.md`). Conversa nova, aberta
pelo owner com `/mss-spec:nova-feature` e as regras da conversa (lista única das escolhas, pergunta de uma vez no
fim, regra que parecer proibir se mostra com arquivo e linha, `git status -sb` sozinho antes da branch).

## Conversamos
- O owner abriu o item 3 da fila de memória: um ajudante do kit usado só pra ler outra conversa, muitos arquivos
  ou outro assunto — nunca em toda tarefa. Escrito do zero; nada do MSIG_Agentes.
- Medi antes, só em leitura, nas 62 conversas deste projeto: o que os ajudantes devolvem já é curto (mediana
  1.060 letras); o que enche a conversa é a leitura direta (mediana 62.831 letras; 20 conversas acima de
  100.000), e em 44 das 62 nenhum ajudante foi chamado.
- Conferi na documentação do Claude Code (por um ajudante) como um plugin entrega ajudante: pasta `agents/`, nome
  `mss-spec:pesquisador`, lista de ferramentas no cabeçalho, sem chave pra impedir o assistente de chamá-lo sozinho.
- Levei o desenho, as minhas escolhas numa lista só e três perguntas (branch com a `main` local 3 commits à
  frente; texto da conversa em `~/mss-spec/conversas/`; spec própria ou parte 4). O owner: *"Aprovo, siga"* — sem
  responder as três; valeu a recomendação em cada uma.
- No fim o owner aprovou a captura: *"Ok, grave"*.

## Pivôs
- **"Resumo curto" → "quando chamar e em que formato".** O item dizia "devolve só o resumo"; a medição mostrou
  que o retorno já é curto e que o problema é a leitura feita direto na conversa.
- **Sem ligar nas portas → passo nas três portas.** Eu tinha dito que não ligaria o ajudante em `tarefa`, `bug` e
  `duvida`. No plano vi que só no texto de um comando o caminho do script chega resolvido ao assistente.
- **Reaproveitar o filtro da busca → filtro próprio.** Eu tinha dito que reaproveitaria `_pedido_do_owner`. A
  revisão independente rodou o script nas conversas reais: a fala do owner digitada no meio do trabalho era
  perdida (4 de 6 casos), `<private>` com tag dentro escapava, fala legítima era cortada e 41 registros do app
  entravam como fala. 15 testes com conversa de exemplo estavam verdes (caso F-061).
- **Dois passos "1b" no `bug.md` → 1c.** O passo novo entrou antes de um 1b que já existia.

## Rejeitado
- Só texto pronto nos comandos, chamando o ajudante genérico (depende de o assistente lembrar; o genérico grava).
- Comando pro owner chamar (ele já recusou comando pra lembrar).
- Dar ao ajudante a ferramenta de rodar comando pra ele mesmo converter a conversa (deixaria de ser só leitura).
- Modelo mais barato pro ajudante (não medido).

## Fizemos
- `agents/pesquisador.md` — o primeiro ajudante do plugin: `Read, Grep, Glob`, modelo da conversa, formato da
  resposta (primeira linha, `arquivo:linha`, não achei, não li, até 3.000 letras).
- `templates/conversa_texto.py` — `listar` e `texto`; falas numeradas, linhas de até 160 letras, em
  `~/mss-spec/conversas/`.
- Regras do kit ("Bola de neve"), `tarefa.md` e `duvida.md` (1b), `bug.md` (1c), `to-dolist.md`,
  `nova-feature.md`, aviso de janela cheia, `docs/LEIA-ME.md`.
- Testes: `tests/test_ajudante_pesquisador.py` (9) e `tests/test_conversa_texto.py` (25); suíte 1416 verdes.
- 0.58.0 nos dois manifestos, CHANGELOG, spec nova, plano curto, plano de teste.
- Prova (aproximação: o texto do ajudante entregue a um ajudante genérico, porque o novo só carrega em conversa
  nova): três pesquisas certas e no formato; leram 28.561, 60.447 e 54.913 letras e devolveram 3.391, 3.385 e
  3.999 — acima do teto de 3.000 nas três.

## Próximo
- Do owner: em conversa nova, ver se `mss-spec:pesquisador` aparece na lista de ajudantes (kit carregado pela
  junção; a documentação não fala desse tipo de instalação). Aprovar o merge na `main` e fazer o push.
- Não agora (no `to-dolist.md`): a busca na memória não vê a fala digitada no meio do trabalho; conversa de outro
  projeto; medir de novo o teto de 3.000 letras; modelo mais barato; limpeza de `~/mss-spec/conversas/`.
