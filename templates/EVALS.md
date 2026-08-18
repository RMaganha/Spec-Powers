<!-- MODELO do corpus de falhas — copie para `docs/EVALS.md` no repo do projeto.

     Para que serve: o assistente erra; sem registro, ele erra de novo três semanas depois. Aqui a
     falha vira CASO, o caso ganha um GUARDRAIL (uma frase num comando/regra/código) e o guardrail
     ganha um TESTE. Só o teste impede a regressão silenciosa — prosa sozinha esquece.

     Regras:
     - **Caso sem guardrail fica `aberto`.** É dívida visível; o /mss-spec:release conta e reporta.
     - Só entra falha que **aconteceu de verdade** neste projeto (com data). Nada de hipótese.
     - **Gatilho** é a coluna que dispara o recall: a condição observável em que este caso volta a
       ameaçar. Escreva "quando <situação>", igual ao `gatilho:` das memórias.
     - Caso **fechado com teste** vive só na linha da tabela — o teste é o guardrail vivo. O bloco
       detalhado existe enquanto o caso está `aberto` ou enquanto o guardrail é só prosa.
     - Nunca cite um teste que não existe: `test_evals_so_cita_teste_que_existe` derruba a suíte.
     - Alimentado pelo `/mss-spec:memory capturar` (premissa derrubada e reincidência viram caso).

     Divisão de trabalho com a memória:
       `memory/MEMORY.md` = o que **ainda vale** (regra, gotcha, preferência).
       `docs/EVALS.md`    = o que **já custou caro** (falha + guardrail + teste). -->

# Falhas — corpus de casos

O que **já custou caro** mora aqui. O que **ainda vale** mora em `memory/MEMORY.md`.
Leia a coluna **gatilho**: se ela descreve o que você está prestes a fazer, o caso é seu.

| id | data | gatilho | classe | guardrail | status |
|---|---|---|---|---|---|
| F-001 | <AAAA-MM-DD> | quando <condição observável que faz o erro voltar> | <premissa não-dita \| memória não carregou \| falha silenciosa \| regressão \| comunicação> | <arquivo + a frase> · `<test_nome>` | fechado |
| F-002 | <AAAA-MM-DD> | quando <condição> | <classe> | — | aberto |

## F-002 · quando <condição> — **aberto**

**Falhou:** <o que eu fiz de errado, concreto, com o custo real>
**Verdade:** <o que era verdade e eu não sabia/não perguntei>
**Guardrail:** <a frase que passou a existir, e onde — ou "nenhum" + o candidato>
**Teste:** <`test_nome` — ou "—" enquanto não existir>
