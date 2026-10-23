# 2026-10-23 — regras do kit pelo plugin: do "sempre bate no limite" à 0.42.0

**Conversamos.** O owner rodou o `/mss-spec:doctor` no Whats e mandou a saída de outra janela, que "se perdia no
CLAUDE.md": *"entendi que já haviamos corrigido isso"*. A 0.31.1 tinha subido o teto do **modelo** pra 10 KB, mas o
mesmo teto valia pro `CLAUDE.md` do projeto, e o modelo sozinho tinha 9.757 B (sobravam 243 B). Dos 4 defeitos que a
outra janela apontou, o C (KB arredondado: "10 KB (teto 10 KB)") e o D (`teto_ao_gravar.py` tratando `wc -c CLAUDE.md`
como gravação) foram conferidos no código; os quatro entraram na 0.42.0. O owner deu a direção:
*"desde que funcione! E é até melhor vir do kit"*, *"cada projeto pode ter infra diferente"* e *"O que não pode
acontecer é ajustarmos e o projeto se perder todo e eu ter que passar tudo novamente"*.

**Pivôs.**
1. **Subir o teto → separar kit e projeto.** Eu propus 12.000 B; o owner: *"mas ainda 12k não é baixo qualquer
   alteração subiria ele, precisamos resolver em definitivo"*. A parte comum (regras do kit copiadas) passou a vir do
   plugin por hook `SessionStart` em dois blocos (limite de 10.000 caracteres por string do hook).
2. **Índice do CLAUDE.md (ideia do owner) → medido antes de adotar.** O owner: *"Tem que ver se isso é totalmente
   viável e se irá funcionar, não é porque eu disse que é regra e está certo"*. Medição nos 76 históricos do Whats:
   o Whats **já** tinha índice (7 regras desde 2026-09-23) e mesmo assim 10.096 B; regra por tipo carrega ao ler e
   falha ao criar (banco 5, testes 2); e os fatos de infra atrás de gatilho de arquivo entraram em 4 de 76 conversas
   — a causa do *"parecia que perdeu toda a memoria e eu tinha que lembrar e falar a todo momento"* (F-040). O
   índice ficou só pra **regra de escrita**; **fato** fica no `## Contexto`, por extenso.
3. **"Não mexemos em nada no arquivo claude.md" (owner) → o arquivo mostrava a mudança** (`CLAUDE.md:41` do Whats,
   2026-09-23, feita pelo assistente seguindo o kit).
4. **Revisão a olho → migração que confere sozinha.** O owner: *"tinha que ter algo automático que compara, valida
   que está tudo OK e só então faz"*. Virou `templates/migrar_claude_md.py`: monta em memória, confere conservação
   linha a linha, Contexto sem ponteiro, e só grava se tudo fechar.
5. **Script commitando → git pela regra de cada projeto.** O revisor do documento achou que o Whats reserva o git
   ao owner; o script nunca mexe no git.

**Rejeitado.** Teto de 12.000 B ou 10 KiB · `@import` do kit no `CLAUDE.md` · índice com gatilho pra regra "nunca
violar" · recall de regra pela palavra do pedido · migrar todos os projetos de uma vez (ver Fora de escopo do INDEX).

**Fizemos.** 0.42.0 em 8 tarefas por subagentes com revisor por tarefa (escolha do owner). As revisões pegaram 8
problemas sérios antes do merge (migração travando pra sempre em projeto do molde anterior, seção engolida,
conservação por conjunto, migração pela metade, branch depois da gravação, `CLAUDE.md` fora de UTF-8 calando as
regras, regra vazia barrando gravação). Merge na `main` em `9b51031`, 950 testes; push é do owner. No caminho,
três reclamações de demora/silêncio — *"está fazendo algo está parado na tarefa 4 há varios minutos"*, *"está a
quase 1hora sem responder"*, *"vai ficar o dia todo nisso?"* (F-041) — e uma de comando trocado: *"uma hora voce
falar para rodar o docto ou o upgrade"*. O owner rodou o `/mss-spec:upgrade` no Whats: prévia 20/18/3, igual ao
dry-run daqui; o `testes.md` que fica vazio pode ficar (o hook ignora regra vazia).

**Próximo.** `git push origin main` (owner) · `--aplicar` no Whats e o commit pelos comandos que ele receber ·
conferir numa janela nova que o bloqueio funciona (pedir um `.sql` novo: a 1ª tentativa volta com o texto da regra
de banco) · `/mss-spec:upgrade` nos outros projetos, um por janela · pendências que podem esperar estão na spec
`docs/specs/regras-do-kit-pelo-plugin.md`.
