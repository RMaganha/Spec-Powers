---
name: project_conversa_gravada_formato
description: Ler a conversa gravada pelo app (.jsonl) por código — a fala que o owner digita no meio do trabalho não é registro `user`, há registros do app que parecem fala, e o filtro de tag da busca não serve pra ler conversa
gatilho: quando escrever ou alterar código que lê a conversa gravada pelo app (o .jsonl de ~/.claude/projects)
metadata:
  type: project
---

Quem lê o `.jsonl` da conversa (`templates/conversa_texto.py`, `templates/memoria_tabela.py`,
`hooks/_transcricao.py`, `hooks/alerta_contexto.py`) precisa saber o que o app grava de fato. Visto em
2026-11-11 nas 62 conversas reais do kit:

1. **A fala que o owner digita enquanto o assistente trabalha não é registro `type: "user"`.** Vem como
   `type: "attachment"`, com `attachment.type: "queued_command"`, `attachment.commandMode: "prompt"`,
   `attachment.origin.kind: "human"` e o texto em `attachment.prompt`. Em 4 de 6 casos não há registro `user`
   correspondente. São as correções de rumo (*"Eu quero uma análise não é para sair desenvolvendo…"*). Quando há
   os dois, a mesma fala entraria duas vezes: conte uma.
2. **Registro `user` que não é fala do owner:** notificação de tarefa (`origin.kind: "task-notification"`,
   `promptSource: "system"`; também vem como `queued_command` com `commandMode: "task-notification"`), mensagem
   de outro ajudante (`origin.kind` diferente de `human`), resumo de compactação (`isCompactSummary: true`),
   `isMeta: true`, e os textos `[Request interrupted by user…]` e `The app was quit while you were working…`.
3. **Registro `assistant` que não é fala:** `isApiErrorMessage: true` e `message.model == "<synthetic>"`
   (`API Error: …`, `No response requested.`).
4. **A gravação de cada ajudante fica à parte**, em `<pasta do projeto>/<id da conversa>/subagents/agent-<id>.jsonl`;
   dentro do arquivo principal, o que é de ajudante vem com `isSidechain: true`.
5. **Não reaproveite o filtro da busca pra ler conversa.** `memoria_tabela._pedido_do_owner` corta qualquer
   `<tag>…</tag>`: serve pra tirar palavras de busca, mas apaga o que o owner escreveu (`<StatusBadge>…`,
   `git switch -c <nome>`) e deixa escapar `<private>` que tenha outra tag dentro. Pra ler: tire primeiro o
   `<private>` (fechado, e também o que ficou sem fechar, até o fim), depois só os blocos que o app põe
   (`<system-reminder>`, `<command-…>`, `<task-notification>`, `<local-command-…>`).
6. **Nome de comando só vale quando o registro É um comando** (o texto começa por `<command-`); citado no meio
   de uma fala ou de um resumo, não é.

**Why:** a 1ª versão do `conversa_texto.py` passou em 15 testes com conversa de exemplo e perdia a fala do owner
nas conversas reais; quem achou foi a revisão independente, rodando o script nos arquivos de verdade (caso F-061).

**How to apply:** antes de dizer pronto, rode o leitor nas conversas reais do projeto e compare a contagem de
falas com o que se vê no app; o teste com conversa de exemplo tem de incluir a fala pela fila, a notificação, o
resumo e o `<private>` com tag dentro. Os dois leitores mais antigos (`memoria_tabela.pedidos_da_conversa` e
`hooks/_transcricao.py`) ainda não olham o anexo de fila. Relacionado: [[project_parse_md_do_kit_descartar_comentario]],
[[project_dogfood_gerador_diff_antes_depois]].
