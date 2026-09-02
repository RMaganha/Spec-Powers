# bpmn — desenho do processo a partir do código

## Estado atual
O `/mss-spec:bpmn` (`commands/bpmn.md`) roda o gerador determinístico `templates/bpmn.py` (irmão do
`mapa_neural.py` e do `anatomia.py`) e produz **duas saídas do mesmo modelo**, ambas em `docs/` e
**fora do git**: `docs/bpmn.md` (índice em texto — é o que o **assistente** lê) e `docs/bpmn.html`
(desenho BPMN em SVG, self-contained, zero CDN — é o que o **humano** vê). A extração é **estática,
via `ast` da stdlib**, e **nunca inventa caixa que não está no código**.

**Um processo por porta de entrada**, descobertas em **cascata**: rota Flask/FastAPI
(`POST /cotacao`) → `main()` de arquivo da raiz → `main()` em qualquer módulo (o 3º degrau nasceu do
dogfood: os scripts deste kit vivem em `templates/`, e sem ele o projeto saía com **zero** processo).
`--entrada <funcao>` aponta uma porta que não é rota nem `main` (um job de cron, por exemplo).
Chamada resolve na ordem **mesmo arquivo → import declarado (`from x.y import z`) → qualquer
arquivo** — sem isso, dois módulos com uma função `gerar` faziam o processo de um desenhar as caixas
internas do outro (desenho errado com cara de certo). Dentro do processo, o mapeamento para a
notação BPMN (numeração do infográfico do Bizagi que o owner usou como modelo):

| elemento | de onde sai |
|---|---|
| 1. evento de início | decorator de rota, ou `main()`/`if __name__` |
| 4. tarefa | chamada a função **definida no projeto** (mesmo módulo incluso — senão o desenho de um script de arquivo único sairia vazio); rótulo = 1ª linha do docstring, senão o nome |
| 5. subprocesso | tarefa que por dentro também tem chamadas/decisões (expande até `--profundidade`, default 2) |
| 6. gateway exclusivo | `if/elif/else`; ramo rotulado pela condição como está escrita no código |
| 7. gateway paralelo | `asyncio.gather`, `ThreadPoolExecutor`/`ProcessPoolExecutor` |
| 3. evento de fim | `return` (rótulo = o que retorna) · `raise` → fim de **erro** |
| 19. evento de borda | `try/except` em volta da tarefa |
| 16. armazenamento de dados | `cursor.execute`, SQLAlchemy, `pyodbc` |
| 11. fluxo de mensagem + 13. piscina | `requests`/`httpx`/cliente de API → piscina externa |
| 14. raia | módulo/pasta da função (`apis/`, `services/`, `persistencia/`) |
| 17. anotação | docstring da função |
| 20. chamada de atividade | subprocesso que aparece em **2+ processos** (reuso de verdade) |

Regras duras: **poda antes de fidelidade** — só vira caixa chamada a função do próprio projeto ou decisão que muda o desfecho (chamada a lib/stdlib não vira)
(`if` interno que não faz nem um nem outro não aparece); guarda (`if not x: raise`) **nunca** desaparece,
vira gateway + fim de erro; corte deixa rastro `… (+N)` (F-009, sem corte calado); `.py` que não parseia
não derruba a geração — vai para a seção **não lido** (falha aberta, sem inventar); todo rótulo vindo
do código é **escapado** (docstring com `<script>` quebraria o SVG); a linha de cada nó é alocada
**globalmente por processo**, senão o ramo de um gateway aninhado cai sobre a linha de um ramo irmão
e duas caixas se empilham. O desenho é **pro humano**; o assistente lê o `.md`.

Saídas do dogfood neste repo (que não tem rota): **5 processos** (os `main()` de `hooks/` e
`templates/`), 7 arquivos `.py` lidos, 1 não lido (`templates/get_connection.py` é molde com
placeholder — reportado, não escondido). Testes: `tests/test_bpmn.py` (33) + `test_bpmn_wiring`.

Fora de escopo: `.bpmn` XML 2.0 importável no Bizagi/Camunda (v1 é só visual — palavra do owner) ·
elementos não deriváveis do código (gateway inclusivo 8, por evento 9, objeto de dados 15, grupo 18) ·
qualquer linguagem fora do Python (JS/TS, SQL, JSON de fluxo do n8n) · processo de **negócio** que não
está no código · editar/arrastar o desenho (é leitura, não modelagem) · o `.html` virar fonte de leitura
do assistente · análise semântica profunda de tipos/chamada dinâmica (mesma fronteira do `INDEX.md`).

## Histórico
- 2026-09-02 — criado: pedido do owner com o infográfico "Elementos do Bizagi" como modelo de notação;
  desenho **A** (fluxo por porta de entrada, raias por camada) aprovado contra B (diagrama único do
  sistema — seria o mapa-neural de novo) e C (sem gerador, o assistente desenha a cada pedido — o custo
  que a decisão de 2026-08-25 já havia rejeitado na `anatomia`).
