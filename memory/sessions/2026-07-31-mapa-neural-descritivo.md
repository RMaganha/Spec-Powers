# 2026-07-31 — mapa neural: o gerador vira descritivo (v0.16.0)

## Conversamos
O owner chegou com um **diagnóstico pronto**, linha a linha, feito na janela de **outro** projeto (Flask)
onde ele rodou o `/mss-spec:mapa-neural` — e onde, corretamente, **não consertou nada** ("é outro projeto
e outro assunto — pela regra de um assunto por janela, não mexo aqui"). O mapa gerado lá afirmava **18
rotas do projeto vizinho** e **zero** das 17 reais, com `apis/` e `persistencia/` invisíveis.

## Pivôs
- **A pergunta que mudou o tom: "mas isso trará benefícios?"** O owner não comprou o conserto de cara —
  pediu o porquê. A resposta que fechou não foi "são 4 bugs", foi **o que o artefato é**: o
  `mapa-neural.md` é o **destilado que o assistente lê no lugar da fonte**; destilado que mente faz uma
  sessão futura "consertar" rota fantasma ou duplicar rota real — a mesma falha que a **regra crítica 6**
  evita nas specs, só que gerada automaticamente e sem revisor. E a alternativa ("ignore o bloco de
  endpoints") é pior: artefato que você precisa **lembrar de desconfiar** tem valor negativo.
- **Enquadramento que apareceu ao explicar:** é a **terceira face** da fronteira das 0.15.0/0.15.1 —
  escrita (âncora), leitura manual (PERGUNTE, não vasculhe) e agora a **leitura automática** (o gerador
  descia sozinho em `.claude/worktrees/` e trazia o vizinho pra dentro).
- **Correção ao diagnóstico (mudou o conserto).** O relato dizia "os extratores leem os `.md` sem
  descartar as linhas de template". O placeholder das decisões está **dentro de comentário HTML** — o
  conserto certo era descartar comentário (o `parse_conexoes` já fazia), não filtrar bullet.
- **Meu falso positivo, pego no dogfood.** Fiz o filtro de `<placeholder>` na **linha inteira** e ele
  **engoliu uma memória real** (gancho com `~/.claude/projects/<proj>/memory/`). Estreitado pro campo do
  assunto; teste de não-regressão no lugar.
- **Segundo achado do mesmo diff:** um `GET /x` fantasma vindo de um decorator citado **em comentário** —
  no meu próprio código. Os dois regex passaram a exigir o decorator no início da linha.
- **Terceiro:** o `hooks/` **estava invisível** no mapa do próprio kit (não está na lista do molde). O bug
  nº 3 não era só "do projeto do outro time" — o kit sofria dele calado.
- **Poda na descida, não na saída:** trocar o `rglob` + filtro por `os.walk` cortando `dirs` — além de
  correto, é o que impede a descida cara em `node_modules/`.

## Rejeitado
- **Conviver** ("ignore o bloco de endpoints; a fonte confiável é o `openapi.py`") — foi a saída que eu
  mesmo sugerira na janela do outro projeto; virou a alternativa **descartada** aqui: ou conserta, ou
  apaga a dimensão.
- **Pôr `apis/` e `persistencia/` na lista de camadas** — seria trocar a prescrição do molde pela
  prescrição do vocabulário de outro time. A lista virou **ordem**, não filtro.
- **Filtro de placeholder no `to-dolist`** — item de verdade cita a sintaxe de comando com `<algo>`
  (o próprio to-dolist do kit faz isso).
- **Django, `add_url_rule` e `url_prefix` de Blueprint** — declarados como limitação no comando, não
  implementados.
- **Árvore recursiva de subpastas** — só 1 nível de fallback quando o código da camada vive abaixo.

## Fizemos
`templates/mapa_neural.py`: `.claude` no ignore + poda na descida (`os.walk`) · `_ROTA_FLASK_RE`/
`_METODO_RE` (1 endpoint por método; GET default) + âncora de início de linha nos 2 regex ·
`_camadas()`/`_tem_py()` no lugar da lista fixa (todo `.py` da raiz + toda pasta com `.py`; molde sem
`.py` mantido; ordem = entrypoints → canônicas → alfabética) · `_linhas_uteis()`/`_e_molde()` nos
extratores de memória. +9 testes com a fixture `proj_alt` (projeto **fora** do molde) → suíte **101
verde** (era 92). Bump **0.16.0** nos 2 manifestos + CHANGELOG; `commands/mapa-neural.md` e o cartão do
`COMO-FUNCIONA.html` atualizados; spec F2.4 + CA23–CA26. Branch `fix/mapa-neural-descritivo`, merge
`--no-ff` na `main`.

## Próximo
**Publicar** (o `git push` é do owner) e **rodar o mapa no projeto Flask que originou o diagnóstico** —
é lá que os 4 consertos se provam: 17 rotas reais aparecendo, 18 fantasmas sumindo, `apis/` e
`persistencia/` visíveis. Continuam na fila: canário da cerca da âncora em sessão nova e o 1º uso real
do `/mss-spec:analise`.
