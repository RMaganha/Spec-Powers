<!-- Prompt avulso — não é copiado pra projeto novo, fica aqui como referência versionada.

     DIFERENTE do PROMPT-MAPEAR-AMBIENTE.md: aquele é sobre INFRA/DEPLOY (docker, banco, Azure) e só
     funciona com acesso a arquivo exato (Claude Code, ou configs anexados). ESTE aqui é sobre
     ENTENDER O PROJETO (o que ele faz, pra quem, como é organizado) — funciona em QUALQUER app:

     ✅ CLAUDE CODE — explora o repositório sozinho, sem você precisar fazer nada.
     ✅ CLAUDE DESKTOP / claude.ai (chat comum) — funciona também, desde que você dê alguma fonte:
        anexe o README.md/CLAUDE.md, cole a estrutura de pastas, ou simplesmente DESCREVA o projeto
        em texto respondendo aos pontos abaixo. Não precisa de arquivo de config exato como no outro
        prompt — entendimento de projeto tolera descrição verbal seu.

     Se não houver NENHUMA fonte (nem arquivo, nem descrição sua), o prompt deve parar e perguntar
     em vez de inventar — mesma regra do outro prompt. -->

# Prompt: Conhecimento do Projeto

-----

Você vai construir um **perfil resumido** deste projeto (ou do projeto que eu descrever/anexar).
Não é sobre infraestrutura/deploy — é sobre O QUE o projeto é e faz. Se você tiver acesso a arquivo
(Claude Code) explore o repositório; se estiver num chat sem acesso a arquivo, use o que eu anexar
ou descrever, e pergunte o que faltar em vez de supor.

Se não houver NENHUMA fonte de informação sobre o projeto (nem arquivo anexado, nem descrição
minha), PARE e me pergunte qual projeto é e peça uma fonte — não invente.

## O que levantar

1. **Identificação** — nome do projeto, pra que serve (1-2 frases de propósito de negócio: que
   problema resolve, pra quem), status atual (produção / homologação / desenvolvimento / múltiplas
   versões coexistindo).
2. **Arquitetura geral** — como é organizado (principais módulos/camadas), stack técnica principal
   (linguagem, framework, banco), como roda (API, bot, worker, CLI, agendado).
3. **Funcionalidades principais** — o que o sistema faz de fato: principais fluxos, endpoints, telas
   ou comandos, na ordem de importância.
4. **Regras de negócio/domínio notáveis** — decisões de domínio que não são óbvias olhando só o
   código por cima (ex.: "usa dois bancos diferentes pra leitura e escrita", "cada cliente tem
   configuração própria com fallback pro padrão").
5. **Integrações externas de negócio** — quais serviços/parceiros o sistema consome (não é infra;
   é negócio: ex. SUSEP, Chatwoot, WhatsApp, provedores de LLM usados e pra quê).
6. **Padrões técnicos dignos de nota** — alguma abordagem aqui que valeria a pena reaproveitar (ou
   evitar) em outro projeto? Se sim, é candidato a virar entrada na skill `precedentes-msig`.
7. **Observações de estado** — algo relevante sobre a maturidade/situação atual (ex.: versão antiga
   em produção e uma nova em homologação — qual é a vigente e o que mudou entre elas).

## Saída esperada

Um perfil curto e direto (bullets, não ensaio) cobrindo os 7 pontos — pensado pra alguém (ou uma IA)
que vai trabalhar nesse projeto depois e precisa de contexto rápido sem ler tudo do zero. Se algum
ponto não se aplicar ou não puder ser respondido com a fonte disponível, diga isso explicitamente em
vez de pular ou inventar.

-----
