# 2026-07-28 — análise de projeto existente (`/mss-spec:analise`, v0.14.0)

## Conversamos
O kit funciona bem em projeto novo, mas falha em **projeto que já existe**: ele não tem conhecimento do
que está lá. Pedido do owner: um `/mss-spec:analise` que navegue nos `.py`/`.html`/`.tsx`/`.json`/`.sql` e
leia os docs que às vezes já existem (`CLAUDE.md`, spec, plan) pra montar os artefatos do framework a
partir do real. O projeto-alvo concreto é um **RAG com pgvector** — "tem que entender tudo".

## Pivôs
- **O eixo mudou na 1ª resposta.** Perguntei *onde o destilado mora* esperando escolher entre "preencher
  os artefatos" e "dossiê novo"; o owner respondeu **"1 e 2"** e emendou a restrição que redefiniu a
  feature: o projeto "já tem o compose e etc, **não pode ajustar** ou seja tentar implementar coisa que o
  kit tem, o que pode **parar tudo** e termos que ajustar". A regra **não-destrutiva** deixou de ser
  detalhe de implementação e virou o eixo do comando.
- **UI própria entrou como emenda** ("é em `.html`, tem UI/UX própria que não posso alterar") e ampliou a
  regra pro front: o design system do kit (`FRONTEND.md`/Tailwind/Mantine) **não é aplicado nem sugerido
  como conserto** numa tela que já existe.
- **Specs retroativas: eu recomendava só semear o INDEX**, o owner pediu **"1 e 2 com certeza"** (INDEX
  *e* spec viva). Reconciliado sem criar spec que mente: spec só pros assuntos com **evidência lida na
  fase 2**, com **marca de proveniência** no Histórico e OK do owner; assunto visto por amostragem fica
  só na linha `existente` do INDEX.
- **RAG/pgvector virou item próprio** da leitura focada (chunking → embedding/dimensão → vector store/
  índice `ivfflat|hnsw` → `top_k`/similaridade → prompt → LLM), com ponte pro `/mss-spec:precedentes`.
- **Achado colateral (bug pré-existente):** a **categoria 1 do `upgrade`** sobrescrevia
  `docker-compose.yml`/`Dockerfile` **sozinha** — num brownfield isso substituiria a infra que roda e
  pararia o projeto. A lista "não nasceu do kit" do dossiê virou o **freio**: passa a mostrar o diff e
  perguntar.
- **Autocrítica na revisão:** eu tinha feito o `analise` gravar as camadas reais no `docs/ESTRUTURA.md`,
  que é **categoria 1** — o levantamento seria apagado no próximo upgrade. Corrigido, e daí nasceu a
  fronteira **prescritivo (`ESTRUTURA.md`, dono `upgrade`) × descritivo (`ARQUITETURA.md`, dono
  `analise`)**.
- **2º assunto não emendado:** "perguntar se o projeto segue a arquitetura de rede MSIG ou própria"
  (surgiu porque o owner usou o kit num projeto fora da MSIG e teve que editar na mão) foi pro
  `to-dolist`, respeitando "um assunto por janela".

## Rejeitado
- **Só relatório em tela** (não gravar nada) — o conhecimento evapora ao fechar a janela, que é o problema
  a resolver.
- **Spec viva pra todo assunto detectado** — num projeto grande são dezenas de docs por inferência; spec
  que mente é a pior falha do fluxo.
- **Ler o repo inteiro** — estoura contexto e degrada justo onde importa. Ficou: inventário → leitura
  focada → amostragem, **declarando o que ficou de fora**.
- **Só manifests e docs** (sem abrir código) — não descobre rota, tabela nem integração: metade do valor.
- **Aplicar molde do kit / reorganizar pastas** em brownfield, e **análise semântica profunda** (call
  graph/tipos), e **executar o código** do projeto.

## Fizemos
`commands/analise.md` + `templates/ARQUITETURA.md` (dossiê: o que é · stack · mapa do código · rotas ·
dados · IA/RAG · **não nasceu do kit** · Lacunas); freio no `commands/upgrade.md`; `kickoff` delega o
levantamento; ponteiro no `templates/CLAUDE.md`; `LEIA-ME` + `COMO-FUNCIONA.html` (cartão **C2**,
glossário RAG/pgvector, 19 → **20 comandos**, nav ganhou `mapa`/`mapa-neural` que faltavam); 4 testes
novos → suíte **72 verde**; bump **0.14.0** nos 2 manifestos + CHANGELOG. Commit `c1938f4` na branch
`feature/analise-projeto-existente`.

## Próximo
Integrar a 0.14.0 na `main` e **publicar** — descobrimos no fecho que a `main` local tem **7 commits não
publicados** (0.13.0/0.13.1/0.13.2 + chore de memória): o `git status` dizia "ahead of origin/main", e o
`git fetch` confirmou que o `origin` não tem nada a mais. Sem `git push`, nenhum outro projeto pega o
`analise` nem com `claude plugin marketplace update`. Primeiro uso real: rodar o `/mss-spec:analise` no
projeto de RAG/pgvector.
