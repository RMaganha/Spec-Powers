---
name: project-dados-de-outros-projetos-fora-do-repo-do-kit
description: Dado gerado a partir das conversas ou dos arquivos de outros projetos (gabarito com pedidos reais do owner, tabela de teste, lotes) nunca entra no repositório do kit — só o roteiro que o gera
gatilho: quando guardar no repositório do kit algo gerado a partir de conversas ou arquivos de outros projetos (gabarito, tabela de teste, lotes, amostras de pedidos)
metadata:
  type: project
---

Em 2026-11-10, ao guardar o teste de mesa da memória em tabela, tentei copiar para `docs/analise/` os dados
gerados (pedidos reais do owner no Whats, Transportes e MSS-UTILS, a tabela de teste e as escolhas dos
ajudantes). A proteção do app **barrou** a cópia; não contornei. O kit é um repositório publicado.

**Why:** esses dados carregam conteúdo dos outros projetos (pedidos, nomes de ambiente, trechos de anotações). A
regra crítica 2 já veta dado pessoal e segredo em tudo que é versionado; um `.gitignore` sozinho não protege de
um `git add` descuidado.

**How to apply:** no repo do kit entram **os roteiros** (`docs/analise/2026-11-10-teste-de-mesa/*.py`) e **os
números** no dossiê; os dados ficam fora (pasta temporária ou pasta do usuário) e se regeneram com o roteiro.
A pasta de roteiros tem as extensões de dado barradas no `.gitignore`. Vale o mesmo para a tabela de memória
(`~/mss-spec/memoria.sqlite3`): nunca dentro de um repositório. Parente de [[feedback_projeto_ativo_read_only]].
