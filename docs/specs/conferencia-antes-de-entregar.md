# Conferência antes de entregar — o que o owner chama de "CI"

## Estado atual
**Nada construído ainda.** Hoje o `/mss-spec:release` aplica só o checklist de compliance do kit; os apontamentos
de um revisor de código não ficam guardados em lugar nenhum, e o mesmo tipo de erro pode voltar na entrega
seguinte. O `.gitlab-ci.yml` do kit está "preparado, não ativado" e não roda no GitHub, onde o kit é publicado.
Este assunto vem **depois** da memória em tabela (`docs/specs/memoria-em-tabela.md`).

## Tudo o que o owner decidiu sobre a conferência (2026-11-10) — o registro que vale

> Quem abrir este assunto numa conversa nova lê **esta seção primeiro**. Se uma regra, decisão antiga ou hook do
> kit parecer proibir algo daqui, **não responda "o plugin não aceita"**: mostre a regra com `arquivo:linha` e
> pergunte ao owner.

1. **Nada do MSIG_Agentes é usado, copiado ou ligado ao kit.** De lá veio só a ideia do ciclo: o apontamento do
   revisor vira item de uma lista, e a próxima entrega passa por ela.
2. **Lista de conferência por projeto.** Cada projeto tem a sua. Ela **cresce a cada apontamento** recebido de
   um revisor, e cada item guarda a origem: quem apontou, onde e quando.
3. **O assistente confere a mudança pela lista antes de dizer "pronto para entregar".** O ganho que o owner quer:
   menos idas e voltas com o revisor, e o mesmo erro não se repete.
4. **Ajudante revisor:** confere a mudança pela lista, com olhos de quem não escreveu o código. Usado **só nesse
   momento**, não em toda tarefa (o ritual completo com ajudantes é lento — `memory/feedback_nivel_cerimonia_velocidade.md`).
   Escrito do zero no kit.
5. **Teste automático do kit a cada publicação. PENDENTE:** a decisão de 2026-07-20 escolheu GitLab CI "em vez de
   GitHub Actions" e o kit hoje é publicado no GitHub. **O owner ainda não disse se revê.** Sem essa resposta,
   este item não começa.
6. **O princípio que o owner cobrou:** *"só faz uma vez e não revê — é o que os itens da CI fazem"*. Conferir
   quer dizer rever com mais de um caso, não passar uma vez.

**Ordem que o owner fixou:** lista de conferência → ajudante revisor → teste automático do kit.

**O que ainda não se sabe:** como os apontamentos chegam ao assistente em cada projeto (Azure DevOps, GitHub, ou
o owner colando o texto) — perguntar ao owner no desenho; no outro projeto o ciclo ainda não tinha rodado numa
entrega real.

Origem e medições: `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md` (seções 1, 2, 3 e 7).

## Histórico
- 2026-11-11 — criado: só o registro das decisões do owner de 2026-11-10; nada construído (motivo: o owner pediu
  que tudo o que foi decidido sobre o que fazer ficasse gravado num lugar só, pra conversa nova não se perder).
