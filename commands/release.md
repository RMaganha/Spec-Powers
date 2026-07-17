---
description: Gate de pré-publicação MSIG — roda os checks aplicáveis (testes, versão, CHANGELOG, segurança, specs, convenções) e dá um veredito ✓/✗ (só reporta, não publica nem conserta)
argument-hint: ""
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Gate de **pré-publicação**: reúne num passo só o "antes de entregar" que hoje está espalhado e reporta **✓/✗**. **Só reporta** — não bumpa versão, não edita CHANGELOG, não faz merge/PR e não conserta nada; aponta o que falta pra você resolver. É o gate MSIG "está pronto pra sair?"; **vem ANTES** do `finishing-a-development-branch` do superpowers (que cuida de merge/PR) — quando o veredito ficar verde, aí sim você segue pro finishing.

Rode **só os checks que se aplicam** (detecte pelos arquivos presentes); check inaplicável é **pulado**, não vira ✗.

Checks:
1. **Testes 100% verde** (se há suíte — `tests/` ou `docs/superpowers/PLANO-TESTE.md`) — rode o comando do PLANO-TESTE **direto** (ex.: `python -m pytest -q`) e **cole a saída**. Menos de 100% verde → ✗ (é o check que mais pesa). Não regrave baseline aqui (isso é o `/mss-spec:plano-teste`, disparado por você).
2. **Versão coerente** (só se o projeto tem versão):
   - **Plugin** (`.claude-plugin/plugin.json`): `plugin.json.version` **igual** a `marketplace.json.version`, e o `CHANGELOG.md` tem uma entrada pra essa versão (ou uma seção "Não lançado" com conteúdo aguardando o bump). Divergência → ✗.
   - **Projeto com `pyproject.toml`/`package.json`**: reporte a versão atual; se houve mudança relevante e a versão não subiu, sinalize (não bumpe).
   - **Web app por branch** (deploy por `dev`/`main`, sem versão semântica): **pule** com a nota "versionamento por branch — sem bump semântico".
3. **CHANGELOG atualizado** (se existe `CHANGELOG.md`) — há linha/entrada pra mudança recente (seção "Não lançado" com conteúdo, ou entrada da versão atual)? Topo obviamente defasado (commits desde a última versão sem nenhuma linha) → ✗.
4. **Segurança revisada** (se a entrega **criou/alterou rota ou endpoint** — detecte por `routers/`/`main.py` no diff) — lembre de rodar `/mss-spec:seguranca` (ou revisar `docs/SEGURANCA.md`: authz por request, entrada validada, `AUTH_TOKEN_ATIVO`/Bearer nos endpoints de integração). Não faça a auditoria pesada aqui; só sinalize ✓/✗/pendente.
5. **Specs/docs coerentes** (se há `docs/specs/` ou `docs/superpowers/INDEX.md`) — a **spec viva** do assunto mexido reflete o que foi entregue (o "Estado atual" não mente) e o `INDEX.md` tem a linha com o **status certo** (`fechada` quando concluído)? Confira contra o diff da entrega e reporte.
6. **Convenções aderentes** (o "jeito da casa") — **aplique aqui o checklist do `/mss-spec:compliance`** (estrutura em camadas, `docs/decisoes.md`, `memory/MEMORY.md` versionada, `.gitignore` com as âncoras, front no padrão se tem UI) e reporte ✓/✗. É uma checagem estática de presença (não roda nada). O `/mss-spec:compliance` continua disponível **avulso** quando você quiser auditar convenção fora de um release. (Não tente *invocar* o comando — ele é `disable-model-invocation`; aplique o checklist dele direto.)
7. **Working tree** (se é repo git) — sem mudança relevante perdida (não-commitada) e **`.env`/segredo fora do stage** (`git status`); nunca ecoe valor de segredo, só sinalize o risco.

Saída: uma linha por check aplicável com **✓** ou **✗** (com o porquê no ✗) e um **veredito** final de uma linha (ex.: "pronto pra sair" / "3 pendências: bumpar versão · CHANGELOG · rodar seguranca"). Num ✗, aponte o próximo passo — sem executá-lo.
