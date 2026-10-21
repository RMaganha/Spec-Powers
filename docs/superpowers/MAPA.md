# Mapa de contexto — mss-spec

## Onde estamos
`main` — **0.41.0 integrada** (`3f71a8a`): o comando é **`/mss-spec:azure-ambiente`** (era `azure-prd`) e cria a homologação (se ainda não existe) e a produção espelho dela, pelo pipeline `<PROJETO>-INFRA`, com receita-base do kit, variáveis pelo `app_settings.py` e aprovação em produção. **MSS-UTILS em produção desde 2026-10-20**, o primeiro criado pelo comando. Captura da sessão na branch `chore/captura-azure-ambiente` (`7c58d7f`), **falta o merge**; diário em `memory/sessions/2026-10-21-azure-ambiente.md`. Casos: F-036, F-037 e F-039 fechados; F-038 aberto; F-033 reincidiu no chat do kit.

<!-- histórico do estado anterior -->
`main` — **0.40.0** do `/mss-spec:azure-prd` (`0adbecb`): identidade do pipeline no log, chamado pronto pra infra, senha do registro vinda do próprio registro, condução das etapas 3 a 6. Antes dela, 0.35.0 ("Fonte ou não sei" + `confere_citacoes.py`) e 0.36.0 (memória com gatilho de ação; rotas não pedidas voltam uma vez).

## Próximo passo
**Integrar a captura** (owner: merge e push da `chore/captura-azure-ambiente`). **Projeto novo sem homologação** ("Pipeline de deploy em HTML"): 1º uso real do caminho "homologação nova" do `/mss-spec:azure-ambiente`; se o pipeline parar por permissão, vai a seção 4 do chamado (`templates/azure-ambiente/permissoes-infra.md`), uma vez só. **No MSS-UTILS (janela de lá):** testar o sistema em produção (roteiro §10), fechar a `feature/azure-prd` na `main`, criar `CADASTROCORRETOR_CONEXAO_SQL=PRD` em produção; o pipeline de código de produção (`MSS-UTILS-PROD`) segue pendente. **Kit:** o F-033 reincidiu → reavaliar o item adiado "hook `Stop` medindo a resposta contra o pedido" (`INDEX.md`, "Descartado na partida que não cresce"); o F-038 fecha quando um projeto for do zero à produção sem reclamação de condução; **observar** o F-035 (`python hooks/_registro.py resumo`). **No Whats (janela de lá, não aqui):** as regras "Comando pra eu rodar = passo a passo", "Responda só o que eu pedi" e "Fonte ou não sei" no `CLAUDE.md` de lá (9.899 bytes — mover um bloco se passar de 10 KB).

<!-- histórico do próximo passo anterior -->
**Canário da 0.34.0** (pendência da outra sessão): no mesmo chat `/mss-spec:nova-feature canario-a` e depois `canario-b` — o 2º bloqueia; num chat novo passa. **Observar** o F-033 (resposta do tamanho do pedido) e o F-034 (memória que não chega na hora da ação) — reincidiu, vira mecanismo. **Regra "não alucinar"**: o owner vai trazer. **No Whats (janela de lá, não aqui):** as regras "Comando pra eu rodar = passo a passo" e "Responda só o que eu pedi" no `CLAUDE.md` de lá (está em 9.899 bytes — mover um bloco se passar de 10 KB).

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-09-25 (captura da janela afogada) · regenerável com /mss-spec:mapa -->
