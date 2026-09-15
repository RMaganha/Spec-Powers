# Orçamento de partida e recall determinístico — design

**Data:** 2026-09-15 · **Versão alvo do kit:** 0.27.0 · **Status:** implementada em 0.27.0 (2026-09-15); aplicada no Whats em 2026-09-15

## 1. Problema (medido, não suposto)

O kit reclamou do `memory/MEMORY.md` do projeto *IA Bot Agent - Whats*: "estourou o teto: 25.711 bytes
(limite 25.600). Acima disso o excedente não carrega. Acrescentar linha sem podar piora." Duas coisas
erradas nessa frase, e uma terceira que ela esconde:

1. **A premissa é falsa para o índice do repo.** "Acima de 25 KB / 200 linhas o excedente não carrega"
   vale para o `MEMORY.md` da pasta **nativa** do Claude Code (`~/.claude/projects/<proj>/memory/`), que
   o Claude Code carrega sozinho e trunca. O `memory/MEMORY.md` do repo entra pelo `Read`, que lê até
   2.000 linhas sem cortar. O kit copiou o número da nativa para o repo (`templates/MEMORY.md`,
   `commands/memory.md`, checks 8 e 9 do `doctor`, `templates/anatomia.py`, `docs/decisoes.md`
   2026-08-18). O teto do índice do repo é **orçamento** (25 KB ≈ 6 mil tokens em toda janela), não
   "não carrega".
2. **A reação prescrita é podar**, o que contradiz a decisão do próprio kit (2026-08-18): *"a poda é
   sempre mover, nunca apagar"*. Num projeto com 93 memórias, "funda linhas parecidas" vira perder
   gancho.
3. **O `MEMORY.md` é 12% do custo.** O ritual de partida inteiro do Whats (o que o `CLAUDE.md` do kit
   manda ler ao abrir a janela: MAPA → MEMORY → INDEX → EVALS, mais o `CLAUDE.md` do projeto que entra
   sozinho) mede:

| arquivo de partida (Whats, 2026-09-14) | bytes | teto do kit | excesso | o que é o excesso |
|---|---:|---:|---:|---|
| `docs/superpowers/MAPA.md` | 89.651 | 6.000 | 15× | 1.104 linhas; "Onde estamos" tem 692; nenhum `MAPA-historico.md` |
| `docs/superpowers/INDEX.md` | 61.399 | 7.000 | 9× | 24 itens `aberta`, 13 `fechada` ainda dentro; nenhum `INDEX-historico.md` |
| `CLAUDE.md` | 27.377 | 8.000 | 3,4× | 11 linhas acima de 600 bytes |
| `memory/MEMORY.md` | 25.421 | 25.600 | no limite | o único de que o kit reclamou |
| `docs/EVALS.md` | 10.352 | — | — | — |
| **total por janela** | **~214 KB ≈ 53 mil tokens** | ~52 KB | | antes de qualquer trabalho útil |

O `doctor` (check 9) mede isso e **só reporta**. Ninguém move. Resultado: cada janela nova paga ~53 mil
tokens para "lembrar" e mesmo assim esquece, porque um MAPA de 1.104 linhas não é lido, é folheado; o
owner volta às conversas antigas e re-explica apontando onde o assunto foi tratado.

**Causa raiz única:** a partida não tem limite **mecânico**, e o recall depende de o modelo lembrar de
abrir o arquivo certo. Por isso é uma spec só.

## 2. Objetivo e não-objetivos

**Objetivo.** Em qualquer projeto MSIG, por maior que seja: (a) o que entra em toda janela fica limitado
por script e teste, não por prosa; (b) o que o modelo precisa saber chega **quando o prompt pede**,
injetado por hook, sem depender de lembrança e sem custar tokens de busca; (c) nada de conteúdo se
apaga — só se move para onde é lido sob demanda.

**Não-objetivos.**
- O kit **não edita outro projeto**. Aplicar isto no Whats é outra janela (regra "um projeto por
  janela"), arquivo a arquivo, com OK do owner. A cerca `projeto_ativo.py` já impede o contrário.
- Não se reescreve conteúdo de memória, MAPA ou INDEX. Reagrupar memórias por gatilho, preencher
  `gatilho:` nas 77 memórias do Whats que não têm, enxugar o `CLAUDE.md` de 27 KB e decidir o que fazer
  com 24 itens `aberta` são **trabalho de conteúdo**, do owner, no projeto. O kit lista a fila; não faz.
- Hook não chama LLM. Casamento é texto local (Python), determinístico, testável.
- Não se cria cache nem índice binário. Ler ~120 arquivos `.md` por prompt custa dezenas de
  milissegundos; se um dia doer, mede-se antes.

## 3. Desenho

### 3.1 Índice de memória em dois níveis

**Topo — `memory/MEMORY.md`.** Uma linha por **família de gatilho**, teto **6 KB** travado por teste:

```markdown
# Memória do projeto — índice por gatilho
<!-- 1 linha por FAMÍLIA. Gatilho bateu? abra o subíndice da família ANTES de agir. -->

- **quando <situação da família>** → [subíndice](indice/<familia>.md) — <N> memórias · <3 a 6 frases de gatilho>
```

As frases de gatilho da linha do topo vêm do `gatilho:` do frontmatter dos arquivos da família (não de
palavras raspadas do texto: a simulação mostrou que isso produz lixo como "Esta", ".md", "GET"). Família
sem nenhum `gatilho:` sai só com título e N, e entra na fila (3.1.3).

**Subíndice — `memory/indice/<familia>.md`.** Uma linha por memória, no formato que o kit já usa:

```markdown
# <Família>
- **quando <gatilho>** → [Título](../arquivo.md) — <gancho de uma frase>
```

Sem teto de carga (só abre quando a família bate). Teto por linha: 600 bytes (mesma régua do
`CLAUDE.md`; linha maior é procedimento disfarçado de índice). Os links são relativos ao subíndice
(`../arquivo.md`).

**Regra de leitura** (entra no `templates/CLAUDE.md`, linha da partida, e na regra crítica de memória):
na partida lê-se **só o topo**; quando uma linha do topo casa com a situação, **abre-se o subíndice da
família antes de agir**. O `/mss-spec:memory capturar` grava memória nova como linha no subíndice da
família certa e atualiza o N da linha do topo (via `verificar`, abaixo).

**Projeto pequeno** (kit incluso: 41 memórias, 8,7 KB) continua com índice plano enquanto couber em 6 KB?
**Não.** Um formato só, para o hook e o `capturar` não terem dois caminhos: todo projeto com `memory/`
passa a topo + `indice/`. O `upgrade` oferece a divisão (dry-run) quando encontra índice plano.

#### 3.1.1 `templates/memoria_indice.py dividir [--aplicar]`

- Lê `memory/MEMORY.md`. Cada `## <seção>` vira `memory/indice/<slug>.md`; cada linha `- [` da seção é
  **movida byte a byte** (só o link muda de `arquivo.md` para `../arquivo.md`, e isso é verificado).
  Linha `- **quando …** → […]` já no formato novo passa igual.
- Gera o topo com N e as frases de gatilho colhidas do frontmatter.
- **Dry-run por padrão:** imprime a tabela (família · linhas · bytes · tokens ≈ bytes/4) e o topo
  resultante; **nada é escrito** sem `--aplicar`.
- **Conservação, verificada antes de gravar:** número de linhas de memória antes = soma depois; cada
  linha movida reaparece idêntica (após a troca do link) em exatamente um subíndice; nenhum ponteiro
  quebrado. Falhou a conservação → não grava, sai 1, diz qual linha.
- O comentário-modelo HTML do topo do índice antigo (~900 bytes) não é memória: sai, e o script diz que
  saiu.

#### 3.1.2 `templates/memoria_indice.py verificar`

Topo ≤ 6 KB · toda linha do topo aponta subíndice existente · todo `memory/*.md` (menos `MEMORY.md`,
`DIARIO.md`, `sessions/`, `indice/`) tem exatamente 1 linha em algum subíndice, salvo `obsoleta:` no
frontmatter · nenhuma linha de subíndice > 600 bytes · N do topo = linhas do subíndice (corrige o N com
`--aplicar`). É o que o `doctor` (check 8) passa a rodar em vez de contar bytes à mão.

#### 3.1.3 `templates/memoria_indice.py fila`

Lista memórias **sem `gatilho:`** (Whats: 77 de 93) e famílias cuja linha do topo ficou sem frase de
gatilho. Só lista; preencher é conteúdo. O `capturar` já exige `gatilho:` em memória nova, então a fila
só encolhe.

### 3.2 Recall determinístico — hook `hooks/recall_memoria.py`

Evento `UserPromptSubmit`. **Rede que não bloqueia, ligada por padrão** (diferente do `capturar_nudge`,
que é opt-in: aqui o custo de disparar é ≤ 600 bytes de contexto, e o custo de não existir é o owner
re-explicar o projeto). Escape consciente: `MSS_RECALL_OFF=1`.

**Fontes**, todas no projeto ativo (`CLAUDE_PROJECT_DIR`, fallback `cwd`):

| fonte | o que casa | o que injeta |
|---|---|---|
| `memory/*.md` frontmatter | `gatilho:` + `description:` + `name:` | `memory/<arquivo>.md — <gatilho>` |
| `memory/indice/*.md` | a linha inteira | `memory/indice/<fam>.md:<n> — <título>` |
| `memory/DIARIO.md` | gist de cada linha `- [assunto] …` | `memory/sessions/<arquivo> — <gist cortado em 120 chars>` |
| `docs/decisoes.md` | cada linha `- <data> — …` | `docs/decisoes.md:<n> — <120 chars>` |
| `docs/EVALS.md` | coluna *gatilho* da tabela | `docs/EVALS.md — <id> <gatilho>` |

**Casamento.** Normaliza prompt e fonte (sem acento, minúsculas, só `[a-z0-9_]`), tokens com ≥ 4
caracteres menos uma lista curta de stopwords em português; pontuação = nº de tokens distintos em comum,
com peso 2 para token que aparece em *code span* ou identificador (`_`, `.`, maiúscula interna — é o que
diferencia `COD_CORR` de "código"). Entra no resultado o que tiver **≥ 2 tokens distintos** em comum;
devolve os **3 melhores**, empate desfeito por fonte (memória > subíndice > EVALS > decisão > diário).

**Saída.** JSON `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"…"}}`,
texto (exemplo ilustrativo do formato; os ponteiros reais vêm do projeto):

```
[mss-spec recall] casou com o seu prompt — abra antes de agir:
- memory/resolvedor-de-token-prefere-processo-ao-header.md — ao chamar validar_corretor numa rota que atende mais de um corretor
- docs/decisoes.md:41 — 2026-09-11 — token explícito por corretor em vez de cache de processo…
```

Teto **600 bytes** de injeção (corta na 3ª linha, nunca no meio de uma). Sem casamento → **nada** na
saída (silêncio, sem "nenhuma memória casou").

**Não dispara** para: prompt que começa com `/` (comando: o comando já tem seu ritual), prompt com < 4
tokens úteis, projeto sem `memory/`. **Falha ABERTA:** qualquer exceção → sai 0 em silêncio (recall que
derruba o prompt do owner é pior que recall mudo). Log de diagnóstico só com `MSS_RECALL_DEBUG=1`
(stderr).

**Por que isto resolve o "bloco de notas".** O owner não precisa lembrar em qual sessão tratou o
assunto: ao descrever o sintoma, o hook aponta o arquivo e a linha. E não custa tokens de busca: o
Python casa; o modelo só recebe 3 ponteiros.

### 3.3 `/mss-spec:memory buscar <termo>`

Terceiro modo do comando `memory` (hoje: `resgatar` | `capturar`). Roda
`python memoria_indice.py buscar "<termo>"` — **o mesmo motor de casamento do hook**, sem teto de 3 (até
10 resultados, com `arquivo:linha`) — e reporta os ponteiros **sem abrir os arquivos**, salvo pedido. É
para quando o owner só lembra a palavra ("onde tratamos do ndots?").

### 3.4 Rodízio mecânico do MAPA e do INDEX — `templates/rodizio_partida.py`

Mesmo princípio: **move, nunca apaga**; dry-run por padrão; conservação verificada.

**`rodizio_partida.py mapa [--aplicar]`.** Nos moldes e no Whats, "Onde estamos" e "Próximo passo" são
sequências de **blocos separados por `---`**, mais novo primeiro. Regra: em cada uma dessas duas seções
ficam os **2 primeiros blocos** (atual + 1 anterior — exatamente o que o `templates/MAPA.md` promete);
do 3º em diante vão para `docs/superpowers/MAPA-historico.md`, **prepend** sob `## <data de hoje> —
rodízio de "<seção>"`, na mesma ordem. "Conexões" não se toca. Seção sem `---` (bloco único) não se toca.
Cria o histórico se não existe. Conservação: cada linha movida reaparece no histórico; bytes do MAPA
depois = antes − movidos (± separadores). Relata bytes antes/depois e contra o teto de 6 KB; se ainda
estourar depois do rodízio (bloco atual gigante), **diz isso** e não corta o bloco: aí é conteúdo.

**`rodizio_partida.py index [--aplicar]`.** Linha de item cujo status casa `fechada` (mesma regra de
status do `um_item_por_janela.py`, reutilizada — não reimplementada) vai para
`docs/superpowers/INDEX-historico.md`, prepend sob `## <data> — fechadas`. Ficam: `aberta`, `em
andamento`, `pausada: …`, tudo da seção "Fora de escopo" (anti-re-litígio) e cabeçalhos. Relata contra o
teto de 7 KB; 24 itens `aberta` que não cabem são **reportados como decisão do owner**, não movidos.

**`doctor` check 9** passa a, para cada arquivo acima do teto, imprimir o **comando exato** do conserto
mecânico (`python …/rodizio_partida.py mapa` / `index`, `python …/memoria_indice.py dividir`), em
dry-run. Continua **só reportando** (o `doctor` não edita) — mas agora o conserto é uma linha que o owner
manda rodar, não uma tarde de edição manual. Para `CLAUDE.md` acima de 8 KB o conserto continua sendo
prosa ("mover procedimento para comando ou `.claude/rules/`"): não há regra mecânica segura ali.

### 3.5 Texto corrigido em todos os pontos que citam o teto

`templates/MEMORY.md` · `commands/memory.md` (passo 3 do capturar) · `commands/doctor.md` (checks 8 e 9)
· `templates/anatomia.py` (TETOS e texto) · `tests/test_orcamento_contexto.py` · `docs/decisoes.md`
(linha nova, não reescrita da de 2026-08-18): o teto do índice do repo é **orçamento de partida** (topo
6 KB); a frase "o excedente não carrega" fica **só** para a pasta nativa; o conserto indicado é **dividir
/ rodar o rodízio**, nunca "funda linhas" ou "pode".

## 4. Testes (cada um nasce de um caso desta spec)

| arquivo | garante |
|---|---|
| `tests/test_memoria_indice.py` | dividir conserva linhas byte a byte (fixture = cópia do índice do Whats de 2026-09-14, 93 linhas, 5 seções) · dry-run não escreve nada · topo ≤ 6 KB · frases do topo vêm do `gatilho:`, não do texto · `verificar` acusa ponteiro quebrado, memória sem linha, N errado, linha > 600 B · `fila` lista as 77 sem gatilho · `buscar` acha `ndots` e `COD_CORR` |
| `tests/test_hook_recall_memoria.py` | casa por gatilho (sintoma real → memória certa, 4 casos do Whats) · não casa com < 2 tokens · ignora `/comando` · ignora prompt curto · injeção ≤ 600 B e nunca corta linha ao meio · sem acento/caixa · falha ABERTA (JSON malformado → exit 0, stdout vazio) · `MSS_RECALL_OFF=1` silencia · sem `memory/` silencia |
| `tests/test_rodizio_partida.py` | mapa mantém 2 blocos por seção e move o resto na ordem · bloco único intocado · "Conexões" intocada · histórico faz prepend datado · conservação byte a byte · index move só `fechada`, mantém `pausada:` e "Fora de escopo" · dry-run não escreve |
| `tests/test_orcamento_contexto.py` | `TETO_MEMORY_TOPO = 6000` substitui os 25 KB · moldes documentam o teto novo e **não** contêm mais "não carrega" fora do trecho da nativa |
| `tests/test_smoke_kit.py` | `hooks.json` registra `recall_memoria.py` em `UserPromptSubmit`; `hooks/README.md` lista 5 hooks |

Fixtures do Whats entram **copiadas** para `tests/fixtures/` (o teste não lê o outro projeto).

## 5. Aplicação no Whats (outra janela, outro repo — fora desta spec, registrada aqui para não perder)

Ordem, cada passo com dry-run mostrado e OK do owner antes do `--aplicar`, e commit por passo:
1. `memoria_indice.py dividir` — 25.421 → ~1.500 bytes na partida (medido na simulação de 2026-09-14:
   topo 1.208 B com palavras raspadas; com frases de gatilho fica um pouco maior).
2. `rodizio_partida.py mapa` — 89.651 → estimativa de 8 a 12 KB (2 blocos por seção); se passar de 6 KB,
   o excesso é o bloco atual e vira edição do owner.
3. `rodizio_partida.py index` — move 13 `fechada`; os 24 `aberta` são decisão do owner.
4. `doctor` para medir o total novo. Meta: ~33 KB ≈ 8 mil tokens por janela (−85%).
5. Fila de conteúdo (sem prazo): 77 `gatilho:` faltando; `CLAUDE.md` 27 KB → 8 KB; reagrupar as
   famílias por gatilho (hoje "Integrações", "Padrões" são assunto, não gatilho — a simulação errou o
   recall de "Confirmar a branch" e "2ª via" por isso).

## 6. Registro

- `CHANGELOG.md` 0.27.0 · `docs/decisoes.md`: "teto do índice do repo é orçamento (6 KB no topo), não
  truncamento; recall passa a ser injetado por hook; MAPA/INDEX têm rodízio mecânico".
- `docs/EVALS.md` caso novo: *quando um teto copiado de outro contexto manda podar conteúdo* — classe
  "premissa não verificada" — guardrail: 3.5 + `test_orcamento_contexto`.
- `hooks/README.md`: 5ª linha da tabela (`recall_memoria.py` · `UserPromptSubmit` · ligado · não
  bloqueia · rede: aponta memória que casou com o prompt).

## Histórico

- 2026-09-14 — pedido inicial era "podar o índice do Whats" (o hook mandou). O owner interrompeu antes da 1ª edição: podar era o sintoma, não o conserto.
- 2026-09-14 — simulação a seco sobre o índice real (tabela de bytes + recall por palavra) antes de qualquer código. Ela expôs dois defeitos de estrutura: famílias por assunto, não por gatilho; palavras raspadas do texto viram lixo. Daí o topo usa frases do `gatilho:`.
- 2026-09-15 — medir a partida inteira mostrou que o índice era 12% (214 KB); a spec cresceu para três mecanismos numa causa raiz só. Rejeitados: teto de 60 KB; índice gerado só do frontmatter.
- 2026-09-15 — aplicada no Whats em janela própria, 3 commits, tudo por script: partida 190.311 → 107.733 bytes (47,6 mil → 26,9 mil tokens); índice 25.549 → 1.436; MAPA 89.651 → 24.430; INDEX 61.399 → 44.042. Hooks confirmados carregando pela junction (canário do recall). Fila de conteúdo: 77 `gatilho:`, `CLAUDE.md` 27 KB, 39 itens abertos.
