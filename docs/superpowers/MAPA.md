# Mapa de contexto — mss-spec

## Onde estamos
`chore/captura-regras-do-kit` (saiu da `main` em `9b51031`) — **0.42.0 integrada na `main`** (`9b51031`, 950 testes, push é do owner): as regras do kit vêm do plugin a cada janela (`hooks/regras_do_kit.py`, só em projeto com a marca `<!-- mss-spec:regras-do-kit -->`); o `CLAUDE.md` do projeto fica só com o projeto, com o `## Contexto` por extenso; regra por tipo de arquivo é lida antes de gravar (`hooks/regra_antes_de_gravar.py`); `/mss-spec:upgrade` migra pelo `templates/migrar_claude_md.py`, que confere tudo antes de gravar e não mexe no git. Captura desta sessão em `8254de9` + MAPA em `56b32b1` (nesta branch, **falta o merge**; nenhuma tarefa em "Em andamento" no INDEX); diário em `memory/sessions/2026-10-23-regras-do-kit-pelo-plugin.md`. Casos novos: F-040 e F-041, abertos.

<!-- histórico do estado anterior -->
`main` — **0.41.0** (`3f71a8a`): `/mss-spec:azure-ambiente` (era `azure-prd`) cria a homologação e a produção espelho pelo pipeline `<PROJETO>-INFRA`; MSS-UTILS em produção desde 2026-10-20. Captura em `chore/captura-azure-ambiente`, integrada em `3301af6`.

## Próximo passo
**Owner:** merge da `chore/captura-regras-do-kit` e `git push origin main`. **No Whats (janela de lá):** terminar o `/mss-spec:upgrade` (`--aplicar` + os comandos de commit que ele entregar; a prévia deu 20/18/3) e, numa janela nova, pedir um `.sql` novo — a 1ª tentativa tem que voltar com o texto da regra de banco (é a conferência ao vivo que falta do `regra_antes_de_gravar.py`); isso fecha o F-040 se o owner não repetir fato de infra. **Outros projetos:** `/mss-spec:upgrade` um por janela. **Kit:** pendências que podem esperar na spec `docs/specs/regras-do-kit-pelo-plugin.md` ("Pendências conhecidas"); o F-041 fecha quando uma execução longa por subagentes terminar sem reclamação de demora; seguem abertos F-033, F-035 e F-038; projeto novo sem homologação continua sendo o 1º uso real do caminho "homologação nova" do `/mss-spec:azure-ambiente`.

<!-- histórico do próximo passo anterior -->
**Integrar a captura do azure-ambiente** (feito em `3301af6`). **Projeto novo sem homologação** ("Pipeline de deploy em HTML") pelo `/mss-spec:azure-ambiente`. **No MSS-UTILS (janela de lá):** testar produção (roteiro §10), fechar a `feature/azure-prd`, criar `CADASTROCORRETOR_CONEXAO_SQL=PRD` em produção; pipeline `MSS-UTILS-PROD` pendente. **Kit:** F-033 reincidiu → reavaliar o hook `Stop` medindo a resposta; observar o F-035.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-10-23 (captura das regras do kit pelo plugin) · regenerável com /mss-spec:mapa -->
