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

**(5) Teto na gravação (0.33.0)** — `hooks/teto_ao_gravar.py` (PostToolUse Write/Edit/MultiEdit; Bash/PowerShell que
cita o arquivo) roda `templates/rodizio_partida.py enxugar --aplicar` quando MAPA/INDEX passam do teto: rodízio de
sempre → INDEX: Backlog, Fora de escopo, Assuntos existentes pra arquivo próprio, linha longa de Em andamento →
`EM-ANDAMENTO.md` (fica nome/link — ponteiro — status verbatim) · MAPA: Conexões → `CONEXOES.md` (fica a lista de
nomes) e, se preciso, só o bloco atual fica. Move, nunca apaga; conservação conferida; para assim que cabe; destino
existente recebe prepend; conflito de merge não é tocado. Dogfood no Whats de antes da limpeza (`6d28a04`): INDEX
70.546 → 1.892 bytes sozinho, 0 linha perdida; MAPA 59.463 → 22.709 (o bloco atual do Painel V2 é conteúdo vivo — o
hook pede o resumo). `CLAUDE.md` > 10 KB só avisa. Escape `MSS_TETO_OFF=1`.

**(6) Outro projeto pelo shell (F-031)** — 3ª cerca no `git_publicacao.py`: nega git de escrita, `--proj … --aplicar`
e `>`/`tee` num repositório git diferente do da âncora, com o comando verbatim pra colar na janela dele. Leitura,
pasta fora de repo e worktree do mesmo repo passam. Falha aberta; `MSS_ANCORA_OFF=1`. Testado ao vivo nesta janela.

**(7) Recall** — lê `docs/superpowers/FORA-DE-ESCOPO.md` (saiu da partida) e pula linha com status `pausada:`/`obsoleta:`.

**(8) Forma do MAPA e do INDEX em toda gravação (0.44.0)** — três regras valem mesmo **abaixo** do teto (o resto do
`enxugar` segue só acima): MAPA → item do `## Próximo passo` com mais de 300 bytes e título em negrito fica
`N. ⬜ **título** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)`, e o texto inteiro vai pro `PROXIMO-PASSO.md`
(prepend datado); `## Conexões`, quando já existe `CONEXOES.md`, fica só com a linha de nomes e as linhas detalhadas
vão pra lá (rodapé `---`/`Atualizado em` e comentário ficam no MAPA) · INDEX → linha `fechada` vai pro
`INDEX-historico.md`. Arquivo já na forma não muda. O `CLAUDE.md` **não** entra (decisão do owner em 2026-10-27:
o que se combinou em 2026-10-23 fica). Os comandos que escrevem no MAPA (`/mss-spec:mapa`, `nova-feature`) já escrevem
na forma; o hook é a rede.

**(9) O teto fala só com o assistente (0.52.0)** — o teto é o **gatilho** da separação em dois níveis, não um aviso pro
owner. `teto_ao_gravar.py`: MAPA/INDEX gravados → o retorno diz o que moveu e "releia" sempre que moveu; se ainda ficou
acima depois de tudo que é mecânico, pede o resumo pra spec **uma vez por sessão** por arquivo (estado em
`mss_teto_<sessão>.json`, chave `_avisados`) e termina em "não é assunto pro owner"; **nunca** "avise o owner", **nunca**
`systemMessage`. `CLAUDE.md` > 10 KB → uma vez por sessão, **com** "avise o owner" e `systemMessage` (o ato é dele: upgrade
ou mover bloco). `orcamento_partida.py`: MAPA/INDEX acima → só o que ler e o lembrete do resumo, sem owner e sem
`systemMessage`; `CLAUDE.md`/`MEMORY.md` acima → "avise o owner" (upgrade · mover bloco · `memoria_indice.py dividir` com
OK dele) e `systemMessage` só com esses nomes. Motivo: o hook mandava avisar o owner até abaixo do teto (MSS-SSC) e em
toda edição quando sobra bloco vivo (Whats, 36× em 7 conversas); o owner: *"pq esse bendito teto, já separamos isso em
índices"*.

**(10) O teto do MAPA e do INDEX conta só conteúdo** — comentário `<!-- -->` não entra na medida
(`rodizio_partida.bytes_de_conteudo`; cópia em `orcamento_partida.py`, travada por teste; `tests/test_orcamento_contexto.py`;
`anatomia.py`; doctor check 9). O molde traz 1.805 B de comentário no MAPA (30% do teto) e 1.108 B no INDEX. Não foi a causa
do aviso do Whats (o MAPA dele não tinha comentário): é correção do molde. `CLAUDE.md` e `MEMORY.md` seguem em bytes do arquivo.

Fora de escopo: **bloquear** a partida acima do teto (rede, não cerca — travar a janela por causa de um
número apagaria o trabalho do dia) · o hook **mover** o `CLAUDE.md` sozinho (destino de regra é julgamento) · resumir o bloco atual do MAPA por
script (é autoria) · a cerca do shell ver script com caminho escrito dentro dele ·
detectar "pedido com várias partes" por máquina (sem assinatura confiável; fica na prosa) · **subir o teto** (número sem
estrutura volta a estourar, `memory/feedback_teto_que_sempre_estoura_e_estrutura.md`) · encurtar o guia do molde do MAPA.

## Histórico
- 2026-09-23 — criado. Sessão `e87ec450` do Whats: pedido de deploy em produção; partida com CLAUDE 28 KB +
  MAPA 60 KB + INDEX 71 KB, janela de 73 mil a 139 mil tokens antes da 1ª resposta, n8n/cotação do
  backlog no plano, pipeline e inventário do banco ao mesmo tempo, 4 interrupções do owner e um relato
  final errado ("não escrevi" um arquivo gravado às 14:46). Nenhum hook negou nada: o "não pode" era o
  assistente prevendo a trava do `nova-feature` pelos 44 itens de backlog.
- 2026-09-23 — 0.33.0: o owner viu o padrão (*"o kit é falho… deixar um projeto atuar em outro, se perder em coisas
  antigas"*) e pediu tratar a raiz na mesma janela, sem perder nada. O rodízio vira mecânico na gravação (o que foi
  feito à mão no Whats virou `enxugar`), a escrita em outro repositório pelo shell passa a ser negada (F-031) e o
  recall pula o que está vencido.
- 2026-10-27 — 0.44.0: forma do MAPA e do INDEX aplicada em toda gravação, não só acima do teto (motivo: o Whats vivia
  em 96–99,7% — MAPA 5.981/6.000, INDEX 5.635/7.000 — e o aviso não fechava; o owner quis o mesmo modo do MEMORY,
  topo curto e detalhe sob demanda). Reabre o "para assim que cabe" de `docs/decisoes.md:40` só nesses três pontos.
  O `CLAUDE.md` ficou fora por decisão do owner.
- 2026-11-03 — 0.52.0: o teto deixa de falar com o owner sobre MAPA/INDEX e a medida passa a contar só conteúdo (motivo: o
  owner, cansado do "alerta do MAPA no limite de 6k" em toda conversa — *"já ajustamos isso e não resolve, fica alarmando"*).
  Antes do código, simulação em cópias do Whats e do MSS-SSC no scratchpad (`memory/feedback_simular_a_seco_com_dados_reais.md`):
  o hook de 0.51.1 manda avisar o owner abaixo do teto (MSS-SSC, 1ª gravação) e em toda edição quando sobra bloco vivo
  (Whats, bloco de 6,9 KB: 3 edições, 3 avisos). Premissa que caiu na simulação: o MAPA do Whats de 26/10 tinha 0 B de
  comentário do molde — a medida sem comentário não teria mudado nada lá.
