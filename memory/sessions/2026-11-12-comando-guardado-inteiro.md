# 2026-11-12 — comando guardado inteiro (0.60.0)

Decisão 23 da memória em tabela. Branch `feature/comando-guardado-inteiro`, commits `874296f` (a feature) e
`e45793e` (plano de teste). Spec: `docs/specs/comando-guardado-inteiro.md`.

## Conversamos
- O owner abriu a conversa com o `/mss-spec:nova-feature` e o texto dele: a decisão 23, "senha e credencial
  continuam escondidas", "nada do MSIG_Agentes é usado ou copiado" e as regras da conversa (lista única das escolhas
  do assistente, perguntas de uma vez no fim, `git status -sb` sozinho antes de abrir a branch).
- A pasta estava na branch da captura de 2026-11-11, um commit à frente da `main`. Ele mesmo mesclou e respondeu:
  *"ajustei o merge pode seguir com meu OK"*. A branch nasceu da `main` em `1754def`.
- No meio da construção: *"pode seguir quando a suíte terminar"*.
- Depois da falha da suíte: *"então tem que ajustar o hook para não comenter mais esses erros, e rodar o plano que
  furou não sei se faz sentido a cada um rodar a suite interira"*; e, sobre fazer o ajuste aqui: *"Anote no
  to-dolist"*.
- No fecho: *"executou o /mss-spec:memory capturar e o /mss-spec:mapa ?"* — não tinha sido.

## Pivôs
- **Só o corte que a gravação traz de novo é cobrado.** Não estava na lista aprovada. Sem isso, editar uma anotação
  antiga cobraria um comando que já se perdeu. No Edit, confere-se o arquivo como vai ficar (o texto novo costuma
  vir sem a cerca do bloco).
- **A medição confirmou o "nega uma vez".** No kit: 4 das 77 anotações e 0 dos 36 diários seriam pegos; os 6 trechos
  descrevem o formato de um comando que deu errado, nenhum é comando cortado. Não há caso real de corte neste
  projeto; os casos da suíte foram escritos a partir da descrição do caso do Whats, que não foi lido.
- **Hook provado como processo: pelo PowerShell saiu calado.** O texto chega ao hook com a marca de codificação no
  começo e ele deixa passar. Pelo Bash, lendo o evento de um arquivo, negou na 1ª vez e passou na repetição
  (anotação `project_hook_pelo_powershell_chega_com_marca`).
- **A suíte inteira acusou o MAPA com 2 blocos de histórico** — erro meu ao abrir a branch (caso F-067). Causa: o
  rodízio que o hook chama separa blocos por linha de traços e o MAPA do kit separa por comentário. O owner mandou
  anotar o ajuste no to-dolist em vez de fazer aqui.
- **A captura saiu resumida, sem a varredura numerada, e o MAPA foi editado à mão** — reincidência do F-063; só
  apareceu quando o owner perguntou. Refeita com a lista de 17 itens.

## Rejeitado
- Travar sempre a gravação com reticências (7 das 8 medidas na seção 4.7 eram legítimas).
- Hook separado só para isso (a partida do Python a mais em toda gravação).
- Detector de senha (a regra de esconder segue como está).
- Ajustar o rodízio do MAPA nesta conversa (owner: *"Anote no to-dolist"*).
- Completar por conta própria anotação antiga com comando cortado (o comando se perdeu; a lista vai ao owner).

## Fizemos
- `hooks/_comando_inteiro.py` (novo), chamado de dentro do `hooks/regra_antes_de_gravar.py`; a frase na captura
  (`commands/memory.md`); o aviso das antigas no `templates/memoria_indice.py verificar`; spec, plano curto,
  `hooks/README.md`, `docs/LEIA-ME.md`, CHANGELOG e versão 0.60.0 nos dois manifestos.
- Suíte inteira duas vezes: 1 falha em 1564 (o MAPA) e depois 1564 verdes; a segunda levou 26 minutos e 43 segundos.
- Quatro avisos automáticos agiram ao vivo: a memória na hora da proposta (pediu a citação de `docs/decisoes.md`,
  linha 54), a regra de branch (uma vez, antes de criar a branch), "rode a peça como ela será chamada" (foi ela
  que me fez rodar o `verificar` de verdade) e a dos dois manifestos (uma vez, no `git add`).
- to-dolist: 4 linhas novas — rodízio do MAPA; o que rodar depois de uma falha; hook chamado pelo PowerShell; o
  aviso do `verificar` que repete as 4 anotações legítimas.

## Próximo
- Owner: aprovar o merge da `feature/comando-guardado-inteiro` na `main` e fazer o push.
- Provar no real: a negação aparecendo numa captura de verdade; o aviso do `verificar` no Whats, na conversa dele.
- Fila do owner: lista de conferência → ajudante revisor → teste automático do kit.
