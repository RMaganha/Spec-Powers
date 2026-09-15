# 2026-09-15 — orçamento de partida e recall determinístico (0.27.0)

**Conversamos:** o hook do kit mandou podar o `memory/MEMORY.md` do Whats ("estourou o teto de 25 KB, o
excedente não carrega"). O owner interrompeu a poda antes da 1ª edição e pediu solução estrutural: o projeto
é grande, ele voltava às conversas antigas pra re-explicar onde cada assunto foi tratado, e isso não podia
custar tokens.

**Pivôs:**
1. de "podar o índice" para "mover, em dois níveis" — a premissa "não carrega" é da pasta nativa, não do
   índice do repo (F-024);
2. de "confiar que o modelo lê o índice" para "recall injetado por hook, zero tokens de busca"
   (`recall_memoria.py`, ≤ 600 B, não bloqueia);
3. de "um arquivo" para "a partida inteira", ao medir 214 KB (o índice era 12%; MAPA 15× o teto);
4. de "spec só da memória" para "uma spec, três mecanismos, mesma causa raiz" — o owner perguntou
   "não deveria tratar tudo nessa janela?"; sim, mas a aplicação no Whats é janela própria.
A simulação a seco antes do código foi o que segurou o desenho: achou famílias por assunto e palavras
raspadas viram lixo.

**Rejeitado:** teto de 60 KB (adia); índice gerado só do frontmatter (não resolve tamanho); qualquer
poda de conteúdo por script; hook com LLM ou cache.

**Fizemos:** 0.27.0 em 12 commits, 336 testes: `memoria_indice.py` (dividir/verificar/fila/buscar +
motor), `recall_memoria.py`, `rodizio_partida.py` mapa/index, moldes e comandos sem a premissa falsa,
dogfood no kit (8.694 → 2.976 B). Owner integrou e publicou. Aplicação no Whats em janela própria, 3
commits: partida 190 → 108 KB (47,6 mil → 26,9 mil tokens). Tropeços: dataclass + importlib no 3.14;
`| tail -1 && git commit` commitou com suíte vermelha (F-025); heredoc grande com acento quebrou.

**Próximo:** fila de conteúdo do Whats (77 `gatilho:`, `CLAUDE.md` 27 KB, 39 itens abertos), uma janela
por item; no kit, podar os 5 comandos grandes com teto por bytes e teste.
