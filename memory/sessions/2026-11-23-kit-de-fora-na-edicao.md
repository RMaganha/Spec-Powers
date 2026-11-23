# 2026-11-23 — conversa inteira sem o kit: edição sem porta, texto pronto sem comando (0.67.0, F-077)

## Conversamos
O owner desconfiou que duas conversas do Atendimento WhatsApp — "Análise de consultas de apólice e boleto" e
"Entrada Apólice e Boleto no Painel_V2" — não usaram o kit ("isso seria absurdo"). Li as duas conversas gravadas
(`.jsonl`). A Análise usou o kit (entrou pelo `/mss-spec:bug`, rodou `memoria_tabela.py buscar`, chamou o
superpowers por dentro). A Entrada abriu com o texto de continuação colado, sem comando do kit, e editou plano,
MAPA, INDEX, spec e teste sem porta, sem busca na memória e sem superpowers.

## Pivôs
- Começou como análise (`/mss-spec:tarefa`) e virou `/mss-spec:bug` quando o owner disse: *"eu quero saber o pq
  falhou e corrigir isso, não quero que faça nada da outra janela aqui, ela foi exemplo para saber que tem coisa
  errada!!"*.
- A falha do Git Bash parecia do kit. O `git reflog` do clone (nenhuma troca de branch à tarde de 19/11) e a busca
  em todas as conversas de 19/11 em diante (só a Análise, 192 falhas de 19:58 a 20:33 UTC) mostraram que foi a
  máquina — a causa do `bash.exe` sumir não se sabe.
- O owner trouxe o 3º sintoma: na Análise, *"Vamos rodar o /mss-spec:memory capturar"* virou 4 buscas do comando
  em `~/.claude/plugins` antes de achar em `~/.claude/skills/mss-spec` — "foi aí que notei que tudo havia se
  perdido". Virou a correção C (caminho do kit resolvido nas regras).
- Causa da B: o texto pronto tinha 4 linhas, abaixo do mínimo de 5 da conferência; o molde já começava pelo
  comando, mas a conferência não o cobrava.
- No teste da B, o texto curto com o comando chegou a 5 linhas e caiu na regra das três partes (F-058): mantive a
  regra e ajustei o teste.
- A prova como processo pelo `echo … |` do Bash saiu calada nos dois hooks; com o evento gravado em arquivo os dois
  responderam certo (memória `project_hook_pelo_powershell_chega_com_marca`).

## Rejeitado
- Mexer no projeto Whats (ordem do owner).
- Voltar a chamar o python sem o Git Bash (`d6a0c01`) — contraria `docs/decisoes.md:87`; fica pro owner decidir
  (`to-dolist.md`).
- Cobrir edição feita pelo `Bash` (`sed -i`, `cat >`) — fica no `to-dolist.md`.

## Fizemos
0.67.0 na branch `fix/kit-primeiro-cobre-edicao`: `hooks/kit_primeiro.py` nega `Write`/`Edit`/`MultiEdit`/
`NotebookEdit` em arquivo de projeto do kit sem porta; `hooks/passagem_de_conversa.py` exige `/mss-spec:<comando>`
na 1ª linha, também no bloco curto; `hooks/regras_do_kit.py` troca `${CLAUDE_PLUGIN_ROOT}` pelo caminho do kit.
Testes do que mudou: 1033 verdes e 1 vermelho (`tests/test_hook_entrada_utf8.py`, bloco sem o comando) corrigido —
23 de 23. Decisão em `docs/decisoes.md`, caso F-077 no `docs/EVALS.md`. Commit `370fee3`, merge `33ab9e6`, push
feito pelo owner.

## Próximo
Ver no real, numa conversa nova: a negativa de edição sem porta e o texto pronto saindo com o comando na 1ª linha.
