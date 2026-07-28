<!-- MODELO de ARQUITETURA.md — o DOSSIÊ do projeto que já existia antes do kit.
     Preenchido pelo `/mss-spec:analise` a partir do código REAL; regenerável rodando de novo.

     Fronteira com os vizinhos (não confundir):
       - `docs/ESTRUTURA.md`  = convenção PRESCRITIVA do kit (onde arquivo novo nasce).
       - este arquivo         = retrato DESCRITIVO do que o projeto É hoje (inclusive quando foge da convenção).
       - `docs/superpowers/MAPA.md` = onde estamos AGORA (volátil, 1 tela); aqui é o retrato estrutural.

     Regra de ouro: **nada inventado**. O que não deu pra inferir do repo vai pra seção "Lacunas"
     como pergunta ao owner — nunca como afirmação. Caminho/host/porta chutado é pior que lacuna. -->

# Arquitetura — <Projeto>

> Dossiê derivado do código por `/mss-spec:analise` em `<data>`. **Descritivo, não prescritivo:**
> descreve o que existe, inclusive o que foge da convenção do kit. Confirmado pelo owner: `<sim | parcial | não>`.

## 1. O que é
- **Propósito:** <1-3 frases, inferido do código/README e confirmado pelo owner>
- **Usuários / quem consome:** <humano via UI · outro sistema via API · job agendado>
- **Estado:** <em produção | homologação | protótipo>  — evidência: <onde isso aparece no repo>

## 2. Stack e como roda
- **Runtime/linguagem:** <ex.: Python 3.11 — evidência: `pyproject.toml`>
- **Dependências-chave:** <libs que definem a arquitetura (framework web, ORM, cliente de LLM…)>
- **Entrypoint:** <arquivo> — <o que ele levanta>
- **Como sobe:** <comando/compose/serviço — SÓ o que está documentado ou no repo>
- **Configuração:** <`.env`/settings — quais chaves o código realmente lê>

## 3. Mapa do código (real)
<!-- Uma linha por pasta/módulo relevante: caminho — responsabilidade observada. Do REAL: se o
     projeto é achatado ou usa outra nomenclatura, registre como está (a divergência vai na seção 7). -->
- `<caminho>` — <responsabilidade>

## 4. Rotas e endpoints
<!-- Extraído dos decorators/registros de rota. Marque quais são de INTEGRAÇÃO (outro sistema chama)
     — é o insumo do /mss-spec:seguranca (authz/Bearer) e da seção Conexões do MAPA. -->
| Método | Rota | O que faz | Arquivo | Integração? |
|---|---|---|---|---|
| <GET> | `</caminho>` | <...> | `<arquivo>` | <sim/não> |

## 5. Dados
- **Banco:** <qual — evidência no código/config>
- **Como conecta:** <módulo de conexão · credencial via env/outro>
- **Tabelas/esquema:** <o que aparece em `.sql`/migrations/models>
- **DDL versionada?** <sim (`sql/NN_*.sql`) | não — como o esquema é criado hoje>

## 6. IA / RAG (só se o projeto tiver)
<!-- Apague a seção se não se aplica. Nada de valor default chutado: se o top_k/dimensão não
     está no código, é Lacuna. -->
- **Provedor/modelo de LLM:** <...> · **modelo de embedding:** <...> · **dimensão:** <...>
- **Vector store:** <ex.: Postgres + extensão `vector` (pgvector) | outro> — tabela `<nome>`, índice `<ivfflat|hnsw|nenhum>`
- **Ingestão:** <origem dos documentos → chunking (tamanho/overlap) → embedding → gravação>
- **Retrieval:** <top_k · métrica de similaridade · reranking/filtro · como o contexto entra no prompt>
- **Prompts:** <onde vivem (arquivo/constante/banco)>
- **Precedente MSIG:** rode `/mss-spec:precedentes` — RAG/busca vetorial já foi resolvido em outro projeto.

## 7. Pré-existente — **não nasceu do kit**
<!-- A seção mais importante do dossiê: o que o projeto JÁ TINHA e que o kit também traria.
     Registrar aqui = o molde do kit NÃO foi aplicado, e o /mss-spec:upgrade passa a PERGUNTAR
     antes de sobrescrever esses arquivos (a categoria 1 dele é automática por padrão).
     Formato: caminho — o que é — divergência em relação ao molde do kit — decisão do owner. -->
| Arquivo/área | O que é hoje | Divergência com o molde do kit | Decisão do owner |
|---|---|---|---|
| `<caminho>` | <...> | <...> | <manter (padrão) \| avaliar depois> |

**Padrão é manter o do projeto.** Nenhuma linha desta tabela é "pendência de conserto".

## 8. Lacunas (o que NÃO sei)
- **Não deu pra inferir:** <pergunta ao owner — 1 linha cada>
- **Não foi lido (amostragem):** <pastas/arquivos que ficaram fora da leitura focada, e por quê>

<!-- Regenerável: rode /mss-spec:analise de novo. Ele reconcilia sem apagar o que o owner escreveu. -->
