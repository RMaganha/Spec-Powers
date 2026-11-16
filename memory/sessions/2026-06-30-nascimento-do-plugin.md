# 2026-06-30 — nascimento do plugin mss-spec (diário retroativo)

conversa: db2be446-fcee-4afe-88da-ad226447067e

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta). Período: 2026-06-30 a 2026-07-08.

## Conversamos
Da pasta de moldes `modelo/` ao plugin `mss-spec`: memória no `memory/` do repositório, levantamento de infra em 7
projetos, níveis de cerimônia e resgate de memória.

## Pivôs
- A memória sai do `~/.claude` e passa a morar no repositório (fala 008).
- Os prompts para o chat do Desktop falharam por falta de acesso ao disco (falas 050-063); o kit virou plugin
  carregado por junção (falas 064-097).
- O certificado da CA saiu (fala 074) e voltou em 4 camadas (fala 133); veio um review externo (fala 155).
- O owner se apresentou: engenheiro de software com mais de 30 anos, "não sou um simples vibecoder" — quer o modelo
  mental e o porquê, não entrega calada (fala 062).
- "branch nova deve ser pedida explicitamente" (fala 076) — substituído em 2026-07-17: toda tarefa nasce numa branch
  a partir da `main` (`memory/feedback_feature_a_partir_da_master.md`).
- Comando explícito em vez de skill que pode não disparar: "disparar o que eu quero via /nome:o-que-eu-quero é a
  melhor forma" (fala 068).

## Rejeitado
`azure-compose.yaml` (o nome não existe, falas 032-033); os dois prompts avulsos (fala 075).

## Fizemos
Comandos `kickoff`, `nova-feature`, `banco`, `ambiente`, `precedentes`, `plano-teste`, `modo` e `memory`;
`projeto.md`; regra global de memória (falas 140 e 148); `.gitignore` padrão (fala 154); versão 0.2.0 com teste
de fumaça (fala 157). TLS canônico com `SSL_VERIFY=true` e a CA embutida, `false` só para diagnóstico (falas 157-158).

## Próximo
O conserto da CA no Dockerfile do painel e o teste da junção ao vivo (fala 158).
