<!-- MODELO de CLAUDE.md — copie para a RAIZ do projeto novo como `CLAUDE.md` e preencha os <...>.
     Regra de ouro: ENXUTO. Só o que o Claude NÃO infere do código (visão, como roda, convenções, regras).
     Detalhe de feature vai na spec viva por assunto (docs/specs/<assunto>.md); histórico/memória NÃO entram aqui. -->

# IA Bot Agent - Whats (`agent_bot` / Miti.AI Agent V3-V4) — agente LLM que atende corretores da Mitsui sobre a base de conhecimento e escala pra especialista humano quando não dá conta

## Modo de trabalho (nunca violar)
- **Idioma**: responda **sempre em português (pt-BR)** — mensagens, docs e relatórios gerados. Vale mesmo quando o gatilho for um slash-command sem texto (não caia no inglês por padrão).
- **Base do projeto (ler PRIMEIRO)**: se existir um `projeto.md` na raiz, leia-o antes de qualquer outra coisa — é a base/contexto fundamental do projeto. Se não existir, siga normalmente.
- **Não codar antes do meu OK explícito**: diagnosticar → plano curto → esperar OK → verificar no real (nada de "análise de memória").
- **Não inventar fatos concretos**: caminhos, paths de deploy, hosts, portas, nomes de recurso/container, estrutura de pastas — use só o que está no repo/`projeto.md` ou o que eu confirmar. Na dúvida, deixe genérico, marque `<a confirmar>` ou pergunte; nunca chute um valor concreto (um caminho errado é pior que uma lacuna).
- **Comando `/mss-spec:<x>` referenciado NÃO é inexistente — leia o arquivo**: → texto inteiro em [`docs/MODO-DE-TRABALHO.md`](docs/MODO-DE-TRABALHO.md) — leia antes de rodar ou citar um `/mss-spec:<x>`.
- **Siga as skills do superpowers à risca** (brainstorming, test-driven-development, verification-before-completion, systematic-debugging, requesting-code-review). Precisão acima de velocidade.
- **Assuma o papel de especialista sênior do domínio da tarefa**: UI/layout → especialista sênior em UI/UX; código → engenheiro sênior; banco → DBA sênior; e assim por diante para segurança, infra, etc. (a lista é aberta — infira o domínio). Anuncie brevemente o papel assumido, trabalhe sob essa ótica até concluir/ter o meu OK, e então volte ao papel padrão: **arquiteto/engenheiro sênior de desenvolvimento**. Entrega genérica sai pior que a de um especialista.
- **Nível de cerimônia** → texto inteiro em [`docs/MODO-DE-TRABALHO.md`](docs/MODO-DE-TRABALHO.md) — leia ao decidir quanto planejar.
- **Git — branch da principal + local-only**: → texto inteiro em [`docs/MODO-DE-TRABALHO.md`](docs/MODO-DE-TRABALHO.md) — leia antes de abrir branch, commitar, fazer merge ou push. Comandos git: sequência inteira, um passo numerado por bloco.
- **Um assunto por janela**: cada janela de chat trata **um assunto só**. Se no meio de uma tarefa surgir um 2º assunto não relacionado, **pare e alerte** — não faça fora de hora nem misture na branch atual: ofereça registrar no to-dolist (`/mss-spec:to-dolist adicionar <assunto>`), sugira **fechar o escopo atual** e abrir **uma nova janela** pra ele. É **alerta, não trava**: se eu mandar seguir assim mesmo, siga.
- **Mapa de contexto (ler PRIMEIRO na partida)**: ao abrir a janela, **antes** de MEMORY/INDEX, leia `docs/superpowers/MAPA.md` — o ponto de partida anti-amnésia (curto, 1 tela): **onde estamos** · **próximo passo** · **conexões** com outros projetos MSIG (o que este projeto integra em runtime — ex.: sistemas que trabalham juntos). Diz de onde retomar sem reler tudo. Reconcilie/atualize com `/mss-spec:mapa`; ao mexer numa **integração** com outro projeto, atualize a seção **Conexões** (declare do código real, nunca invente).
- **Índices do projeto**: no início, leia `memory/MEMORY.md` (topo por **gatilho**, 1 linha por família; família bateu → abra `memory/indice/<f>.md` **antes de agir**) e `docs/superpowers/INDEX.md` (tarefas). Ambos são só índices (1 linha por item). Abra o arquivo individual só quando o índice apontar relevância; nunca leia a pasta inteira. **Ao mexer num assunto que já existe, abra antes a spec viva dele em `docs/specs/<assunto>.md` (linkada pelo INDEX) — a seção "Estado atual" diz como o comportamento está HOJE.** Fallback: Grep/Glob sobre `docs/`.
- **Diário de sessão (sob demanda, não na partida)**: `memory/DIARIO.md` é o índice datado do "o que conversamos/decidimos" (camada mais funda que os fatos). Quando reabrir um assunto e precisar do histórico da conversa, leia esse índice e abra **só** o `memory/sessions/<data>-<assunto>.md` relevante — **nunca a pasta inteira** (é o que mantém o custo de tokens baixo). Gravado pelo `/mss-spec:memory capturar`.
- **`<private>` na memória**: trecho marcado `<private>…</private>` na conversa **nunca** é gravado em memória/diário/decisões versionados — é o jeito de marcar segredo/ruído que não deve durar. O `/mss-spec:memory capturar` filtra `<private>` antes de rascunhar qualquer coisa.
- **Plano de teste base (anti-regressão)**: → texto inteiro em [`docs/MODO-DE-TRABALHO.md`](docs/MODO-DE-TRABALHO.md) — leia antes de declarar qualquer coisa pronta.
- **Pré-vôo de ambiente (doctor)**: → texto inteiro em `.claude/rules/deploy-e-ambiente.md` (carrega sozinho ao tocar `Dockerfile`, `docker-compose*.yml`, `azure-pipelines*.yml`…).

## Contexto

> Levantado do código pelo `/mss-spec:analise` em 2026-07-28, **reconciliado em 2026-07-31** (runtime, git, testes e os artefatos de deploy). **Dossiê completo: [docs/ARQUITETURA.md](docs/ARQUITETURA.md)** — leia antes de mexer em área que você não conhece.

- **Stack/runtime:** Python 3.10 (imagem `python:3.10-slim`). Flask + flask-cors, `openai`, `psycopg2-binary`, `requests`, `python-dotenv`. **Sem** langchain/fastapi/pandas/chromadb — isso é do Sistema A legado, que vive em outro projeto.
- **Infra:** **MSIG** — rede `mitiai_network`, proxy, CA do FortiGate (`certs/corp-ca.pem`), SQL corporativo (`docs/AMBIENTE.md`).
- **Como roda:** → texto inteiro em `.claude/rules/deploy-e-ambiente.md` (carrega sozinho ao tocar `Dockerfile`, `docker-compose*.yml`, `azure-pipelines*.yml`…).
- **Homologação (Azure):** → texto inteiro em `.claude/rules/deploy-e-ambiente.md` (carrega sozinho ao tocar `Dockerfile`, `docker-compose*.yml`, `azure-pipelines*.yml`…).
- **UI:** → texto inteiro em `.claude/rules/ui-propria.md` (carrega sozinho ao tocar `web/**`, `**/*.html`).
- **Integrações externas:** Chatwoot (handoff L2, com webhook de volta) · CRM MSIG Cobrança/Emissão (`www4.ms-seg.com.br`, host interno) · n8n (workflow de Cotação via Chat, com callback) · Portal MSIG (identidade via `?ID=<base64>`) · canal WhatsApp (posta em `/chat` com `canal="whatsapp"`; o cliente do WhatsApp **não vive neste repo**). Detalhe e direção do dado em [docs/superpowers/MAPA.md](docs/superpowers/MAPA.md).
- **Banco:** → texto inteiro em `.claude/rules/banco.md` (carrega sozinho ao tocar `**/*.sql`, `sql/**`, `persistencia/**`).
- **Testes:** → texto inteiro em `.claude/rules/testes.md` (carrega sozinho ao tocar `tests/**`, `docs/superpowers/PLANO-TESTE.md`).
- **Versionamento:** → texto inteiro em `.claude/rules/deploy-e-ambiente.md` (carrega sozinho ao tocar `Dockerfile`, `docker-compose*.yml`, `azure-pipelines*.yml`…).
- **Estado:** `<a confirmar>` — o repo tem sinais de produção (integrações reais, `restart: unless-stopped`, logs de conversa de jun/2026) e de protótipo local (PG em `host.docker.internal`, `.bat` de duplo-clique, `MITI_DEV_AUTH`). Ver seção 8 do dossiê.

## Mapa de arquivos
- Movido para [`docs/MAPA-DE-ARQUIVOS.md`](docs/MAPA-DE-ARQUIVOS.md) em 2026-09-23: onde cada arquivo e pasta mora — abra quando precisar achar algo (o dossiê completo é o `docs/ARQUITETURA.md`).

## Regras críticas (nunca violar) — cada uma nasce de um bug ou decisão real
1. **Registro/memória/notas NUNCA em um arquivo `CLAUDE.md`** (ele é instrução sempre-ativa e polui o contexto). Memória persistente = pasta `memory/` deste projeto (dentro do repo, versionada com `MEMORY.md` como índice — NÃO em `~/.claude/projects/<proj>/memory/`); estado/handoff = plan files do superpowers.
2. Nunca commitar `.env` nem segredos; nunca hardcode de credencial.
3. **A UI deste projeto é PRÓPRIA e INTOCÁVEL** → texto inteiro em `.claude/rules/ui-propria.md` (carrega sozinho ao tocar `web/**`, `**/*.html`).
4. **Estrutura em camadas — migração em curso desde 2026-07-28.** → texto inteiro em `.claude/rules/estrutura-em-camadas.md` (carrega sozinho ao tocar `**/*.py`).
5. **Segurança (secure-by-default)** → texto inteiro em `.claude/rules/seguranca.md` (carrega sozinho ao tocar `apis/**`, `chat_server.py`, `services/**`).
6. **Spec viva não pode mentir** (`docs/specs/<assunto>.md`): a seção "Estado atual" reflete sempre o comportamento de HOJE. Toda `feat` cria/atualiza a spec do assunto; todo `bugfix`/`refactor` que **alterar** um comportamento descrito numa spec existente atualiza o "Estado atual" + 1 linha no "Histórico". Spec desatualizada faz o assistente reintroduzir bug ao ler valor velho numa tarefa futura.
7. **Logging — estado misto, declarado.** → texto inteiro em `.claude/rules/logging.md` (carrega sozinho ao tocar `**/*.py`).
8. **Nunca tocar o que é do RAG em produção.** → texto inteiro em `.claude/rules/banco.md` (carrega sozinho ao tocar `**/*.sql`, `sql/**`, `persistencia/**`).
9. **Segredo e ambiente:** o `.env` desta pasta **nunca** é aberto, copiado ou impresso — as 45 chaves que o código lê estão documentadas por **nome** em `.env.example` e na seção 2 do dossiê. `MITI_DEV_AUTH=1` liga um caminho de autenticação provisório que o próprio código marca como **risco de segurança ativo** (Pending #80): não usar como solução, não propagar.

<!-- Mantenha este arquivo curto. Se uma seção crescer demais, mova o detalhe para a spec viva do assunto
     (docs/specs/<assunto>.md) ou para um doc em docs/, e deixe aqui só um ponteiro. -->
