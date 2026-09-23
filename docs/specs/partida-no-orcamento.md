# Partida no orçamento — a janela abre sabendo o que estourou, e backlog deixa de ser fato

## Estado atual
Caso **F-030** (`docs/EVALS.md`). Quatro peças, todas nascidas onde a falha acontece:

**(1) `hooks/orcamento_partida.py`** — `SessionStart`, ligado por padrão (`hooks/hooks.json`), **não
bloqueia**. Mede em bytes, na raiz (`CLAUDE_PROJECT_DIR` › `cwd`), `CLAUDE.md` (10 KB), `docs/superpowers/
MAPA.md` (6 KB), `docs/superpowers/INDEX.md` (7 KB) e `memory/MEMORY.md` (6 KB) — os mesmos tetos do
`tests/test_orcamento_contexto.py` e do `templates/rodizio_partida.py` (um teste trava os três). Dentro
do teto → calado. Acima → `additionalContext` (≤ 1.000 bytes; no Whats real, 615) que nomeia só o que
estourou, com bytes e teto, e manda: não ler inteiro; MAPA → só `## Onde estamos` até o 1º `---`; INDEX →
só `## Em andamento`; o resto por `grep`; backlog, fora de escopo e diário antigo **não** são o estado
atual; avisar o owner em 1 linha e oferecer `/mss-spec:doctor`. `systemMessage` de 1 linha pro terminal.
Falha aberta; escape `MSS_ORCAMENTO_OFF=1`; registro `avisou` com os bytes.

**(2) `hooks/um_item_por_janela.py` ignora `## Backlog`** (e as subseções `###` embaixo dele), como já
ignorava "Fora de escopo". Backlog é o que ainda não começou; contar como feature aberta travava o
`nova-feature` pra sempre (44 → 6 no INDEX real do Whats — as 6 de "Em andamento"). `templates/INDEX.md`
ganhou as seções `## Em andamento` · `## Backlog` · `## Fora de escopo`; o `kickoff` semeia sob `## Backlog`;
o `nova-feature` grava sob `## Em andamento` (item vindo do backlog **sobe**, não duplica).

**(3) Recall sem diário** — o hook `recall_memoria.py` chama `casar(..., diario=False)`: diário de sessão
é passado, sob demanda (o `CLAUDE.md` já dizia). O `/mss-spec:memory buscar` segue achando o diário.

**(4) Prosa no `templates/CLAUDE.md`** (8.735/10.000 bytes, frases-chave travadas): **"Pedido com várias
partes"** — listar as partes na ordem de dependência do owner, uma spec por parte, fazer só a 1ª;
**"Relate o que está no disco"** — ferramenta recusada/interrompida → conferir `git status` antes de
dizer o que existe.

Fora de escopo: **bloquear** a partida acima do teto (rede, não cerca — travar a janela por causa de um
número apagaria o trabalho do dia) · o hook **mover** conteúdo sozinho (mover é decisão do owner:
`rodizio_partida.py` em dry-run, janela própria no projeto) · `rodizio_partida.py index` mover Backlog e
Fora de escopo pra arquivo próprio (fica pra quando o 2º projeto precisar; no Whats foi à mão) ·
detectar "pedido com várias partes" por máquina (sem assinatura confiável; fica na prosa).

## Histórico
- 2026-09-23 — criado. Sessão `e87ec450` do Whats: pedido de deploy em produção; partida com CLAUDE 28 KB +
  MAPA 60 KB + INDEX 71 KB, janela de 73 mil a 139 mil tokens antes da 1ª resposta, n8n/cotação do
  backlog no plano, pipeline e inventário do banco ao mesmo tempo, 4 interrupções do owner e um relato
  final errado ("não escrevi" um arquivo gravado às 14:46). Nenhum hook negou nada: o "não pode" era o
  assistente prevendo a trava do `nova-feature` pelos 44 itens de backlog.
