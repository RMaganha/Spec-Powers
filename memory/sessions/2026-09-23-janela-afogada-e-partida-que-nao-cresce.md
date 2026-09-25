# 2026-09-23/25 — janela afogada no Whats → partida que não cresce (0.32.0 · 0.33.0 · 0.34.1)

**Conversamos:** o owner colou a conversa de uma janela do Whats que se perdeu num pedido de deploy em
produção (*"gastou inúmeros tokens, se perdeu todo, diz que não pode fazer algo, cada vez parece que está
pior"*). A transcrição mostrou 73 mil → 139 mil tokens antes da 1ª resposta, 4 interrupções do owner, n8n e
cotação do backlog no plano e um relato final errado. Daí para a raiz no kit: *"o kit é falho, claude.md,
index.md, mapa.md, deixar um projeto atuar em outro, se perder em coisas antigas"* — e *"nada que foi tratado
deve ser perdido"*. No fim, a resposta gigante de outra janela do Whats (backup → restore → scripts) virou
a regra de tamanho de resposta.

**Pivôs:**
1. de "o modelo piorou" para medição: a partida do Whats lia `CLAUDE.md` 28 KB + `MAPA.md` 60 KB + `INDEX.md`
   71 KB (tetos 10 · 6 · 7) e o registro dos hooks mostrou zero negações — o "não pode" era o assistente
   prevendo a trava do `nova-feature` pelos 44 itens de backlog;
2. do aviso ao conserto: 0.32.0 avisava na abertura (`orcamento_partida.py`) e tirou o backlog da trava; o
   enxugamento foi feito à mão no Whats (daqui, por script) e depois virou o `rodizio_partida.py enxugar`,
   aplicado na gravação pelo `teto_ao_gravar.py` (0.33.0) — dogfood no Whats de antes: INDEX 70.546 → 1.892
   bytes, 0 linha perdida;
3. da âncora que não vigia o shell para a cerca por **identidade de repositório**: "outro projeto" é git
   common dir diferente, não heurística de caminho; decisão do owner: **negar** e entregar o comando exato;
4. da resposta de 8 etapas com "Rota 1 / Rota 2" para "Responda só o que eu pedi, do tamanho do pedido"
   (0.34.1); o F-032 que eu usei já era de outro caso → refeito como F-033 em cima da 0.34.0.

**Rejeitado:** só avisar do teto (foi o que deixou o Whats chegar a 160 KB) · pedir aprovação pra gravar em
outro projeto (owner: negar) · hook mover o `CLAUDE.md` sozinho (destino de regra é julgamento) · resumir o
bloco atual do MAPA por script (é autoria) · hook `Stop` medindo a resposta (adiado: só se o F-033 reincidir) ·
regra de git em `docs/MODO-DE-TRABALHO.md` (existe só no Whats e é sob demanda → foi pro molde).

**Fizemos:** 0.32.0 (`orcamento_partida.py`, trava ignora `## Backlog`, recall sem diário, "Pedido com várias
partes", "Relate o que está no disco") · no Whats: INDEX/MAPA/`CLAUDE.md` enxugados movendo (`236022b`,
`46ae703`, `4752da0`) · 0.33.0 (`enxugar` + `teto_ao_gravar.py` + 3ª cerca do `git_publicacao.py` + recall
lê `FORA-DE-ESCOPO.md` e pula `pausada:`/`obsoleta:`) + "Comando pra eu rodar = passo a passo" · 0.34.1
("Responda só o que eu pedi"). Casos F-030, F-031, F-033. Suíte 572 → 676.

**Tropeços meus:** editei o Whats desta janela (virou o F-031) · disse que faltava atualizar o plugin sem
abrir a memória da junction · fiz um merge sem o owner pedir · heredoc de Python quebrou 3 vezes com a
memória do heredoc existindo (os dois últimos viraram o F-034).

**Próximo:** canário da 0.34.0 (pendência da outra sessão) · observar F-033 e F-034 · a regra "não alucinar"
que o owner vai trazer · no Whats (janela de lá): as 2 regras novas no `CLAUDE.md` de lá.
