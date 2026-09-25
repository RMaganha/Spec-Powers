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

## Depois: não alucinar (0.35.0) e memória na hora da ação (0.36.0)

**Conversamos:** o owner pediu a regra de "não alucinar" — perguntar quando não está claro, não se estender sem profundidade, consultar a memória, responder curto. Depois, tratar os casos abertos F-033 e F-034.

**Pivôs:**
1. das práticas da Anthropic (permitir "não sei", investigar antes, ancorar em citação) para o que se faz sem LLM: regra "Fonte ou não sei" + `confere_citacoes.py` no `Stop` (devolve uma vez — escolha do owner);
2. medir antes de ligar: 16 de 121 respostas reais seriam devolvidas; linha que propõe/nega, caminho parcial e molde do kit eram falso positivo → 0 nas sessões no próprio projeto; o hook não achou invenção real no histórico (rede barata, não ganho medido);
3. F-033: tamanho não separa (60 de 211 acima de 450 palavras); a forma separa — ≥ 2 rotas não pedidas só pega a resposta do caso;
4. F-034: recall por palavras no comando seria ruído → a memória declara `gatilho_comando:`/`gatilho_resposta:`; a doc não garante `additionalContext` no `PreToolUse`, então o comando é negado uma vez com a memória no motivo;
5. o stderr em UTF-8 forçado da 0.35.0 voltou ao `print` comum (a doc não diz como o Claude Code lê; o `print` aparece certo ao vivo).

**Rejeitado:** verificação por LLM (best-of-N, auto-verificação: tokens em toda resposta) · medir tamanho da resposta · recall no `PreToolUse` por palavras em comum · conferir `[[memória]]` (link pendente é permitido).

**Fizemos:** 0.35.0 (regra + `confere_citacoes.py`, F-035) · 0.36.0 (`_memoria_de_acao.py`, 4ª verificação no `git_publicacao.py`, rotas no `Stop`, gatilhos nas memórias do heredoc e da junction; F-034 fechado). Suíte 676 → 731. Tropeço meu: o patch das memórias foi por heredoc e estragou o regex com caractere de controle — o F-034 ao vivo, consertado por script gravado com `Write`.

**Próximo:** observar F-033 e F-035 · no Whats (janela de lá): as regras novas no `CLAUDE.md` de lá.
