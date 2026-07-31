# 2026-07-31 — mapa neural: corte silencioso e camadas por conteúdo (v0.17.0)

## Conversamos
Mesma janela da 0.16.0, segunda rodada: o owner rodou o mapa consertado no projeto Flask e colou o
relatório de lá. Os 4 pontos da manhã confirmados (0 rotas do vizinho, 24 de 24 rotas, camadas
próprias presentes, 0 ruído de template) e **dois achados novos** — 11 memórias escondidas e pastas
de fora do mapa.

## Pivôs
- **A pergunta que reorientou tudo: *"eu ainda não entendi se o mapa está falhando"*.** Eu tinha
  respondido com proposta técnica em cima de um relatório técnico; o que faltava era **separar as
  duas coisas**: o corte em 25 é **falha nossa** (o índice afirma um todo que não é o todo), as
  pastas são **limite de desenho** (nunca funcionaram, não é regressão). Só depois disso a conversa
  destravou.
- **Minha proposta foi cortada por complexidade.** Eu havia proposto uma seção declarativa
  `## Camadas` no `MAPA.md` (`- ignorar:` / `- incluir:`). Resposta: *"não entendi muito bem"*.
  Virou **uma regra** — *se está no repo, está no mapa* — com 4 exceções de uma linha, e a
  declaração de "isto não é o projeto" delegada ao **`.gitignore`**, que o projeto já mantém.
  Aprendizado gravado em `feedback_regra_unica_em_vez_de_config`.
- **Duas premissas minhas corrigidas pelo owner:** (1) `n8n/` **tem** que entrar — a janela de lá
  dizia "ausência desejável", mas são os fluxos de trabalho do projeto; (2) **pasta com código
  dentro de pasta com código tem que ser mapeada** — eu tinha deixado a recursão fora de escopo na
  rodada anterior, e era exatamente o buraco que fazia `apis/v1/rotas.py` não existir no mapa.
- **O critério de camada mudou de extensão para conteúdo.** Detectar por `.py` (0.16.0) pegava
  `_investigacao/` (scripts descartáveis) e perdia `web/` (HTML) e `prompts/` (Markdown) — inversão
  perfeita do que se queria. Nenhum critério mecânico acerta os dois; quem decide é o projeto, e o
  lugar onde ele já decide é o `.gitignore`.
- **Bug meu, silencioso, achado por teste real:** `subprocess` com `text=True` no Windows converte
  `\n` em `\r\n` na entrada; o `git check-ignore` recebia `backup/\r` e devolvia aspeado — o filtro
  virava `set()` vazio **sem erro nenhum**. Só apareceu porque o teste faz `git init` de verdade em
  vez de mockar. Gravado em `project_subprocess_texto_windows_quebra_git`.
- **Dogfood de novo produtivo:** `skills/` (só `.md`) apareceu no mapa do kit pela primeira vez, e o
  `_resumo` exigia o **fecho** da docstring na janela de 2000 caracteres — como a docstring do
  `mapa_neural.py` cresceu nesta rodada, ele **próprio** ficou sem resumo. Dois consertos que teste
  de fixture nenhum pegaria.

## Rejeitado
- **Seção declarativa `## Camadas` no `MAPA.md`** (minha, cortada pelo owner) e **ler intenção na
  prosa do `CLAUDE.md`** ("`_investigacao/` é descartável" não é contrato executável).
- **Heurística de prefixo `_`** para pasta descartável — adivinhação com cara de regra.
- **Ordenar memórias por data** em vez da ordem do índice: com limite 200 o problema evapora.

## Fizemos
`_LIMITE` (200) + `_cortar()` com rastro `… (+N)` nos 6 ramos + `--limite` · `_tem_conteudo()` e
`_filhos_pasta()` recursivo (`_PROF_MAX`) · `_pastas_fora()` + `_git_ignorados()`
(`git check-ignore -z`, bytes, degrada gracioso) + `--ignorar`, propagado ao `_py_files` (pasta fora
do mapa não expõe endpoint) · `_resumo` sem exigir o fecho da docstring. +8 testes (fixture
`proj_pastas`) → suíte **109 verde**. Bump **0.17.0**; spec F2.5 + CA27–CA31; `COMO-FUNCIONA.html` e
`commands/mapa-neural.md` em dia.

## Próximo
Rodar de novo no projeto Flask (a junction já entrega a 0.17.0 sem publicar): 36 memórias inteiras,
`web/`/`prompts/`/`n8n/` como camadas, subpastas descendo, `_investigacao/` e `backup/` saindo por
`.gitignore` ou `--ignorar`. Depois o push.
