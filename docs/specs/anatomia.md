# anatomia — painel de runtime do kit

## Estado atual
O `/mss-spec:anatomia` (`commands/anatomia.md`, invocável) roda o gerador determinístico `templates/anatomia.py` (irmão do `mapa_neural.py`) e produz `docs/anatomia.html` — self-contained, **fora do git** (ancorado `/docs/anatomia.html` nos dois gitignores). Quatro seções: **quando cada peça entra na janela** (partida/evento/demanda/fecho — a lane "sob demanda" se distribui sozinha pelo frontmatter dos comandos, invocável × `disable-model-invocation`) · **matriz lê×escreve** por artefato · **riscos** (classes curadas + o que a geração mediu: casos abertos do EVALS, orçamento estourado) · **fila** (Próximo passo do MAPA + "A fazer" do INDEX). Regra dura: número no HTML é **medido** (manifestos com `utf-8-sig`, bytes, `hooks.json`, rules, tabela do EVALS); o metadado curado (matriz/riscos/lanes fixas) declara `alvos` e o teste confere que todos existem — painel não mente em silêncio. O painel é **pro humano**; o assistente segue lendo MAPA/INDEX/memória. Testes: `tests/test_anatomia.py` (9) + `test_anatomia_wiring`.

Fora de escopo: inferência automática de risco (curado, não julgado por máquina) · rodar em projeto sem o kit · o painel virar fonte de leitura do assistente.

## Histórico
- 2026-08-25 — criado: protótipo manual da sessão de avaliação do kit virou gerador testável; item veio do to-dolist do mesmo dia.
