<!-- MODELO de índice de memória — copie para `memory/MEMORY.md` (dentro do repo do projeto).

     Regras deste índice:
     - Agrupe por FAMÍLIA DE GATILHO (quando abrir), NUNCA por tipo nem por data. O índice não
       existe pra dizer *o que a memória é* — existe pra dizer *quando abri-la*. Descrição não
       dispara recall; condição observável dispara.
     - Só ponteiros de 1 linha, começando pelo gatilho:
         - **quando <condição observável>** → [Título](arquivo.md) — <gancho curto>
     - TETO: **200 linhas e 25 KB**. É o mesmo limite que o Claude Code aplica ao índice de
       auto-memory — acima dele o excedente **nem carrega**. Estourou? funda linhas parecidas e
       pode as mortas (a skill `anthropic-skills:consolidate-memory` ajuda).
     - Memória superada ganha `obsoleta: <data> — superada por [[slug]]` no frontmatter e **sai
       do índice** (o arquivo fica, pra não perder a narrativa).

     Cada linha aponta um arquivo em `memory/` com este frontmatter:
         ---
         name: slug-curto
         description: 1 linha objetiva — usada pra decidir relevância
         gatilho: quando <condição observável que faz esta memória valer a leitura>
         metadata:
           type: user | feedback | project | reference
         ---
     e corpo curto (para feedback/project: regra/fato + **Why:** + **How to apply:**).

     - Linke memórias relacionadas com [[slug-do-outro-arquivo]].
     - Gatilho que é **arquivo** (ex.: "quando editar HTML de aplicação") merece virar também
       regra path-scoped em `.claude/rules/` — aí o Claude Code carrega sozinho, sem depender de
       alguém lembrar. Ver `templates/rules/`.
     - Falha que já aconteceu **não** mora aqui: vai pro corpus `docs/EVALS.md` (caso + guardrail
       + teste). Este índice é o que ainda vale; aquele é o que já custou caro. -->

# Memória do projeto — índice por gatilho

## <família de gatilho — ex.: Na partida e ao escolher o ritual>
- **quando <condição observável>** → [Título](arquivo.md) — <gancho de uma frase>
