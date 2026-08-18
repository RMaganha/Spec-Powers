---
paths:
  - "**/*.html"
  - "**/*.css"
  - "**/*.jsx"
  - "**/*.tsx"
---

# Front-end deste projeto

- **Tailwind CSS** + `@tailwindcss/typography`. **JS e CSS em arquivos próprios**, nunca inline no
  HTML — a exceção é documento standalone que precisa abrir sem servidor.
- Tela **densa** (grid com sort/filtro, dashboard, muitos campos, date picker) → **React + TypeScript
  + Mantine**, instalado por `/mss-spec:frontend`. Página simples → Jinja + Tailwind.
- **HTML com JS inline** (gerador que escreve script na página): valide a **sintaxe** com
  `node --check` no teste. Assert de substring passa com JS quebrado — foi assim que nasceu a tela
  branca (caso **F-007** de `docs/EVALS.md`).
- Nunca dirigir o browser ao vivo pra validar tela: teste determinístico faz a checagem, smoke visual
  é do humano.

Memória de origem: `memory/feedback_frontend_tailwind_arquivos_separados.md` ·
`memory/feedback_testar_js_gerado_node_check.md` · `memory/feedback_validacao_ui_deterministica.md`
