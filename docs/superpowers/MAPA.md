# Mapa de contexto — mss-spec

## Onde estamos
`feature/partida-em-dois-niveis` (worktree `.claude/worktrees/partida-em-dois-niveis`, saiu da `main` em `7948da0`) — **0.44.0 pronta na branch; merge é do owner**: a forma do MAPA e do INDEX vale em toda gravação, mesmo abaixo do teto (`fechada` sai do INDEX; item longo do Próximo passo vai pro `PROXIMO-PASSO.md`; com `CONEXOES.md`, Conexões só com os nomes). Simulado numa cópia do Whats: MAPA 5.981 → 2.254 B, INDEX 5.635 → 2.424 B, nenhuma linha perdida. `CLAUDE.md` fora (decisão do owner). A `feature/bug-e-duvida` (0.43.0) segue não integrada.

<!-- histórico do estado anterior -->
`chore/captura-regras-do-kit` (saiu da `main` em `9b51031`) — **0.42.0 integrada na `main`** (`9b51031`, 950 testes, push é do owner): as regras do kit vêm do plugin a cada janela (`hooks/regras_do_kit.py`, só em projeto com a marca `<!-- mss-spec:regras-do-kit -->`); o `CLAUDE.md` do projeto fica só com o projeto, com o `## Contexto` por extenso; regra por tipo de arquivo é lida antes de gravar (`hooks/regra_antes_de_gravar.py`); `/mss-spec:upgrade` migra pelo `templates/migrar_claude_md.py`, que confere tudo antes de gravar e não mexe no git. Captura desta sessão em `8254de9` + MAPA em `56b32b1` (nesta branch, **falta o merge**; nenhuma tarefa em "Em andamento" no INDEX); diário em `memory/sessions/2026-10-23-regras-do-kit-pelo-plugin.md`. Casos novos: F-040 e F-041, abertos.

## Próximo passo
**Owner:** merge da `feature/bug-e-duvida` (0.43.0) e depois da `feature/partida-em-dois-niveis` (0.44.0) na `main`, e `git push origin main`. **No Whats (janela de lá):** qualquer gravação no MAPA ou no INDEX já aplica a forma; pra aplicar de uma vez, `/mss-spec:mapa`.

<!-- histórico do próximo passo anterior -->
**Owner:** merge da `chore/captura-regras-do-kit` e `git push origin main`. **No Whats (janela de lá):** terminar o `/mss-spec:upgrade` (`--aplicar` + os comandos de commit que ele entregar; a prévia deu 20/18/3) e, numa janela nova, pedir um `.sql` novo — a 1ª tentativa tem que voltar com o texto da regra de banco (é a conferência ao vivo que falta do `regra_antes_de_gravar.py`); isso fecha o F-040 se o owner não repetir fato de infra. **Outros projetos:** `/mss-spec:upgrade` um por janela. **Kit:** pendências que podem esperar na spec `docs/specs/regras-do-kit-pelo-plugin.md` ("Pendências conhecidas"); o F-041 fecha quando uma execução longa por subagentes terminar sem reclamação de demora; seguem abertos F-033, F-035 e F-038; projeto novo sem homologação continua sendo o 1º uso real do caminho "homologação nova" do `/mss-spec:azure-ambiente`.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-27 (partida em dois níveis, 0.44.0) · regenerável com /mss-spec:mapa -->
