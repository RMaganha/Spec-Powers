# upgrade — sincroniza projeto com a evolução dos templates (design)

Data: 2026-07-16 · feature do próprio kit mss-spec.

## Estado atual (0.54.0)
O `/mss-spec:upgrade` trata **tudo numa rodada e numa conversa**, nesta ordem: **passe 1** migração do `CLAUDE.md` (só sem a marca `<!-- mss-spec:regras-do-kit -->`) → **passe 2** conversão do to-dolist e do fora de escopo (só com achado do `converter_to_dolist.py checar`; dois tempos, dois commits) → **passe 3** categorias 1-3 (sempre). A abertura é o `templates/upgrade_plano.py checar --proj <raiz>` (só lê): imprime `migração do CLAUDE.md ✓/⬜ · to-dolist ✓/⬜ · categorias ⬜`, os passes que se aplicam e a situação do git num bloco só (branch, principal `main`/`master`, remoto, modificados, não rastreados).

Git: trabalho pendente do owner em outra branch é **guardado uma vez** (`git stash push` dos modificados, com o OK dele; não rastreados ficam no lugar) e **nunca commitado**; **uma branch** `chore/upgrade-kit` a partir da principal atualizada; **um commit por passe** (é o commit que separa o `git diff` de cada passe); no fecho, com o OK do owner, merge na principal (o hook `git_publicacao.py` pede a aprovação), `git merge --ff-only <principal>` na branch em que ele estava (pra nenhuma janela nova acusar o `CLAUDE.md` antigo), `git stash pop` e **conferência colada** (`git branch --show-current` · `git log --oneline -5` · `git status --short` · `git stash list`) antes de dizer "pronto". Passe que sai com falha não para a rodada: fica pendente no relatório e os outros seguem. Projeto que reserva o git ao owner: mesmo roteiro, um comando por bloco, conferido por leitura. `--dry-run`: abertura + prévias de cada passe, sem arquivo e sem git. Push: nunca o assistente.

Fora de escopo: varrer `apps/*` na conversão (to-dolist linha 7) · mudar o `converter_to_dolist.py` · mudar o `doctor`.

## Objetivo
Comando `/mss-spec:upgrade` que traz um projeto existente pra versão atual do kit com o **mínimo de interação** — atualiza os arquivos de referência sozinho e **mescla** o `CLAUDE.md`/`AMBIENTE.md` sem perder o do owner; só conflito real pergunta.

## Problema
O kit evolui rápido (0.1→0.7 em duas semanas). Projetos feitos antes ficam pra trás. Na 0.7.0 isso já apareceu (o `/mss-spec:frontend` passou a re-sincronizar o `FRONTEND.md` a cada run). Falta generalizar pra todos os arquivos, **sem destruir a customização do projeto**.

## Critérios de aceite
- DADO um `docs/SEGURANCA.md` desatualizado, QUANDO rodo `/mss-spec:upgrade`, ENTÃO ele é atualizado pra versão do template, sem me perguntar.
- DADO uma regra nova no kit que falta no `CLAUDE.md` do projeto, QUANDO rodo o upgrade, ENTÃO a regra é ACRESCENTADA e o resto do meu `CLAUDE.md` fica intacto.
- DADO uma regra que diverge (kit diz A, projeto editou pra B), QUANDO rodo o upgrade, ENTÃO ele PERGUNTA qual fica (único caso que interage).
- DADO um `get_connection.py` (código) desatualizado, QUANDO rodo o upgrade, ENTÃO ele só mostra o diff e avisa — NÃO aplica sozinho.

## Design
Comando `commands/upgrade.md` (`disable-model-invocation`). Três categorias:
1. **Referência (só-do-kit):** SEGURANCA · ESTRUTURA · FRONTEND · Docker · gitignore → atualiza sozinho.
2. **`CLAUDE.md` + `AMBIENTE.md`:** mescla por seção/regra — acrescenta o que falta do kit, mantém o do owner, conflito → pergunta.
3. **Código (`get_connection.py`):** só avisa (diff), não aplica.

Não commita — deixa no working tree pro owner revisar via `git diff`.
**Limite:** sem a versão antiga do template, a mescla é por seção/regra (não 3-way); na dúvida, mantém o do owner.

## Modo `--dry-run` (preview)
`/mss-spec:upgrade --dry-run` mostra o que o upgrade **faria**, sem escrever nenhum arquivo (working tree intacto):
- **Categoria 1 (referência):** diff unificado (git-style) do que seria sobrescrito — é o passo hoje silencioso, o alvo da prevenção.
- **Categorias 2 e 3 (CLAUDE/AMBIENTE e código):** o mesmo relatório descritivo do upgrade normal (o que mesclaria · conflitos · código a revisar), sem diff linha-a-linha.

Ao fim, o relatório deixa explícito que foi só preview e diz como aplicar de verdade (`/mss-spec:upgrade` sem a flag). A flag é **aditiva**: sem ela, o upgrade aplica como sempre.

## Fora de escopo
Merge automático de código · rollback (o git já faz) · guardar histórico de versões de template · dry-run como padrão (segue opt-in via flag) · diff linha-a-linha da mescla do `CLAUDE.md`.

## Arquivos tocados
- `commands/upgrade.md` (comando + modo `--dry-run`)

## Histórico
- 2026-07-16 — criado: design do upgrade (aprovado no chat).
- 2026-07-20 — acrescentado o modo `--dry-run` (item 10): preview com diff da categoria 1 + relatório, sem escrever arquivo (motivo: prevenir o merge silencioso dos arquivos de referência que o upgrade sobrescreve sozinho).
- 2026-11-09 — **uma rodada, uma conversa** (0.54.0): os 3 passes na mesma conversa, uma branch `chore/upgrade-kit`, um commit por passe, stash único do trabalho pendente do owner, integração na principal + `--ff-only` de volta pra branch dele, conferência colada; abertura pelo `templates/upgrade_plano.py` (só lê, testado) (motivo: no Transportes V2, 2026-11-09, o desenho "cada passe termina sozinho e exige árvore limpa" virou 3 conversas paradas na mesma pergunta sobre 3 arquivos modificados sem commit na `fix/atm-virada-outubro`; na 1ª o assistente ofereceu commitar o trabalho do owner).
