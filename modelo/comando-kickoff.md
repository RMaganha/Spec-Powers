---
description: Constitui o projeto (greenfield ou brownfield) — entrevista o owner e gera/atualiza o CLAUDE.md
argument-hint: "[ideia em 1 linha, ou aponte para um repo existente]"
disable-model-invocation: true
---

Você vai **constituir este projeto**. NÃO escreva código nesta etapa.

1. Invoque a skill **superpowers:brainstorming**.
2. Se já existe código no repositório, faça primeiro um scan rápido (estrutura de pastas, stack, entrypoints, como roda) e proponha um rascunho do contexto antes de perguntar.
3. Pergunte ao owner **uma coisa por vez** (multiple choice quando der): objetivo em 1 frase · usuários · stack/runtime · como roda (CLI/serviço/porta/container/cron) · tem UI? (se sim, padrão **FastAPI + Jinja** — guias e ações) · integrações externas (sites/APIs) · banco (qual, como conecta) · restrições · critérios de sucesso.
4. Ao final, preencha o **`CLAUDE.md`** (enxuto: Modo de trabalho, Contexto, Mapa de arquivos, Regras críticas), usando o modelo do kit como base.
5. Garanta que `memory/MEMORY.md` exista (índice de memória do projeto, dentro do repo); se não existir, crie vazio a partir do modelo do kit.
6. Garanta que `docs/AMBIENTE.md` exista (referência de ambiente corporativo MSIG — rede, proxy, Postgres, SQL Server, Azure); se não existir, copie do modelo do kit e ajuste os `<...>` específicos deste projeto (nome do banco, recursos Azure). Se o projeto não usa algum desses itens (ex.: sem SQL Server), apague a seção correspondente.
7. NÃO crie ESTADO/ROADMAP/specs agora — só o `CLAUDE.md`, o índice de memória e a referência de ambiente. Features vêm depois com `/nova-feature`.

Ideia/insumo do owner: $ARGUMENTS
