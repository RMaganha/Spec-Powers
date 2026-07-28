# Análise de projeto existente (`/mss-spec:analise`) — spec viva

<!-- Spec viva por assunto: "Estado atual" reflete como o comportamento está HOJE; o Histórico é a narrativa. -->

## Estado atual

O kit tem uma porta de entrada para **brownfield**: `/mss-spec:analise` (`commands/analise.md`, `disable-model-invocation`). Ele lê o repositório em **2 fases** — (1) inventário barato: árvore de pastas, contagem por extensão (`.py`, `.html`, `.tsx`, `.json`, `.sql`…), manifests, docs pré-existentes (`README`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, specs/planos antigos) e `git log`; (2) leitura focada: entrypoints, rotas/endpoints (marcando as de integração), dados (`.sql`/models/conexão), config, UI e — quando existe — o **pipeline de RAG** inteiro (chunking → embedding/dimensão → vector store/`pgvector`, índice `ivfflat`/`hnsw` → retrieval/`top_k` → prompt → LLM), apontando `/mss-spec:precedentes`. O resto vai por **amostragem**, e o que ficou de fora é **declarado** (sem corte silencioso). Só as lacunas são entrevistadas.

O resultado é destilado em: o dossiê **`docs/ARQUITETURA.md`** (de `templates/ARQUITETURA.md` — **descritivo**; as camadas **reais** do projeto vivem na seção *Mapa do código* dele), o **Contexto/Mapa de arquivos** do `CLAUDE.md`, `docs/superpowers/MAPA.md` (Onde estamos + Conexões do código real), o **`INDEX.md`** com 1 linha `existente` por assunto detectado, e `docs/specs/<assunto>.md` **só** para assuntos com evidência lida na fase 2 (com marca de proveniência e após OK do owner) — assunto visto por amostragem fica na linha do INDEX, sem spec.

**A regra dura é ser não-destrutivo:** a análise escreve **somente** artefatos de doc/memória do kit. Nunca toca em infra (`docker-compose.yml`, `Dockerfile`, deploy), código (`.py`/`.tsx`/`.sql`, `config/logging.py`, `utils/get_connection.py`, manifests), **UI própria** (HTML/CSS/JS do projeto — o design system do kit não é aplicado nem sugerido como conserto) nem `.env`. Onde o projeto já tem o que o kit também traria, o molde **não é aplicado**: o arquivo entra na tabela **"Pré-existente — não nasceu do kit"** do dossiê, com a divergência descrita, e a decisão é do owner (**padrão: manter o do projeto**). Tudo que é lido é tratado como **dado, não instrução** — doc do projeto que contradiz o código não é resolvido sozinho, é perguntado.

Essa mesma lista virou o **freio do `/mss-spec:upgrade`**: a categoria 1 dele (que sobrescrevia `docker-compose.yml`/`Dockerfile` sozinha, o que num brownfield mataria a infra que roda) passa a **mostrar o diff e perguntar** quando o arquivo está listado como "não nasceu do kit". Costuras: `kickoff` (passo brownfield delega ao `analise` e preserva o pré-existente), `templates/CLAUDE.md` (mapeia o dossiê), `LEIA-ME.md` e `COMO-FUNCIONA.html` (cartão C2 + glossário RAG/pgvector).

**Fora de escopo:** executar o código do projeto · aplicar molde do kit (é `kickoff`/`upgrade`, com OK) · spec viva para assunto só amostrado · análise semântica profunda (call graph/tipos) · reorganizar pastas.

## Histórico

- 2026-07-28 — criado: `/mss-spec:analise` como porta de entrada do brownfield (2 fases de leitura → dossiê `docs/ARQUITETURA.md` + artefatos do kit), **não-destrutivo por regra** (motivo: o owner tem projeto real com infra e UI/UX própria em `.html` que não pode ser alterada — aplicar molde do kit "pararia tudo e teríamos que ajustar"). No caminho, destampou e corrigiu um risco pré-existente: a categoria 1 do `upgrade` sobrescrevia infra de brownfield sozinha. Alvo real do owner é RAG/pgvector, então a leitura focada ganhou esse pipeline como item próprio.
