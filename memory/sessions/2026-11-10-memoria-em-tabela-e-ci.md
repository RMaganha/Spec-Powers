# 2026-11-10 — memória em tabela e conferência antes de entregar (análise + teste de mesa)

Branch `docs/memoria-em-tabela-e-ci` (da `main` em `7c64fd3`). Dossiê:
`docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`. Nenhum código do kit mudou; só documentação.

## Conversamos
- O owner abriu com `/mss-spec:tarefa`: viu no MSIG_Agentes (conversa "Design system do menu Análise de
  Contratos") memória em banco que gasta pouco pra achar, agente que "sabe tudo dos projetos", rapidez e a
  revisão antes do PR. Pediu entender e resumir como melhorar o kit. Lembrou que no Whats uma busca demorou e
  veio quebrada (um UPDATE guardado cortado, sem o `WHERE`).
- Fechamos 6 itens por tópico, um a um, em linguagem simples: busca, conferência antes de entregar, tabela
  SQLite, ajudantes (pesquisador e revisor), teste automático do kit, comando guardado inteiro.
- O owner fixou: nada do MSIG_Agentes é usado ou copiado; arquivo é o original e a tabela é cópia; SQLite local
  sem Docker; um comando remonta na máquina nova, com o passo a passo na memória; tabela antes da busca.
- Teste de mesa nos 4 projetos (kit, Whats, Transportes V2, MSS-UTILS), refeito várias vezes a pedido dele até
  cobrir tudo o que é memória: 3.046 trechos, 944 casos de gabarito, 2.854 pedidos reais.

## Pivôs
- **1 caso → 310 → 944 casos.** A primeira rodada concluiu de 1 caso ("resumir o pedido ajuda"); com 310 a
  conclusão caiu. O owner: *"voce está assumindo esse 1 teste como verdade absoluta"*.
- **Só `memory/` → tudo o que é memória.** Os subíndices, specs, planos, MAPA, INDEX e documentos tinham ficado
  fora; a afirmação "40% das anotações do Whats sem 'quando usar'" estava errada (todas têm, no subíndice).
  Incluir os documentos virou o maior ganho medido (13% → 32%).
- **"A busca é fraca" → "não consulta na hora de agir e não revê".** Lidas as 172 falhas registradas dos
  projetos (`docs/EVALS.md`), que não tinham sido abertas na partida: 30% afirmar sem medir, 20% regra que já
  existia e não foi usada, 15% forma da resposta.
- **Estrutura dada como certa → 9 formas medidas** (quase todas empatam) e **1 × 2 × 8 tabelas** (várias não
  ganham).
- **Ideia do owner: buscar 30 e ficar com 10.** Reordenar por contagem de palavras não funciona; alguém lendo
  as 30 linhas e escolhendo melhora (27 → 32 de 60), com amostra pequena.
- **Forma da conversa**: o owner se perdeu com jargão, respostas longas e a pergunta repetida na caixa do fim
  da rodada; passou a valer resposta curta, em linguagem simples, com a pergunta só no texto.

## Rejeitado
- Banco como fonte (SQL Server, como lá) e tabela no OneDrive como original.
- Várias tabelas, uma por tipo (36% × 41%, o dobro do tempo).
- Resumir o pedido antes de buscar (piorou: 83% → 73%; 24% → 19%).
- Reordenar os 30 por contagem de palavras (5 jeitos, sem ganho que se repita).
- Guardar no repositório os dados do teste (pedidos reais do owner em outros projetos): ficaram fora.

## Fizemos
- `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md` (escopo, régua, o que não prova, textos prontos) e os 9
  roteiros de teste em `docs/analise/2026-11-10-teste-de-mesa/`; `.gitignore` barra os dados nessa pasta.
- `docs/decisoes.md` (tabela SQLite local como cópia), `docs/superpowers/INDEX.md` (itens 8 a 15) e
  `docs/superpowers/MAPA.md` (próximo passo).

## Próximo
- Uma janela por item, na ordem do INDEX (textos prontos no dossiê, seção 9): comando guardado inteiro →
  tabela → busca → consultar pela ação (falta o sim do owner) → ajudante pesquisador → conferência antes de
  entregar → ajudante revisor → teste automático do kit (falta decidir GitLab × GitHub).
- `/mss-spec:memory capturar` pras falhas desta sessão (seção 6 do dossiê) virarem casos no `docs/EVALS.md`.
- Merge na `main` com a aprovação do owner; `git push` é dele.
