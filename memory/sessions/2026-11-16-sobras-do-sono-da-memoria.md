# 2026-11-16 — sobras do sono da memória (0.64.0)

## Conversamos
Três sobras da parte 2 do sono, numa entrega só (origem: conversa d23210d6, 2026-11-13 a 2026-11-16): os hooks
passam a ler a entrada em UTF-8; a regra 3 de front fica "conforme o projeto"; o fecho do sono só roda a suíte quando
a rodada muda arquivo fora de `memory/**` e `docs/decisoes.md`. O owner trouxe tudo decidido; o assistente mostrou 7
escolhas e 1 pergunta, aprovadas.

## Pivôs
- **"Por tela" × "por projeto".** `templates/FRONTEND.md` dizia "escolha por tela, não por projeto" e
  `commands/nova-feature.md` mandava escolher o nível "por tela" — o contrário da decisão do owner. Ele mandou
  reescrever os dois e dar `substituiu:` na nota `project_front_moderno_mantine` (por tela, 2026-07-13 → por projeto,
  2026-11-16).
- **O teste que discrimina, na condição real.** Rodado contra os hooks da `main` (cópia no rascunho), o hook do
  `Stop` devolveu exatamente "falta no bloco `Já decidido…`" para um bloco com o título; com `hooks/_entrada.py`,
  os 23 casos passam. O caso "texto que não é UTF-8" também discriminava: lendo como cp1252, o hook antigo aceitava.
- **`linhas-do-kit.txt` já guardava o texto antigo.** É gerado do histórico git do molde (`templates/CLAUDE.md`), e a
  regra 3 antiga está lá (commits `8609a61` e `f43f318`); regenerar só acrescentou as 2 linhas novas.

## Rejeitado
Ler o stdin com `utf-8-sig` ou fallback pra cp1252 (decidido: UTF-8; o resto falha aberto); mexer na fixture
`tests/fixtures/molde-7b0809b/` (histórica); mandar algum dos três ajustes pro `to-dolist.md`.

## Fizemos
- `hooks/_entrada.py` (`ler_evento`), usado pelos 18 hooks; `tests/test_hook_entrada_utf8.py` (23).
- Regra 3 em `templates/regras-do-kit/2-regras-criticas.md`; nível por projeto em `templates/FRONTEND.md`, nas duas
  cópias de `rules/frontend.md`, em `commands/nova-feature.md` e `commands/compliance.md`; linha **UI:** do
  `templates/CLAUDE.md`; `linhas-do-kit.txt` regenerado.
- Notas `feedback_frontend_tailwind_arquivos_separados` (sai de conflito, confirmada) e
  `project_front_moderno_mantine` (`substituiu:`); 1 linha em `docs/decisoes.md`.
- Fecho do sono em `commands/memory.md` (passo 8) + teste; spec `docs/specs/sono-da-memoria.md` (Estado atual e
  Histórico); versão 0.64.0 nos dois manifestos.

## Próximo
Diff pro OK do owner antes do merge; o conflito `UserPromptSubmit` exit 0 × exit 2 continua com ele.

## Continuação 2026-11-17
- **Demora:** o owner perguntou *"qual o motivo de tanta demora é o pytest, ou está rodando algo no max do modelo"*.
  Medido nesta conversa: a suíte inteira levou 2379.61s (0:39:39) na 1ª vez e 517.74s (0:08:37) na 2ª, mesmo código;
  3 arquivos (102 testes) levaram 53888.63s (14:58:08), com a data virando no meio; o 1º `pytest` do
  `test_hook_entrada_utf8.py` travou mais de 2 min sem processo filho (morto; o mesmo arquivo depois: 1.62s) e um
  `pytest -k fecho` rodou enquanto ele estava travado. Causa não medida — item no `to-dolist.md`.
- **1ª suíte com 1 falha:** a linha **UI:** do molde dizia "Tailwind" e o `test_frases_chave_estao_nos_blocos` proíbe
  regra do kit repetida no molde; virou `Nível 1 (Jinja) ou Nível 2 (React + TS + Mantine)` e a suíte rodou de novo
  inteira: 1651 verdes.
- **Como o sono roda** (pergunta do owner): sem comando; o `memoria_tabela_em_dia.py` conta as conversas na abertura,
  com 10 ou mais o assistente oferece em 1 linha, o owner diz sim ou não; o roteiro e o fecho novo estão em
  `commands/memory.md` ("Uso interno: sono").
- **Achado ao conferir o upgrade:** o `/mss-spec:upgrade` nunca sobrescreve um `.claude/rules/frontend.md` que já
  existe no projeto (`commands/upgrade.md:71`) — os projetos que já o têm ficam com o texto antigo. Item no
  `to-dolist.md`.
- **Merge:** `feature/sobras-sono-da-memoria` na `main` com `--no-ff` (`859115c`), aprovado pelo owner; falta o push
  dele. Captura gravada na `docs/captura-sobras-sono` (nota `project_hook_le_entrada_em_utf8`, decisão, caso F-070).
