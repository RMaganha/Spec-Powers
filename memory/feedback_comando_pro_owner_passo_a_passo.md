---
name: feedback_comando_pro_owner_passo_a_passo
description: Comando que o OWNER vai rodar (git sempre; e qualquer outro) sai em passo numerado — título em negrito dizendo o que faz, o comando sozinho num bloco bash logo abaixo, e a linha do que conferir na saída; um comando por bloco
gatilho: quando for passar ao owner um comando git (ou qualquer comando) pra ele rodar no terminal
metadata:
  type: feedback
---

O owner pediu, com um print de exemplo (2026-09-23, *"é de suma importância todos os comandos git deve ser
nesse estilo do print, dizendo o que é e o que faz e o git abaixo"*), que todo comando passado a ele saia assim:

**1. Criar a branch dos documentos de hoje**

```bash
git checkout -b docs/deploy-azure-prd-fluxo
```

**2. Commitar**

```bash
git commit -F "<arquivo da mensagem>"
```

Confira que a saída diz `3 files changed`.

Regras do formato:
- **passo numerado** com **título em negrito em linguagem simples** dizendo o que o comando faz (não o nome do
  comando): "Voltar para a main", "Trazer a branch para a main", "Conferir que a dev tem tudo o que a main tem";
- o comando **sozinho** num bloco ` ```bash ` logo abaixo — **um comando por bloco** (o app põe botão Run em cada
  um); nunca vários comandos num bloco só, nem `&&` encadeando passos que o owner precisa acompanhar;
- depois do bloco, quando houver: **o que conferir na saída** ("Confira que a saída vem vazia") ou **o que fazer
  se algo abrir** ("Se abrir um editor pedindo mensagem de merge, só salve e feche");
- a sequência inteira na ordem de execução, inclusive o passo de voltar pra branch de trabalho no fim.

**Why:** o owner executa os comandos de publicação (push em dev/prod é ato dele — [[feedback_publicacao_e_ato_do_owner]]);
comando solto num parágrafo ou vários num bloco só é onde ele erra a ordem ou não sabe o que conferir.

**Reincidiu (2026-10-15, chat do kit, assunto azure):** fechei uma entrega com *"merge e push"* sem os
comandos; o owner: *"preciso do comando git para fazer o merge isso já está no plugin, não faz sentido não
ter vindo!"*. E um erro da mesma família: pus `/mss-spec:azure-prd` — que se digita **no chat do Claude** —
num bloco ` ```bash `, junto de `az version`; o owner achou que era comando de terminal. Regras somadas:
- **comando do chat** (`/mss-spec:<x>`) **nunca** vai em bloco de terminal: diga *"digite no chat:"*;
- pedido de **rodar de novo** comandos já passados: diga que são **os mesmos** e repita o passo a passo
  inteiro (*"Não entendi eu não juntei nada"*, 2026-10-21).

**How to apply:** vale em toda resposta que entrega comando pro owner rodar — no fecho de feature, no release, no
merge/push, e na mensagem pronta pra outra janela. Mora também no `templates/CLAUDE.md` (regra sempre-ativa) com a
frase-chave travada em `tests/test_orcamento_contexto.py`. Relacionada: [[feedback_estilo_resposta_direto]].
