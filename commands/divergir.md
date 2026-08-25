---
description: Divergência antes de convergir — subagentes isolados (1 frame cada) geram abordagens; a janela critica, pontua e marca armadilhas. Anti-ancoragem pra decisão de design aberta e cara de reverter
argument-hint: "[decisão ou problema a divergir]"
disable-model-invocation: true
---

Divergir: **$ARGUMENTS**

O problema que este comando ataca: o raciocínio linear **ancora na primeira resposta** que produz e segue essa linha até o fim — as "2-3 abordagens" viram três variações da mesma resposta de manual. A correção é **mecânica**, não prometida num prompt só: gerar em ramos que não se veem, criticar num passo separado. (Ideia do repositório `adhd` de uditakhourii, reimplementada em prosa — o stack npm foi rejeitado; ver `docs/decisoes.md` 2026-08-25.)

## Gate de pré-voo (só rode se os 3 valerem)

1. **Decisão aberta** — 2+ arquiteturas viáveis e **nenhum precedente decide**. Se outro projeto MSIG já resolveu, o `/mss-spec:precedentes` manda e **reuso vence divergência** — não gaste 10 chamadas reinventando o que a casa já tem.
2. **Cara de reverter** — errar custa migração, quebra de contrato (API que outro sistema consome, esquema de banco, mecanismo central) ou retrabalho grande. CRUD com padrão existente, tela (o `docs/FRONTEND.md` decide) e kickoff **não** qualificam.
3. **Owner ciente do custo** — ~10 chamadas de agente, **5-10× uma resposta direta**. Se você (assistente) auto-propôs a partir do `nova-feature`, anuncie o custo e **espere o sim** antes de disparar.

## Fase 1 — divergir (ramos isolados)

Dispare **3-5 subagentes em paralelo** (Agent tool), **um frame por subagente**, prompts independentes — **nenhum ramo vê o outro**: o isolamento é o que mata a ancoragem. Cada subagente recebe o problema + seu frame e devolve **3-5 abordagens em rascunho** (2-4 frases cada), **sem julgar viabilidade** (o julgamento é da fase 2; misturar as fases devolve a ancoragem).

Frames (escolha os mais **distantes** do problema; vocabulário e postura distintos):
- **inversão** — "como garantir que isso fracasse?", depois negue cada resposta;
- **plantonista às 3h** — o que não pode te acordar? projete pra operação mínima;
- **orçamento $0 / $∞** — os dois extremos quebram o meio-termo ancorado;
- **auditor/regulador** — provável, rastreável, recusável;
- **concorrente** — como um adversário atacaria ou faria melhor?;
- **leigo (criança de 10 anos)** — a pergunta ingênua que ninguém fez.

## Fase 2 — focar (a janela é o crítico)

Reúna tudo e faça o papel **oposto** ao dos geradores: **agrupe** por abordagem de fundo (ideias iguais com nomes diferentes são uma só) · **pontue** novidade × viabilidade × encaixe no projeto · marque em **cada grupo** a **armadilha sedutora** — por que a ideia bonita quebraria *aqui* (é onde mora o maior ganho medido pelo original). **Aprofunde as top-2** em esboço acionável.

## Saída

Tabela curta (**abordagem · frame de origem · pontos · armadilha**) + as top-2 esboçadas, com a sua recomendação. Este comando **não grava nada**: o design segue o fluxo normal do `nova-feature` (premissas com fonte, OK do owner antes de código, spec viva).
