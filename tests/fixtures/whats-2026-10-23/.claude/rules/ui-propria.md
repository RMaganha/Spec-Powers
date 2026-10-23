---
paths:
  - "web/**"
  - "**/*.html"
---

# UI própria e intocável

<!-- Movido do CLAUDE.md em 2026-09-23 (teto de 10 KB; F-029/F-030 do kit): texto VERBATIM. A regra continua valendo — o CLAUDE.md mantém a frase-chave e aponta pra cá. -->

- **UI:** web, **própria e intocável** — `chat.html` e `chat_v2.html` (HTML único, JS vanilla, CSS autoral, Tailwind por CDN + `marked` + `DOMPurify`). O design system do kit (`docs/FRONTEND.md`) **não se aplica** e não foi instalado. Decisão do owner.

3. **A UI deste projeto é PRÓPRIA e INTOCÁVEL** (decisão do owner, 2026-07-28). **A UI do sistema é uma só: `web/chat_v2.html`, servida em `/v2`** — é a URL real de uso. Layout, CSS e JS feitos à mão, com changelog dentro do próprio arquivo. **Não** aplicar o design system do kit (Tailwind buildado, React+Mantine, `docs/FRONTEND.md` — que nem foi instalado aqui), **não** refatorar para separar JS/CSS em pastas, **não** "modernizar" por iniciativa própria. Mexer nela só com pedido explícito meu e no padrão que já existe lá. A **v1** (`chat.html`, servida em `/`) era obsoleta e foi **arquivada em `backup/v1/`**; a rota `/` hoje só redireciona para `/v2`. Não reviva a v1 nem a use como referência de padrão. Se algum dia nascer uma **tela nova**, converse comigo antes: aí o padrão do kit volta a ser candidato. Exceção que continua valendo: **documentação/relatório** standalone via `/mss-spec:documentacao`.
