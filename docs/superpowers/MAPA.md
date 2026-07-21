# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.10.1 integrada** (merge `--no-ff` da `feature/mapa-neural-abrir-md`; suíte **54 verde**). Entregue (F2.1 do mapa neural): clique num balão-folha `.md` abre o arquivo **renderizado em nova aba** (conteúdo dos `.md` embutido inline na geração via `coletar_docs` + renderizador markdown vanilla `mdToHtml`/`openDoc`; self-contained, `file://`, zero CDN). **`git push` pendente** (só quando o owner pedir). Spec (F2.1): `docs/superpowers/specs/2026-07-20-mapa-de-contexto-design.md`.

<!-- histórico do release anterior (v0.10.0) -->
`main` — **v0.10.0 integrada e publicada no GitHub** (branch `feature/captura-de-memoria` apagada; suíte **51 passed**). Entregue: modo **`capturar`** no `/mss-spec:memory` (2º modo, ao lado do `resgatar`) que destila a sessão em **decisões** (incl. as negativas) + **diário de sessão** datado/indexado (`memory/sessions/<data>-<assunto>.md` + `memory/DIARIO.md`, foco nos **pivôs**), roteando pras 3 camadas de memória, com `<private>`, OK do owner e delegação do MAPA ao `/mss-spec:mapa`; fecho do `nova-feature` passou a **delegar** ao `capturar`; hook `Stop`/`PreCompact` **opt-in** (off por padrão) só como rede. Integração do claude-mem **rejeitada** (serviço/firehose/vetorial bate nos pilares). Spec: `docs/superpowers/specs/2026-07-21-captura-de-memoria-design.md`.

## Próximo passo
**`git push` da `main` (v0.10.1)** quando o owner pedir. Opcional/backlog: atualizar o card do `mapa-neural` no `COMO-FUNCIONA.html` mencionando o clique-para-abrir (fora do gate; próxima janela pra não misturar assunto). Depois: aguardando próxima feature (`/mss-spec:nova-feature`). **Publicado no GitHub** (2026-07-21): remote `origin` = `https://github.com/RMaganha/Spec-Powers.git`; principal renomeada `master`→`main`; todas as branches subidas.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
