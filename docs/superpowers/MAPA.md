# Mapa de contexto — mss-spec

## Onde estamos
`feature/captura-de-memoria`, a partir da master — **em brainstorming/spec** (inspiração: avaliação do [claude-mem](https://github.com/thedotmack/claude-mem), integração completa rejeitada por bater nos pilares do kit; captura das ideias que cabem). Assunto: comando-prosa determinístico `/mss-spec:capturar` que, no fecho da feature/sessão, rascunha candidatos a memória + atualiza o "onde estamos/próximo passo" do MAPA (com OK do owner), para parar de depender de o assistente *lembrar*; + convenção `<private>` na memória; + hook `Stop`/`SessionEnd` **opcional/experimental** (só atalho — se não disparar, o comando cobre o fecho). Spec: `docs/superpowers/specs/2026-07-21-captura-de-memoria-design.md`.

## Próximo passo
Integrar (passo do owner): `/mss-spec:plano-teste` (regrava o baseline) → `/mss-spec:release` (gate) → `finishing` (merge/commit). Nada mais pendente no assunto.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-20 · regenerável com /mss-spec:mapa -->
