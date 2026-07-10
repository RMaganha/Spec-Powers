---
name: precedentes-msig
description: Use ao implementar algo em um projeto MSIG que pode já ter sido resolvido em outro projeto (busca vetorial/RAG, extração de documentos com LLM, conexão SQL Server/Postgres, deploy Azure homolog/produção, rede/proxy corporativo). Antes de desenhar do zero, consulte este catálogo pra saber qual projeto já fez isso e ir olhar a arquitetura de lá.
---

# Catálogo de precedentes entre projetos MSIG

Este é um índice, não a implementação. Cada entrada aponta pra um projeto real — antes de replicar
um padrão, **abra o caminho indicado e leia o código atual**, porque ele pode ter evoluído desde a
última atualização deste catálogo (código muda; este arquivo só diz "olhe aqui").

## Catálogo

| Tópico | Projeto de referência | O que faz | Observação |
|---|---|---|---|
| RAG / busca vetorial | `C:\Ronaldo\_Mitsui\Python\IA Bot Agent\V2 - IA Bot Agent\api\_opcao4` | Usa `pgvector` no Postgres compartilhado (tabelas `rag_documents`, `rag_avaliacao`) | **Não replicar** o Chromadb do projeto antigo (mesma pasta, um nível acima, em `api\`) — ficou obsoleto. `_opcao4` é a evolução. |
| Extração de PDF + multi-LLM | `C:\Ronaldo\_Mitsui\Python\IA Jeday Cosseguro\Azure` | Lê PDF com PyMuPDF, extrai dados via prompts Gemini + GPT | Ver `utils/`, `config/settings.py` e `config/seguradora/` (config por cliente com fallback) pra estrutura geral do pipeline |
| Ambiente/infra corporativa (rede, proxy, Postgres, SQL Server, Azure pipeline) | plugin `mss-spec` — ver `templates/AMBIENTE.md` (copiado pro projeto pelo `/mss-spec:kickoff`) | Fatos fixos + padrões já consolidados num único doc de referência | Use esse arquivo diretamente em vez de reinvestigar do zero |
| Conexão SQL Server — padrão canônico multi-ambiente | `C:\Ronaldo\_Mitsui\Python\Transportes\V2\get_connection.py` | Par Fernet KEY/CIPHERTEXT por base (SSC, MS10=`tkgs_corp`, TRP, OnBase) e ambiente (D0/HML/PRD); `.env` só com `CONEXAO_SQL` + `CONEXAO_SQL_PORTA` | Credencial NUNCA em `.env`. Pares prontos lá — copiar entre projetos é decisão do owner. Portas verificadas: SSC dev `10.170.210.36,1435`; SSC prod `10.170.210.48` |

## Como crescer este catálogo

Toda vez que aparecer um padrão de aplicação novo digno de nota (uma abordagem que valeria a pena
reaproveitar, ou uma evolução que superou uma abordagem antiga), acrescente uma linha na tabela:
tópico, caminho do projeto, o que faz, e uma observação se uma variante for a recomendada e outra
estiver obsoleta. Não precisa de investigação formal toda vez — uma linha já ajuda.
