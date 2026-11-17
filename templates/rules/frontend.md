---
paths:
  - "**/*.html"
  - "**/*.css"
  - "**/*.jsx"
  - "**/*.tsx"
---

# Front-end deste projeto

- **Nível conforme o projeto** (linha **UI:** do `CLAUDE.md`; níveis em `docs/FRONTEND.md`): Nível 1 =
  Jinja + **Tailwind CSS** + `@tailwindcss/typography`; sobe pro Nível 2 = **React + TypeScript +
  Mantine** (instalado por `/mss-spec:frontend`) quando uma tela pede (grid com sort/filtro, dashboard,
  muitos campos, date picker). **Nunca os dois no mesmo app.**
- **JS e CSS em arquivos próprios** nos dois níveis, nunca inline no HTML — a exceção é documento
  standalone que precisa abrir sem servidor.
- **HTML com JS inline** (gerador que escreve script na página): valide a **sintaxe** com
  `node --check` no teste. Assert de substring passa com JS quebrado — foi assim que nasceu a tela
  branca (caso **F-007** de `docs/EVALS.md`).
- Nunca dirigir o browser ao vivo pra validar tela: teste determinístico faz a checagem, smoke visual
  é do humano.

Memória de origem: `memory/feedback_frontend_tailwind_arquivos_separados.md` ·
`memory/feedback_testar_js_gerado_node_check.md` · `memory/feedback_validacao_ui_deterministica.md`
