# 2026-11-18 — custo dos hooks medido no Claude real; troca sem o Git Bash descartada

## Conversamos
O owner abriu `/mss-spec:bug`: os hooks do kit pesam em todo projeto, pior nos grandes. Já decidido: medir antes
de mexer, no projeto grande que ele indicasse, só lendo o projeto; a máquina está OK.

## Pivôs
- **Imitação × real.** A 1ª medição imitou o Claude (`python hook.py` + JSON no stdin) no Transportes V2 e no
  Atendimento WhatsApp e apontou "os 5 hooks do Stop releem a conversa inteira" (3,3 s com conversa de 18 MB).
  No real, a conversa não pesa: o próprio Claude anota `durationMs` de cada hook no arquivo da conversa
  (`attachment` `hook_success` e `system` `stop_hook_summary`), e as conversas acima de 10 MB esperaram 0,9 s.
- **Caixa de areia.** O 1º ensaio rodou os hooks de verdade e atualizou a tabela `~/mss-spec/memoria.sqlite3`
  e o registro dos hooks. O owner: nada pode gravar na memória do projeto. Dali em diante, HOME, TEMP,
  `CLAUDE_CONFIG_DIR` e `MSS_MEMORIA_TABELA` apontados pra uma pasta descartável, com cópia da tabela e das
  conversas, e conferência no fim (`FORA DA CAIXA MUDOU: nada`).
- **Tabela pros hooks.** O owner sugeriu um hook ler e deixar um resumo numa tabela pros outros. A documentação
  do Claude Code: os hooks de um evento rodam em paralelo, sem ordem. O owner decidiu: nada de tabela.
- **Git Bash.** A documentação: no Windows o hook em linha única roda pelo Git Bash; com `args` (exec form) o
  python é chamado direto. Feito na branch `fix/hooks-sem-bash` (686 passed); numa conversa nova do WhatsApp
  os hooks rodaram no formato novo sem erro, mas o fim da resposta ficou em 2,4 s sem o sono (antes: 1,3 s) e
  até 9,1 s com 7 ajudantes do sono. Sem ganho → descartado.

## Rejeitado
Ler só o fim da conversa (perderia o que foi gravado antes); tabela `memoria_hook`; juntar os 5 hooks num só;
exec form (medido sem ganho).

## Fizemos
Medição real (95 conversas do WhatsApp desde 01/11; kit desde 10/11): ~1 a 2 s por ação, sem depender do tamanho
do projeto nem da conversa; abertura ~3 s (`memoria_tabela_em_dia.py` chega a 11 s). Item fechado no
`to-dolist.md` e MAPA, merge `f6c0577` na `main`.

## Próximo
O custo maior visto foi a abertura (`memoria_tabela_em_dia.py`) e os picos com o sono rodando ajudantes; nenhum
foi pedido nesta conversa.
