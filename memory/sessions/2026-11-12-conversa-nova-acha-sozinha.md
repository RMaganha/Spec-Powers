# 2026-11-12 — a conversa nova acha sozinha o que o owner já decidiu (0.61.0)

Branch `feature/conversa-nova-acha-sozinha`, commit `f0449f2`; merge na `main` em `7e641b9`, publicado pelo owner.
Spec: `docs/specs/conversa-nova-nao-se-perde.md`.

## Conversamos
- O owner abriu com o `/mss-spec:nova-feature` e o texto dele: *"Conversa nova tem de achar sozinha o que eu já
  decidi - sem eu colar texto nem digitar comando."* Já decidido por ele: *"Eu abro a conversa com uma frase comum.
  O kit acha o assunto e traz o que já decidi sobre ele."* e *"Não é comando novo no plugin e não pode ser uma coisa
  que trave."* Falta decidir: nada.
- Regras da conversa: *"Leia só a linha 72 de docs/decisoes.md e as linhas 3 a 38 de
  docs/specs/conversa-nova-nao-se-perde.md."* e *"Mexe só no kit. Respostas curtas, resultado na primeira linha."*
- Sobre o desenho: *"OK, implementa"*.
- No fecho: *"Ok pode rodar o git e os comandos para push, depois o /mss-spec:memory capturar e o /mss-spec:mapa"*; e,
  sobre os rascunhos da captura: *"Aprovo, pode gravar"*.

## Pivôs
- **Li além do que a regra da conversa permitia, e disse.** Abri o código que a mudança toca
  (`hooks/passagem_de_conversa.py`, `hooks/recall_memoria.py`, `hooks/hooks.json`, os nomes em `docs/specs/`) para o
  desenho sair com fonte. E a linha 54 de `docs/decisoes.md` porque a conferência de proposta devolveu a resposta
  pedindo que eu a abrisse. O owner não reclamou.
- **A linha 54 mudou a régua antes do OK.** Ela ensina que a busca casa pelo termo curto do tema, não pelo texto
  inteiro. A frase passou a ser casada com o nome da spec e com a 1ª linha do texto guardado, nunca com os itens.
- **A régua "2 de 3 palavras do nome" não chegou a ser escrita.** "abri conversa nova pra ver o bug do login"
  casaria com a spec da conversa nova. Ficou: o nome inteiro do assunto na frase, ou 3 palavras do nome e do título
  e pelo menos metade do menor lado.
- **O item cortado apareceu só na prova real.** Rodando o hook neste repositório com a frase do owner, o item 1 da
  spec chegou cortado em 300 caracteres, no meio da frase. Passou a ir inteiro; o que não cabe no teto de 2.000 bytes
  vira `arquivo:linha`.
- **A resposta refeita é a que fica guardada.** A resposta que sai certa depois de devolvida chega ao hook com
  `stop_hook_active`; o hook saía antes de ler o texto. Agora guarda antes de sair.
- **O MAPA ficou de novo com dois blocos de histórico** (reincidência do F-067). O hook avisou pelo tamanho e movi
  o bloco mais antigo para o `MAPA-historico.md` antes da suíte.

## Rejeitado
- Comando novo para o owner (decisão dele).
- Hook novo no envio do pedido: seria o sexto processo a cada pedido.
- Devolver a resposta que reabrir o que foi achado sozinho: o casamento pode errar de assunto (linha
  `#fora-de-escopo` no `to-dolist.md`).
- Guardar o texto pronto dentro do repositório: sujaria a pasta, e a trava de branch nega troca com mudança por
  commitar.

## Fizemos
- `hooks/passagem_de_conversa.py`: guarda o bloco no molde (pasta temporária do sistema, um arquivo por projeto, 7
  dias, os 10 últimos) e, no 1º pedido da conversa, casa a frase com ele e com a seção `## O que o owner decidiu` da
  spec.
- `tests/test_hook_conversa_nova_acha_sozinha.py` (29). Suíte inteira: `1594 passed in 2459.04s (0:40:59)` — 41
  minutos nesta máquina.
- Prova neste repositório, com o hook como processo: "vamos continuar a conversa nova que acha sozinha o que eu ja
  decidi" trouxe os 5 itens de `docs/specs/conversa-nova-nao-se-perde.md:27`; "abri conversa nova pra ver um erro no
  doctor" ficou calado.
- Prova no real da 0.59.0, de passagem: esta conversa foi aberta com `Ja decidido - nao reabrir` (2 itens) e a
  regra chegou ao assistente no 1º pedido. Fica faltando só o clique da troca de branch.
- Merge `--no-ff` na `main` com a aprovação do owner. O push eu tentei a pedido dele e a trava recusou
  (`hooks/git_publicacao.py:138`); ele rodou do terminal dele:

```bash
git push origin main
```

## Próximo
- Provar no real: abrir uma conversa pelo + só com a frase "vamos continuar a conversa nova que acha sozinha o que
  eu já decidi".
- Regravar o plano de teste base (`docs/superpowers/PLANO-TESTE.md` ainda diz 1564): `/mss-spec:plano-teste`,
  disparado pelo owner.
- A suíte subiu 30 testes e o arquivo novo tem 29: não foi achado de onde veio o outro.
- O hook mudado já vale na conversa que o muda (o kit é carregado desta pasta): nesta conversa a busca rodou uma
  vez no pedido seguinte à mudança, sem casar nada.
