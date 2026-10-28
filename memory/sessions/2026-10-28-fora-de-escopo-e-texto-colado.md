# 2026-10-27/28 — texto colado conferido, worktree limpo, "fora de escopo" redefinido

## Conversamos
1. O owner colou o texto que a conversa da 0.44.0 entregou ("fora de escopo achado antes do desenho"): *"a confiança que eu tenho disso é 0%!!!"*.
2. Conferido fato a fato contra o repo: o INDEX do kit já tinha 1.579 B (o hook moveu o "Fora de escopo" na sessão `584b3e53`, `"INDEX.md=7042->1560"`); o F-042 só existia numa branch fora da `main`; a premissa central era falsa.
3. *"analise pelo menos o projeto do whatsapp"*: 13 projetos com "Fora de escopo", 222 itens; Whats com 115 itens que a busca lê (106 de 432 acionamentos apontaram o arquivo); o do kit, em blocos `> `, com 0 itens legíveis. Na conversa da 0.44.0, a decisão de 23/10 (`docs/decisoes.md:48`) chegou pela busca às 10:30, foi lida às 10:31 e desrespeitada às 10:36: o texto que a conversa anterior passou já mandava mexer no `CLAUDE.md`. O hook do teto ficava calado no worktree porque `CLAUDE_PROJECT_DIR` apontava a pasta principal.
4. *"geralmente eu não uso nenhum worktree; se foi usado, foi indevidamente"*; *"cada chat vem uma solução diferente para o mesmo problema"*.
5. Duas features definidas pelo owner (nunca worktree; fora de escopo) + limpar o worktree; os comandos bug, dúvida e diagnóstico conferidos na `main` e no remoto.
6. Abri a feature 1 numa conversa filha: *"está ficando perdido"*. Soltei-a desta e ela saiu do grupo: *"a conversa sumiu voce sozinho deletou ela"* (não estava apagada).
7. Texto da feature 2 citava outros projetos: *"isso é um absurdo o comando upgrade é o responsável por isso"*. Depois: *"não ficou claro o que isso vai fazer e como ele irá consertar"*.
8. As duas leituras (A: se metia em outro assunto; B: travava o que o owner fazia): *"O assistente fez tanto o A como o B!!"* — *"naquela data eu não iria fazer agora eu vou!"*.
9. O owner propôs o to-dolist com a tag; análise sem desenho, depois de *"Eu quero uma análise não é para sair desenvolvendo nem planejando nada!!!"*.
10. *"deveremos padronizar para que tudo tenha o mesmo significado"*: recomendação aceita ("Ok") e texto da conversa nova entregue.

## Pivôs
- Do texto colado ("procurar o nome do arquivo no Fora de escopo antes do desenho") para os fatos: a decisão foi achada e lida; o erro nasceu no texto de passagem entre conversas (F-044).
- Do conserto do hook no worktree para nunca trabalhar em worktree (0.46.0, feita na conversa própria).
- Do `FORA-DE-ESCOPO.md` com índice (ideia de 2026-10-27) para o to-dolist com a tag `#fora-de-escopo`, no git.
- De consertar cada projeto pela conversa do kit para "o doctor aponta, o upgrade converte".

## Rejeitado
- A regra do F-042 ("procurar o nome do arquivo"): não teria evitado o erro.
- O conserto do `teto_ao_gravar` no worktree: o owner não usa worktree e a 0.46.0 trava.
- `FORA-DE-ESCOPO.md` com índice: mais um arquivo para gerenciar e barrar em tamanho.
- Perguntar uma vez por conversa quando o pedido toca um item: o assistente não cita sozinho.
- To-dolist fora do git: perde ao trocar de máquina.

## Fizemos
- `eeba6a9` (merge `00998bc`): o útil das capturas do worktree; worktree e `feature/partida-em-dois-niveis` apagados.
- 0.46.0 (merge `4cbbdfb`), feita na conversa "Nunca trabalhar em worktree".
- Item "padronizar os projetos" no `to-dolist.md` do kit e no INDEX.
- Texto da conversa nova da feature "fora de escopo vira item do to-dolist".

## Próximo
- O owner abre a conversa nova com o texto entregue (INDEX item 2).
- Depois, a padronização dos projetos (INDEX item 3).
