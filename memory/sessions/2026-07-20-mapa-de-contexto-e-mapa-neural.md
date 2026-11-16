# 2026-07-20 — mapa de contexto e mapa neural (diário retroativo)

conversa: 743aa556-9e60-48e1-b0b6-1c5242e1ff9e

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta). Período: 2026-07-20 a 2026-07-21.

## Conversamos
`MAPA.md` por projeto contra a amnésia de partida, e o mapa neural.

## Pivôs
- A F2 voltou para a mesma branch: "apesar da F2 estar fora faz parte da mesma branch e escopo" (fala 009).
- O grafo entre projetos, que o owner achou "ridículo" (fala 015), virou mapa mental de 4 dimensões; o assistente
  tinha estreitado a ideia do owner ("Eu reduzi a sua ideia", fala 016). Um mockup em HTML foi aprovado antes de
  codar o gerador (falas 016-025).
- **O SVG feito à mão saiu no mesmo dia:** o owner cobrou "o .js que eu havia escolhido… opção b" (fala 037) e o
  assistente trocou pela `vis-network` vendorizada — "O SVG+vanilla… foi descartado" (fala 038). A linha de
  `docs/decisoes.md` de 2026-07-20 ficou dizendo "SVG + JS vanilla". A versão que saiu com a `vis-network` foi a
  0.9.0 (fala 056; `CHANGELOG.md:579`).
- Física do grafo desligada (fala 042); o owner pegou releitura de arquivo (fala 029) e consulta ao visual (fala 045).
- Um padrão do `.gitignore` sem âncora engoliu `commands/mapa-neural.md` (fala 052).
- Mensagem de commit com here-string do PowerShell (`@'...'@`) num shell Bash deixou o título como `@` (fala 052);
  `git merge -F -` não leu da entrada padrão (fala 058).

## Rejeitado
Registro central; grafo só entre projetos; animação.

## Fizemos
`/mss-spec:mapa`, `/mss-spec:mapa-neural`, o `upgrade` passa a mesclar o `MAPA.md`, `.gitignore` ancorado, 0.9.0,
merge `a4399c0`, cartões C18/C19 no COMO-FUNCIONA.

## Próximo
Provar a partida numa janela nova.
