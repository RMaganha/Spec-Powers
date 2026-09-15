<!-- MODELO do TOPO do índice de memória — copie para `memory/MEMORY.md` (dentro do repo do projeto).

     O índice tem DOIS níveis:
     - TOPO (este arquivo): 1 linha por FAMÍLIA de gatilho. Entra em toda janela → teto **6 KB**
       (orçamento de partida — o que se lê antes de qualquer trabalho útil).
     - SUBÍNDICE (`memory/indice/<familia>.md`): 1 linha por memória, aberto SÓ quando a família bate.
       Não tem teto de carga; tem teto de 600 bytes por linha.
     Regra de leitura: na partida lê-se o topo; uma família casou com a situação → abra o subíndice
     ANTES de agir. O hook `recall_memoria.py` faz o casamento por prompt e injeta os ponteiros.

     Cresceu? NÃO pode. Mova: `python <kit>/templates/memoria_indice.py dividir` transforma um índice
     plano em topo + subíndices (dry-run; `--aplicar` grava depois de conferir conservação byte a byte);
     `memoria_indice.py verificar` audita e corrige o N; `memoria_indice.py fila` lista memória sem
     `gatilho:`. (O limite que o Claude Code aplica à pasta NATIVA — 200 linhas, 25 KB — não vale
     para este arquivo: a nativa só guarda um ponteiro pra cá, e este entra pelo `Read`.)

     Cada memória em `memory/` tem este frontmatter:
         ---
         name: slug-curto
         description: 1 linha objetiva — usada pra decidir relevância
         gatilho: quando <condição observável que faz esta memória valer a leitura>
         metadata:
           type: user | feedback | project | reference
         ---
     e corpo curto (para feedback/project: regra/fato + **Why:** + **How to apply:**).
     - Memória superada ganha `obsoleta: <data> — superada por [[slug]]` e SAI do subíndice.
     - Gatilho que é ARQUIVO ("quando editar HTML de aplicação") merece virar também regra path-scoped
       em `.claude/rules/` — o Claude Code carrega sozinho. Ver `templates/rules/`.
     - Falha que já aconteceu não mora aqui: vai pro corpus `docs/EVALS.md`. -->

# Memória do projeto — índice por gatilho

<!-- 1 linha por FAMÍLIA. Gatilho bateu? abra o subíndice da família ANTES de agir. -->

- **<Família — ex.: Ao diagnosticar uma falha>** → [subíndice](indice/<familia>.md) — <N> memórias · quando: <frase 1> · <frase 2>

<!-- memory/indice/<familia>.md:
# <Família>
- **quando <condição observável>** → [Título](../arquivo.md) — <gancho de uma frase> -->
