# 2026-09-24/25 — um item por janela conta por chat (0.34.0)

**Conversamos:** o owner colou o print do bloqueio no Whats — *"novamente hook bloqueando os comandos,
nunca sei quando devo usar ou se posso abrir um chat novo"*. O `/mss-spec:nova-feature Roteiro Azure
Banco Produção` num chat NOVO foi bloqueado por 6 features abertas em outros chats; ele vinha tirando o
comando do prompt pra conseguir trabalhar. Escolheu, entre "por chat", "por projeto com mensagem
melhor" e "deixar como está", **por chat**.

**Pivôs:**
1. de "uma feature aberta por projeto" para "uma por chat" (`session_id`): o dano do F-022 é a mesma
   janela absorvendo outro assunto; feature aberta de outro chat vira aviso + worktree;
2. testando com o prompt real (comando + parágrafos), o texto todo virava nome da feature → o nome é
   o resto da linha do comando;
3. 1ª revisão: casamento por pedaço de texto (`ui` em `guia`, v1 fechada encerrando v2 aberta, chat
   preso depois de fechar a própria) → palavra inteira + "foto do INDEX" na abertura;
4. 2ª revisão: a foto atribuía ao chat a linha do vizinho (prendia e deixava assumir a feature do
   outro) → tirei a foto: ligação só pelo nome; sem linha, "nada aberto e algo fechou desde a
   abertura"; custo aceito e declarado na mensagem;
5. 3ª revisão: "a linha que casa melhor" deixava a v1 fechada encerrar a `busca vetorial hibrida`
   aberta do chat → encerrada olha toda linha que casa.

**Rejeitado:** ler o transcript do chat (formato não é contrato) · bloquear quando outro chat tem
feature na mesma pasta (fica aviso) · a foto do INDEX · remendar a foto com palavras em comum.

**Fizemos:** 0.34.0 na `feature/um-item-por-chat` (`73b554f` → `8a6ad77` → baseline `c0eda5e` → MAPA
`1d6c506`), suíte 649 → 676, F-032, memória `feedback_nao_adivinhar_dono_do_dado`. Tropeços meus: dois
heredocs de Python pelo Bash quebraram (um deles gravou `\t`/`\n` reais numa regex) — script em
arquivo no scratchpad resolveu; e um teste que passou por comparação de string frouxa.

**Próximo:** push da `main` pelo owner · canário ao vivo (`canario-a`/`canario-b` no mesmo chat) ·
no Whats, marcar `pausada:` as abertas paradas.
