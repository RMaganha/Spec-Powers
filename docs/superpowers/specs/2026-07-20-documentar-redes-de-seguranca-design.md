# documentar redes de segurança — design

Data: 2026-07-20 · feature do próprio kit mss-spec (branch `feature/documentar-redes-de-seguranca`).

## Objetivo
Tornar **explícitas na documentação** as três redes de segurança que **já existem** no kit — auto-teste, git-como-rollback e CHANGELOG — fechando os falsos-negativos da análise externa e o **item 11** do backlog.

## Contexto (o falso-negativo)
A análise em `docs/analise/Claude.txt` marcou como 🔴 lacuna o item 21 (*"não há menção a como o kit é testado"*) e o 22 (*rollback/desinstalação*), e ficou em dúvida sobre o CHANGELOG. Os três **existem** — só não estavam visíveis na doc que o analista leu (`COMO-FUNCIONA.html`):
- **auto-teste** — `tests/test_smoke_kit.py` + `test_logging_template.py`; `pytest tests/ -q` confere que todo caminho citado em commands/skills existe. Estava só no `LEIA-ME` (§Autoteste), ausente no HTML.
- **git-como-rollback (item 11)** — como `kickoff`/`upgrade` só mexem em arquivos versionados sob working tree limpo, `git restore`/descartar a branch já desfaz; sem comando dedicado (YAGNI). Não estava documentado em lugar nenhum.
- **CHANGELOG** — `CHANGELOG.md` versionado na raiz; é a rede contra *drift* entre cópias. Citado de passagem, sem enquadramento de rede.

## Estado atual
As três redes estão explícitas na doc de distribuição:
- **`docs/COMO-FUNCIONA.html`** ganha a seção **"Redes de segurança"** (`id="redes"`, nº 09; roadmap vira 10) que nomeia as três: o kit se testa (`pytest tests/`), o **git é o rollback** (working tree limpo → `git restore`/descartar branch; sem comando dedicado, YAGNI) e o **CHANGELOG** como rede contra *drift* entre cópias. Entrada correspondente no menu lateral.
- **`commands/upgrade.md`** e **`commands/kickoff.md`** trazem 1-2 linhas "o git é o rollback" (`git restore`/descartar branch desfaz; sem rollback dedicado).
- **`docs/LEIA-ME.md`** reforça a rede que faltava (rollback via git) junto às que já cita (§Autoteste + CHANGELOG).
- **`tests/test_smoke_kit.py`** ganha `test_redes_de_seguranca_documentadas()`, que falha se HTML/commands/LEIA-ME deixarem de citar as três redes.

## Critérios de aceite
1. DADO um leitor no `COMO-FUNCIONA.html`, QUANDO procura como o kit é testado, ENTÃO encontra menção explícita ao auto-teste (`pytest tests/`).
2. DADO um leitor querendo desfazer um `kickoff`/`upgrade`, QUANDO consulta a doc, ENTÃO lê que "o git é o rollback" (working tree limpo → `git restore`/descartar branch; sem comando dedicado) — no **HTML** e em `commands/upgrade.md` + `commands/kickoff.md`.
3. DADO um leitor procurando o histórico, QUANDO lê o HTML, ENTÃO entende que o `CHANGELOG.md` versionado é a rede contra *drift* entre cópias.
4. DADO o `LEIA-ME.md`, QUANDO leio, ENTÃO as três redes aparecem (a de rollback é a nova).
5. DADO a suíte, QUANDO rodo `pytest tests/ -q`, ENTÃO `test_redes_de_seguranca_documentadas()` passa.
6. DADO o `docs/superpowers/INDEX.md`, QUANDO leio o item 11, ENTÃO está marcado como fechado.

## Design
- **Só doc + teste de wiring** — nenhuma mudança de comportamento; segue o padrão dos outros wirings do kit (afirma strings de convenção nos arquivos certos).
- **Nada de comando de rollback dedicado** — a mensagem é justamente que o git já resolve (YAGNI). Documentar ≠ construir.

## Fora de escopo
Comando de rollback/desinstalação dedicado (YAGNI); CI com artefatos (item 12); distribuição por git interno (itens 15/16); alterar os testes existentes ou os fluxos.

## Arquivos tocados
- `docs/COMO-FUNCIONA.html` — nova seção "Redes de segurança" + item no menu + renumeração do roadmap
- `commands/upgrade.md` — 1-2 linhas "o git é o rollback"
- `commands/kickoff.md` — 1-2 linhas "o git é o rollback"
- `docs/LEIA-ME.md` — reforço da rede de rollback
- `tests/test_smoke_kit.py` — novo `test_redes_de_seguranca_documentadas()`
- `docs/superpowers/INDEX.md` — item 11 → fechado + 1 linha da tarefa

## Histórico
- 2026-07-20 — criado: design da documentação das redes de segurança já existentes (auto-teste, git-rollback [item 11], changelog), aprovado no chat.
