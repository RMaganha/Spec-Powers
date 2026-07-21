# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.11.0 integrada e publicada no GitHub** (merges `--no-ff`; suíte **62 verde**; push até `1994719`). Entregue (mapa neural F2.2+F2.3): **datas nos balões** (mtime), **camada associativa leve** (memória↔memória por `[[links]]`; spec↔código por `## Arquivos tocados`; nunca inventada) que **só aparece no hover** — bojando à direita, setas ‹ ›, realce da caixa conectada — e **layout tidy-tree horizontal** (curvas cubicBezier, balões modernos, zero-sobreposição). Bônus: fix da tela branca (`})` a mais, parse-time) + guarda `node --check`; `COMO-FUNCIONA.html` em dia (card do mapa + seção "memória viva" com mapa+precedentes). Spec: `docs/superpowers/specs/2026-07-20-mapa-de-contexto-design.md`.

<!-- histórico do release anterior (v0.10.1) -->
`main` — **v0.10.1** (F2.1 do mapa neural): clique num balão-folha `.md` abre o arquivo **renderizado em nova aba** (`coletar_docs` + `mdToHtml`/`openDoc`; self-contained, zero CDN).

## Próximo passo
Aguardando próxima feature (`/mss-spec:nova-feature` — backlog aberto no `INDEX.md`). A v0.11.0 está **integrada e publicada** (origin `https://github.com/RMaganha/Spec-Powers.git`, `main`) e a **memória da sessão foi capturada** (diário + 2 memórias + "fora de escopo" do SOM). Nada pendente — só o commit da própria captura, ainda **local** (push a pedido).

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
