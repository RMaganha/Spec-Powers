# 2026-11-13 — sono da memória, parte 1: conferir, juntar e marcar o estado das notas (0.62.0)

Branch `feature/sono-da-memoria-acervo`, commit `0554ba7` (a captura vai num commit a seguir). Spec:
`docs/specs/sono-da-memoria.md`. Análise de origem: `docs/analise/2026-11-13-sono-da-memoria.md`.

## Conversamos
- O owner abriu com o `/mss-spec:nova-feature` e o pedido em molde: *"Já decidido — não reabrir"* (duas partes, uma
  conversa cada; escopo da parte 1; conversas fora da tabela; sem comando e sem tarefa agendada; saída numa branch
  com o diff pro OK; medição de partida; credencial nunca em nota) e *"Falta decidir"* (onde gravar o estado; quantas
  conversas disparam o aviso e quem conta; nota mais velha que a conversa mais antiga).
- As 5 respostas dele: estado no frontmatter no formato proposto **e** uma coluna de estado na tabela de memória;
  10 conversas, contadas pelo hook de abertura, com a data do último sono na linha de controle da tabela, sem hook
  novo; idade não rebaixa a nota; só as anotações de `memory/` ganham estado; ajudantes pesquisadores autorizados
  como exceção ao "sem subagentes" do nível médio, uns 6.
- No commit: *"ok"*. Na revisão: correção posterior clara não é conflito (critério do cookbook), 7 conflitos
  resolvidos por ele, 2 ficam pra ele decidir, conferir o recall antes do merge e gravar a regra no roteiro.

## Pivôs
- **Onde mora a data do último sono.** Eu propus a conferência mais nova entre as anotações e o "agora não" em
  `~/mss-spec/`; o owner mandou as duas para a linha de controle da tabela. Ficou: a data vem das anotações no
  `montar` e o "agora não" é preservado entre montagens.
- **9 conflitos viraram 2.** A passada marcou como conflito toda divergência entre fontes. O owner aplicou o critério
  do cookbook: 7 eram correção posterior clara (ficam confirmadas, com `substituiu:`), e a do tamanho do `MEMORY.md`
  do Whats era só dois números de momentos diferentes (F-069).
- **O "recall não pula" estava errado.** O ajudante procurou em `hooks/recall_memoria.py`, que só chama o motor, e eu
  gravei a marca sem conferir (F-068). Conferido no código, o recall pula; o teste novo achou outra brecha, real — a
  linha de subíndice esquecida de uma anotação `obsoleta:` — e ela foi fechada.
- **O teste de citações pegou a minha própria spec.** O nome body.js entre crases contou como citação morta e
  derrubou a suíte inteira (1 falha em 1615).
- **Suíte em paralelo deu falha falsa.** Rodei a suíte inteira junto com 2 testes: 2 falhas em testes que sobem
  processo, 2 testes em 57 min. Sozinha, 1617 verdes em 17 min (anotação
  `project_pytest_em_paralelo_estoura_nesta_maquina`).
- **Teste que contradiz a regra.** O teste do acervo exigia `conferida:` em toda anotação viva; a anotação nova desta
  captura nasce sem ele, como a regra manda. O teste passou a exigir as 78 da passada.

## Rejeitado
- Hook novo para o aviso; arquivo próprio para registrar o sono; o "agora não" em `~/mss-spec/`.
- Fundir ou reescrever linhas de `docs/decisoes.md` e `docs/EVALS.md` — só marcas no fim da linha.
- Rebaixar nota pela idade (decisão 11 do owner).

## Fizemos
- 0.62.0: `conferida:` cobrado pelo `verificar`; `memoria_indice.py sono`; coluna `estado` na tabela (esquema 2);
  `memoria_tabela.py adiar-sono`; aviso de 10 conversas no `hooks/memoria_tabela_em_dia.py`; "Uso interno: sono" no
  `commands/memory.md`; o recall e o `verificar` não deixam voltar a anotação aposentada.
- Passada no kit: 78 anotações — 75 confirmadas (7 com `substituiu:`), 1 não confirmada, 2 em conflito; citações
  mortas 40 → 0; 6 endereços velhos corrigidos; marcas no EVALS e nas decisões; nenhuma credencial.
- Provado no real: a tabela de `~/mss-spec/` no esquema 2 com os estados certos, e o hook de abertura calado (0
  conversas depois do último sono). Suíte: 1617 verdes.

## Próximo
- Owner: decidir os 2 conflitos (Tailwind × Mantine; `UserPromptSubmit` com exit 0 × exit 2 — pede teste no app).
- Parte 2 do sono (ler as conversas novas) em conversa nova.
- Owner: as 2 duplicatas possíveis do EVALS (F-051 × F-028; F-060 × F-047); `docs/decisoes.md:62` cita uma decisão
  de 2026-07-22 que não está no arquivo; os 4 comandos cortados.
- Só se prova no real: o aviso aparecendo numa conversa nova depois de 10 conversas.

## Acrescentado no sono de 2026-11-16

> A partir do texto da conversa `e9deb630-81ff-4abf-bd36-5791622a7d62` (só falas; sem saída de ferramenta).

As falas 021-024 ficaram fora deste diário: o MAPA com dois blocos de histórico pela 3ª vez (fala 020; o F-067
só registra a de 2026-11-12); o owner: "Não vamos rodar a suite inteira, já fizemos isso algumas vezes nessa
janela e não faz sentido rodar novamente" (fala 023); a branch curta `docs/mapa-sono-mesclado` (fala 024).
