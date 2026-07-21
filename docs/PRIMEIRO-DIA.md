# Seu primeiro dia com o mss-spec

Um roteiro curto pra quem acabou de instalar o kit e quer sair usando. Aqui é o **como começar**;
o **o quê** cada comando faz está no [LEIA-ME](LEIA-ME.md) (referência) e o **por quê** no
[COMO-FUNCIONA.html](COMO-FUNCIONA.html). Não precisa decorar os 19 comandos — o dia a dia usa poucos.

## Antes de tudo (uma vez)
Instale o `mss-spec` e habilite o **superpowers** — os dois passos estão no [LEIA-ME](LEIA-ME.md#instalação).
Precisa de **Claude Code v2.1.140+** e, depois de instalar/atualizar plugin, **feche e reabra** o Code
por inteiro (aba nova não basta). Feito isso, você não repete mais — é "instala e esquece".

## Passo 1 — Constitua o projeto
Abra seu projeto (novo ou já existente) no Claude Code e rode:
```
/mss-spec:kickoff "em 1 frase, o que é e pra quem"
```
Ele te **entrevista** (uma pergunta por vez) e monta a base no padrão da casa: instruções do projeto
(`CLAUDE.md`), pastas em camadas, memória, índice de tarefas, segurança, log. Você não copia arquivo
à mão — ele gera. Ao terminar, o superpowers já fica ligado naquele projeto.

## Passo 2 — Deixe o doctor conferir o ambiente
Logo na primeira tarefa o **doctor** roda sozinho (ou chame `/mss-spec:doctor`): ele checa proxy, certificado,
driver do banco, rede, `.env`… e dá um **✓/✗**. Ele **só avisa** — não conserta. Se aparecer algum ✗,
resolva antes de seguir (ex.: instalar o driver ODBC antes de conectar no banco). Rodar de novo nunca muda nada.

## Passo 3 — Sua primeira feature
```
/mss-spec:nova-feature "cadastro de clientes"
```
O que esperar: primeiro ele escreve os **Critérios de Aceite** (o que a funcionalidade precisa fazer) e
**espera o seu OK** — nada de código antes disso. Depois vem plano curto, e a implementação em **TDD**
(teste primeiro, código depois) com a saída dos testes colada pra você conferir. Você aprova o rumo; o
assistente executa com disciplina. Mudança pequena (corrigir um bug, um ajuste) **não** precisa deste
comando — é só pedir.

## Passo 4 — Confie, mas verifique
Antes de dar algo por pronto, a suíte de testes roda e tem que estar **100% verde**. Quando está, o
`/mss-spec:plano-teste` grava esse retrato como **baseline** — a rede que avisa se algo quebrar depois.
"Passou tudo" deixa de ser fé e vira evidência.

## Dois hábitos que poupam dor
- **Um assunto por janela.** Uma conversa = uma tarefa. Surgiu outro assunto no meio? Anote com
  `/mss-spec:to-dolist adicionar <assunto>` e abra uma janela nova pra ele — em vez de emendar.
- **Memória mora no repo.** O que o assistente aprende sobre o projeto vai pra `memory/` (versionado),
  não some numa reinstalação e viaja com o código. Ao **fechar** um assunto, a `nova-feature` roda o
  **`/mss-spec:memory capturar`** (ou chame você a qualquer hora): ele guarda as **decisões** — inclusive
  o que se decidiu **não** fazer — e um **diário da sessão** datado, com foco nos *pivôs* (o que se
  cogitou, por que mudou, pra onde foi). É o que evita, semanas depois, repropor algo que já foi
  descartado — e é barato de reler (índice datado em `memory/DIARIO.md` → abre só a entrada que importa).

## Travou?
- Ambiente estranho → `/mss-spec:doctor`.
- "Será que já fizeram isso em outro projeto?" → `/mss-spec:precedentes <assunto>`.
- Achou o fluxo lento (ou rápido demais) → `/mss-spec:modo <mínimo|médio|alto>` (padrão é médio).

Bem-vindo. Da segunda tarefa em diante, o ciclo é sempre o mesmo: `nova-feature` → seu OK → TDD → verde → **captura** (decisões + diário).
