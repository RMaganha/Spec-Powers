<!-- Índice de tarefas ABERTAS do próprio kit mss-spec (dogfood). 1 linha por tarefa, mantido à mão.
     Lido na PARTIDA — por isso só o que está vivo + a seção anti-re-litígio 'Fora de escopo'.
     Tarefa fechada sai daqui pro docs/superpowers/INDEX-historico.md (lido sob demanda).
     Nomes em linguagem simples (os do owner) — nada de apelido-código. -->

# Índice de tarefas — mss-spec

## A fazer (ordem)
5. upgrade — sincroniza projeto existente com a evolução dos templates — **em andamento** (sem commit)

## Fora de escopo (não fazer)
Key Vault direto (escolhemos variável de ambiente) · profiles multi-nuvem · generators no lugar de templates · registry / capabilities / catálogo de arquiteturas · policies como camada nova · feature matrix · hooks pre-commit bloqueantes · `modo` mexendo no `effortLevel` · **na análise de projeto existente:** spec viva pra assunto visto só por **amostragem** · aplicar molde do kit ou reorganizar pastas em brownfield · análise semântica profunda (call graph/tipos) · executar o código do projeto · **na cerca da âncora:** vigiar Bash/PowerShell (heurística de shell é furada e dá falso positivo) · vigiar leitura de outro projeto (é o objetivo do `precedentes`) · check "a cerca está ativa?" no `doctor` · **no mapa-neural:** Django (`path()`/`re_path()`), `add_url_rule` e resolver o `url_prefix` de Blueprint no registro (o caminho sai como está escrito no decorator) · filtro de placeholder no `to-dolist` (item de verdade cita `<algo>`) · **seção declarativa `## Camadas` no `MAPA.md`** e **ler intenção em prosa do `CLAUDE.md`** (quem declara "isto não é o projeto" é o `.gitignore` ou o `--ignorar`) · **no divergir:** integrar o stack npm `adhd-agent` (a ideia vive em prosa + subagentes do Agent tool; frames não viram configuração) · **na anatomia:** inferência automática de risco (classe de risco é metadado curado, não julgamento de máquina) e o painel virar fonte de leitura do assistente (visual é pro humano; o assistente lê MAPA/INDEX/memória)


> **Descartado em evals/context engineering (0.19.0):** **harness/plataforma de eval** que roda modelo e julga resposta (lento, não-determinístico; validação de comportamento ao vivo é do humano — a mesma razão do smoke visual) · **tipo novo de memória** pra premissa derrubada e pra acerto (reusam `feedback_*`) · **premissas explícitas fora do `nova-feature`** (`analise`, `kickoff`, regra sempre-ativa no `CLAUDE.md`) · **embeddings/busca semântica** sobre a memória (o gatilho é texto casado por leitura, não vetor) · `release` **bloquear** por caso aberto (⚠ basta).
> **Reaberto pelo mapa mental (F2):** `knowledge-graph` e `dependency-graph` saíram desta lista — o `/mss-spec:mapa-neural` cobre a fatia **leve/heurística** (memórias e arquitetura como dimensões do mapa mental do projeto). Grafo semântico profundo (análise de tipos/chamadas) segue fora de escopo.

> **SOM/ML de verdade descartado (v0.11.0):** o `mapa-neural` **não** vira um self-organizing map (vetor de features + treino) — deps pesadas, resultado não-determinístico, ganho duvidoso com ~50 itens. A camada "neural" fica na **fatia leve/heurística**: datas (mtime) + associações **determinísticas** (memória↔memória por `[[links]]`; spec↔código por `Arquivos tocados`), nunca inventadas.
