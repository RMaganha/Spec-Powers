# Mapa de contexto — mss-spec

## Onde estamos
`feature/analise-projeto-existente` (da `main`@0.13.2) — **v0.14.0**: `/mss-spec:analise`, a porta de entrada do **brownfield**. Lê o repo em 2 fases (inventário/manifests/docs pré-existentes → leitura focada em entrypoint, rotas, `.sql`, config, UI e pipeline **RAG/pgvector**; resto por amostragem, declarando o que ficou de fora) e destila no dossiê `docs/ARQUITETURA.md` + `CLAUDE.md`/`MAPA.md`/`INDEX.md` (assunto = linha `existente`) e specs só com evidência lida. **Não-destrutivo por regra**: nunca toca em infra, código ou **UI própria** — o pré-existente é registrado na lista "não nasceu do kit", que passou a **frear a categoria 1 do `upgrade`** (que sobrescrevia `docker-compose`/`Dockerfile` sozinha). Suíte **72 verde**; bump 0.13.2→0.14.0 nos 2 manifestos + CHANGELOG. Dois commits na branch: `c1938f4` (feature) + `a86022b` (captura de memória — decisão transversal, 2 aprendizados duráveis, diário). Spec: `docs/superpowers/specs/2026-07-28-analise-projeto-existente-design.md`.

<!-- histórico do estado anterior -->
`fix/mapa-neural-overlap-drag-doubleclick` (da `main`@0.12.0) — **mapa neural v0.12.1**: correções vistas rodando em outro projeto (MSS-SSC) — balões de 2-3 linhas **não sobrepõem mais** (faixa vertical proporcional à altura real, `boxH`), **caixa arrastável de novo** (move só ela; offset preservado ao expandir), e **abrir `.md` = duplo clique** (1 clique só expande). Suíte **63 verde**; bump 0.12.0→0.12.1 nos 2 manifestos + CHANGELOG. Spec: `docs/superpowers/specs/2026-07-20-mapa-de-contexto-design.md`.

<!-- histórico do estado anterior -->
`main` — **v0.12.0** (doctor: check "versão do kit — instalada × publicada no remoto"; `git fetch` no clone, semver, só reporta ✓/⚠/ℹ, degrada gracioso). Spec: `docs/superpowers/specs/2026-07-21-doctor-check-versao-remoto-design.md`.

`main` — **v0.11.0 integrada e publicada no GitHub** (merges `--no-ff`; suíte **62 verde**; push até `1994719`). Entregue (mapa neural F2.2+F2.3): **datas nos balões** (mtime), **camada associativa leve** (memória↔memória por `[[links]]`; spec↔código por `## Arquivos tocados`; nunca inventada) que **só aparece no hover** — bojando à direita, setas ‹ ›, realce da caixa conectada — e **layout tidy-tree horizontal** (curvas cubicBezier, balões modernos, zero-sobreposição). Bônus: fix da tela branca (`})` a mais, parse-time) + guarda `node --check`; `COMO-FUNCIONA.html` em dia (card do mapa + seção "memória viva" com mapa+precedentes). Spec: `docs/superpowers/specs/2026-07-20-mapa-de-contexto-design.md`.

<!-- histórico do release anterior (v0.10.1) -->
`main` — **v0.10.1** (F2.1 do mapa neural): clique num balão-folha `.md` abre o arquivo **renderizado em nova aba** (`coletar_docs` + `mdToHtml`/`openDoc`; self-contained, zero CDN).

## Próximo passo
**Integrar** a v0.14.0: revisar o diff, merge `--no-ff` de `feature/analise-projeto-existente` na `main` e — quando o owner pedir — `git push` (**confirmado por `git fetch` em 2026-07-28**: a `main` tem **7 commits não publicados** — 0.13.0/0.13.1/0.13.2 + chore de memória — e o `origin` não tem nada a mais; sem `git push`, os outros projetos não pegam o `analise` nem com `claude plugin marketplace update`). Primeiro uso real previsto: rodar o `/mss-spec:analise` no projeto de **RAG/pgvector** do owner. No `to-dolist`, aberto: perguntar na constituição se o projeto segue a **arquitetura de rede MSIG** ou tem **arquitetura própria** (hoje o kit assume MSIG).

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
