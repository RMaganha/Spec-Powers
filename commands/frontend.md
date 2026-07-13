---
description: Instala o front moderno MSIG (React + TypeScript + Mantine, tema MSIG) para telas densas — scaffold Vite pronto, guia ilha × rota SPA
argument-hint: "[tela/assunto, ex.: grid de apólice]"
disable-model-invocation: true
---

Você vai instalar o **front moderno** (Nível 2 do `docs/FRONTEND.md`: React + TypeScript + Mantine) neste projeto. É para **telas densas** (grids, muitos campos, date pickers) — telas simples continuam no Nível 1 (Jinja + Tailwind). Mostre o que vai copiar e **confirme antes de gravar**. Não escreva a tela agora; primeiro deixe a base de pé.

1. **Cheque o encaixe:** a tela em questão (**$ARGUMENTS**) justifica o Nível 2 (componentes que doeria fazer à mão: DataTable, DatePicker, Select com busca, form complexo)? Se for simples, oriente ficar no Nível 1 (+ HTMX/Alpine) e pare. A decisão é por-tela (ver a tabela em `docs/FRONTEND.md`).
2. **Copie o scaffold** de `${CLAUDE_PLUGIN_ROOT}/templates/frontend/` para `frontend/` no projeto (package.json, vite.config.ts, tsconfig.json, index.html, src/main.tsx, src/theme.ts, src/components/, README.md). O tema MSIG (`src/theme.ts`) já vem com `brand`/`navy`.
3. **Garanta o `.gitignore`:** `node_modules/` ignorado; o **bundle compilado** (`static/js/frontend.js`/`.css`) é **versionado** (igual ao `app.css` do Tailwind). Se faltar, ajuste (base em `${CLAUDE_PLUGIN_ROOT}/templates/gitignore`).
4. **Decida ilha × rota SPA** e explique ao owner (regra no `docs/FRONTEND.md`): um pedaço de uma página → **ilha** (`<div id="mantine-root">` + bundle); tela inteira → **rota SPA** (o FastAPI serve a casca). Não espalhe várias ilhas na mesma tela.
5. **Endpoint de dados:** o React consome **JSON** do FastAPI — crie/aponte o endpoint dedicado (a camada Python vira API/BFF). Nunca fazer o React ler HTML renderizado.
6. **Explique o build e o atrito** (ver `docs/AMBIENTE.md` §2 e `frontend/README.md`): `npm install`/`npm run build` → bundle em `static/js/`; atrás do FortiGate, `npm install` pede registry/proxy ou build numa rede boa; no Docker, **multi-stage** (Node só builda; runtime Python só copia o `static/js/` pronto) ou bundle versionado no host.
7. NÃO misture Tailwind e Mantine no mesmo app React — onde a Mantine entra, o Tailwind sai (ela já traz tema/espaçamento/dark mode).

Feito o scaffold, a tela em si vem depois com `/mss-spec:nova-feature` (spec → OK → plano → TDD → verificação).
