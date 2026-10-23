---
name: project-regra-por-tipo-carrega-ao-ler
description: Regra em .claude/rules/ com paths: entra na janela quando o assistente LÊ um arquivo que casa — não quando ele CRIA um arquivo novo nem quando edita sem ter lido; fato do projeto nunca fica atrás desse gatilho
gatilho: quando um desenho depender de uma regra de .claude/rules/ com paths: entrar na janela
metadata:
  type: project
---

Medido nas 76 conversas do Whats (2026-10-23), só nas que aconteceram depois de as regras existirem
(2026-09-23): toda **leitura** de arquivo existente que casava com o `paths:` carregou a regra (deploy,
camadas, logging, segurança, tela: 0 falhas). **Criar** arquivo novo ou **editar sem ter lido** antes não
carregou: `banco.md` faltou em 5 conversas que criaram arquivos `sql/`, `testes.md` em 2.

Consequências que viraram desenho na 0.42.0:
- **fato** que o owner cita em conversa (infra, como roda, ambiente) fica no `## Contexto` do `CLAUDE.md`, por
  extenso — nunca atrás de gatilho de arquivo. Foi isso que fez o Whats "perder a memória" (F-040): os fatos de
  infra foram para `deploy-e-ambiente.md`, que entrou em 4 de 76 conversas;
- `.claude/rules/` fica só com **como escrever** aquele tipo de arquivo;
- o buraco do "criar" é fechado pelo `hooks/regra_antes_de_gravar.py`, que nega uma vez por sessão a gravação
  com o texto da regra no motivo.

**How to apply:** ao propor mover algo pra `.claude/rules/`, pergunte "o owner citaria isso sem abrir arquivo
nenhum?" — se sim, é fato e fica no `CLAUDE.md`. Como medir de novo: [[reference-historico-mostra-o-que-carregou]].
Spec: `docs/specs/regras-do-kit-pelo-plugin.md`.
